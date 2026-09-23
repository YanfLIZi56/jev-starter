# Jev Starter

一个可视化的 Jev 控制台，帮你在浏览器里配好 Noul / Choice / Score 问题，
试跑看效果，然后一键导出成 Python / JavaScript / cURL 代码，直接用到你自己的项目里。

也可以到 `examples/` 目录中看看别人的一些案例

## 快速开始

### 启动后端
``` shell
cd backend
pip install fastapi uvicorn typesafe-sdk
python main.py
```

### 启动前端
``` shell
cd frontend
npm install
npm run dev
```
[对方] 你是不是忘了今天是什么日子
[自己] 记得记得 我想想
[对方] 你最好是
[自己] 是你的生日吗?
[对方] 对,你说的都对,你说确定吗?

打开 http://localhost:5173，填入你的 TypeSafe API Key 即可开始。

## 怎么用

1. 在左侧配置你的问题（Noul / Choice / Score）
2. 填入 state（可选）
3. 点"提交请求"看结果
4. 满意后点"导出"，选择目标格式，复制代码到你的项目

## 贡献示例

用这个控制台配出有价值的场景后，点"导出 JSON"，把配置文件提交到 `examples/` 目录。
让别人看到 Jev 能怎么用。