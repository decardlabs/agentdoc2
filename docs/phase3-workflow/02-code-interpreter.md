# Phase 3-02: 代码解释器集成

## 为什么 Agent 需要沙箱执行代码？

Agent 最常见的需求之一就是"分析数据"——给个 CSV，让它做统计、画图、算公式。如果让 LLM 直接算，它可能算错（LLM 不擅长精确计算）。正确做法是：**让 LLM 写代码，然后在沙箱中执行**。

## 最小实现：使用 Python subprocess

```python
import subprocess
import tempfile
import os

def execute_python(code: str, timeout: int = 30) -> dict:
    """在 subprocess 中执行 Python 代码"""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False
    ) as f:
        f.write(code)
        f.flush()
        script_path = f.name

    try:
        result = subprocess.run(
            ["python3", script_path],
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
        return {
            "stdout": "",
            "stderr": "执行超时",
            "return_code": -1,
        }
    finally:
        os.unlink(script_path)


# Agent 中的代码解释器 tool

CODE_INTERPRETER_TOOL = {
    "type": "function",
    "function": {
        "name": "run_python",
        "description": "在沙箱环境中执行 Python 代码，用于数据分析、计算等",
        "parameters": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "要执行的 Python 代码（可以包含 pandas/numpy）",
                }
            },
            "required": ["code"],
        },
    },
}


def handle_run_python(code: str) -> str:
    result = execute_python(code)
    if result["stderr"]:
        return f"执行错误: {result['stderr']}"
    return result["stdout"]
```

## 安全沙箱模式

生产环境需要更严格的安全隔离：

```python
import subprocess

def execute_in_docker(code: str) -> dict:
    """在 Docker 沙箱中执行"""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False
    ) as f:
        f.write(code)
        f.flush()
        script_path = f.name

    try:
        cmd = [
            "docker", "run", "--rm",
            "-v", f"{script_path}:/code/script.py:ro",
            "python:3.11-slim",
            "python", "/code/script.py",
        ]
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=60
        )
        return {"stdout": result.stdout, "stderr": result.stderr}
    finally:
        os.unlink(script_path)
```

## Agent 让 LLM 写代码来分析数据

```python
class DataAnalysisAgent:
    """Agent 可以动态生成代码来分析用户提供的数据"""

    def __init__(self):
        self.client = OpenAI(base_url="https://api.deepseek.com")
        self.tools = [CODE_INTERPRETER_TOOL]

    def analyze(self, data_description: str, csv_path: str = None) -> str:
        # 读取数据预览
        preview = ""
        if csv_path:
            import pandas as pd
            df = pd.read_csv(csv_path)
            preview = f"数据预览:\n{df.head().to_string()}\n\n列名: {list(df.columns)}\n形状: {df.shape}"

        # 构建 tool call
        response = self.client.chat.completions.create(
            model="deepseek-v4-flash",
            messages=[{"role": "user", "content": f"""
用户想分析的数据: {data_description}

{preview}

请分析这些数据，输出你需要的 Python 代码。
使用 tool call 执行 Python 代码。
要求：
1. 先读取并探索数据
2. 根据用户问题做具体分析
3. 给出统计结果和结论
"""}],
            tools=self.tools,
        )

        # 执行 tool call 循环
        messages = [{"role": "user", "content": f"分析数据: {data_description}"}]
        for _ in range(5):
            response = self.client.chat.completions.create(
                model="deepseek-v4-flash",
                messages=messages,
                tools=self.tools,
            )
            msg = response.choices[0].message

            if msg.tool_calls:
                messages.append(msg)
                for tc in msg.tool_calls:
                    args = json.loads(tc.function.arguments)
                    result = execute_python(args["code"])
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps(result),
                    })
            else:
                return msg.content

        return "分析超时"
```

## 典型用例

### 1. 数据统计

```
用户: "这个月的销售额比上个月增长了多少？"
Agent: 生成 pandas 代码 → 执行 → 返回结果
```

### 2. 数据可视化

Agent 可以生成图表代码并保存：

```python
code = """
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('sales.csv')
monthly = df.groupby('month')['revenue'].sum()
monthly.plot(kind='bar')
plt.savefig('/tmp/chart.png')
print('图表已保存')
"""
```

### 3. 复杂计算

```
用户: "根据我们过去 3 个月的退货率，预测下个月需要准备多少退款准备金？"
Agent: 生成回归分析代码 → 执行 → 返回预测结果
```

## 安全注意事项

1. **永远不要在 Agent 的主进程中执行未知代码** — 使用 subprocess 或容器
2. **设置资源限制** — CPU 时间、内存、磁盘写入
3. **禁止网络访问** — 沙箱模式应该隔离网络
4. **清理临时文件** — 执行完成后删除所有生成的文件

## 练习

1. 用提供的 `execute_python` 工具实现一个 CSV 数据统计 Agent
2. 设计一个沙箱安全检查，禁止 `os.remove` / `subprocess.run` 等危险操作
3. 处理代码执行超时和无限循环

## 检查清单

- [ ] 能通过 subprocess 在沙箱中执行 LLM 生成的代码
- [ ] 能处理代码执行错误和超时
- [ ] 理解代码执行的安全风险
- [ ] 能用代码解释器完成数据分析任务
