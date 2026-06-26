# Phase 1-02: Function Calling

## 什么是 Function Calling？

Function Calling 不是让 LLM 去执行函数，而是让 LLM **识别需要调用函数的意图并输出参数**。实际的函数执行由你的代码完成。

流程：

```
用户提问 → LLM 分析 → 决定调用哪个工具 → 输出工具名+参数
         → 你的代码执行工具 → 结果返回 LLM → LLM 生成自然语言回复
```

## Tool Schema 定义

你需要告诉 LLM 有哪些工具可用，每个工具的参数结构是什么。DeepSeek 兼容 OpenAI 格式，使用 JSON Schema 描述：

```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "查询指定城市的实时天气",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称",
                    }
                },
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_clothing_advice",
            "description": "根据天气给出穿衣建议",
            "parameters": {
                "type": "object",
                "properties": {
                    "temperature": {
                        "type": "number",
                        "description": "当前温度（摄氏度）",
                    },
                    "weather": {
                        "type": "string",
                        "description": "天气状况（晴/雨/雪等）",
                    },
                },
                "required": ["temperature", "weather"],
            },
        },
    },
]
```

## 核心调用模式

```python
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)

response = client.chat.completions.create(
    model="deepseek-v4-flash",
    messages=[{"role": "user", "content": "深圳今天穿什么？"}],
    tools=tools,           # ← 注册可用工具
    tool_choice="auto",    # ← 让模型自主决定是否调工具
)

message = response.choices[0].message

# 检查模型是否要求调用工具
if message.tool_calls:
    for tool_call in message.tool_calls:
        func_name = tool_call.function.name
        func_args = json.loads(tool_call.function.arguments)
        print(f"调用: {func_name}({func_args})")
else:
    print(f"直接回复: {message.content}")
```

## 工具执行分发

```python
def execute_tool(name: str, args: dict) -> str:
    """工具路由：根据名称执行对应的函数"""
    if name == "get_weather":
        return json.dumps({"temperature": 28, "weather": "晴"})
    elif name == "get_clothing_advice":
        temp = args["temperature"]
        weather = args["weather"]
        if temp > 25:
            return "建议穿短袖短裤，注意防晒。"
        elif temp < 10:
            return "建议穿羽绒服，注意保暖。"
        else:
            return "建议穿长袖 T 恤。"
    else:
        raise ValueError(f"未知工具: {name}")
```

## 完整的一轮 Tool Calling 流程

```python
import json
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)

# 第 1 轮：用户提问，LLM 返回 tool call
response = client.chat.completions.create(
    model="deepseek-v4-flash",
    messages=[{"role": "user", "content": "深圳今天穿什么？"}],
    tools=tools,
    tool_choice="auto",
)

msg = response.choices[0].message

# 第 2 轮：执行工具，将结果送回 LLM
if msg.tool_calls:
    messages = [{"role": "user", "content": "深圳今天穿什么？"}]
    messages.append(msg)  # 加入 assistant 的 tool_calls 响应

    for tc in msg.tool_calls:
        result = execute_tool(tc.function.name, json.loads(tc.function.arguments))
        messages.append({
            "role": "tool",
            "tool_call_id": tc.id,
            "content": result,
        })

    # 让 LLM 基于工具结果生成最终回复
    final = client.chat.completions.create(
        model="deepseek-v4-flash",
        messages=messages,
        tools=tools,
    )
    print(final.choices[0].message.content)
```

## tool_choice 策略

| 值 | 行为 | 适用场景 |
|----|------|---------|
| `"auto"` | 模型自主决定 | 大部分场景 |
| `"required"` | 强制调用工具 | 测试或特定流程 |
| `{"type": "function", "function": {"name": "xxx"}}` | 强制使用指定工具 | 定向路由 |

## DeepSeek Function Calling 注意事项

DeepSeek v4 Flash 的 Function Calling 完全兼容 OpenAI 格式，但需要注意：

- **tool_call_id**：格式与 OpenAI 一致，使用 `call_` 前缀
- **并行工具调用**：支持一次返回多个 tool_calls（parallel tool calling）
- **tool_choice 行为**：`"auto"`、`"required"`、`"none"` 三种策略均支持
- **严格模式**：不支持 OpenAI 的 `strict` 参数，但 JSON Schema 定义足够严格时效果相当

```python
# DeepSeek 的 tool_choice 用法与 OpenAI 完全一致
tool_choice = "auto"                                   # 自主决定
tool_choice = "required"                               # 强制调用
tool_choice = {"type": "function", "function": {"name": "get_weather"}}  # 指定工具
```

## 常见错误

1. **Parameter 命名不一致：** tool schema 里的参数名和实际函数的参数名必须一致。
2. **缺少 required 字段：** 都必须的参数必须标注 `"required": [...]`。
3. **description 太模糊：** LLM 依赖 description 决定是否调用某个工具，写得越清楚越好。

## 练习

1. 实现三个工具：天气查询、汇率转换、新闻搜索
2. 让 LLM 自主选择：用户问"东京气温多少度？"时调用天气工具，"人民币兑美元"时调用汇率工具
3. 处理工具调用失败的情况（如 API 没响应），让 LLM 给出友好提示

## 检查清单

- [ ] 能编写工具 Schema 并注册到 LLM
- [ ] 能解析 LLM 返回的 tool_calls
- [ ] 能实现工具路由分发
- [ ] 能处理一轮完整的 tool_calling 循环
- [ ] 了解 auto/required/强制指定三种策略
