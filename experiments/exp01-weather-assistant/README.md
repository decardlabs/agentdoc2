# 实验 1：基础工具调用助手（天气助手）

## 实验目标

跑通第一个 Agent Demo，理解 Tool Calling 的完整链路。

## 实验内容

Agent 能判断何时调用天气 API，何时直接回答，覆盖两类场景。

## 运行方式

```bash
export DEEPSEEK_API_KEY="sk-..."
python main.py
```

## 评估

运行 `python main.py eval` 运行 10 个自动化测试用例。

## 学习要点

- Tool Schema 定义
- tool_choice 策略（auto / required / 指定工具）
- 一轮完整的 Tool Calling 循环
