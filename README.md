# Jev Starter

一个可视化的 Jev 控制台，帮你在浏览器里配好 Noul / Choice / Score 问题，试跑看效果，然后一键导出成 Python / JavaScript / cURL 代码，直接用到你自己的项目里。

**不需要写代码，也能参与这个项目。** 往下看 ↓

---

## 🤝 三种参与方式（不需要写代码）

### 1. 分享一个 Example（最推荐）

你只要在控制台里配好一组问题、跑通、觉得有价值，就能把它变成别人的起点。

**流程：**

1. 打开控制台，配好你的问题（Noul / Choice / Score）
2. 点「提交请求」确认结果符合预期
3. 点「导出代码 → 导出为 Example → 填写基本信息后 → 下载JSON」获得一个完整的example.json
4. 到 GitHub 提一个 Pull Request，把 JSON 文件放进 `examples/` 目录

**命名建议：** 用场景命名+作者名，比如 `chat-emotion-YanfLIZi56.json`、`resume-screening-YanfLIZi56.json`。

**不会用 Git？** 在 [Issues](../../issues/new) 里贴出你的 JSON，并说明这个示例解决什么问题，维护者会帮你加进去。

---

### 2. 报告一个问题

用的时候遇到 bug、界面错位、导出格式不对、结果不符合预期？

👉 [提一个 Issue](../../issues/new)，写清楚：
- 你做了什么操作
- 期望看到什么
- 实际看到了什么（最好附截图或错误日志）

---

### 3. 提一个功能需求

想要某个新功能？比如「支持批量导入多个 JSON」「加一个 XX 场景的模板」「接入 XX 后端」？

👉 到 [Issues](../../issues/new) 里描述你的使用场景和期望，不需要写代码，只需要说清楚“你想解决什么问题”。

---

## 🚀 快速开始

### 1. 启动后端

```shell
cd backend
pip install -r requirements.txt
python main.py
```

### 2. 启动前端

```shell
cd frontend
npm install
npm run dev
```

打开 `http://localhost:5173`，填入你的 TypeSafe API Key 即可开始。

> 没有 API Key？到 [typesafe.ai](https://typesafe.ai) 注册即可获取。

---

## 📖 怎么用

1. 在左侧配置你的问题（Noul / Choice / Score）
2. 填入 state（可选，留空则模型仅根据 instructions 独立作答）
3. 点「提交请求」看结果
4. 满意后点「导出代码」，选择 Python / JavaScript / cURL / JSON，复制代码到你的项目
5. 配好的配置会自动存到浏览器本地，下次打开还在

---

## 📂 看看别人的配置

`examples/` 目录里是社区贡献的配置，导入控制台就能直接用：

| 文件                                                          | 场景 | 类型组合                           |
|-------------------------------------------------------------|---|--------------------------------|
| [`chat-emotion.json`](./examples/chat-emotion.json)         | 聊天情绪分析 | Choice + Noul + Choice         |
| [`resume-screening.json`](./examples/resume-screening.json) | 简历初筛 | Score + Choice + Choice + Noul |
| [`overall-qualiity.json`](./examples/rag-relevance.json)    | RAG 检索相关性评估 | Score × n                      |

**怎么用：** 打开控制台 → 点「导入配置」→ 选择 JSON 文件（或直接粘贴内容）→ 加载完成。

---

## 🧩 关于 Jev

Jev 是 TypeSafe AI 推出的决策模型。它**不生成任何文字**，只输出类型化的决策结果（Choice / Score / Noul）以及带校准的概率。

如果你需要：
- 分类、路由、判断（用 **Choice**）
- 打分、排序、评估（用 **Score**）
- 是/否、真/假、风险高低（用 **Noul**）

Jev 比传统 LLM 更快、更便宜、更稳定。这个控制台就是让你在浏览器里把这些配置试出来、导出去。

---

## 📄 License

MIT