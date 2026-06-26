# 实验 2：单文档问答 + 评估体系

## 实验目标

掌握 RAG 管道 + LLM-as-Judge 评估。

## 实验内容

输入一篇 PDF 论文，Agent 做 chunking → embedding → 检索 → 回答，并自动评估回答质量。

## 运行方式

```bash
# 1. 安装依赖
pip install openai chromadb pypdf pandas

# 2. 准备论文（或使用 sample_doc 中的示例）
# 3. 运行
python main.py
```

## 实验拆分

建议分两步走：

1. **2a：** 单篇论文的 RAG 问答（先跑通 pipeline）
2. **2b：** 评估脚本 + 多篇论文的综述生成

## 核心技术

- RAG 全链路（Chunking → Embedding → Retrieval → Generation）
- Reranking
- LLM-as-Judge
