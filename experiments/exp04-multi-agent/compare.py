"""
实验 4：单 Agent vs 多 Agent 对照实验

对比两个版本在同一任务集上的表现。
"""

import json
from single_agent import SingleAgent
from multi_agent import MultiAgentTeam
from rich.console import Console
from rich.table import Table

console = Console()

TEST_CASES = [
    "我想查一下我的订单 ORD-2024-001",
    "帮我查一下 ORD-2024-003 到哪了",
    "我上周买了个蓝牙耳机，想退款",
    "我的订单 ORD-2024-002 什么时候发货？",
    "我收到的手机构有质量问题，要求退货退款",
]

def estimate_cost(usage: dict) -> float:
    """估算费用（gpt-4o-mini 价格）"""
    prompt_cost = 0.15 / 1_000_000  # 每 token
    completion_cost = 0.60 / 1_000_000
    return (usage.get("prompt_tokens", 0) * prompt_cost +
            usage.get("completion_tokens", 0) * completion_cost)


def main():
    console.print("=" * 60, style="bold")
    console.print("  单 Agent vs 多 Agent 对照实验", style="bold")
    console.print("=" * 60)

    single = SingleAgent()
    multi = MultiAgentTeam()

    table = Table(title="对照结果")
    table.add_column("测试用例", style="cyan", no_wrap=True)
    table.add_column("单 Agent", justify="center")
    table.add_column("多 Agent", justify="center")

    single_results = []
    multi_results = []

    for i, test in enumerate(TEST_CASES, 1):
        console.print(f"\n[{i}/{len(TEST_CASES)}] {test}", style="yellow")

        console.print("  [单 Agent]", style="green")
        sr = single.run(test)
        single_results.append(sr)

        console.print("  [多 Agent]", style="blue")
        mr = multi.run(test)
        multi_results.append(mr)

        single_ok = len(sr["answer"]) > 10
        multi_ok = len(mr["answer"]) > 10

        single_label = f"{'✅' if single_ok else '❌'} ${estimate_cost(sr['usage']):.5f}"
        multi_label = f"{'✅' if multi_ok else '❌'} ${estimate_cost(mr['usage']):.5f}"

        table.add_row(test[:30] + "...", single_label, multi_label)

    console.print(table)

    # 统计汇总
    print("\n" + "=" * 60)
    print("汇总对比")
    print("=" * 60)

    s_total_tokens = sum(r["usage"].get("prompt_tokens", 0) + r["usage"].get("completion_tokens", 0) for r in single_results)
    m_total_tokens = sum(r["usage"].get("prompt_tokens", 0) + r["usage"].get("completion_tokens", 0) for r in multi_results)
    s_total_cost = sum(estimate_cost(r["usage"]) for r in single_results)
    m_total_cost = sum(estimate_cost(r["usage"]) for r in multi_results)
    s_avg_time = sum(r["elapsed_seconds"] for r in single_results) / len(single_results)
    m_avg_time = sum(r["elapsed_seconds"] for r in multi_results) / len(multi_results)

    print(f"\n{'指标':<25} {'单 Agent':>15} {'多 Agent':>15}")
    print("-" * 55)
    print(f"{'总 Token':<25} {s_total_tokens:>15} {m_total_tokens:>15}")
    print(f"{'总费用 ($)':<25} {s_total_cost:>15.6f} {m_total_cost:>15.6f}")
    print(f"{'平均耗时 (秒)':<25} {s_avg_time:>15.2f} {m_avg_time:>15.2f}")
    print(f"{'测试用例数':<25} {len(TEST_CASES):>15} {len(TEST_CASES):>15}")

    # 结论
    print(f"\n{'结论':<25}")
    print("-" * 55)
    if s_total_cost < m_total_cost:
        print(f"→ 单 Agent 更低成本 (${s_total_cost:.6f} vs ${m_total_cost:.6f})")
    else:
        print(f"→ 多 Agent 更高成本 (${s_total_cost:.6f} vs ${m_total_cost:.6f})")
    if s_avg_time < m_avg_time:
        print(f"→ 单 Agent 响应更快 ({s_avg_time:.2f}s vs {m_avg_time:.2f}s)")
    else:
        print(f"→ 多 Agent 响应更快 ({s_avg_time:.2f}s vs {m_avg_time:.2f}s)")


if __name__ == "__main__":
    main()
