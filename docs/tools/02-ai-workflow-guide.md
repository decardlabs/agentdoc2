# 如何用 AI 管理每个实验

> 学 Agent 的过程中，AI 本身就是最好的辅助工具。
> 但不是让它帮你写代码——而是用它做 Code Review、调试辅助、文档整理和质量检查。

---

## 1. 概览：学 Agent 的过程中，AI 扮演什么角色

本项目的核心原则是**手写代码、理解原理**。AI 的角色是：

| 场景 | AI 做什么 | 你做什么 |
|------|----------|---------|
| 调试 Bug | 分析堆栈、定位代码行 | 理解根因，写修复方案 |
| 理解概念 | 解释某个概念的不同角度 | 对照文档验证准确性 |
| 代码 Review | 检查潜在问题、安全隐患 | 判断哪些建议真正有用 |
| 写测试用例 | 生成测试骨架 | 补充边界用例，跑通测试 |
| 重写/重构 | 给出改动方案 | 理解每处改动再决定是否接受 |
| 写文档 | 整理格式、补充遗漏 | 检查内容是否准确 |

**底线：** AI 可以加速，但不能替代理解。如果你看不懂 AI 生成的代码，说明你跳过了某一步。

---

## 2. 配置工作环境

### 2.1 获取 DeepSeek API Key

```bash
# 1. 注册 DeepSeek
#    打开 https://platform.deepseek.com/ → 注册 → 登录

# 2. 充值（可选）
#    实验期间预计总消耗 ≤ ¥50，首次注册通常赠送 ¥10 额度

# 3. 创建 API Key
#    控制台 → API Keys → 创建密钥
#    复制以 "sk-" 开头的 key

# 4. 设置到环境变量（建议加到 ~/.zshrc 永久生效）
export DEEPSEEK_API_KEY="sk-your-key-here"
```

**验证是否生效：**

```bash
python3 -c "import os; print('OK' if os.getenv('DEEPSEEK_API_KEY') else 'MISSING')"
# 输出 OK → 配置正确
```

---

### 2.2 配置 WorkBuddy

