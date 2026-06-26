# Phase 1-03: Structured Output

## 为什么要约束输出格式？

Agent 的核心机制依赖程序理解 LLM 的输出。如果输出是自由文本，程序很难稳定解析。**约束输出格式**是让 LLM 从"聊天工具"变成"可编程组件"的关键一步。

## DeepSeek Structured Outputs

DeepSeek v4 Flash 支持 OpenAI 兼容的 `response_format` 参数，可以强制 LLM 输出 JSON，并严格匹配你提供的 JSON Schema：

### Pydantic 方式

```python
from pydantic import BaseModel
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)

class WeatherResponse(BaseModel):
    city: str
    temperature: float
    unit: str
    condition: str
    advice: str

completion = client.beta.chat.completions.parse(
    model="deepseek-v4-flash",
    messages=[{"role": "user", "content": "深圳今天天气如何？"}],
    tools=[weather_tool],
    response_format=WeatherResponse,   # ← 约束输出格式
)
weather = completion.choices[0].message.parsed
print(f"{weather.city}: {weather.temperature}°C, {weather.condition}")
print(f"建议: {weather.advice}")
```

### 纯 JSON Schema 方式

不依赖 Pydantic 也可以直接使用：

```python
response = client.chat.completions.create(
    model="deepseek-v4-flash",
    messages=[...],
    response_format={
        "type": "json_schema",
        "json_schema": {
            "name": "weather_response",
            "schema": {
                "type": "object",
                "properties": {
                    "city": {"type": "string"},
                    "temperature": {"type": "number"},
                    "unit": {"type": "string", "enum": ["C", "F"]},
                    "condition": {"type": "string"},
                    "advice": {"type": "string"},
                },
                "required": ["city", "temperature", "unit", "condition", "advice"],
                "additionalProperties": False,
            },
        },
    },
)
```

## 在 Function Calling 中结合 Structured Output

Tool 的 Parameters 本身就是 JSON Schema，这意味着你的工具定义天然具备结构化约束：

```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "search_papers",
            "description": "搜索学术论文",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词"},
                    "max_results": {"type": "integer", "description": "返回条数", "default": 5},
                    "sort_by": {
                        "type": "string",
                        "enum": ["relevance", "date", "citations"],
                        "description": "排序方式",
                    },
                },
                "required": ["query"],
            },
        },
    }
]
```

## 为什么 structured output 对 Agent 重要？

1. **Tool 调用天然是结构化的。** LLM 输出的 tool_calls 本身就是 JSON，不需要猜测。
2. **评估可以自动化。** Agent 的输出如果是结构化 JSON，你可以写检查脚本自动验证。
3. **状态共享。** 多轮对话或跨 Agent 传递信息时，结构化数据比自然语言可靠得多。

## 不支持的模型怎么办？

DeepSeek v4 Flash 原生支持 `response_format`，但在以下情况你可能需要退而求其次：

1. **使用的模型不支持 `response_format`**：某些旧模型或其他厂商的模型可能不支持
2. **需要更灵活的控制**：原生 Structured Output 无法覆盖所有边界情况

替代方案——通过 system prompt 约束：

```python
# 通过 system prompt 约束
system_prompt = """
你是一个数据提取助手。请始终以 JSON 格式回复，格式如下：
{
    "city": "城市名",
    "temperature": 数字,
    "condition": "天气状况"
}
不要输出任何其他文字。
"""
```

这种方式可靠性比原生 Structured Output 低，建议在关键场景尽量使用支持此功能的模型。

## 练习

1. 定义一个会议日程的 JSON Schema（标题、时间、参与人、地点），让 LLM 从一段自由文本中提取结构化数据并输出
2. 实现一个 tool，其参数包含嵌套的 JSON 对象
3. 对比 prompt 约束 vs 原生 Structured Output 的可靠性

## 检查清单

- [ ] 能使用 Structured Outputs 约束 LLM 输出为 JSON
- [ ] 能定义包含枚举、嵌套对象的 JSON Schema
- [ ] 能在 Function Calling 的 tool schema 中使用结构化参数
