"""
实验 5：Agent 质量监控与退化检测系统

核心概念：自动化评估 pipeline、退化检测、离线回放
"""

import json
import os
import random
from datetime import datetime
from openai import OpenAI


# ==================== 1. 日志模型 ====================

class AgentLog:
    """单条 Agent 对话日志"""
    def __init__(self, session_id: str, question: str, answer: str,
                 tools_called: list[str], tokens: int, latency_ms: int,
                 passed: bool = True, timestamp: str = None):
        self.session_id = session_id
        self.question = question
        self.answer = answer
        self.tools_called = tools_called
        self.tokens = tokens
        self.latency_ms = latency_ms
        self.passed = passed
        self.timestamp = timestamp or datetime.now().isoformat()

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "question": self.question,
            "answer": self.answer,
            "tools_called": self.tools_called,
            "tokens": self.tokens,
            "latency_ms": self.latency_ms,
            "passed": self.passed,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, d: dict):
        return cls(**d)


class LogStore:
    """日志存储"""

    def __init__(self, path: str = "logs.json"):
        self.path = path
        self.logs: list[AgentLog] = []
        self._load()

    def _load(self):
        if os.path.exists(self.path):
            with open(self.path, "r") as f:
                data = json.load(f)
                self.logs = [AgentLog.from_dict(item) for item in data]

    def save(self):
        with open(self.path, "w") as f:
            json.dump([log.to_dict() for log in self.logs], f, ensure_ascii=False, indent=2)

    def add(self, log: AgentLog):
        self.logs.append(log)
        self.save()

    def recent(self, n: int = 50) -> list[AgentLog]:
        return self.logs[-n:]

    def filter(self, **kwargs) -> list[AgentLog]:
        results = self.logs
        for key, value in kwargs.items():
            results = [l for l in results if getattr(l, key, None) == value]
        return results


# ==================== 2. 评估器 ====================

class QualityEvaluator:
    """评估 Pipeline：规则检查 + LLM-as-Judge"""

    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com")

    def rule_check(self, log: AgentLog) -> dict:
        """规则级别检查"""
        issues = []

        # 空回答
        if not log.answer or len(log.answer) < 5:
            issues.append("回答为空或过短")

        # 重复内容
        if log.answer and len(set(log.answer.split())) < len(log.answer.split()) * 0.3:
            issues.append("回答存在大量重复")

        # 工具调用异常
        if not log.tools_called and ("查询" in log.question or "查" in log.question):
            issues.append("需要工具调用但未调用")

        # 成本异常
        if log.tokens > 2000:
            issues.append(f"token 消耗过高 ({log.tokens})")

        return {
            "passed": len(issues) == 0,
            "issues": issues,
            "score": max(0, 5 - len(issues)),
        }

    def llm_judge(self, question: str, answer: str) -> dict:
        """LLM-as-Judge 评分"""
        response = self.client.chat.completions.create(
            model="deepseek-v4-flash",
            messages=[{
                "role": "user",
                "content": f"""你是一个评估专家。请从以下维度评分（1-5分）：

问题: {question}
回答: {answer}

{{
    "accuracy": 准确性 - 回答是否正确,
    "relevance": 相关性 - 回答是否切题,
    "helpfulness": 有用性 - 回答是否有帮助
}}

输出 JSON。""",
            }],
            response_format={"type": "json_object"},
        )

        try:
            return json.loads(response.choices[0].message.content)
        except json.JSONDecodeError:
            return {"accuracy": 3, "relevance": 3, "helpfulness": 3}

    def evaluate_log(self, log: AgentLog) -> dict:
        """综合评估单条日志"""
        rule_result = self.rule_check(log)
        llm_scores = self.llm_judge(log.question, log.answer)

        avg_llm = sum(llm_scores.values()) / len(llm_scores) if llm_scores else 0

        return {
            "session_id": log.session_id,
            "rule_check": rule_result,
            "llm_scores": llm_scores,
            "overall": (rule_result["score"] + avg_llm) / 2,
            "flagged": rule_result["score"] < 3 or avg_llm < 3,
        }


