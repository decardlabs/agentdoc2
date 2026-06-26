# Phase 3-01: LangGraph 工作流编排

## 为什么需要工作流？

ReAct 循环是"思考→行动→观察"的简单循环，但实际业务中需要的是**有状态、有分支、有条件**的流程：

```
用户输入
  ↓
意图识别 ───→ 退款 → 验证身份 → 查询订单 → 执行退款 → 通知结果
  ↓                                                       ↑
咨询 → 查询知识库 → 生成回答 ────────────────────────────────┘
```

这就是工作流编排解决的问题。

## LangGraph 核心概念

LangGraph 是 LangChain 生态中用来构建**有状态图（Graph）**的工具。核心概念：

- **State（状态）：** 整个图共享的数据对象
- **Node（节点）：** 每个步骤的执行单元
- **Edge（边）：** 节点间的连接，决定执行顺序
- **Conditional Edge（条件边）：** 根据状态决定走哪条路

## 第一个 LangGraph（简单问答）

```python
from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END
from openai import OpenAI

# 1. 定义状态
class AgentState(TypedDict):
    messages: list[dict]
    next_step: str

client = OpenAI()

# 2. 定义节点
def call_llm(state: AgentState) -> AgentState:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=state["messages"],
    )
    state["messages"].append({
        "role": "assistant",
        "content": response.choices[0].message.content,
    })
    return state

def check_finish(state: AgentState) -> AgentState:
    # 简单的结束判断
    if len(state["messages"]) > 10:
        state["next_step"] = "end"
    return state

# 3. 构建图
workflow = StateGraph(AgentState)

workflow.add_node("llm", call_llm)
workflow.add_node("check", check_finish)

workflow.set_entry_point("llm")
workflow.add_edge("llm", "check")
workflow.add_conditional_edges(
    "check",
    lambda state: state["next_step"],
    {"end": END, "continue": "llm"},
)

app = workflow.compile()
```

## 带工具调用的 LangGraph 工作流

```python
from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END
from openai import OpenAI
import json

class WorkflowState(TypedDict):
    messages: list[dict]
    tool_result: str | None

client = OpenAI()

# 工具定义
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "classify_ticket",
            "description": "分类工单类型",
            "parameters": {
                "type": "object",
                "properties": {
                    "description": {"type": "string"},
                },
                "required": ["description"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "process_refund",
            "description": "处理退款",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string"},
                    "amount": {"type": "number"},
                },
                "required": ["order_id", "amount"],
            },
        },
    },
]

def handle_ticket(state: WorkflowState) -> WorkflowState:
    """节点1：工单处理"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=state["messages"],
        tools=TOOLS,
    )
    msg = response.choices[0].message

    if msg.tool_calls:
        state["messages"].append(msg)
        # 执行工具（简化）
        for tc in msg.tool_calls:
            state["tool_result"] = f"执行 {tc.function.name}"
            state["messages"].append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": state["tool_result"],
            })
    return state

def generate_response(state: WorkflowState) -> WorkflowState:
    """节点2：生成回复"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=state["messages"],
    )
    state["messages"].append({
        "role": "assistant",
        "content": response.choices[0].message.content,
    })
    return state

def should_continue(state: WorkflowState) -> Literal["generate", "__end__"]:
    """条件判断：还有 tool call 就继续，否则生成回复"""
    if state["messages"][-1].get("role") == "tool":
        return "generate"
    return "__end__"

# 构建图
graph = StateGraph(WorkflowState)
graph.add_node("handle", handle_ticket)
graph.add_node("generate", generate_response)

graph.set_entry_point("handle")
graph.add_conditional_edges("handle", should_continue)
graph.add_edge("generate", END)

app = graph.compile()
```

## 错误处理

工作流中的错误可能发生在任意节点，需要在 state 中追踪：

```python
class RobustState(TypedDict):
    messages: list[dict]
    errors: list[str]
    retry_count: int

def safe_execute(state: RobustState) -> RobustState:
    try:
        # 带重试的执行
        for attempt in range(3):
            try:
                response = client.chat.completions.create(...)
                state["messages"].append(...)
                break
            except Exception as e:
                if attempt == 2:
                    state["errors"].append(f"LLM 调用失败: {str(e)}")
    except Exception as e:
        state["errors"].append(f"严重错误: {str(e)}")
    return state
```

## 练习

1. 用 LangGraph 实现一个"意图识别 → 分类 → 处理"的三步工作流
2. 在 state 中加入 `errors` 字段，处理节点执行失败的情况
3. 实现一个条件分支：根据意图识别结果走不同的处理链路

## 检查清单

- [ ] 理解 StateGraph 的 State / Node / Edge 概念
- [ ] 能构建多节点的工作流图
- [ ] 能使用条件边实现分支路由
- [ ] 能处理节点执行失败并优雅降级
