# Phase 1-01: LLM SDK 直调

## 为什么从 SDK 开始而不是 LangChain？

LangChain 在诞生时解决了一个真实问题：让调用 LLM 变得简单。但到了 2025-2026 年，各大模型厂商的原生 SDK 已经非常成熟，直接使用 SDK 有两个好处：

1. **没有抽象泄漏。** 你看到的每一行代码都在直接操作 LLM，没有隐形的 prompt 注入或上下文拼装。
2. **出了问题能定位。** 是 API 错误、schema 不匹配、还是速率限制？原生 SDK 的报错信息更直接。

## DeepSeek SDK 快速入门

DeepSeek v4 Flash API 完全兼容 OpenAI SDK 格式，使用相同的 `openai` Python 包，只需修改 API Key 和 Base URL 即可切换。

### 安装

```bash
pip install openai
export DEEPSEEK_API_KEY="sk-..."
```

### 基础调用

```python
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)

response = client.chat.completions.create(
    model="deepseek-v4-flash",       # 开发调试用低成本模型
    messages=[
        {"role": "system", "content": "你是一个助手。"},
        {"role": "user", "content": "深圳今天天气怎么样？"},
    ],
    temperature=0.7,
)

print(response.choices[0].message.content)
```

### 流式输出

```python
stream = client.chat.completions.create(
    model="deepseek-v4-flash",
    messages=[{"role": "user", "content": "讲个笑话"}],
    stream=True,
)

for chunk in stream:
    if chunk.choices[0].delta.content is not None:
        print(chunk.choices[0].delta.content, end="")
```

### 错误处理

```python
from openai import (
    APITimeoutError,
    APIConnectionError,
    RateLimitError,
    APIStatusError,
)

try:
    response = client.chat.completions.create(...)
except APITimeoutError:
    print("请求超时，重试...")
except RateLimitError:
    print("速率限制，等待后重试...")
except APIStatusError as e:
    print(f"API 错误 {e.status_code}: {e.message}")
```

## DeepSeek 注意事项

DeepSeek v4 Flash 的特点：

- **上下文窗口：** 128K tokens，支持长文档处理
- **模型名称：** `deepseek-v4-flash`（注意：旧的 `deepseek-chat` 已于 2026/07/24 废弃）
- **API 兼容性：** 完全兼容 OpenAI 格式，`openai` Python 包可直接使用
- **定价：** 低于同级别 GPT 模型，适合大规模实验和部署
- **嵌入（Embedding）：** DeepSeek 不提供 embedding API，需要结合其他 embedding 服务使用（详见 RAG 章节）

```python
# 快速验证连接
def test_connection():
    try:
        response = client.chat.completions.create(
            model="deepseek-v4-flash",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=10,
        )
        print("连接成功:", response.choices[0].message.content)
    except Exception as e:
        print("连接失败:", e)
```

## 关键理解

### Messages 结构

LLM 调用本质上是一个**消息列表**的输入输出：

```
[
    {"role": "system",    "content": "你是..."},   # 系统指令
    {"role": "user",      "content": "你好"},      # 用户输入
    {"role": "assistant", "content": "你好！"},     # 模型回复
    {"role": "user",      "content": "再来一个"},   # 继续对话
]
```

- **system**: 设定角色和规则（并非所有模型都支持）
- **user**: 用户输入
- **assistant**: 模型的回复

### 重要参数

| 参数 | 作用 | 建议值 |
|------|------|--------|
| temperature | 输出随机性 | 0.0（精确）~ 0.7（创意） |
| max_tokens | 输出上限 | 按需设置 |
| top_p | 采样策略 | 默认即可 |
| stop | 停止标记 | 用于控制输出 |


## 练习

1. 完成一个基础对话，要求模型用 JSON 格式输出：
   ```
   用户：列出深圳、广州、上海的天气（用 JSON 格式）
   ```
2. 实现带重试机制的自动调用（失败自动重试 3 次）
3. 实现一个简单的对话历史管理，支持多轮对话

## 检查清单

- [ ] 能独立完成流式调用
- [ ] 能处理 API 错误（超时、限速、认证失败）
- [ ] 能管理多轮对话的消息列表
- [ ] 了解 temperature 对输出的影响