# ==================== 3. 退化检测器 ====================

class DegradationDetector:
    """检测 Agent 的退化趋势"""

    def __init__(self, window_size: int = 10):
        self.window_size = window_size
        self.history: list[dict] = []
        self.threshold = 0.5  # 连续下降阈值

    def feed(self, eval_result: dict):
        """加入一次评估结果"""
        self.history.append({
            "session_id": eval_result["session_id"],
            "overall": eval_result["overall"],
            "timestamp": datetime.now().isoformat(),
        })

        if len(self.history) > self.window_size * 2:
            self.history.pop(0)

    def check_degradation(self) -> dict | None:
        """检查是否发生退化"""
        if len(self.history) < self.window_size:
            return None

        # 比较最近 window 和之前 window 的平均分
        recent = [h["overall"] for h in self.history[-self.window_size:]]
        prev = [h["overall"] for h in self.history[-self.window_size*2:-self.window_size]]

        recent_avg = sum(recent) / len(recent)
        prev_avg = sum(prev) / len(prev)

        if prev_avg - recent_avg > self.threshold:
            return {
                "alert": "退化检测告警",
                "previous_avg": round(prev_avg, 2),
                "recent_avg": round(recent_avg, 2),
                "drop": round(prev_avg - recent_avg, 2),
                "sample_count": len(recent),
            }
        return None

    def summary(self) -> dict:
        """生成退化报告"""
        if len(self.history) < 5:
            return {"status": "数据不足", "count": len(self.history)}

        scores = [h["overall"] for h in self.history]
        trend = "上升" if len(scores) > 1 and scores[-1] > scores[0] else "下降"

        return {
            "status": "正常",
            "count": len(self.history),
            "avg_score": round(sum(scores) / len(scores), 2),
            "trend": trend,
            "min_score": min(scores),
            "max_score": max(scores),
        }


# ==================== 4. 采样日志生成 ====================

def generate_sample_logs(count: int = 100) -> list[AgentLog]:
    """生成采样日志（含部分退化样本）"""
    questions = [
        "深圳天气怎么样？",
        "1+1等于几？",
        "北京今天穿什么？",
        "中国首都是哪里？",
        "搜索一下Agent的最新论文",
        "推荐一本Python入门书",
        "什么是机器学习？",
        "给我讲个笑话",
        "苹果公司的创始人是谁？",
        "如何提高编程效率？",
    ]

    logs = []
    for i in range(count):
        q = random.choice(questions)
        # 后 20 条故意降质（模拟退化）
        if i >= count - 20:
            answer = "不知道" if random.random() < 0.6 else f"关于{q}，我可以告诉你..."
            passed = random.random() < 0.3
        else:
            answer = f"关于{q}，我可以告诉你..." if random.random() > 0.3 else ""
            passed = random.random() > 0.1

        logs.append(AgentLog(
            session_id=f"session-{i:04d}",
            question=q,
            answer=answer,
            tools_called=["get_weather"] if "天气" in q or "穿" in q else [],
            tokens=random.randint(100, 1500),
            latency_ms=random.randint(500, 5000),
            passed=passed,
        ))
    return logs


# ==================== 5. 主流程 ====================

