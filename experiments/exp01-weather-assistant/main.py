"""
实验 1：基础工具调用助手（天气助手）
核心概念：ReAct + Tool Calling
"""

import json
import os
import sys
from openai import OpenAI


# ==================== 工具定义 ====================

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "查询指定城市的实时天气，返回温度、天气状况等",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称，如 深圳、北京、上海、广州",
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
            "description": "根据温度和天气状况给出穿衣建议",
            "parameters": {
                "type": "object",
                "properties": {
                    "temperature": {
                        "type": "number",
                        "description": "当前温度（摄氏度）",
                    },
                    "condition": {
                        "type": "string",
                        "description": "天气状况，如 晴、雨、雪、多云",
                    },
                },
                "required": ["temperature", "condition"],
            },
        },
    },
]


# ==================== 工具实现 ====================

# 模拟天气数据
WEATHER_DB = {
    "深圳": {"temperature": 28, "condition": "晴", "humidity": 65},
    "北京": {"temperature": 15, "condition": "多云", "humidity": 40},
    "上海": {"temperature": 22, "condition": "小雨", "humidity": 80},
    "广州": {"temperature": 30, "condition": "晴", "humidity": 70},
    "成都": {"temperature": 20, "condition": "阴", "humidity": 55},
    "哈尔滨": {"temperature": 5, "condition": "晴", "humidity": 30},
}


def get_weather(city: str) -> str:
    """查询天气（模拟实现）"""
    data = WEATHER_DB.get(city)
    if data:
        return json.dumps({
            "city": city,
            "temperature": data["temperature"],
            "condition": data["condition"],
            "humidity": data["humidity"],
        }, ensure_ascii=False)
    return json.dumps({"error": f"未找到城市 {city} 的天气数据"})


def get_clothing_advice(temperature: float, condition: str) -> str:
    """给出穿衣建议"""
    advice_parts = []

    if temperature >= 25:
        advice_parts.append("建议穿短袖短裤，天气炎热注意防暑。")
    elif temperature >= 15:
        advice_parts.append("建议穿长袖 T 恤或薄外套。")
    else:
        advice_parts.append("建议穿厚外套或羽绒服，注意保暖。")

    if "雨" in condition:
        advice_parts.append("有雨，请携带雨具。")
    if "晴" in condition:
        advice_parts.append("紫外线较强，注意防晒。")

    return " ".join(advice_parts)


TOOL_HANDLERS = {
    "get_weather": get_weather,
    "get_clothing_advice": get_clothing_advice,
}


# ==================== ReAct Agent ====================

class ReActAgent:
    def __init__(self, model: str = "gpt-4o-mini"):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = model

    def run(self, user_input: str, max_turns: int = 10) -> tuple[str, list]:
        """执行 ReAct 循环，返回 (最终回答, 调用记录)"""
        messages = [
            {
                "role": "system",
                "content": (
                    "你是一个天气助手。你可以查询天气和给出穿衣建议。\n"
                    "规则：\n"
                    "1. 如果用户问天气或穿衣，调用对应工具\n"
                    "2. 如果用户问简单问题（算术、常识等），直接回答\n"
                    "3. 不要编造工具，只使用提供的工具\n"
                    "4. 给出最终答案前确保信息完整"
                ),
            },
            {"role": "user", "content": user_input},
        ]

        tool_calls_log = []

        for turn in range(max_turns):
            print(f"\n  [Turn {turn + 1}] LLM 思考中...")

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
            )

            msg = response.choices[0].message

            if msg.tool_calls:
                messages.append(msg)
                for tc in msg.tool_calls:
                    name = tc.function.name
                    args = json.loads(tc.function.arguments)
                    handler = TOOL_HANDLERS.get(name)
                    if handler:
                        result = handler(**args)
                    else:
                        result = json.dumps({"error": f"未知工具: {name}"})

                    print(f"  → 调用 {name}({args})")
                    tool_calls_log.append({"tool": name, "args": args, "result": result})

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": result,
                    })
            else:
                answer = msg.content
                return answer, tool_calls_log

        return "达到最大轮数，未完成。", tool_calls_log


# ==================== 交互式运行 ====================

def main():
    agent = ReActAgent()

    print("=" * 50)
    print("  天气助手（实验 1）")
    print("  输入 'exit' 退出，输入 'test' 运行评估")
    print("=" * 50)

    while True:
        try:
            user_input = input("\n你: ").strip()
            if user_input.lower() in ("exit", "quit", "q"):
                break
            if user_input.lower() == "test":
                run_eval(agent)
                continue
            if not user_input:
                continue

            answer, calls = agent.run(user_input)
            print(f"\n助手: {answer}")

        except KeyboardInterrupt:
            print("\n\n再见！")
            break
        except Exception as e:
            print(f"\n[错误] {e}")


def run_eval(agent):
    """运行内置评估测试"""
    print("\n" + "=" * 50)

    test_cases = [
        # (question, should_call_tool, expected_keywords)
        ("深圳天气怎么样？", True, ["28", "晴"]),
        ("北京今天穿什么？", True, ["外套", "长袖"]),
        ("上海气温多少度？", True, ["22"]),
        ("1 + 1 等于几？", False, ["2"]),
        ("中国的首都是哪里？", False, ["北京"]),
        ("广州今天适合穿短袖吗？", True, ["短袖", "30"]),
        ("什么是人工智能？", False, ["智能", "机器"]),
        ("哈尔滨冷不冷，该穿什么？", True, ["羽绒服", "厚外套"]),
        ("成都有雨吗？", True, ["阴"]),
        ("地球到月球的距离？", False, ["公里", "万"]),
    ]

    passed = 0
    for i, (question, should_tool, keywords) in enumerate(test_cases, 1):
        print(f"\n  [{i}/10] {question}")
        answer, calls = agent.run(question)
        called_tool = bool(calls)

        # 评估工具调用是否正确
        tool_ok = called_tool == should_tool
        # 评估关键词匹配
        kw_ok = all(kw in answer for kw in keywords)

        status = "✅" if (tool_ok and kw_ok) else "❌"
        if status == "❌":
            reasons = []
            if not tool_ok:
                reasons.append(f"工具调用: 期望={should_tool}, 实际={called_tool}")
            if not kw_ok:
                reasons.append(f"关键词缺失: {keywords}")
            print(f"  {status} 失败: {'; '.join(reasons)}")
        else:
            print(f"  {status} 通过")

        if status == "✅":
            passed += 1

    print(f"\n  通过: {passed}/{len(test_cases)} ({passed/len(test_cases)*100:.0f}%)")
    print("=" * 50)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "eval":
        agent = ReActAgent()
        run_eval(agent)
    else:
        main()
