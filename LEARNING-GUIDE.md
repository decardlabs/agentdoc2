# AI Agent 智能体研发学习路线指导

> 一份面向实操的学习指南。不讲理论，只教你怎么一步步走下去。
> 每周 10-15 小时，6 个月走完全程。

---

## 目录

- [怎么用这份指南](#怎么用这份指南)
- [阶段一：LLM 调用与 Agent 核心范式（第 1-5 周）](#阶段一llm-调用与-agent-核心范式第-1-5-周)
- [阶段二：工具标准化与记忆系统（第 6-11 周）](#阶段二工具标准化与记忆系统第-6-11-周)
- [阶段三：工作流编排与复杂工具集成（第 12-17 周）](#阶段三工作流编排与复杂工具集成第-12-17-周)
- [阶段四：多 Agent 协作与生产化（第 18-25 周）](#阶段四多-agent-协作与生产化第-18-25-周)
- [实验清单 & 执行顺序](#实验清单--执行顺序)
- [每周例行操作](#每周例行操作)
- [常见瓶颈与解决策略](#常见瓶颈与解决策略)
- [学习成果检查表](#学习成果检查表)
- [辅助工具文档](#辅助工具文档)
- [辅助工具文档](#辅助工具文档)

---

## 怎么用这份指南

### 三件你必须做的事

1. **按周推进，不要跳阶段。** 每一周的内容建立在前几周的基础上。跳过的内容会回来找你。
2. **每周结束自查「里程碑检查点」。** 没通过就不进下一周。
3. **每做一个实验，同时写它的评估和失败手册。** 这不是可选的。

### 文档关系

```
LEARNING-GUIDE.md  ← 你在这里：每周该做什么
    ├── docs/phaseX-*/  ← 每阶段的技术文档（学习时对照阅读）
    └── experiments/expXX-*/  ← 实验代码（每个阶段对应的动手实践）
```

### 你需要的东西

- Python 3.10+
- DeepSeek API Key（注册后可得，￥0.5/百万 token，实验期间总花费 ≤ ￥50）
- 一台能联网的电脑
- 每周 10-15 小时专注时间

---

## 阶段一：LLM 调用与 Agent 核心范式（第 1-5 周）

> **核心信条：这一阶段不碰任何框架。** 不用 LangChain、不用 LangGraph、不用向量数据库。
> 所有代码你用手写。这样才能真正理解 Agent 的工作原理。

### 第 1 周：LLM SDK 直调

**学习目标：** 把第一条 `chat.completions.create` 跑通。

**具体步骤：**

| 天 | 任务 | 预计耗时 |
|----|------|---------|
| 1 | 注册 DeepSeek 账号，获取 API Key | 20 min |
| 1 | `pip install openai`，写一个 hello world 脚本 | 1 hr |
| 2 | 阅读 `docs/phase1-llm-basics/01-llm-sdk.md` | 1 hr |
| 2-3 | 实现流式输出（`stream=True`） | 2 hr |
| 3 | 实现错误处理（限速重试、超时、网络断开） | 2 hr |
| 4 | 实现 system/user/assistant 多轮对话 | 2 hr |
| 4-5 | 实现 token 用量统计（`response.usage`） | 1 hr |
| 5 | 写一个简单的对话脚本，和 DeepSeek 聊 10 轮 | 1 hr |

**代码产出：** 一个 `deepseek_chat.py`，支持流式对话 + 错误重试 + 用量统计。

**里程碑检查点：**
- [x] 能发送单轮请求并拿到完整回复
- [x] 能实现流式输出（字一个一个地出来）
- [x] 网络断了能自动重试 3 次
- [x] 能保存每次对话的 token 消耗

---

### 第 2 周：Function Calling

**学习目标：** 让 LLM 能调用外部函数。

**具体步骤：**

| 天 | 任务 | 预计耗时 |
|----|------|---------|
| 1 | 阅读 `docs/phase1-llm-basics/02-function-calling.md` | 1.5 hr |
| 1-2 | 实现第一个 Tool：`get_weather(city)` | 2 hr |
| 2-3 | 理解 tool schema 的 JSON 结构（`parameters` 用 JSON Schema 定义） | 1 hr |
| 3 | 实现 tool call → execute → result → response 的完整链路 | 3 hr |
| 4-5 | 实现两个 Tool 并存：`get_weather` + `get_current_time` | 2 hr |

**代码产出：** `tools.py`（Tool 定义）+ `function_calling.py`（调用逻辑）。

**里程碑检查点：**
- [x] LLM 能正确选择工具并传入参数
- [x] 工具返回结果后 LLM 能正确组织自然语言回复
- [x] 不需要调用工具的问题（如"1+1=?") 能直接回答而不误触工具

---

### 第 3 周：Structured Output

**学习目标：** 让 LLM 按你想要的格式输出。

**具体步骤：**

| 天 | 任务 | 预计耗时 |
|----|------|---------|
| 1 | 阅读 `docs/phase1-llm-basics/03-structured-output.md` | 1 hr |
| 1-2 | 用 `response_format={"type": "json_object"}` 做 JSON 输出 | 2 hr |
| 2-3 | 用 `response_format` + JSON Schema 约束输出结构 | 2 hr |
| 3-4 | 对比 free-form 输出和结构化输出的可靠性差异 | 1 hr |
| 4 | 实现：从一段文本中抽取结构化信息（如：日期、人名、金额） | 2 hr |
| 5 | 实现：用 Structured Output 做意图分类 | 1 hr |

**代码产出：** `structured_output.py`（JSON Schema 约束 + 信息抽取 + 意图分类）。

**里程碑检查点：**
- [x] 能准确输出符合 JSON Schema 的结果
- [x] 复杂的嵌套结构也能稳定输出
- [x] 和不约束格式相比，结构化输出的可靠性有明显提升

---

### 第 4 周：手写 ReAct 循环

**学习目标：** 从零手写 ReAct（思考-行动-观察）循环。这是整个 Agent 学习的基石。

**具体步骤：**

| 天 | 任务 | 预计耗时 |
|----|------|---------|
| 1 | 阅读 `docs/phase1-llm-basics/04-react-loop.md` | 1.5 hr |
| 1-2 | 阅读 ReAct 原始论文摘要（docs 里有关键引用） | 30 min |
| 2-3 | 手写第一个 ReAct 循环：system prompt + tool registry 的基础结构 | 3 hr |
| 3 | 实现最大迭代轮次控制（`max_iterations=10`） | 1 hr |
| 4 | 实现终止条件检测（"Final Answer" 关键词） | 1 hr |
| 4-5 | 测试：一个请求走通 Thought → Action → Observation → Final Answer 完整链路 | 2 hr |

**代码产出：** `react_agent.py`（ReAct 循环核心逻辑）。

**关键认知：**
- ReAct 的核心就是 `while True` —— 没有魔法。LLM 输出 → 解析 → 执行 → 反馈 → 再给 LLM。
- 90% 的 Bug 来自解析不规则的 LLM 输出。务必写防御性解析。

**里程碑检查点：**
- [x] 能跑通 Thought → Action → Observation → Final Answer 完整循环
- [x] 超过最大轮次后自动终止
- [x] 不调用工具的简单问题能直接返回 Final Answer
- [x] 你清楚什么时候该停止循环（自己写这段逻辑）

---

### 第 5 周：实验 1 - 天气助手 + 评估

**学习目标：** 完成第一个完整 Agent，同时建立评估意识。

**具体步骤：**

| 天 | 任务 | 预计耗时 |
|----|------|---------|
| 1-2 | 阅读 `experiments/exp01-weather-assistant/README.md` + 代码 | 1 hr |
| 2-3 | 实现天气 API 调用 + 穿衣建议 Tool | 2 hr |
| 3 | 集成到 ReAct 循环中 | 1 hr |
| 3-4 | 编写 10 条评估用例（5 条"应该调工具" + 5 条"不应调工具"） | 2 hr |
| 4 | 运行评估：`python main.py eval` | 30 min |
| 4-5 | 分析评估结果，修复失败的用例 | 2 hr |
| 5 | 写 `FAILURES.md`：记录这个 Agent 在什么情况下会挂 | 1 hr |

**验证标准：**
- "今天深圳天气怎么样？" → 调用天气 API，输出温度 + 穿衣建议
- "1 + 1 等于几？" → 不调用任何工具，直接回答
- 10 条测试用例全部通过

**里程碑检查点（阶段一毕业）：**
- [x] 手写 ReAct Agent 能跑通
- [x] 实验 1 的 10 条评估用例全部通过
- [x] 了解 Agent 的常见失败模式（写了 FAILURES.md）
- [x] 记录了实验的 token 消耗

> 💡 **学习工具准备：** 开始前建议先阅读 [Obsidian 使用指南](docs/tools/01-obsidian-guide.md) 和 [AI 工作流配置指南](docs/tools/02-ai-workflow-guide.md)，准备好笔记环境和 AI 辅助工具再动手。

---

## 阶段二：工具标准化与记忆系统（第 6-11 周）

> 进入这一阶段前，确认阶段一的所有里程碑已经通过。

### 第 6 周：MCP 协议基础

**学习目标：** 理解 MCP 协议，编写第一个 MCP Server。

**具体步骤：**

| 天 | 任务 | 预计耗时 |
|----|------|---------|
| 1 | 阅读 `docs/phase2-mcp-rag/01-mcp-protocol.md` | 1 hr |
| 1-2 | `pip install mcp`，搭建 MCP Server 骨架 | 1.5 hr |
| 2-3 | 实现一个工具（如 `get_stock_price`），通过 MCP 暴露 | 2 hr |
| 3-4 | 在 Agent 中通过 MCP 客户端调用该工具 | 2 hr |
| 4-5 | 将阶段一的天气 Tool 迁移为 MCP Server | 2 hr |

**代码产出：** `mcp_server.py` + MCP 客户端调用代码。

**关键认知：**
- MCP 的核心是标准化：任何 MCP Server 写的工具，任何兼容 MCP 的 Agent 都能调用。
- 对比阶段一的手写 Tool 封装，MCP 的收益不在功能，在**互操作性**。

**里程碑检查点：**
- [x] 能独立编写一个 MCP Server
- [x] Agent 能通过 MCP 调用外部工具
- [x] 理解 MCP 的 Resources、Tools、Prompts 三要素

---

### 第 7-8 周：RAG 管道搭建

**学习目标：** 跑通从文档到问答的完整 RAG 管道。

**具体步骤：**

| 周 | 天 | 任务 | 预计耗时 |
|----|----|------|---------|
| 7 | 1-2 | 阅读 `docs/phase2-mcp-rag/02-rag-pipeline.md` | 1.5 hr |
| 7 | 2-3 | `pip install chromadb`，写第一个 embedding 查询 | 2 hr |
| 7 | 3 | 实现文档 chunking（对比 fixed-size 和 semantic chunking） | 2 hr |
| 7 | 4 | 实现 embedding → 向量库存入 → 检索的全链路 | 2 hr |
| 7 | 5 | 实现基本的 RAG 问答 | 1 hr |
| 8 | 1-2 | 实现 Reranking（用 `cross-encoder` 模型重排序） | 3 hr |
| 8 | 2-3 | 对比有/无 Reranking 的检索精度差异 | 1.5 hr |
| 8 | 3 | 阅读 `docs/phase2-mcp-rag/04-agentic-rag.md` | 1 hr |
| 8 | 4-5 | 实现 Agentic RAG：Agent 动态决定检索时机和策略 | 3 hr |

**代码产出：**
- `rag_pipeline.py`（chunking → embedding → 检索 → 回答）
- `reranker.py`（检索后重排序）
- `agentic_rag.py`（动态检索 Agent）

**里程碑检查点：**
- [x] 能对一篇文档做 chunking 并存入 ChromaDB
- [x] 检索结果经过 reranking 后有明显提升（用 NDCG 或 MRR 量化）
- [x] Agentic RAG 能根据问题决定是否检索、检索几次

---

### 第 9 周：建立评估体系

**学习目标：** 学会评估一个 Agent/管道的好坏。

**具体步骤：**

| 天 | 任务 | 预计耗时 |
|----|------|---------|
| 1 | 阅读 `docs/phase2-mcp-rag/03-evaluation.md` | 1 hr |
| 1-2 | 建立 Ground Truth 数据集（10 个问答对） | 1.5 hr |
| 2-3 | 实现 LLM-as-Judge 评估脚本 | 2 hr |
| 3-4 | 实现规则匹配评估（关键信息提取 + 字符串对比） | 1.5 hr |
| 4-5 | 生成评估报告（分类别统计通过率） | 1 hr |

**代码产出：** `evaluator.py`（LLM-as-Judge + 规则匹配 + 报告生成）。

**里程碑检查点：**
- [x] 能对 Agent 输出做自动评分
- [x] 理解的 LLM-as-Judge 的偏差（LLM 倾向给自己打高分）
- [x] 生成过至少一份评估报告

---

### 第 10-11 周：实验 2 - 文档问答 + 评估

**学习目标：** 完成完整的 RAG + 评估实验。

**具体步骤：**

| 周 | 任务 | 预计耗时 |
|----|------|---------|
| 10 | 阅读 `experiments/exp02-doc-qa-eval/README.md` + 代码 | 1 hr |
| 10 | 准备测试文档（sample_doc/ 下已有一份示例，可替换为自己的 PDF） | 1 hr |
| 10 | 运行 RAG 管道，验证单篇文档深度问答 | 2 hr |
| 10 | 编写至少 15 条评估用例 | 2 hr |
| 10-11 | 运行评估 pipeline，调整 chunking 策略和检索参数 | 3 hr |
| 11 | 集成 LangFuse tracing（`pip install langfuse`） | 2 hr |
| 11 | 写 `FAILURES.md`：记录 RAG 的失败模式 | 1 hr |

**里程碑检查点（阶段二毕业）：**
- [x] RAG 管道能准确回答文档中的事实性问题
- [x] 评估报告显示通过率 > 80%
- [x] 接入了 LangFuse tracing，能看到每次查询的 token 消耗
- [x] 知道 RAG 在什么情况下会回答错误（写了 FAILURES.md）

---

## 阶段三：工作流编排与复杂工具集成（第 12-17 周）

> 进入这一阶段前，确认阶段二的所有里程碑已经通过。

### 第 12-13 周：LangGraph 入门

**学习目标：** 掌握用状态图编排多步骤工作流。

**具体步骤：**

| 周 | 天 | 任务 | 预计耗时 |
|----|----|------|---------|
| 12 | 1 | 阅读 `docs/phase3-workflow/01-langgraph.md` | 1.5 hr |
| 12 | 1-2 | `pip install langgraph`，跑通第一个 hello world 图 | 1 hr |
| 12 | 2-3 | 实现链式节点：Node A → Node B → Node C | 2 hr |
| 12 | 3-4 | 实现条件边（conditional edge）：根据 LLM 输出走不同分支 | 2 hr |
| 12-13 | 4-5 | 实现循环：允许 Agent 在节点间来回跳转 | 2 hr |
| 13 | 1-3 | 配置 LangFuse tracing 集成 LangGraph（`LangGraphTracer`） | 2 hr |
| 13 | 3-5 | 对比：同一个任务，手写 ReAct vs LangGraph 实现的差异 | 2 hr |

**代码产出：** `langgraph_basics.py`（节点、条件边、循环示例）。

**关键认知：**
- LangGraph 的"图"是对手写 ReAct 循环的形式化抽象。本质是一样的。
- 核心概念只有三个：**节点**（做什么）、**边**（怎么走）、**状态**（带什么数据）。

**里程碑检查点：**
- [x] 能设计一个有分支和循环的 LangGraph 工作流
- [x] 理解 StateGraph 的 state 设计模式
- [x] LangFuse 图上能看到每个节点的执行时间和调用链

---

### 第 14 周：代码解释器集成

**学习目标：** 让 Agent 能执行代码并解析结果。

**具体步骤：**

| 天 | 任务 | 预计耗时 |
|----|------|---------|
| 1 | 阅读 `docs/phase3-workflow/02-code-interpreter.md` | 1 hr |
| 1-2 | 在子进程中安全执行 Python 代码（`subprocess` + 超时控制） | 2 hr |
| 2-3 | 实现结果捕获：stdout、stderr、错误信息 | 1.5 hr |
| 3-4 | 实现工具级别：`execute_python(code)` → 返回执行结果 | 1.5 hr |
| 4-5 | 集成到 LangGraph 中，Agent 可在工作流中自主执行代码 | 1 hr |

**代码产出：** `code_interpreter.py`（安全执行 + 结果捕获 + 超时控制）。

**安全提醒：** 这是生产中最危险的工具。本实验所有代码在本地执行，上线必须用 Docker 沙箱。

**里程碑检查点：**
- [x] Agent 生成的 Python 代码能被执行并返回结果
- [x] 代码执行超时会被自动中断
- [x] 执行错误的代码不会导致整个 Agent 崩溃

---

### 第 15 周：异常处理与错误恢复

**学习目标：** 让 Agent 面对异常时能优雅降级而非直接崩溃。

**具体步骤：**

| 天 | 任务 | 预计耗时 |
|----|------|---------|
| 1 | 阅读 `docs/phase3-workflow/03-error-handling.md` | 1.5 hr |
| 1-2 | 实现单次操作的三层重试（间隔 1s → 5s → 15s） | 2 hr |
| 2-3 | 实现降级策略：工具 A 失败后尝试工具 B | 1.5 hr |
| 3 | 实现安全终止：多次失败后记录错误并继续下一步 | 1 hr |
| 3-4 | 实现数据校验装饰器：空值、类型错误、格式错误 | 2 hr |
| 4-5 | 用单元测试测试所有异常路径 | 1.5 hr |

**代码产出：** `error_handler.py`（重试 → 降级 → 安全终止三层架构）。

**里程碑检查点：**
- [x] 一个工具调用的完整异常生命周期：尝试 → 重试 → 降级 → 报告
- [x] Agent 从部分失败中恢复后，工作流能继续

---

### 第 16-17 周：实验 3 - 自动化工单处理

**学习目标：** 完成一个需要多步骤编排、含异常数据的复杂实验。

**具体步骤：**

| 周 | 任务 | 预计耗时 |
|----|------|---------|
| 16 | 阅读 `experiments/exp03-ticket-processor/README.md` + 代码 | 1 hr |
| 16 | 设计工单处理的状态图（分类 → 统计 → 报告） | 1 hr |
| 16 | 实现 LangGraph 工作流 | 3 hr |
| 16 | 注入 3 条异常数据（空字段、格式错误） | 1 hr |
| 16-17 | 运行并调试，确保异常被正确处理 | 3 hr |
| 17 | 测量：正常工单 vs 异常工单的处理成功率和耗时 | 1.5 hr |
| 17 | 写 `FAILURES.md` | 1 hr |

**验证标准：**
- 10 条正常工单 → 全部分类正确，报告生成
- 混入 3 条异常数据 → Agent 捕获异常，继续处理后续工单，报告中标记异常条目

**里程碑检查点（阶段三毕业）：**
- [x] LangGraph 工作流能处理 10 条工单并在 5 分钟内完成
- [x] 异常工单被正确标记，不影响正常工单处理
- [x] 每次运行都有 token 消耗记录
- [x] 清楚工单处理 Agent 的失败模式（写了 FAILURES.md）

---

## 阶段四：多 Agent 协作与生产化（第 18-25 周）

> 进入这一阶段前，确认阶段三的所有里程碑已经通过。
> **注意：** 这是最重的一阶段，节奏放慢。

### 第 18-20 周：多 Agent 协作

**学习目标：** 理解多 Agent 的角色分配、消息路由和冲突解决。

**具体步骤：**

| 周 | 天 | 任务 | 预计耗时 |
|----|----|------|---------|
| 18 | 1 | 阅读 `docs/phase4-production/01-multi-agent.md` | 1.5 hr |
| 18 | 1-2 | 熟悉 AutoGen 0.4+（AgentChat API）：`pip install autogen-agentchat` | 2 hr |
| 18 | 2-3 | 实现最简单的多 Agent 对话（Agent A → Agent B） | 1.5 hr |
| 18 | 3-5 | 也试试 CrewAI：`pip install crewai`，实现类似的 demo | 2 hr |
| 19 | 1-2 | 阅读并运行 `experiments/exp04-multi-agent/single_agent.py` | 1.5 hr |
| 19 | 2-4 | 阅读并运行 `experiments/exp04-multi-agent/multi_agent.py` | 2 hr |
| 19 | 4-5 | 理解两者的差异 | 1.5 hr |
| 20 | 1-3 | 用你的自己的数据集跑对比实验（至少 20 条用例） | 3 hr |
| 20 | 3-4 | 运行 `compare.py` 自动生成对比报告 | 1 hr |
| 20 | 5 | 写分析报告：什么场景适合单 Agent，什么场景适合多 Agent | 2 hr |

**代码产出：** 你的对照实验报告 + 对比数据分析。

**关键认知（非常重要）：**
- **多 Agent 不是更好的方案。** 它是更重、更贵的方案。
- 对照实验的目标不是证明多 Agent 好，而是**量化收益和代价**，找到分界线。

**里程碑检查点：**
- [x] 跑通了一个多 Agent 协作 demo
- [x] 有能力在自己的场景中选择单 Agent 还是多 Agent
- [x] 理解 AutoGen 和 CrewAI 的核心区别

---

### 第 21-22 周：可观测性

**学习目标：** 建立生产级 tracing 和监控。

**具体步骤：**

| 周 | 天 | 任务 | 预计耗时 |
|----|----|------|---------|
| 21 | 1 | 阅读 `docs/phase4-production/02-observability.md` | 1 hr |
| 21 | 1-2 | LangFuse 深度配置：pip install langfuse + 项目创建 | 1 hr |
| 21 | 2-4 | 将以往所有实验接入 LangFuse tracing | 3 hr |
| 21-22 | 4-5 | 建立监控指标：成功率、平均 token 消耗、p95 响应时间 | 2 hr |
| 22 | 1-3 | 部署一个简单的 Grafana dashboard（可选） | 2 hr |
| 22 | 3-5 | 模拟一次 Agent 退化，验证是否能从 tracing 中定位问题 | 2 hr |

**里程碑检查点：**
- [x] LangFuse 上能看到每个请求的完整调用链
- [x] 能从 tracing 数据中发现异常（如 token 消耗突然飙升）

---

### 第 23 周：Guardrails

**学习目标：** 建立安全防线，防止 Agent 做不该做的事。

**具体步骤：**

| 天 | 任务 | 预计耗时 |
|----|------|---------|
| 1 | 阅读 `docs/phase4-production/03-guardrails.md` | 1 hr |
| 1-2 | `pip install guardrails-ai`，跑通第一个输入校验 | 1.5 hr |
| 2-3 | 实现输出校验：敏感信息检测（API key、手机号） | 2 hr |
| 3-4 | 实现工具调用权限控制：敏感操作需要二次确认 | 2 hr |
| 4-5 | 测试：尝试让 Agent 执行越权操作，验证 Guardrails 拦截 | 1 hr |

**代码产出：** `guardrails_demo.py`（输入校验 + 输出过滤 + 权限控制）。

**里程碑检查点：**
- [x] 敏感信息不会被 Agent 输出
- [x] Agent 不会执行越权操作
- [x] 理解 Guardrails 的局限性（规则总有覆盖不到的地方）

---

### 第 24-25 周：实验 5 - 质量监控与退化检测系统

**学习目标：** 建立 Agent 质量监控体系。

**具体步骤：**

| 周 | 天 | 任务 | 预计耗时 |
|----|----|------|---------|
| 24 | 1 | 阅读 `experiments/exp05-quality-monitor/README.md` + 代码 | 1 hr |
| 24 | 1-2 | 模拟生成 100 条对话日志 | 1 hr |
| 24 | 2-4 | 实现评估 pipeline：规则检测 + LLM-as-Judge 打分 | 3 hr |
| 24 | 4-5 | 实现退化检测：滑动窗口 + 阈值告警 | 2 hr |
| 25 | 1-3 | 实现离线回放：用历史对话做回归测试 | 2 hr |
| 25 | 3-4 | 故意引入退化 prompt，验证系统能否检出 | 1.5 hr |
| 25 | 5 | 写 `FAILURES.md` | 1 hr |

**验证标准：**
- 模拟 100 条对话日志，自动生成质量报告
- 故意引入一个退化 prompt，系统能在 10 分钟内检出并告警

**里程碑检查点（最终毕业）：**
- [x] 质量监控 pipeline 能自动运行并生成报告
- [x] 退化检测能在质量下降时及时告警
- [x] 离线回放可以一键回归所有历史测试用例
- [x] 你清楚地知道"我的 Agent 在哪些场景下不行"（写了完整的 FAILURES.md）

---

## 实验清单 & 执行顺序

```
实验 1 ─→ 实验 2 ─→ 实验 3 ─→ 实验 4 ─→ 实验 5
 │          │          │          │          │
评估       RAG       工作流     多Agent     质量监控
10用例     +评估      +异常      对照实验    退化检测
```

| 实验 | 路径 | 运行命令 | 前置条件 |
|------|------|---------|---------|
| 1 | `experiments/exp01-weather-assistant/` | `python main.py` | DEEPSEEK_API_KEY |
| 2 | `experiments/exp02-doc-qa-eval/` | `python main.py` | 实验 1 |
| 3 | `experiments/exp03-ticket-processor/` | `python main.py` | 实验 1 |
| 4 | `experiments/exp04-multi-agent/` | `python compare.py` | 实验 2-3 |
| 5 | `experiments/exp05-quality-monitor/` | `python main.py` | 实验 2 |

---

## 每周例行操作

### 每周开始

- [ ] 阅读本周的「具体步骤」和「学习目标」
- [ ] 确认上周的「里程碑检查点」全部通过

### 每天结束时

- [ ] 代码提交到 git（一个 commit 一个主题）
- [ ] 记录的今天花了多少时间、消耗了多少 token
- [ ] 写一行笔记：今天学会了什么、卡在哪里

### 每周结束时

- [ ] 检查本周的「里程碑检查点」
- [ ] 更新 `docs/failures/`（汇总所有实验的失败模式）
- [ ] 提交一个周报 commit（`git commit -m "week X: ..."`）

---

## 常见瓶颈与解决策略

| 瓶颈 | 表现 | 解决策略 |
|------|------|---------|
| API 调用太慢 | 等一个回复要 10 秒+ | 启用 stream=True，不等待完整输出；检查网络到 api.deepseek.com 的延迟 |
| Token 消耗太快 | 一天花了 10 元 | 缩小上下文（system prompt 别写小说）；用 `deepseek-v4-flash` 而非大模型；设置 max_tokens 上限 |
| LLM 不听话 | 就是不按 tool schema 来 | 写更具体的 system prompt；给 few-shot examples；测试后发现 structured output 比 free text 稳定 10 倍 |
| 调试困难 | 不知道 Agent 在想什么 | 打开 verbose logging：`logging.basicConfig(level=logging.DEBUG)`；打印每一步的 LLM 输出 |
| 时间不够 | 每周挤不出 15 小时 | 宁愿慢一点也不要跳内容。把"下周最后期限"延到"下下周" |
| 无限循环 | Agent 卡死在 tool call → response 循环 | 设置 `max_iterations` 硬限；检测输出是否重复 |
| 向量检索不准 | 明明文档里有就是查不到 | 换 chunking 策略；加 Reranking；检查 embedding 模型是否匹配你的语言 |
| 多 Agent 通信混乱 | Agent 之间答非所问 | 从 2 个 Agent 开始；给每个 Agent 清晰的 system prompt + 输出格式约束；记录所有中间消息 |

---

## 学习成果检查表

### 阶段一结束时

- [ ] 能用 SDK 调用 LLM，实现流式输出和错误处理
- [ ] 能写 Function Calling，LLM 正确选择工具
- [ ] 能用 Structured Output 约束输出格式
- [ ] 能不依赖框架，手写 ReAct 循环
- [ ] 实验 1 完成，10 条评估用例通过
- [ ] 写了实验 1 的 FAILURES.md
- [ ] 记录了一次实验的完整 token 消耗

### 阶段二结束时

- [ ] 能写 MCP Server 和 Client
- [ ] 跑通了完整的 RAG 管道（chunking → embedding → 检索 → reranking → 回答）
- [ ] 有评估脚本，能自动评分
- [ ] 接入了 LangFuse tracing
- [ ] 实验 2 完成，通过率 > 80%
- [ ] 写了实验 2 的 FAILURES.md

### 阶段三结束时

- [ ] 能用 LangGraph 建模多步骤工作流
- [ ] 实现了代码解释器集成
- [ ] 实现了三层异常处理架构（重试 → 降级 → 安全终止）
- [ ] 实验 3 完成，异常工单被正确处理
- [ ] 写了实验 3 的 FAILURES.md

### 阶段四结束时

- [ ] 跑通了多 Agent 协作 demo
- [ ] 完成了单 Agent vs 多 Agent 对照实验并写分析报告
- [ ] 接入生产级 tracing 和监控
- [ ] 实现了 Guardrails 安全防护
- [ ] 实验 5 完成，质量监控 pipeline 能自动告警
- [ ] 写了实验 5 的 FAILURES.md

### 最终产出

- [ ] 一个手写的 ReAct Agent 脚手架（阶段一产物）
- [ ] 一个 MCP Server 模板（阶段二产物）
- [ ] 一个可恢复的工作流引擎模板（阶段三产物）
- [ ] 一份单 Agent vs 多 Agent 对照实验报告（阶段四产物）
- [ ] 一套 Agent 质量监控系统（阶段四产物）
- [ ] 所有实验的 FAILURES.md 汇总

---

## 附录：每周进度模板

复制以下模板，每周创建并填写：

```markdown
# 第 X 周进度（YYYY-MM-DD ~ YYYY-MM-DD）

## 本周目标
- [ ] 目标 1
- [ ] 目标 2
- [ ] 目标 3

## 实际完成
（简述）

## 学习笔记
（关键认知、踩坑记录）

## Token 消耗
- 本周总消耗：____ tokens
- 本周消费金额：￥____
- 累计消耗：____ tokens

## 里程碑检查
- [ ] 项目 1
- [ ] 项目 2

## 下周计划
- [ ] 计划 1
- [ ] 计划 2
```

---

## 辅助工具文档

在学习过程中，下面两份文档可以帮你准备好环境：

| 文档 | 路径 | 说明 |
|------|------|------|
| **Obsidian 使用指南** | [`docs/tools/01-obsidian-guide.md`](docs/tools/01-obsidian-guide.md) | 安装 Obsidian、创建学习笔记、使用双向链接和标签组织知识 |
| **AI 工作流配置指南** | [`docs/tools/02-ai-workflow-guide.md`](docs/tools/02-ai-workflow-guide.md) | 配置 WorkBuddy / Claude Code 使用 DeepSeek v4 Flash，每个实验的 AI 协作流程 |

**建议：** 阶段一开始之前，先把 Obsidian 装好、把 DeepSeek API Key 配好。这两件事不花多少时间，但能让你后续 6 个月的学习顺畅很多。

---

*文档版本：2026-06-26*
*对应项目仓库：https://github.com/decardlabs/agentdoc2*