[WorkBuddy](https://www.codebuddy.cn) 是内置 AI 编程助手的 IDE（基于 VS Code）。以下是配置步骤：

#### 2.2.1 安装 WorkBuddy

```bash
# macOS
brew install --cask workbuddy
# 或从 https://www.codebuddy.cn/download 下载安装包
```

#### 2.2.2 设置 DeepSeek 为默认模型

打开 WorkBuddy → 左下角设置 ⚙️ → **Model** → 添加自定义模型：

| 字段 | 值 |
|------|----|
| Provider | OpenAI Compatible |
| Name | deepseek-v4-flash |
| Base URL | `https://api.deepseek.com` |
| API Key | `$DEEPSEEK_API_KEY`（或直接粘贴 key） |
| Model | `deepseek-v4-flash` |

#### 2.2.3 本项目的 WorkBuddy 使用场景

| 场景 | 触发方式 | 提示词示例 |
|------|---------|-----------|
| 理解一段代码 | 选中代码 → `/explain` | "用 ReAct 的视角解释这段循环逻辑" |
| 调试错误 | 贴报错信息 → 提问 | "这个 AttributeError 是什么原因？" |
| 代码 Review | 选中代码 → `/review` | "检查这个 tool call 的 schema 是否有问题" |
| 生成测试用例 | 打开文件 → `/test` | "为这个 process_ticket 函数生成 5 条测试用例" |
| 解释概念 | 打开 Terminal → 提问 | "解释 MCP 协议的 Tools/Resources/Prompts 三要素" |

**重要：** 任何时候 AI 给出了代码/答案，先问自己"为什么"再接受。这是学 Agent 而不是抄代码。

---

### 2.3 配置 Claude Code

[Claude Code](https://claude.ai/code) 是 Anthropic 推出的终端 AI 编程工具，同样可以配置为使用 DeepSeek。

> 注意：Claude Code 默认使用 Anthropic 的 Claude 模型。以下是如何配置它使用 DeepSeek 的 OpenAI 兼容接口。

#### 2.3.1 安装 Claude Code

```bash
# 通过 npm 安装
npm install -g @anthropic-ai/claude-code

# 或使用 Homebrew
brew install claude-code
```

#### 2.3.2 配置 DeepSeek 作为底层模型

Claude Code 本身是一个 AI 编程助手，它**默认使用 Claude 模型**。要让 Claude Code 使用 DeepSeek，你需要通过环境变量或配置文件覆盖其 API 端点：

**方案一：创建 `.clauderc` 配置文件**

在项目根目录创建 `.clauderc.json`：

```json
{
  "apiKey": "${DEEPSEEK_API_KEY}",
  "model": "deepseek-v4-flash",
  "apiBaseUrl": "https://api.deepseek.com"
}
```

> 注意：Claude Code 的配置方式可能随版本更新变化。如果上述配置不生效，请运行 `claude config` 查看最新的配置选项。

**方案二：通过环境变量覆盖**

```bash
# 临时使用 DeepSeek
ANTHROPIC_BASE_URL=https://api.deepseek.com \
ANTHROPIC_MODEL=deepseek-v4-flash \
ANTHROPIC_API_KEY=$DEEPSEEK_API_KEY \
claude

# 或者永久写入 shell 配置
echo 'export ANTHROPIC_BASE_URL="https://api.deepseek.com"' >> ~/.zshrc
echo 'export ANTHROPIC_MODEL="deepseek-v4-flash"' >> ~/.zshrc
```

#### 2.3.3 本项目的 Claude Code 使用场景

| 场景 | 命令 | 说明 |
|------|------|------|
| 从终端快速提问 | `claude -p "解释 ReAct 循环的终止条件"` | 单次问答，不进入交互模式 |
| 在当前目录打开 AI 终端 | `claude` | 交互式，可在当前项目中执行命令 |
| 代码审查 | `claude "review the code in experiments/exp01"` | 对实验目录做完整的代码审查 |
| 调试 | `claude -p "这个错误是什么意思" < error.log` | 把错误日志传给 AI 分析 |
| 写文档 | `claude "帮我整理这个函数的调用链"` | 从代码中自动提取并生成文档 |

**⚠️ 提醒：** Claude Code 是一个独立的编程助手，不是本项目的必需工具。如果你已经在使用 WorkBuddy，Claude Code 不是必须的。选一个用就可以。

---

## 3. 每个实验的 AI 协作流程

### 实验 1：天气助手

```
你写代码 → 遇到 Bug → AI 帮忙调试 → 你理解原因 → 继续
                                  ↓
                          AI Review 代码 → 你评估建议 → 采纳/拒绝
                                  ↓
                          AI 生成测试用例骨架 → 你补充边界情况
```

**具体操作：**

```bash
# 1. 写完 main.py 后让 AI Review
# 在 WorkBuddy 中选中代码 → /review
# 或在终端：
claude "请 review experiments/exp01-weather-assistant/main.py，重点检查：
1. ReAct 循环的终止条件是否完备
2. Tool schema 定义是否正确
3. 是否有无限循环的风险"

# 2. 运行失败时
# 复制错误日志给 AI：
claude -p "这个错误的原因是什么？如何修复？" < error.log

# 3. 跑通之后
claude "为 experiments/exp01 的 weather agent 生成 5 条额外的评估用例，
覆盖边界情况：空城市名、温度极高/极低、多轮对话"
```

### 实验 2：文档问答

```bash
# RAG 结果不准时
claude "我的 RAG pipeline 对这个问题的回答是错的：
问题：[你的问题]
检索到的 chunks：[粘贴检索结果]
回答：[Agent 的回答]
请分析是 chunking 策略、检索质量还是回答生成的问题"

# 评估脚本
claude "帮我 review experiments/exp02-doc-qa-eval/main.py 中的 LLM-as-Judge
实现，检查评分标准和 prompt 是否合理"
```

### 实验 3：工单处理

```bash
# 工作流卡住时
claude "我的 LangGraph 工作流在 state X 卡住了，
state 内容是：[粘贴 state]，
请分析是哪条条件边出了问题"

# 异常处理
claude "请 review experiments/exp03-ticket-processor/main.py 中的
异常处理逻辑，哪些异常路径没有被覆盖？"
```

### 实验 4：多 Agent 对照

```bash
# 对比分析
claude "阅读 experiments/exp04-multi-agent/single_agent.py 和
multi_agent.py，分析两种方案的优缺点和适用场景"
```

### 实验 5：质量监控

```bash
# 退化检测逻辑
claude "review experiments/exp05-quality-monitor/main.py 中的退化检测算法，
滑动窗口大小和阈值设置是否合理？有没有更好的方案？"
```

---

## 4. 配置检查清单

### WorkBuddy 配置检查

- [ ] 已安装 WorkBuddy
- [ ] 已在模型中添加 `deepseek-v4-flash`（Base URL: `https://api.deepseek.com`）
- [ ] 环境变量 `DEEPSEEK_API_KEY` 已设置
- [ ] 已打开本项目目录作为工作区
- [ ] 已试用 `/explain` 解释一段代码，验证连通性

### Claude Code 配置检查

- [ ] 已安装 Claude Code（`npm install -g @anthropic-ai/claude-code`）
- [ ] 已在 `.clauderc` 或环境变量中配置 DeepSeek 端点
- [ ] 验证：`claude -p "使用中文回答，1+1=?"` 能正常获得回复
- [ ] 已了解基本的 claude 命令用法

---

## 5. 注意事项

### 不要踩的坑

1. **不要让 AI 替你做实验。** 如果 AI 直接生成了完整的 `main.py`，你什么都没学到。正确的做法是：你先写，卡住了问 AI，理解了再继续。

2. **AI 的 Review 不是权威。** 代码审查是 AI 辅助，不是 AI 决定。特别是安全问题——AI 可能漏报，也可能误报。

3. **DeepSeek 的 tokens 虽然便宜（￥0.5/百万 token），但滥用还是会超支。** 建议：
   - 每个实验设定 token 预算上限
   - 不要在 AI 对话中重复粘贴大段代码
   - 用 `claude -p "..."` 代替交互模式做快速问答

4. **WorkBuddy 和 Claude Code 不要混用。** 选一个当主力。建议用 WorkBuddy（IDE 内集成更方便），Claude Code 只作为终端备选。

5. **记录你的 AI 使用方式。** 每个实验笔记中记一栏：这个实验中 AI 帮你做了什么、你学会了什么。这是你未来改进工作流的依据。

---

## 附录：快速命令参考

### WorkBuddy

| 操作 | 方式 |
|------|------|
| 解释代码 | 选中代码 → `Cmd+L` 或在输入框中输入 `/explain` |
| 代码 Review | 打开文件 → 输入 `/review` |
| 生成测试 | 打开文件 → 输入 `/test` |
| 终端提问 | `Cmd+J` 打开终端 → 直接输入问题 |
| 搜索文档 | `Cmd+Shift+P` → 输入关键字 |

### Claude Code

```bash
claude -p "单次问答"          # 单次模式
claude                        # 交互模式
claude "分析这个文件"          # 分析文件
claude "review this dir"      # 审查目录
```

> 最终提醒：这个项目的目标是你**学会**开发 AI Agent，不是**生产**一个产品。AI 工具能加速学习，但不能代替学习。
