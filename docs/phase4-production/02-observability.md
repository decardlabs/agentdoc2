# Phase 4-02: 可观测性（Observability）

## 为什么 Agent 需要可观测性？

传统应用的问题排查方式在 Agent 世界不适用：没有统一的调用栈、没有确定的输出、没有可复现的 bug。

可观测性要回答三个问题：

```
发生了什么？（Logging）
为什么发生？（Tracing）
可能发生什么？（Monitoring）
```

## 需要追踪的核心数据

| 数据 | 说明 | 示例 |
|------|------|------|
| LLM 调用 | 每次调用模型、输入、输出、token | deepseek-v4-flash, 1200 tokens |
| Tool 调用 | 工具名、参数、结果、耗时 | get_weather({city:深圳}), 200ms |
| 成本 | 每次 LLM 调用的费用 | $0.003 |
| 错误 | 错误类型、堆栈、上下文 | API timeout after 30s |
| 延迟 | 每步耗时 | ReAct 循环总耗时 4.2s |

## 自建日志系统

```python
import json
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime

@dataclass
class TraceStep:
    step_type: str          # llm_call / tool_call
    model: str | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    tool_name: str | None = None
    tool_args: dict | None = None
    tool_result: str | None = None
    error: str | None = None
    duration_ms: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class AgentTrace:
    session_id: str
    user_input: str
    steps: list[TraceStep] = field(default_factory=list)
    total_duration_ms: float = 0.0
    total_cost: float = 0.0

    def add_step(self, step: TraceStep):
        self.steps.append(step)

    def summary(self) -> dict:
        llm_calls = sum(1 for s in self.steps if s.step_type == "llm_call")
        tool_calls = sum(1 for s in self.steps if s.step_type == "tool_call")
        errors = sum(1 for s in self.steps if s.error)
        total_tokens = sum(s.input_tokens + s.output_tokens for s in self.steps)

        return {
            "session_id": self.session_id,
            "total_duration_ms": self.total_duration_ms,
            "total_cost": self.total_cost,
            "llm_calls": llm_calls,
            "tool_calls": tool_calls,
            "errors": errors,
            "total_tokens": total_tokens,
        }

    def save(self, path: str = "traces/"):
        import os
        os.makedirs(path, exist_ok=True)
        filepath = f"{path}/{self.session_id}.json"
        with open(filepath, "w") as f:
            json.dump(asdict(self), f, ensure_ascii=False, indent=2)
        return filepath
```

## 在 Agent 中嵌入日志

```python
class ObservableReActAgent(ReActAgent):
    """带可观测性的 ReAct Agent"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.trace = None

    def run(self, user_input: str) -> str:
        import uuid
        self.trace = AgentTrace(
            session_id=uuid.uuid4().hex[:8],
            user_input=user_input,
        )
        start_time = time.time()

        try:
            result = super().run(user_input)
        finally:
            self.trace.total_duration_ms = (time.time() - start_time) * 1000
            self.trace.save()

        print(f"\n[Trace] {self.trace.summary()}")
        return result

    def _call_llm(self, messages):
        step = TraceStep(step_type="llm_call", model=self.model)
        start = time.time()

        try:
            response = super()._call_llm(messages)
            step.input_tokens = response.usage.prompt_tokens
            step.output_tokens = response.usage.completion_tokens
            step.duration_ms = (time.time() - start) * 1000
        except Exception as e:
            step.error = str(e)
            raise
        finally:
            self.trace.add_step(step)

        return response

    def _execute_tool(self, tool_call):
        name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)
        step = TraceStep(
            step_type="tool_call",
            tool_name=name,
            tool_args=args,
        )
        start = time.time()

        try:
            result = super()._execute_tool(tool_call)
            step.tool_result = result
            step.duration_ms = (time.time() - start) * 1000
        except Exception as e:
            step.error = str(e)
            raise
        finally:
            self.trace.add_step(step)

        return result
```

## LangFuse 集成

LangFuse 是专门为 LLM 应用设计的开源可观测平台：

```python
from langfuse import Langfuse

langfuse = Langfuse(
    public_key="pk-...",
    secret_key="sk-...",
    host="https://cloud.langfuse.com",
)

# 创建一个 trace
trace = langfuse.trace(
    name="weather-agent",
    session_id="session-001",
)

# 记录 LLM 调用
span = trace.span(
    name="llm-call",
    input={"messages": [...]},
    output={"response": "..."},
    usage={"input": 100, "output": 50},
)
span.end()

# 记录成本
trace.update(
    metadata={"cost_usd": 0.003},
)
```

## 练习

1. 为实验 1 的天气助手加入日志系统，记录每次 LLM 调用和工具调用
2. 输出 trace 摘要（调用次数、token 消耗、耗时）
3. 注册 LangFuse 并接入，对比自建日志和 LangFuse 的体验

## 检查清单

- [ ] 能为 Agent 建立完整的调用追踪
- [ ] 能记录 LLM 调用、工具调用、错误、耗时
- [ ] 能将 trace 保存为结构化日志
- [ ] 了解 LangFuse 的基本使用
