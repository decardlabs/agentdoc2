# Phase 4-01: 多 Agent 协作

## 什么时候需要多 Agent？

多 Agent 不是默认选择。在考虑多 Agent 之前，先回答一个问题：

> 单 Agent + 好工具 能否解决这个问题？

如果答案是"能"，不要上多 Agent。

### 适合多 Agent 的场景

| 场景 | 说明 | 例子 |
|------|------|------|
| 角色分离 | 不同任务需要不同知识和权限 | 客服接待 vs 财务退款 |
| 专业分工 | 每个 Agent 专注一个领域 | 检索 Agent vs 分析 Agent vs 写作 Agent |
| 多角度验证 | 从不同角度分析同一问题 | 辩论式 Agent 团队 |
| 任务并行 | 可以同时进行的不同任务 | 同时查库存、查物流、查价格 |

### 不适合多 Agent 的场景

- 简单问答
- 单工具调用
- 线性数据流

## 多 Agent 架构模式

### 1. 管理者-执行者（Manager-Worker）

```
                ┌→ Worker 1（检索）
Manager ────────┼→ Worker 2（分析）
  任务分配       └→ Worker 3（写作）
     ↓
结果汇总
```

- **Manager：** 负责任务分解、分配、结果汇总
- **Worker：** 执行具体任务，返回结果

### 2. 辩论模式（Debate）

```
Agent A ──→ 输出 1 ──→ Agent B ──→ 输出 2 ──→ Agent A ──→ 最终结论
（支持方）           （反对者）           （反思）
```

### 3. 流水线模式（Pipeline）

```
Agent A → Agent B → Agent C → Agent D
(输入)   (处理1)   (处理2)   (输出)
```

## 最小多 Agent 实现（直接 LLM 调用）

不依赖任何多 Agent 框架，用 LLM 本身做协调：

```python
import json
from openai import OpenAI

client = OpenAI(base_url="https://api.deepseek.com")

class SimpleMultiAgent:
    """最简单的多 Agent 协调（Manager-Worker 模式）"""

    def __init__(self, agents: dict[str, str]):
        """
        agents: {"agent_name": "agent_system_prompt"}
        """
        self.agents = agents

    def _call_agent(self, name: str, task: str) -> str:
        """调用单个 Agent"""
        response = client.chat.completions.create(
            model="deepseek-v4-flash",
            messages=[
                {"role": "system", "content": self.agents[name]},
                {"role": "user", "content": task},
            ],
        )
        return response.choices[0].message.content

    def run(self, task: str) -> dict:
        """Manager 负责任务分配和汇总"""
        # 1. Manager 拆解任务
        plan = self._call_agent("manager", f"拆解以下任务为子任务: {task}")
        print(f"[Manager] 计划: {plan}")

        # 2. 分配子任务给 Worker
        worker_results = {}
        for name in self.agents:
            if name == "manager":
                continue
            worker_results[name] = self._call_agent(name, f"用户任务: {task}\n\n你的任务: {plan}")

        # 3. Manager 汇总结果
        summary = self._call_agent("manager", f"""
原始任务: {task}

各 Agent 的输出:
{json.dumps(worker_results, ensure_ascii=False, indent=2)}

请汇总这些结果，生成最终回答。
""")
        return {"plan": plan, "worker_results": worker_results, "summary": summary}
```

## 使用简单的 Agent Team

```python
# 定义一个客服团队
agents = {
    "manager": "你是客服团队的经理。负责拆分用户问题，分配给合适的 Agent，最后汇总结果。",
    "reception": "你是接待 Agent，负责理解用户意图、安抚用户情绪。不要自行处理订单。",
    "query": "你是查询 Agent，负责查询订单信息。可以模拟查询数据库。",
    "processor": "你是处理 Agent，负责执行退换货操作。只有在收到 manager 指令后才能执行。",
}

team = SimpleMultiAgent(agents)
result = team.run("用户想退一个上周买的订单，订单号是 ORD-2024-001")
print(result["summary"])
```

## 对比：单 Agent 版本

```python
def single_agent_answer(task: str) -> str:
    """同一个任务，用一个 Agent 解决"""
    response = client.chat.completions.create(
        model="deepseek-v4-flash",
        messages=[{"role": "system", "content": "你是全能客服，负责完成所有任务。"},
                  {"role": "user", "content": task}],
    )
    return response.choices[0].message.content
```

## 框架介绍

### CrewAI

```python
from crewai import Agent, Task, Crew

# 定义 Agent
researcher = Agent(
    role="研究员",
    goal="研究并收集信息",
    backstory="你是一个经验丰富的研究员",
)

analyst = Agent(
    role="分析师",
    goal="分析数据并得出结论",
    backstory="你擅长数据分析",
)

# 定义任务
research_task = Task(
    description="研究人工智能的最新趋势",
    agent=researcher,
)

analysis_task = Task(
    description="基于研究结果分析市场影响",
    agent=analyst,
)

# 组建 Crew
crew = Crew(
    agents=[researcher, analyst],
    tasks=[research_task, analysis_task],
)

result = crew.kickoff()
```

### AutoGen

```python
import autogen

assistant = autogen.AssistantAgent(
    name="assistant",
    llm_config={"config_list": [{"model": "deepseek-v4-flash", "api_key": "..."}]},
)

user_proxy = autogen.UserProxyAgent(
    name="user_proxy",
    human_input_mode="NEVER",
    code_execution_config=False,
)

user_proxy.initiate_chat(
    assistant,
    message="深圳今天天气怎么样？",
)
```

## 多 Agent 的陷阱

| 陷阱 | 表现 | 解决方案 |
|------|------|---------|
| 通信开销 | Agent 间来回对话，token 浪费 | 限对话轮数 |
| 信息丢失 | Agent A 给的信息被 Agent B 误解 | 结构化通信格式 |
| 冲突 | 两个 Agent 给出矛盾的结论 | 加仲裁者 |
| 人设混淆 | Agent 扮演的角色不稳定 | 更好的 system prompt + 更低 temperature |

## 练习

1. 用最简单的方式（直接 LLM 调用，不用框架）实现一个 Manager-Worker 双 Agent 系统
2. 对比单 Agent 和双 Agent 在同一个任务上的表现（质量、成本、速度）
3. 找出一个"单 Agent 够用但你硬用了多 Agent"的例子，并对比两者差距

## 检查清单

- [ ] 能用最简单的方式实现多 Agent 协作
- [ ] 理解 Manager-Worker / Debate / Pipeline 三种模式
- [ ] 完成了单 Agent vs 多 Agent 的对照实验
- [ ] 知道什么时候应该用多 Agent，什么时候不应该
