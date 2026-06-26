# AI Agent 智能体研发学习项目

> 从零开始，逐步深入。四个阶段，五个实验，六个月掌握 AI Agent 研发。

## 项目结构

```
AI-Agent-Learning-Project/
├── README.md                        ← 项目总览与学习计划（你在这里）
├── docs/                            ← 学习文档（分阶段）
│   ├── phase1-llm-basics/           ← 阶段一：LLM 调用与 Agent 核心范式
│   ├── phase2-mcp-rag/              ← 阶段二：MCP 协议与 RAG
│   ├── phase3-workflow/             ← 阶段三：工作流编排与工具集成
│   └── phase4-production/           ← 阶段四：多 Agent 协作与生产化
├── experiments/                     ← 实验代码（由浅入深）
│   ├── exp01-weather-assistant/     ← 实验 1：基础工具调用助手
│   ├── exp02-doc-qa-eval/           ← 实验 2：单文档问答 + 评估
│   ├── exp03-ticket-processor/      ← 实验 3：自动化工单处理
│   ├── exp04-multi-agent/           ← 实验 4：多 Agent 客服对照
│   └── exp05-quality-monitor/       ← 实验 5：质量监控与退化检测
└── scripts/                         ← 工具脚本
```

## 学习计划（业余时间，每周 10-15 小时）

| 阶段 | 内容 | 预计时长 | 产物 |
|------|------|---------|------|
| 一 | LLM SDK 直调 → Function Calling → Structured Output → 手写 ReAct | 4-5 周 | 手写 ReAct Agent 脚手架 |
| 二 | MCP 协议 → RAG 管道 → 评估体系 → Agentic RAG | 5-6 周 | MCP Server 模板 + 评估脚本 |
| 三 | LangGraph 工作流 → 代码解释器 → 异常处理 | 5-6 周 | 可恢复工作流引擎 |
| 四 | 多 Agent 协作 → 可观测性 → Guardrails | 6-8 周 | 对照实验报告 + 监控系统 |

## 五实验对照表

| # | 实验 | 核心概念 | 难度 | 前置依赖 |
|---|------|---------|------|---------|
| 1 | 天气助手 | ReAct + Tool Calling | ⭐ | Python 基础 |
| 2 | 文档问答 + 评估 | RAG + LLM-as-Judge | ⭐⭐ | 实验 1 |
| 3 | 工单处理 | LangGraph + 异常处理 | ⭐⭐⭐ | 实验 1 |
| 4 | 多 Agent 客服 | 多 Agent 协作 + 对照实验 | ⭐⭐⭐⭐ | 实验 2-3 |
| 5 | 质量监控 | 评估 pipeline + 退化检测 | ⭐⭐⭐⭐ | 实验 2 |

## 如何开始

```bash
# 1. 克隆或进入项目
cd AI-Agent-Learning-Project

# 2. 全局依赖安装
pip install -r requirements.txt

# 3. 设置 API Key
export OPENAI_API_KEY="sk-..."    # 或
export ANTHROPIC_API_KEY="sk-..."

# 4. 从实验 1 开始
cd experiments/exp01-weather-assistant
python main.py
```

## 学习原则

1. **先手动，后框架。** 每个新概念都先手写一遍，理解原理后再引入框架。
2. **每个实验配评估。** 代码跑通不是终点，能衡量好坏才是。
3. **记录成本。** 每次实验记录 token 消耗，形成成本直觉。
4. **写失败手册。** 每个实验结束后记录它会在什么情况下挂。

## 技术栈总览

| 层 | 技术选型 | 说明 |
|----|---------|------|
| LLM | OpenAI / Anthropic SDK | 原生，不套壳 |
| 工具协议 | MCP (Model Context Protocol) | 2025 年事实标准 |
| 向量库 | ChromaDB | 轻量，开发友好 |
| 工作流 | LangGraph | 唯一使用的 LangChain 生态组件 |
| 可观测 | LangFuse | 开源 tracing |
| 安全 | Guardrails-AI | 输入输出校验 |
| 多 Agent | AutoGen 0.4+ / CrewAI | 两者都浅尝 |

---

*当前版本: 2026-06-26*
