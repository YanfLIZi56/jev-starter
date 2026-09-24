"""
Jev 结构化问答 API
依赖安装：
    pip install fastapi uvicorn typesafe-sdk
"""
import json
import time
import traceback
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typesafe_sdk import Choice, Noul, Score, TypeSafeClient, TypeSafeAPIError

MODEL_NAME = "jev-latest"
EXAMPLES_DIR = Path(__file__).parent.parent / "examples"


# ============================================================
# 请求 / 响应模型
# ============================================================

class QuestionConfig(BaseModel):
    """单个问题的配置。前端自由编写。"""

    name: str = Field(..., min_length=1, max_length=64, description="问题名称，须唯一")
    type: str = Field(..., pattern="^(noul|choice|score)$", description="问题类型")
    instructions: str = Field(..., min_length=1, description="给模型的指令")

    # choice：键=标签，值=描述
    criteria_map: Optional[dict[str, str]] = Field(
        default=None, description="choice 类型的 criteria"
    )
    # score：有序的层级列表，从低到高
    criteria_list: Optional[list[str]] = Field(
        default=None, description="score 类型的 criteria"
    )


class AskRequest(BaseModel):
    api_key: str = Field(..., min_length=1, description="TypeSafe API Key")
    state: Optional[str] = Field(default=None, description="被评估的上下文，选填")
    questions: list[QuestionConfig] = Field(..., min_length=1, max_length=32)


class AnswerItem(BaseModel):
    """单个问题的答案，统一结构。"""

    name: str
    type: str
    instructions: str

    answer_label: Optional[str] = None  # choice 选中标签 / score 命中层级文本
    answer_description: Optional[str] = None  # choice 选中标签对应的描述
    answer_value: Optional[float] = None  # noul 概率 / score 数值
    confidence: Optional[float] = None
    probabilities: Optional[dict[str, float]] = None
    legend: Optional[dict[str, str]] = None  # score 的层级映射


class AskResponse(BaseModel):
    state: Optional[str]
    model: str
    answers: list[AnswerItem]
    latency_ms: float
    usage: Optional[dict[str, Any]] = None


class ExampleItem(BaseModel):
    """单个 example 的完整数据。"""

    filename: str
    name: str
    description: str = ""
    author: str = ""
    config: dict
    cases: list = []


class ExampleListResponse(BaseModel):
    examples: list[ExampleItem]


# ============================================================
# 工具函数
# ============================================================

def build_questions(configs: list[QuestionConfig]) -> dict:
    """将用户配置转换为 SDK 的 questions 字典，并做严格校验。"""
    questions: dict = {}
    seen: set[str] = set()

    for cfg in configs:
        if cfg.name in seen:
            raise HTTPException(422, detail=f"问题名称重复：{cfg.name}")
        seen.add(cfg.name)

        if cfg.type == "noul":
            questions[cfg.name] = Noul(instructions=cfg.instructions)

        elif cfg.type == "choice":
            cm = {k.strip(): v.strip() for k, v in (cfg.criteria_map or {}).items() if k.strip()}
            if len(cm) < 2:
                raise HTTPException(
                    422, detail=f"choice 问题「{cfg.name}」至少需要 2 个选项。"
                )
            questions[cfg.name] = Choice(instructions=cfg.instructions, criteria=cm)

        elif cfg.type == "score":
            cl = [s.strip() for s in (cfg.criteria_list or []) if s.strip()]
            if len(cl) < 2:
                raise HTTPException(
                    422, detail=f"score 问题「{cfg.name}」至少需要 2 个层级。"
                )
            questions[cfg.name] = Score(instructions=cfg.instructions, criteria=cl)

    return questions


