# Phase 1-04: ReAct 循环手写

## ReAct 是什么？

ReAct = **Rea**soning + **Act**ion。

它让 LLM 在"思考"（推理）和"行动"（调用工具/查询知识）之间循环，直到得出最终答案。

```
思考 → 行动 → 观察 → 思考 → 行动 → 观察 → ... → 最终答案
```

## 核心循环

```python
class ReActAgent:
    """手写 ReAct Agent，不依赖任何框架"""

    def __init__(self, tools: list[dict], tool_handlers: dict[str, callable]):
        self.tools = tools
        self.tool_handlers = tool_handlers

    def run(self, user_input: str, max_turns: int = 10) -> str:
        messages = [{"role": "user", "content": user_input}]

        for turn in range(max_turns):
            # 1. 调用 LLM
            response = self._call_llm(messages)

            # 2. 检查是否有 tool call
            if response.tool_calls:
                for tc in response.tool_calls:
                    # 记录思考
                    messages.append(response)

                    # 3. 执行工具
                    result = self._execute_tool(tc)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": result,
                    })
                    print(f"  [{turn}] 调用 {tc.function.name} → {result[:60]}...")
            else:
                # 4. 没有 tool call，输出最终答案
                return response.content

        return "达到最大轮数，未完成。"
```

## 完整实现

```python
import json
from openai import OpenAI

class ReActAgent:
    def __init__(self, tools: list[dict], tool_handlers: dict[str, callable], model: str = "gpt-4o-mini"):
        self.client = OpenAI()
        self.tools = tools
        self.tool_handlers = tool_handlers
        self.model = model

    def _call_llm(self, messages: list[dict]):
        return self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=self.tools if self.tools else None,
        ).choices[0].message

    def _execute_tool(self, tool_call) -> str:
        name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)

        handler = self.tool_handlers.get(name)
        if not handler:
            return json.dumps({"error": f"未知工具: {name}"})

        try:
            result = handler(**args)
            return json.dumps(result, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": str(e)})

    def run(self, user_input: str, system_prompt: str = "你是一个智能助手。使用工具有效回答问题。", max_turns: int = 10) -> str:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input},
        ]

        for turn in range(max_turns):
            print(f"  [Turn {turn + 1}] 请求 LLM...")
            response = self._call_llm(messages)

            if response.tool_calls:
                messages.append(response)
                for tc in response.tool_calls:
                    result = self._execute_tool(tc)
                    print(f"  → 工具: {tc.function.name}, 参数: {tc.function.arguments}")
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": result,
                    })
            else:
                print(f"  ✓ 最终回答")
                return response.content

        return "达到最大轮数，未完成。"


# ===== 使用示例 =====

def search_arxiv(query: str, max_results: int = 3):
    """模拟 arXiv 搜索"""
    return {"papers": [
        {"title": f"Paper about {query}", "authors": ["A. Researcher"], "year": 2025},
        {"title": f"Advances in {query}", "authors": ["B. Scientist"], "year": 2024},
    ]}

def get_weather(city: str):
    """模拟天气查询"""
    import random
    temps = {"深圳": 28, "北京": 15, "上海": 22, "广州": 30}
    return {"city": city, "temperature": temps.get(city, 25), "condition": "晴"}

tools = [
    {
        "type": "function",
        "function": {
            "name": "search_arxiv",
            "description": "搜索 arXiv 学术论文",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词"},
                    "max_results": {"type": "integer", "description": "返回条数"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "查询天气",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "城市"},
                },
                "required": ["city"],
            },
        },
    },
]

handlers = {
    "search_arxiv": search_arxiv,
    "get_weather": get_weather,
}

if __name__ == "__main__":
    agent = ReActAgent(tools=tools, tool_handlers=handlers)
    result = agent.run("深圳今天天气怎么样？搜索一下有关 Agent 的最新论文")
    print(f"\n最终回答:\n{result}")
```

## ReAct 的变体

### 1. 带反思（Reflection）

在 ReAct 基础上增加一步：在给出最终答案前，先自我检查并修正：

```python
def run_with_reflection(self, user_input: str):
    # 第一遍：正常 ReAct
    answer = self.run(user_input)

    # 第二遍：反思
    reflection_prompt = f"""
    用户问题: {user_input}
    你的回答: {answer}

    请检查你的回答是否完整准确。如果发现错误或遗漏，请修正。
    """
    reflection = self._call_llm([{"role": "user", "content": reflection_prompt}])
    return reflection.content
```

### 2. 带规划（Plan-Act）

先规划再执行，而不是边想边做：

```python
def run_with_plan(self, user_input: str):
    # 先让 LLM 制定计划
    plan_prompt = f"""
    用户问题: {user_input}
    请制定一个分步骤的执行计划，列出需要调用哪些工具，按什么顺序。
    """
    plan = self._call_llm([{"role": "user", "content": plan_prompt}])

    # 再按计划执行
    return self.run(f"按照以下计划执行: {plan.content}\n\n原始问题: {user_input}")
```

## ReAct 的常见失败模式

| 模式 | 表现 | 解决方法 |
|------|------|---------|
| 无限循环 | 不断调用工具，没有终止 | 加 max_turns 硬限制 |
| 过早终止 | 应该继续却输出了最终答案 | 在 system prompt 强调"不要过早结束" |
| 幻觉参数 | 编造不存在的工具参数 | 参数校验 + 重试 |
| 上下文溢出 | 对话太长超过 token 限制 | 对话摘要/截断策略 |

## 练习

1. 运行上面的 ReAct Agent，观察它在多轮 tool call 时的行为
2. 增加一个"反思"步骤：在最终回答前先自我检查
3. 增加 max_turns 保护，防止无限循环
4. 写一个 FAILURES.md，记录你的 Agent 在什么情况下会挂

## 检查清单

- [ ] 能不依赖框架手写 ReAct 循环
- [ ] 理解 thought → action → observation 的完整链路
- [ ] 能处理多轮 tool call
- [ ] 能设置 max_turns 防止无限循环
- [ ] 知道 ReAct 的常见失败模式
