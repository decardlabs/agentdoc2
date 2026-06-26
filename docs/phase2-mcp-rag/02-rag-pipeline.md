# Phase 2-02: RAG 管道（检索增强生成）

## RAG 是什么？

RAG (Retrieval-Augmented Generation) 是让 LLM 在回答问题时先检索相关知识，再基于检索结果生成回答。

```
用户输入 → [检索] → 知识库 → 相关段落 → [生成] → 基于知识的回答
```

### 为什么需要 RAG？

1. **知识截止：** LLM 的训练数据有截止日期
2. **幻觉：** LLM 可能会编造不知道的信息
3. **私有数据：** LLM 不了解你的业务数据
4. **可验证：** RAG 可以展示信息来源，让用户验证

## RAG 管道的核心步骤

### 1. 文档加载（Loading）

```python
from pypdf import PdfReader

def load_pdf(file_path: str) -> str:
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text
```

### 2. 文本分块（Chunking）

分块策略直接影响检索质量：

```python
def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """按固定长度分块，带重叠"""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks

def semantic_chunk(text: str) -> list[str]:
    """按语义边界分块（基于段落/标题）"""
    import re
    # 按双换行符或标题分割
    chunks = re.split(r'\n\s*\n|(?=#{1,6}\s)', text)
    return [c.strip() for c in chunks if c.strip()]
```

### 3. Embedding（向量化）

```python
from openai import OpenAI

client = OpenAI()

def embed_texts(texts: list[str]) -> list[list[float]]:
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=texts,
    )
    return [item.embedding for item in response.data]

def embed_query(query: str) -> list[float]:
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=[query],
    )
    return response.data[0].embedding
```

### 4. 向量存储与检索（ChromaDB）

```python
import chromadb
from chromadb.utils import embedding_functions

# 使用 OpenAI 的 embedding 函数
openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    model_name="text-embedding-3-small"
)

# 创建集合
client = chromadb.Client()
collection = client.create_collection(
    name="my_docs",
    embedding_function=openai_ef,
)

# 添加文档
collection.add(
    documents=["文档段落1...", "文档段落2..."],
    metadatas=[{"source": "paper1.pdf"}, {"source": "paper1.pdf"}],
    ids=["chunk1", "chunk2"],
)

# 检索
results = collection.query(
    query_texts=["什么数据集被使用了？"],
    n_results=3,
)
```

### 5. 生成回答

```python
def generate_with_context(query: str, context_chunks: list[str]) -> str:
    context = "\n\n".join(context_chunks)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": f"""
你是一个研究助手。基于以下资料回答问题。
如果资料不足以回答问题，请明确说明。

资料：
{context}
"""},
            {"role": "user", "content": query},
        ],
    )
    return response.choices[0].message.content
```

## 完整 RAG 流程

```python
def rag_pipeline(pdf_path: str, query: str) -> str:
    # 1. 加载文档
    text = load_pdf(pdf_path)

    # 2. 分块
    chunks = chunk_text(text)

    # 3. 存入向量库
    collection.delete_all()
    collection.add(
        documents=chunks,
        ids=[f"chunk_{i}" for i in range(len(chunks))],
    )

    # 4. 检索
    results = collection.query(
        query_texts=[query],
        n_results=3,
    )

    # 5. 生成回答
    return generate_with_context(query, results["documents"][0])
```

## 进阶：Reranking

初检索找回 top-k 个结果后，用更精确的模型重新排序：

```python
def rerank(query: str, documents: list[str], top_n: int = 3) -> list[str]:
    """用 LLM 对初步检索结果重新排序"""
    doc_text = "\n\n".join([f"[{i}] {d}" for i, d in enumerate(documents)])

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": f"""
        问题: {query}

        文档:
        {doc_text}

        请选出最相关的 {top_n} 个文档，按相关性从高到低输出序号，用逗号分隔。
        只输出序号，不要其他文字。
        """}],
    )
    # 解析输出
    indices = [int(i.strip()) for i in response.choices[0].message.content.split(",")]
    return [documents[i] for i in indices[:top_n]]
```

## 练习

1. 找一篇 PDF 论文，完成从加载到问答的完整 RAG pipeline
2. 对比不同 chunking 策略对问答质量的影响
3. 实现一个简单的 Reranking 步骤，并比较 rerank 前后的效果

## 检查清单

- [ ] 能完成文档加载 → 分块 → embedding → 检索 → 生成的完整流程
- [ ] 理解不同 chunking 策略的优劣
- [ ] 能用 ChromaDB 做语义检索
- [ ] 能实现 reranking 提升检索精度
