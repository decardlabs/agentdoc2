# 实验 3：自动化工单处理机器人

## 实验目标

掌握多步骤工作流编排与异常处理。

## 实验内容

Agent 接收 CSV 格式的工单数据，自动分类 → 统计分析 → 生成报告，并处理异常数据。

## 运行方式

```bash
pip install openai pandas langgraph
python main.py
```

## 核心概念

- 状态机/工作流编排（LangGraph）
- 代码解释器集成
- 异常恢复机制
