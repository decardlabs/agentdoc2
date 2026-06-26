# Phase 2-03: Agent 评估（LLM-as-Judge）

## 为什么要从一开始就做评估？

Agent 的输出是**非确定性的**——同样的输入，每次运行可能得到不同结果。如果你不在实验阶段就建立评估体系，等上了生产你根本不知道 Agent 是变好了还是变坏了。

## 评估维度

| 维度 | 含义 | 测量方式 |
|------|------|---------|
| 准确性 | 回答是否正确 | LLM-as-Judge / Ground Truth 对比 |
| 相关性 | 回答是否切题 | 规则匹配 / LLM 打分 |
| 完整性 | 是否遗漏了关键信息 | LLM-as-Judge |
| 工具使用 | 工具调用是否正确 | 工具调用日志分析 |
| 效率 | token 消耗、调用次数 | 成本统计 |

## LLM-as-Judge

用一个 LLM 给另一个 LLM 的输出打分。这不是完美的方案，但在实践中足够好用：

```python
import json
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)

def evaluate_answer(question: str, answer: str, ground_truth: str = None) -> dict:
    """用 LLM 评估回答质量"""
    judge_prompt = f"""
你是一个评估专家。请对以下回答从三个维度打分（1-5分）：

问题: {question}
回答: {answer}
"""

    if ground_truth:
        judge_prompt += f"""
标准答案: {ground_truth}
"""

    judge_prompt += """
请输出 JSON 格式的评分：
{{
    "accuracy": 整数 1-5,
    "relevance": 整数 1-5,
    "completeness": 整数 1-5,
    "explanation": "简要说明"
}}
"""

    response = client.chat.completions.create(
        model="deepseek-v4-flash",
        messages=[{"role": "user", "content": judge_prompt}],
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content)
```

## 自动化评估脚本

```python
import json
from dataclasses import dataclass, asdict

@dataclass
class TestCase:
    id: str
    question: str
    expected_tool: str | None       # 期望调用的工具名
    expected_output_contains: list[str]  # 期望输出包含的关键词

@dataclass
class TestResult:
    test_id: str
    passed: bool
    actual_output: str
    tools_called: list[str]
    token_usage: int
    scores: dict | None

class EvalSuite:
    def __init__(self, agent):
        self.agent = agent
        self.results = []

    def run_test(self, test: TestCase) -> TestResult:
        """运行一个测试用例"""
        output = self.agent.run(test.question)
        # ... 记录工具调用和 token 使用
        return TestResult(...)

    def run_all(self, tests: list[TestCase]):
        for test in tests:
            result = self.run_test(test)
            self.results.append(result)

    def summary(self) -> dict:
        passed = sum(1 for r in self.results if r.passed)
        return {
            "total": len(self.results),
            "passed": passed,
            "failed": len(self.results) - passed,
            "pass_rate": passed / len(self.results),
        }

    def report(self):
        """生成评估报告"""
        s = self.summary()
        report = f"""
# 评估报告

运行时间: {datetime.now()}
通过率: {s['passed']}/{s['total']} ({s['pass_rate']:.1%})

## 各测试详情
"""
        for r in self.results:
            status = "✅" if r.passed else "❌"
            report += f"\n| {status} {r.test_id} | 得分: {r.scores} |"
        return report
```

## 评估 Pipeline（实验 2 起使用）

```python
def eval_pipeline():
    """完整的评估流程"""
    tests = [
        TestCase("Q001", "深圳天气怎么样？", "get_weather", ["28°C"]),
        TestCase("Q002", "1+1等于几？", None, ["2"]),
        TestCase("Q003", "搜索一下 Agent 的最新论文", "search_arxiv", ["论文"]),
    ]

    agent = ReActAgent(tools=tools, tool_handlers=handlers)
    suite = EvalSuite(agent)
    suite.run_all(tests)

    with open("eval_report.md", "w") as f:
        f.write(suite.report())

    print(suite.report())
```

## 练习

1. 为实验 1 的天气助手编写 10 个测试用例，包含"应该调用工具"和"不应该调用工具"两类
2. 运行评估脚本并生成报告
3. 故意改错一个工具，验证评估能否检测到退化

## 检查清单

- [ ] 能编写 TestCase 和 TestResult 结构
- [ ] 能使用 LLM-as-Judge 对回答打分
- [ ] 能生成结构化评估报告
- [ ] 理解评估的局限性（LLM-as-Judge 不是完美的）
