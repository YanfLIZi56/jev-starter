# 如何贡献
你只要在控制台里配好一组问题、跑通、觉得有价值，就能把它变成别人的起点。

## 提交新的示例配置
1. Fork 本仓库
2. 在控制台制作好自己的问题配置
3. 点「导出代码 → 导出为 Example → 填写基本信息后 → 下载JSON」获得一个完整的example.json
4. 到 GitHub 提一个 Pull Request，把 JSON 文件放进 examples/ 目录

## 格式要求
- 用场景命名+作者名，比如 chat-emotion-YanfLIZi56.json、resume-screening-YanfLIZi56.json。
- 必须包含 `questions` 字段
- 建议在 state 中留占位符提示

**不会用 Git？** 在 Issues 里贴出你的 JSON，并说明这个示例解决什么问题，维护者会帮你加进去。