"""
实验 4 - 版本 B：多 Agent 客服团队
角色分工：接待 → 查询 → 处理
"""

import json
import os
import time
from openai import OpenAI

# 模拟订单数据库
ORDER_DB = {
    "ORD-2024-001": {"status": "已发货", "amount": 299.00, "date": "2026-06-15", "items": "蓝牙耳机"},
    "ORD-2024-002": {"status": "待发货", "amount": 159.00, "date": "2026-06-18", "items": "手机壳"},
    "ORD-2024-003": {"status": "已送达", "amount": 899.00, "date": "2026-06-10", "items": "键盘"},
}


class MultiAgentTeam:
    """多 Agent 客服团队"""

    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com")

    def _call(self, system_prompt: str, user_input: str, tools: list = None) -> tuple[str, dict]:
        """调用 LLM（简化版，不含 tool call）"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input},
        ]
        response = self.client.chat.completions.create(
            model="deepseek-v4-flash",
            messages=messages,
            tools=tools,
        )
        msg = response.choices[0].message
        usage = {
            "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
            "completion_tokens": response.usage.completion_tokens if response.usage else 0,
        }
        return msg.content or "", usage

    def run(self, user_input: str) -> dict:
        start_time = time.time()
        total_usage = {"prompt_tokens": 0, "completion_tokens": 0}
        tool_calls_log = []

        # === Step 1: 接待 Agent ===
        print("  [接待] 接收用户...")
        reception_prompt = (
            "你是客服接待员。负责理解用户意图，安抚情绪。\n"
            "请从用户输入中提取：意图（退款/查询/投诉）、订单号（如果有）、情绪状态。\n"
            "输出格式：意图=XXX, 订单号=XXX, 情绪=XXX"
        )
        reception, usage = self._call(reception_prompt, user_input)
        total_usage["prompt_tokens"] += usage["prompt_tokens"]
        total_usage["completion_tokens"] += usage["completion_tokens"]
        tool_calls_log.append({"agent": "接待", "output": reception})
        print(f"  → {reception}")

        # === Step 2: 查询 Agent ===
        print("  [查询] 查询订单...")
        query_tools = [
            {
                "type": "function",
                "function": {
                    "name": "query_order",
                    "description": "查询订单",
                    "parameters": {
                        "type": "object",
                        "properties": {"order_id": {"type": "string"}},
                        "required": ["order_id"],
                    },
                },
            }
        ]

        query_messages = [
            {"role": "system", "content": "你负责查询订单信息。使用 query_order 工具。"},
            {"role": "user", "content": f"用户输入: {user_input}\n\n接待分析: {reception}\n查询订单信息。"},
        ]

        query_response = self.client.chat.completions.create(
            model="deepseek-v4-flash",
            messages=query_messages,
            tools=query_tools,
        )
        qmsg = query_response.choices[0].message
        total_usage["prompt_tokens"] += query_response.usage.prompt_tokens or 0
        total_usage["completion_tokens"] += query_response.usage.completion_tokens or 0

        query_result = ""
        if qmsg.tool_calls:
            for tc in qmsg.tool_calls:
                name = tc.function.name
                args = json.loads(tc.function.arguments)
                oid = args.get("order_id", "")
                order = ORDER_DB.get(oid, {"error": "未找到"})
                query_result = json.dumps(order, ensure_ascii=False)
                tool_calls_log.append({"agent": "查询", "tool": name, "args": args, "result": query_result})

        print(f"  → {query_result}")

        # === Step 3: 处理 Agent ===
        print("  [处理] 执行操作...")
        process_prompt = (
            "你是客服处理员。根据前面的信息执行最终操作。\n"
            "如果用户要求退款且订单状态允许，确认处理。\n"
            "如果只是查询，将查询结果组织成友好的回复。\n"
            "如果无法处理，说明原因。"
        )
        process_info = f"接待分析: {reception}\n订单信息: {query_result}\n用户原始输入: {user_input}"
        process_result, usage = self._call(process_prompt, process_info)
        total_usage["prompt_tokens"] += usage["prompt_tokens"]
        total_usage["completion_tokens"] += usage["completion_tokens"]
        tool_calls_log.append({"agent": "处理", "output": process_result})

        elapsed = time.time() - start_time
        return {
            "answer": process_result,
            "tool_calls": tool_calls_log,
            "usage": {
                "prompt_tokens": total_usage["prompt_tokens"],
                "completion_tokens": total_usage["completion_tokens"],
            },
            "elapsed_seconds": round(elapsed, 2),
        }
