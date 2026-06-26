# Phase 2-01: MCP 协议入门

## 什么是 MCP？

MCP (Model Context Protocol) 是 Anthropic 在 2025 年推出的开放协议，定义了 LLM 应用如何与外部工具和数据源交互。它的核心思想是：

> LLM 通过一个标准化的 Server 发现和使用工具，而不是硬编码到代码里。

```
LLM 应用 ←→ MCP Client ←→ MCP Server ←→ 外部系统（API/数据库/文件系统）
```

## 为什么 MCP 重要？

在 MCP 出现之前，集成一个新工具需要：
1. 在代码中写 tool schema
2. 写工具执行函数
3. 手动注册到 Agent

有了 MCP：
- Server 声明自己有哪些工具、资源
- Client 自动发现并注册
- 工具执行通过标准协议传递

## 编写第一个 MCP Server

```python
# mcp_weather_server.py
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types

server = Server("weather-server")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="get_weather",
            description="查询指定城市的实时天气",
            inputSchema={
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称，如 深圳、北京",
                    },
                },
                "required": ["city"],
            },
        ),
        types.Tool(
            name="get_clothing_advice",
            description="根据天气情况给出穿衣建议",
            inputSchema={
                "type": "object",
                "properties": {
                    "temperature": {"type": "number", "description": "温度"},
                    "condition": {"type": "string", "description": "天气状况"},
                },
                "required": ["temperature", "condition"],
            },
        ),
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent]:
    if name == "get_weather":
        city = arguments.get("city", "深圳")
        # 模拟天气查询
        weather_data = {
            "深圳": {"temperature": 28, "condition": "晴"},
            "北京": {"temperature": 15, "condition": "多云"},
            "上海": {"temperature": 22, "condition": "小雨"},
        }
        result = weather_data.get(city, {"temperature": 25, "condition": "未知"})
        return [types.TextContent(type="text", text=str(result))]

    elif name == "get_clothing_advice":
        temp = arguments.get("temperature", 25)
        condition = arguments.get("condition", "晴")
        if temp > 25:
            advice = "建议穿短袖短裤，注意防晒。"
        elif temp < 10:
            advice = "建议穿羽绒服，注意保暖。"
        else:
            advice = "建议穿长袖 T 恤。"
        return [types.TextContent(type="text", text=advice)]

    raise ValueError(f"Unknown tool: {name}")

async def main():
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="weather-server",
                server_version="0.1.0",
            ),
        )

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

## 在 Agent 中使用 MCP Client

```python
# mcp_client.py
import asyncio
from openai import OpenAI
import mcp.types as types

class MCPAgent:
    """通过 MCP 协议连接工具的 Agent"""

    def __init__(self, server_process, tools: list):
        self.client = OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com",
        )
        self.server_process = server_process
        self.mcp_tools = tools

    def _to_openai_tools(self) -> list[dict]:
        """将 MCP tool 格式转换为 OpenAI (DeepSeek) tool 格式"""
        openai_tools = []
        for tool in self.mcp_tools:
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema,
                },
            })
        return openai_tools

    async def run(self, user_input: str):
        tools = self._to_openai_tools()
        messages = [{"role": "user", "content": user_input}]

        response = self.client.chat.completions.create(
            model="deepseek-v4-flash",
            messages=messages,
            tools=tools,
        )

        msg = response.choices[0].message
        if msg.tool_calls:
            print("调用 MCP 工具...")
            # 实际使用中需要通过 MCP 通信执行工具
            for tc in msg.tool_calls:
                print(f"  工具: {tc.function.name}, 参数: {tc.function.arguments}")
```

## MCP 的更多能力

- **Resources（资源）：** Server 可以暴露文件、数据等资源，Client 通过 URI 读取
- **Prompts（提示）：** Server 可以提供预设的提示模板
- **Sampling（采样）：** Server 可以反过来请求 LLM 生成内容（双向通信）

## 练习

1. 运行上面的 MCP Server，测试工具发现和执行
2. 增加一个"translate"工具，支持文本翻译
3. 写一个 MCP Client 连接到你的 Server，通过 Agent 调用工具

## 检查清单

- [ ] 能编写 MCP Server 并注册工具
- [ ] 能运行 MCP Server 并通过 stdio 通信
- [ ] 理解 MCP 的 Tool/Resource/Prompt 三层概念
- [ ] 能将 MCP tool 与 LLM 的 Function Calling 对接
