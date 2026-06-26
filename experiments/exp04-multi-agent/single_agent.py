"""
实验 4 - 版本 A：单 Agent 客服
一个 Agent 完成所有任务（意图识别 → 查询 → 处理）
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

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "query_order",
            "description": "查询订单信息",
            "parameters": {
                "type": "object",
                "properties": {"order_id": {"type": "string", "description": "订单号"}},
                "required": ["order_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "process_refund",
            "description": "执行退款操作",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string"},
                    "reason": {"type": "string", "description": "退款原因"},
                },
                "required": ["order_id", "reason"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_order_by_description",
            "description": "根据用户描述查找可能的订单",
            "parameters": {
                "type": "object",
                "properties": {"description": {"type": "string", "description": "用户对订单的描述"}},
                "required": ["description"],
            },
        },
    },
]


class SingleAgent:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def run(self, user_input: str) -> dict:
        messages = [{
            "role": "system",
            "content": "你是客服。你可以查询订单、处理退款。一步步完成用户的需求。"
        }, {"role": "user", "content": user_input}]

        tool_calls_log = []
        start_time = time.time()

        for turn in range(10):
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                tools=TOOLS,
            )
            msg = response.choices[0].message

            # 记录 token
            usage = {
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
            }

            if msg.tool_calls:
                messages.append(msg)
                for tc in msg.tool_calls:
                    name = tc.function.name
                    args = json.loads(tc.function.arguments)
                    result = self._execute(name, args)
                    tool_calls_log.append({"tool": name, "args": args, "result": result})
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps(result, ensure_ascii=False),
                    })
            else:
                elapsed = time.time() - start_time
                return {
                    "answer": msg.content,
                    "tool_calls": tool_calls_log,
                    "usage": usage,
                    "elapsed_seconds": round(elapsed, 2),
                }

        return {"answer": "超时", "tool_calls": tool_calls_log, "usage": {}, "elapsed_seconds": round(time.time() - start_time, 2)}

    def _execute(self, name, args):
        if name == "query_order":
            oid = args.get("order_id")
            return ORDER_DB.get(oid, {"error": "订单不存在"})
        elif name == "process_refund":
            return {"status": "success", "message": f"订单 {args['order_id']} 退款已发起"}
        elif name == "find_order_by_description":
            return {"suggestions": [k for k in ORDER_DB.keys()]}
        return {"error": "未知工具"}
