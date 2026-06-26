# Obsidian 安装及使用指南

> 为什么要用 Obsidian？
>
> 本地存储、纯 Markdown、双向链接。你的学习笔记永远属于你，不会被任何平台锁定。
> 本项目的每周进度模板也是为 Obsidian 设计的。

---

## 1. 下载安装

### macOS

```bash
# 方式一：官网下载
# 打开 https://obsidian.md  →  Download  →  macOS

# 方式二：Homebrew
brew install --cask obsidian
```

### Windows

```bash
# 官网下载安装包
# https://obsidian.md  →  Download  →  Windows
# 或使用 winget
winget install Obsidian.Obsidian
```

### Linux

```bash
# AppImage（推荐，通用）
# https://obsidian.md  →  Download  →  Linux

# Ubuntu/Debian
sudo dpkg -i obsidian_*.deb
```

### 移动端

iOS 和 Android 直接在应用商店搜索 "Obsidian" 安装。手机端免费，支持与桌面端通过 iCloud / Syncthing / 官方 sync 同步。

---

## 2. 打开项目作为 Vault

安装完成后：

1. 打开 Obsidian → **Open folder as vault**
2. 选择本项目目录：`AI-Agent-Learning-Project/`
3. Obsidian 会问你是否信任作者 → **Trust**（因为这不是第三方插件）

现在整个项目都在 Obsidian 里了——文档、实验代码、README，全部可以直接浏览和编辑。

---

## 3. 基础操作

### 创建笔记

| 操作 | 快捷键 | 说明 |
|------|--------|------|
| 新建笔记 | `Cmd/Ctrl + N` | 在 vault 根目录创建 |
| 指定路径 | `Cmd/Ctrl + Shift + N` | 在新目录中创建 |
| 快速切换 | `Cmd/Ctrl + O` | 搜索并打开任意文件 |

### 双向链接（Obsidian 的核心武器）

这是 Obsidian 区别于普通 Markdown 编辑器的关键功能。

```markdown
# 写法一：链接到另一篇笔记
[[函数调用的关键细节]]

# 写法二：链接时自定义显示文字
[[函数调用的关键细节|这里写了什么]]

# 写法三：链接到笔记内的标题
[[RAG 管道的构建方法#Chunking 策略]]
```

**对学习有什么用？**

每个实验你会学很多概念。用 `[[ ]]` 把概念串起来，Obsidian 会自动生成**知识图谱**（Graph View）。学到第 3 个实验的时候，回头看看图谱，你会看到你的知识网络是怎么长出来的。

### 标签

```markdown
# 在笔记开头打标签
---
tags:
  - agent/learning
  - experiment/exp-01
  - concept/function-calling
---

# 或在正文任意位置
#agent #exp01 #function-calling
```

**建议标签体系：**

| 类别 | 标签示例 | 用途 |
|------|---------|------|
| 阶段 | `phase/1`, `phase/2` | 标记笔记属于哪个学习阶段 |
| 实验 | `exp/01`, `exp/02` | 关联到具体实验 |
| 概念 | `concept/react`, `concept/rag` | 标记核心概念 |
| 状态 | `status/done`, `status/review` | 标记学习完成度 |

### 查看知识图谱

`Cmd/Ctrl + G` 打开 Graph View。你会看到 `[[链接]]` 构建出的知识网络。

**过滤技巧：** 在搜索框中输入 `path:phase1` 只看第一阶段的知识连接。

---

## 4. 本项目的 Obsidian 学习用法

### 用法一：按 LEARNING-GUIDE 写学习日志

每周开始，复制这个模板到 Obsidian 的新笔记：

```markdown
# 第 X 周进度

## 本周目标
- [ ] 读完 01-llm-sdk.md
- [ ] 写出 stream chat demo
- [ ] 记录 token 消耗

## 每天的记录
### 周一
- 做了什么：
- 卡在哪里：
- Token 用了多少：

### 周二
...

## 关键认知
（这周学到的核心概念，用 [[ ]] 链接）

## 失败模式记录
（Agent 在什么情况下会挂）

## 里程碑检查
- [ ] 项目 1
- [ ] 项目 2
```

每周一篇，按周编号，积累下来就是你完整的学习轨迹。

### 用法二：实验笔记模板

每做一个实验，同时创建实验笔记：

```markdown
# 实验 X：XXX

## 运行记录
- 日期：YYYY-MM-DD
- 耗时：X 小时
- Token 消耗：XXXX
- 花费：￥X.XX

## 实验结果
- 通过率：
- 失败用例：

## 失败模式
（这个 Agent 在什么情况下会挂）

## 学到的东西
（用 [[ ]] 链接到其他笔记）
```

### 用法三：概念卡片

小知识点单独成卡片，用标签和链接串联：

```markdown
---
tags: [concept/rag, status/done]
---

# Chunking 策略

## Fixed-size chunking
按固定字符数切分，简单但可能切断语义。

## Semantic chunking
按句子/段落边界切分，保留语义完整性。

## 比较
| 策略 | 优点 | 缺点 |
|------|------|------|
| Fixed-size | 简单、可预测 | 可能切断语义 |
| Semantic | 语义完整 | 实现复杂 |

## 参考
- [[RAG 管道的构建]] 中的实现细节
- [[实验 2]] 的评估对比
```

---

## 5. 进阶技巧

### 插件推荐（纯学习用途）

| 插件 | 用途 | 建议 |
|------|------|------|
| Calendar | 右侧日历视图，点日期看当天的笔记 | 必装 |
| Kanban | 用看板管理学习任务 | 可选 |
| Excalidraw | 在手绘白板中画系统架构、流程图 | 调试 Agent 逻辑时很有用 |
| Tag Wrangler | 批量管理标签 | 标签多了以后有用 |

### 文件组织建议

```
AI-Agent-Learning-Project/
├── docs/                     ← 项目文档（不改动）
├── experiments/              ← 实验代码（不改动）
├── learning-notes/           ← 你的学习笔记（新建目录，不提交 git）
│   ├── weekly/week-01.md
│   ├── weekly/week-02.md
│   ├── exp-01-notes.md
│   ├── exp-02-notes.md
│   ├── concepts/
│   │   ├── react-loop.md
│   │   ├── function-calling.md
│   │   └── rag-pipeline.md
│   └── failures-summary.md
└── LEARNING-GUIDE.md
```

> 注意：`learning-notes/` 不会被 git 提交（已在 `.gitignore` 中添加），确保 `.gitignore` 中有 `learning-notes/`。

---

## 6. 常见问题

### 笔记能不能同步到手机？

可以。三种方案按你的隐私需求选：

| 方案 | 费用 | 说明 |
|------|------|------|
| Obsidian Sync | ￥60/月 | 官方加密同步，最省心 |
| iCloud Drive | 免费（macOS + iOS） | 简单可靠，需同一 Apple ID |
| Syncthing | 免费 | 开源跨平台，需要点配置 |

### 笔记会不会丢？

Obsidian 存的是纯 Markdown 文件。就算 Obsidian 倒闭了，你的笔记也是一堆 `.md` 文件，任何文本编辑器都能打开。这是选 Obsidian 而不是 Notion 的核心原因。

### 每天要花多少时间在笔记上？

每天 5-10 分钟记录就够了。不要为了"做好笔记"而拖延"学东西"本身。笔记是副产品，不是目的。