def format_answer(cfg: QuestionConfig, raw: Any) -> AnswerItem:
    """把 SDK 的答案对象归一化为 AnswerItem。"""
    item = AnswerItem(name=cfg.name, type=cfg.type, instructions=cfg.instructions)

    if cfg.type == "noul":
        item.answer_value = round(float(raw.noul), 4)

    elif cfg.type == "choice":
        item.answer_label = raw.choice
        item.answer_description = (cfg.criteria_map or {}).get(raw.choice)
        item.confidence = round(float(raw.confidence), 4)
        if getattr(raw, "probabilities", None):
            item.probabilities = {str(k): round(float(v), 4) for k, v in raw.probabilities.items()}

    elif cfg.type == "score":
        score = float(raw.score)
        item.answer_value = round(score, 4)
        item.confidence = round(float(raw.confidence), 4)

        legend = getattr(raw, "legend", None)
        if legend:
            item.legend = {str(k): str(v) for k, v in legend.items()}
            # 用最近邻匹配层级文本
            try:
                idx = int(round(score))
                item.answer_label = item.legend.get(str(idx))
            except Exception:
                pass

        if getattr(raw, "probabilities", None):
            item.probabilities = {str(k): round(float(v), 4) for k, v in raw.probabilities.items()}

    return item


def extract_usage(response: Any) -> Optional[dict]:
    u = getattr(response, "usage", None)
    if not u:
        return None
    if hasattr(u, "model_dump"):
        return u.model_dump()
    if hasattr(u, "dict"):
        return u.dict()
    return {k: getattr(u, k, None) for k in ("input_tokens", "output_tokens")}


def load_examples() -> list[ExampleItem]:
    """扫描 examples 目录，返回所有合法的 example。"""
    if not EXAMPLES_DIR.exists():
        return []

    items: list[ExampleItem] = []
    for f in sorted(EXAMPLES_DIR.glob("*.json")):
        if f.name.startswith("_"):
            continue
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"[examples] 跳过 {f.name}: JSON 解析失败 - {e}")
            continue

        name = data.get("name")
        config = data.get("config")
        if not name or not isinstance(config, dict) or "questions" not in config:
            print(f"[examples] 跳过 {f.name}: 缺少 name 或 config.questions")
            continue

        items.append(
            ExampleItem(
                filename=f.name,
                name=str(name),
                description=str(data.get("description") or ""),
                author=str(data.get("author") or ""),
                config=config,
                cases=data.get("cases") or [],
            )
        )
    return items


# ============================================================
# FastAPI 应用
# ============================================================

app = FastAPI(
    title="Jev 结构化问答 API",
    description="基于 TypeSafe Jev 的多问题类型化决策接口。",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境请改为具体域名
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"service": "Jev 结构化问答 API", "docs": "/docs"}


@app.get("/api/examples", response_model=ExampleListResponse)
def list_examples():
    """返回 examples 目录下的所有示例配置。"""
    return ExampleListResponse(examples=load_examples())


@app.post("/api/ask", response_model=AskResponse)
def ask(req: AskRequest):
    """核心接口：接收用户配置，调用 Jev，返回结构化答案。"""

    global response
    questions = build_questions(req.questions)
    client = TypeSafeClient(api_key=req.api_key)

    start = time.perf_counter()
    try:
        kwargs: dict[str, Any] = {"model": MODEL_NAME, "questions": questions, "state": ""}
        if req.state and req.state.strip():
            kwargs["state"] = req.state.strip()
        response = client.system_one(**kwargs)
    except TypeSafeAPIError as error:
        print(error.status, error.request_id)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(502, detail=f"Jev API 调用失败：{e}")
    latency_ms = (time.perf_counter() - start) * 1000

    answers: list[AnswerItem] = []
    for cfg in req.questions:
        raw = response.answers.get(cfg.name)
        if raw is None:
            answers.append(AnswerItem(
                name=cfg.name, type=cfg.type, instructions=cfg.instructions
            ))
        else:
            answers.append(format_answer(cfg, raw))

    return AskResponse(
        state=req.state,
        model=MODEL_NAME,
        answers=answers,
        latency_ms=round(latency_ms, 2),
        usage=extract_usage(response),
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)