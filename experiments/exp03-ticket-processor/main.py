"""
实验 3：自动化工单处理机器人

核心概念：工作流编排（LangGraph）、异常处理、代码解释器
"""

import csv
import json
import os
import sys
import subprocess
import tempfile
from typing import TypedDict, Literal
from openai import OpenAI
from rich.table import Table


# ==================== 状态定义 ====================

class TicketState(TypedDict):
    """工作流状态"""
    file_path: str                     # CSV 文件路径
    raw_data: list[dict]               # 原始数据
    errors: list[str]                  # 异常记录
    classification: dict | None        # 分类结果
    statistics: dict | None            # 统计数据
    report: str | None                 # 最终报告
    completed: bool                    # 是否完成


# ==================== 工具：代码解释器 ====================

def execute_python(code: str, timeout: int = 30) -> dict:
    """在沙箱中执行 Python 代码"""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False
    ) as f:
        f.write(code)
        f.flush()
        script_path = f.name

    try:
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "return_code": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"stdout": "", "stderr": "执行超时", "return_code": -1}
    finally:
        os.unlink(script_path)


# ==================== 工作流节点 ====================

def load_csv(state: TicketState) -> TicketState:
    """节点1：加载 CSV 数据"""
    print("  [Step 1/5] 加载 CSV 数据...")
    try:
        with open(state["file_path"], "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            state["raw_data"] = list(reader)
        print(f"  读取了 {len(state['raw_data'])} 条记录")
        print(f"  列名: {list(state['raw_data'][0].keys()) if state['raw_data'] else '空'}")
    except Exception as e:
        state["errors"].append(f"CSV 加载失败: {e}")
        state["completed"] = True
    return state


def validate_data(state: TicketState) -> TicketState:
    """节点2：数据校验"""
    print("  [Step 2/5] 校验数据...")

    if "errors" not in state:
        state["errors"] = []

    for i, row in enumerate(state["raw_data"]):
        issues = []
        # 检查必要字段
        for field in ["id", "type", "description"]:
            if field not in row or not row[field].strip():
                issues.append(f"缺少字段: {field}")

        if issues:
            state["errors"].append(f"第 {i+1} 行异常: {'; '.join(issues)}")
            print(f"  ⚠ 异常数据: 第 {i+1} 行 - {issues[0]}")

    if state["errors"]:
        print(f"  共发现 {len(state['errors'])} 个异常")
    else:
        print("  数据校验通过")
    return state


def classify_tickets(state: TicketState) -> TicketState:
    """节点3：工单分类（用代码解释器）"""
    print("  [Step 3/5] 分类工单...")

    # 让 LLM 生成统计代码
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    data_json = json.dumps(state["raw_data"][:5], ensure_ascii=False)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": f"""CSV 数据样例: {data_json}

根据 type 字段对工单进行分类统计。请生成 Python 代码（使用 json 和 collections.Counter）：
1. 解析数据
2. 按 type 统计数量
3. 输出 JSON 格式的统计结果

只输出代码，不要解释。""",
        }],
    )

    code = response.choices[0].message.content
    # 包装代码
    wrapped_code = f"""
import json
from collections import Counter

data = {json.dumps(state["raw_data"], ensure_ascii=False)}

counter = Counter(item.get("type", "unknown") for item in data)
result = {{
    "total": len(data),
    "by_type": dict(counter),
    "valid": sum(1 for item in data if item.get("type")),
    "invalid": sum(1 for item in data if not item.get("type")),
}}
print(json.dumps(result, ensure_ascii=False))
"""

    exec_result = execute_python(wrapped_code)

    if exec_result["return_code"] == 0:
        try:
            state["classification"] = json.loads(exec_result["stdout"].strip())
            print(f"  分类完成: {state['classification']}")
        except json.JSONDecodeError:
            state["errors"].append("分类结果解析失败")
            print(f"  ⚠ 分类输出异常: {exec_result['stdout'][:100]}")
    else:
        state["errors"].append(f"分类执行失败: {exec_result['stderr']}")
        print(f"  ⚠ 分类执行失败")

    return state


def analyze_data(state: TicketState) -> TicketState:
    """节点4：数据分析"""
    print("  [Step 4/5] 分析数据...")

    # 如果分类失败，使用降级方案
    if not state.get("classification"):
        print("  ⚠ 使用降级方案：跳过代码执行，基于已有信息生成本地统计")
        local_stats = {"total": len(state["raw_data"])}
        type_counts = {}
        for row in state["raw_data"]:
            t = row.get("type", "unknown")
            type_counts[t] = type_counts.get(t, 0) + 1
        local_stats["by_type"] = type_counts
        state["statistics"] = local_stats
        print(f"  {local_stats}")
        return state

    state["statistics"] = state["classification"]
    return state


def generate_report(state: TicketState) -> TicketState:
    """节点5：生成报告"""
    print("  [Step 5/5] 生成报告...")

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    stats_text = json.dumps(state.get("statistics", {}), ensure_ascii=False, indent=2)
    errors_text = "\n".join(state.get("errors", [])) if state.get("errors") else "无异常"

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": f"""根据以下工单处理结果生成一份简洁的汇总报告：

统计: {stats_text}

异常记录:
{errors_text}

报告格式：
- 总览（工单总数、分类分布）
- 异常情况
- 建议"""

        }],
    )

    state["report"] = response.choices[0].message.content
    state["completed"] = True
    print(f"\n{state['report']}")
    return state


# ==================== 条件边 ====================

def should_proceed(state: TicketState) -> Literal["validate", "report"]:
    """判断是否需要跳过异常数据"""
    if state.get("errors"):
        return "report"
    return "validate"

def should_generate_report(state: TicketState) -> Literal["generate", "end"]:
    if state.get("completed"):
        return "end"
    return "generate"


# ==================== 图构建 ====================

from langgraph.graph import StateGraph, END

def build_workflow() -> StateGraph:
    """构建工单处理工作流图"""
    workflow = StateGraph(TicketState)

    # 添加节点
    workflow.add_node("load", load_csv)
    workflow.add_node("validate", validate_data)
    workflow.add_node("classify", classify_tickets)
    workflow.add_node("analyze", analyze_data)
    workflow.add_node("generate", generate_report)

    # 连接边
    workflow.set_entry_point("load")
    workflow.add_edge("load", "validate")
    workflow.add_conditional_edges("validate", should_proceed, {
        "validate": "classify",
        "report": "generate",
    })
    workflow.add_edge("classify", "analyze")
    workflow.add_edge("analyze", "generate")
    workflow.add_edge("generate", END)

    return workflow.compile()


# ==================== 主流程 ====================

def main():
    app = build_workflow()

    print("=" * 50)
    print("  自动化工单处理（实验 3）")
    print("=" * 50)

    # 准备样本数据
    sample_file = "sample_data.csv"
    if not os.path.exists(sample_file):
        create_sample_data(sample_file)

    # 执行
    initial_state: TicketState = {
        "file_path": sample_file,
        "raw_data": [],
        "errors": [],
        "classification": None,
        "statistics": None,
        "report": None,
        "completed": False,
    }

    print(f"\n处理文件: {sample_file}")
    print("-" * 50)

    result = app.invoke(initial_state)

    print("\n" + "=" * 50)
    print("最终报告:")
    print(result.get("report", "无报告"))
    print("=" * 50)


def create_sample_data(file_path: str):
    """创建示例 CSV 数据"""
    import random

    ticket_types = ["退款", "咨询", "投诉", "退货", "售后"]
    descriptions = [
        "收到商品与描述不符，要求退款",
        "询问发货时间",
        "产品质量有问题，要求赔偿",
        "想退货但已过了退货期",
        "咨询售后政策",
        "物流太慢，投诉快递",
        "收到破损商品",
        "询问退换货流程",
        "要求重新发货",
        "咨询会员优惠",
    ]

    with open(file_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "type", "description", "amount", "date"])

        for i in range(15):
            row = [
                f"ORD-{2024000 + i}",
                random.choice(ticket_types),
                random.choice(descriptions),
                round(random.uniform(50, 500), 2),
                f"2026-06-{random.randint(1, 20):02d}",
            ]
            writer.writerow(row)

        # 故意加一条异常数据
        writer.writerow(["ORD-999999", "", "", "", "2026-06-21"])

    print(f"  已创建样本数据: {file_path}（含 1 条异常）")


if __name__ == "__main__":
    main()