def run_monitor():
    """运行监控系统"""
    store = LogStore()
    evaluator = QualityEvaluator()
    detector = DegradationDetector()

    # 生成并保存采样日志
    if not store.logs:
        print("生成采样日志...")
        logs = generate_sample_logs(100)
        for log in logs:
            store.add(log)
        print(f"已生成 {len(logs)} 条采样日志")

    print("\n" + "=" * 50)
    print("  质量监控面板")
    print("=" * 50)

    # 评估所有日志
    results = []
    for log in store.recent(50):
        eval_result = evaluator.evaluate_log(log)
        results.append(eval_result)
        detector.feed(eval_result)

    # 统计
    flagged = [r for r in results if r["flagged"]]
    avg_overall = sum(r["overall"] for r in results) / len(results) if results else 0

    print(f"\n  平均分: {avg_overall:.2f}/5")
    print(f"  标记数: {len(flagged)}/{len(results)}")
    print(f"  标记率: {len(flagged)/len(results)*100:.1f}%")

    # 打印被标记的日志
    if flagged:
        print("\n  被标记的条目:")
        for f in flagged[:5]:
            log = next((l for l in store.logs if l.session_id == f["session_id"]), None)
            if log:
                print(f"    ❌ {log.session_id}: {log.question[:30]}")
                print(f"       规则: {f['rule_check']['issues']}")
                print(f"       LLM 评分: {f['llm_scores']}")

    # 退化检测
    degradation = detector.check_degradation()
    if degradation:
        print(f"\n  ⚠ {degradation['alert']}")
        print(f"  前 {degradation['sample_count']} 条均分: {degradation['previous_avg']}")
        print(f"  最近 {degradation['sample_count']} 条均分: {degradation['recent_avg']}")
        print(f"  下降: {degradation['drop']}")

    # 退化趋势报告
    report = detector.summary()
    print(f"\n  趋势: {report}")


def run_eval_pipeline():
    """运行评估 Pipeline"""
    evaluator = QualityEvaluator()
    detector = DegradationDetector()

    print("=" * 50)
    print("  评估 Pipeline")
    print("=" * 50)

    # 模拟实时日志流
    logs = generate_sample_logs(30)

    for i, log in enumerate(logs):
        result = evaluator.evaluate_log(log)
        detector.feed(result)

        status = "✅" if not result["flagged"] else "❌"
        if i % 5 == 0:  # 每 5 条输出一次进度
            print(f"  [{i+1:02d}/{len(logs)}] {status} {log.question[:25]}... 总体={result['overall']:.1f}")

    degradation = detector.check_degradation()
    if degradation:
        print(f"\n  ⚠ 退化检测: {degradation}")
    else:
        print("\n  ✅ 未检测到退化")

    print(f"\n  最终报告: {detector.summary()}")


def run_replay():
    """离线回放测试"""
    print("=" * 50)
    print("  离线回放回归测试")
    print("=" * 50)

    # 模拟历史测试集
    test_cases = [
        {"question": "深圳天气怎么样？", "expected_tools": ["get_weather"]},
        {"question": "1+1等于几？", "expected_tools": []},
        {"question": "什么是人工智能？", "expected_tools": []},
        {"question": "查一下 Python 的递归", "expected_tools": []},
    ]

    # 模拟旧版和新版 Agent 的表现
    class MockAgent:
        def __init__(self, version: str):
            self.version = version

        def answer(self, q: str) -> dict:
            if self.version == "old":
                return {"answer": f"关于 {q}...", "tools": []}
            else:
                return {"answer": f"关于 {q}...（优化版）", "tools": []}

    old_agent = MockAgent("old")
    new_agent = MockAgent("new")

    passed = 0
    failed = 0
    for tc in test_cases:
        old_result = old_agent.answer(tc["question"])
        new_result = new_agent.answer(tc["question"])

        test_passed = len(new_result["answer"]) > 5
        if test_passed:
            passed += 1
            status = "✅"
        else:
            failed += 1
            status = "❌"

        print(f"  {status} {tc['question'][:25]}... | old: {len(old_result['answer'])}b → new: {len(new_result['answer'])}b")

    print(f"\n  通过: {passed}/{len(test_cases)} ({passed/len(test_cases)*100:.0f}%)")
    print(f"  失败: {failed}")


def main():
    import sys

    if len(sys.argv) > 1:
        mode = sys.argv[1]
        if mode == "eval":
            run_eval_pipeline()
        elif mode == "replay":
            run_replay()
        else:
            print("参数: eval / replay / (无参数=监控面板)")
    else:
        run_monitor()


if __name__ == "__main__":
    main()
