# Phase 3-03: 错误恢复与重试策略

> Demo 和生产的区别就在于异常处理。

## Agent 中的常见错误类型

| 错误类型 | 例子 | 严重程度 |
|---------|------|---------|
| API 错误 | 超时、限速、认证失败 | 高 |
| 工具执行错误 | API 无响应、参数非法 | 高 |
| LLM 输出错误 | JSON 解析失败、tool call 格式异常 | 中 |
| 逻辑错误 | 死循环、重复调用、过早终止 | 中 |
| 数据错误 | 空值、格式不对、编码问题 | 中 |

## 三层错误处理架构

```
第 1 层: 单次操作重试（retry 3 次）
第 2 层: 单节点重试（换条路走）
第 3 层: 整个工作流回退（给用户友好提示）
```

## 第 1 层：单次操作重试

```python
import time
from functools import wraps

def retry(max_attempts=3, delay=1, backoff=2):
    """带指数退避的重试装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        wait = delay * (backoff ** attempt)
                        print(f"  重试 {attempt + 1}/{max_attempts}, 等待 {wait}s...")
                        time.sleep(wait)
            raise last_error
        return wrapper
    return decorator

@retry(max_attempts=3, delay=1)
def call_llm(client, **kwargs):
    return client.chat.completions.create(**kwargs)
```

## 第 2 层：降级策略

当某个工具彻底不可用时，是否有替代方案？

```python
class DegradationHandler:
    """工具降级管理器"""

    def __init__(self):
        self.fallback_map = {
            "search_web": ["search_arxiv", "search_news"],
            "get_weather_api": ["get_weather_offline_cache"],
            "process_refund_api": ["create_refund_ticket"],
        }

    def get_fallback(self, tool_name: str) -> list[str]:
        """获取降级工具列表"""
        return self.fallback_map.get(tool_name, [])

    def execute_with_fallback(self, tool_name: str, args: dict, handlers: dict) -> str:
        """尝试执行工具，失败时按优先级降级"""
        tried = []

        # 尝试主工具
        for attempt_tool in [tool_name] + self.get_fallback(tool_name):
            if attempt_tool in tried:
                continue
            tried.append(attempt_tool)

            handler = handlers.get(attempt_tool)
            if not handler:
                continue

            try:
                result = handler(**args)
                if result:
                    return result
            except Exception as e:
                print(f"  {attempt_tool} 失败: {e}, 尝试降级...")

        return json.dumps({"error": f"所有降级方案均失败，尝试过: {tried}"})
```

## 第 3 层：安全终止与用户沟通

```python
def safe_termination(state: dict, error_msg: str) -> str:
    """当所有重试和降级都失败时，生成对用户友好的错误信息"""
    return f"""
抱歉，我在处理您的请求时遇到了问题。

错误信息: {error_msg}

建议您:
1. 稍后重试该操作
2. 简化您的请求，分步完成
3. 如果问题持续，请联系技术支持

当前处理进度:
- 已完成了 {state.get('completed_steps', 0)}/{state.get('total_steps', 1)} 个步骤
- 第 {state.get('failed_step', '?')} 步失败
"""
```

## Agent 中的错误状态追踪

```python
from dataclasses import dataclass, field

@dataclass
class ErrorState:
    """Agent 的错误状态追踪"""
    errors: list[dict] = field(default_factory=list)
    retry_counts: dict[str, int] = field(default_factory=dict)
    degraded_tools: list[str] = field(default_factory=list)
    should_abort: bool = False

    def record_error(self, step: str, error: str, severity: str = "medium"):
        self.errors.append({
            "step": step,
            "error": error,
            "severity": severity,
            "timestamp": time.time(),
        })

    def should_retry(self, step: str, max_retries: int = 3) -> bool:
        if step not in self.retry_counts:
            self.retry_counts[step] = 0
        self.retry_counts[step] += 1
        return self.retry_counts[step] <= max_retries
```

## 完整例子：带错误恢复的工作流

```python
def robust_workflow(user_input: str) -> str:
    error_state = ErrorState()
    state = {"input": user_input, "error_state": error_state}

    try:
        # Step 1: 意图识别
        result = classify_intent(state)
    except Exception as e:
        error_state.record_error("intent_classification", str(e))
        if error_state.should_retry("classify"):
            # 用降级的方法重试
            result = classify_intent_fallback(state)
        else:
            return safe_termination(state, "意图识别失败")

    try:
        # Step 2: 执行
        result = execute_action(state, result)
    except Exception as e:
        error_state.record_error("action", str(e))
        # 检查是否有降级方案
        return safe_termination(state, f"执行失败: {str(e)}")

    return result
```

## 死循环检测

Agent 最常见的问题是陷入无限循环：

```python
class LoopDetector:
    """检测 Agent 是否陷入循环"""

    def __init__(self, window_size: int = 5):
        self.history = []
        self.window_size = window_size

    def record(self, action: str):
        self.history.append(action)
        if len(self.history) > self.window_size * 2:
            self.history.pop(0)

    def is_looping(self) -> bool:
        if len(self.history) < self.window_size * 2:
            return False

        recent = self.history[-self.window_size:]
        prev = self.history[-self.window_size*2:-self.window_size]

        return recent == prev
```

## 练习

1. 为实验 1 的天气助手增加重试逻辑（API 调用失败时自动重试）
2. 实现一个降级方案：主天气 API 失败时，改用备选天气 API
3. 在代理中加入循环检测，防止陷入无限 tool calling

## 检查清单

- [ ] 能实现指数退避重试
- [ ] 能设计降级方案（主路不通走辅路）
- [ ] 能检测死循环
- [ ] 能生成对用户友好的错误信息
- [ ] 理解"从失败中恢复" vs "失败了给用户看错误堆栈"的区别
