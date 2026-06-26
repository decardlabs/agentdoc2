"""
实验 2：单文档 RAG 问答 + 评估体系

核心概念：RAG 管道、LLM-as-Judge 评估
"""

import json
import os
import re
from typing import Optional
from openai import OpenAI
import chromadb


# ==================== 1. 文档加载与分块 ====================

def load_text(file_path: str) -> str:
    """加载文本文件"""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def chunk_by_fixed_size(text: str, chunk_size: int = 500, overlap: int = 50) -> list[dict]:
    """按固定大小分块（含重叠）"""
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk_text = text[start:end]
        chunks.append({
            "text": chunk_text,
            "start": start,
            "end": end,
        })
        start += chunk_size - overlap
    return chunks


def chunk_by_paragraph(text: str) -> list[dict]:
    """按段落分块（语义分块）"""
    paragraphs = re.split(r'\n\s*\n', text)
    chunks = []
    for i, para in enumerate(paragraphs):
        para = para.strip()
        if len(para) > 50:  # 过滤过短的段落
            chunks.append({
                "text": para,
                "index": i,
            })
    return chunks


# ==================== 2. 向量库 ====================

class VectorStore:
    """基于 ChromaDB 的向量存储与检索"""

    def __init__(self):
        self.client = chromadb.Client()
        self.collection = self.client.create_collection(
            name="doc_qa",
            metadata={"hnsw:space": "cosine"},
        )

    def add_documents(self, chunks: list[dict]):
        """添加文档 chunks 到向量库"""
        texts = [c["text"] for c in chunks]
        ids = [f"chunk_{i}" for i in range(len(chunks))]
        metadatas = [{"source": "sample_doc", "index": i} for i in range(len(chunks))]

        self.collection.add(
            documents=texts,
            ids=ids,
            metadatas=metadatas,
        )
        print(f"  已添加 {len(chunks)} 个文档块")

    def search(self, query: str, n_results: int = 5) -> list[str]:
        """语义检索"""
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
        )
        return results["documents"][0] if results["documents"] else []

    def clear(self):
        """清空集合"""
        try:
            self.client.delete_collection("doc_qa")
            self.collection = self.client.create_collection(name="doc_qa")
        except Exception:
            pass


# ==================== 3. Reranking ====================

def rerank(query: str, documents: list[str], top_n: int = 3) -> list[str]:
    """用 LLM 对检索结果重排序"""
    if not documents:
        return []

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    doc_text = "\n\n".join(
        [f"[{i}] {d[:200]}..." for i, d in enumerate(documents)]
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": f"""问题: {query}

文档列表:
{doc_text}

请选出与问题最相关的 {top_n} 个文档序号（按相关性从高到低），用逗号分隔。
只输出序号，不要其他文字。""",
        }],
    )

    try:
        indices = [int(i.strip()) for i in response.choices[0].message.content.split(",")]
        return [documents[i] for i in indices if i < len(documents)]
    except (ValueError, IndexError):
        return documents[:top_n]


# ==================== 4. RAG Agent ====================

class RAGAgent:
    """基于 RAG 的问答 Agent"""

    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.vector_store = VectorStore()
        self.doc_loaded = False

    def load_document(self, file_path: str, chunk_strategy: str = "paragraph"):
        """加载文档到向量库"""
        print(f"正在加载文档: {file_path}")
        text = load_text(file_path)

        if chunk_strategy == "paragraph":
            chunks = chunk_by_paragraph(text)
        else:
            chunks = chunk_by_fixed_size(text)

        self.vector_store.clear()
        self.vector_store.add_documents(chunks)
        self.doc_loaded = True
        print(f"文档加载完成，共 {len(chunks)} 个块")

    def answer(self, question: str, use_rerank: bool = True) -> dict:
        """回答问题"""
        if not self.doc_loaded:
            return {"answer": "请先加载文档", "context": [], "reranked": False}

        # 1. 检索
        results = self.vector_store.search(question, n_results=5)
        if not results:
            return {"answer": "知识库中没有找到相关信息", "context": [], "reranked": False}

        # 2. Rerank（可选）
        if use_rerank and len(results) > 1:
            results = rerank(question, results, top_n=3)

        # 3. 生成回答
        context = "\n\n---\n\n".join(results)
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "你是基于文档的问答助手。请基于提供的资料回答问题。\n"
                        "规则：\n"
                        "1. 只使用资料中的信息，不要编造\n"
                        "2. 如果资料不足以回答，请明确说明\n"
                        "3. 引用资料中的具体内容支持你的回答"
                    ),
                },
                {"role": "user", "content": f"资料:\n{context}\n\n问题: {question}"},
            ],
        )

        return {
            "answer": response.choices[0].message.content,
            "context": results,
            "reranked": use_rerank,
        }


# ==================== 5. 评估器（LLM-as-Judge） ====================

class Evaluator:
    """LLM-as-Judge 评估器"""

    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def evaluate(self, question: str, answer: str, context_chunks: list[str]) -> dict:
        """评估回答质量"""
        context_preview = "\n".join([c[:200] for c in context_chunks[:2]])

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": f"""你是一个评估专家。请从以下三个维度对回答评分（1-5分）：

问题: {question}
回答: {answer}
参考资料: {context_preview[:500]}

评分标准：
- accuracy（准确性）：回答是否与资料一致，有无幻觉
- relevance（相关性）：回答是否切题
- completeness（完整性）：是否涵盖了所有关键信息

请输出 JSON 格式：
{{
    "accuracy": 整数 1-5,
    "relevance": 整数 1-5,
    "completeness": 整数 1-5,
    "explanation": "简要说明评分理由"
}}""",
            }],
            response_format={"type": "json_object"},
        )

        try:
            return json.loads(response.choices[0].message.content)
        except json.JSONDecodeError:
            return {"accuracy": 3, "relevance": 3, "completeness": 3, "explanation": "评分解析失败"}


# ==================== 6. 主流程 ====================

def main():
    rag = RAGAgent()
    evaluator = Evaluator()

    print("=" * 50)
    print("  单文档 RAG 问答（实验 2）")
    print("  输入 'exit' 退出")
    print("=" * 50)

    # 尝试加载默认文档
    doc_path = "sample_doc/sample.txt"
    if os.path.exists(doc_path):
        rag.load_document(doc_path)

    while True:
        try:
            question = input("\n问题: ").strip()
            if question.lower() in ("exit", "quit", "q"):
                break
            if question.lower() == "load":
                path = input("  文档路径: ").strip()
                if os.path.exists(path):
                    rag.load_document(path)
                else:
                    print("  文件不存在")
                continue
            if not question:
                continue

            # 问答
            result = rag.answer(question)

            print(f"\n回答: {result['answer']}")
            print(f"\n引用资料数: {len(result['context'])}")

            # 评估
            scores = evaluator.evaluate(question, result["answer"], result["context"])
            print(f"\n评估分数:")
            print(f"  准确性:     {'★' * scores['accuracy']}{'☆' * (5 - scores['accuracy'])} ({scores['accuracy']}/5)")
            print(f"  相关性:     {'★' * scores['relevance']}{'☆' * (5 - scores['relevance'])} ({scores['relevance']}/5)")
            print(f"  完整性:     {'★' * scores['completeness']}{'☆' * (5 - scores['completeness'])} ({scores['completeness']}/5)")
            print(f"  说明: {scores['explanation']}")

        except KeyboardInterrupt:
            print("\n\n再见！")
            break
        except Exception as e:
            print(f"\n[错误] {e}")


def batch_eval():
    """批量评估测试"""
    rag = RAGAgent()
    evaluator = Evaluator()

    doc_path = "sample_doc/sample.txt"
    if not os.path.exists(doc_path):
        print("请先准备 sample_doc/sample.txt")
        return

    rag.load_document(doc_path)

    test_questions = [
        "这篇文档主要讨论什么主题？",
        "文档中提到了哪些关键概念？",
        "文档的作者或来源是谁？",
        "文档中是否包含具体的数据或例子？",
    ]

    print("\n" + "=" * 50)
    print("批量评估")
    print("=" * 50)

    total_scores = {"accuracy": 0, "relevance": 0, "completeness": 0}

    for i, q in enumerate(test_questions, 1):
        print(f"\n[{i}/{len(test_questions)}] {q}")
        result = rag.answer(q)
        scores = evaluator.evaluate(q, result["answer"], result["context"])

        for k in total_scores:
            total_scores[k] += scores[k]

        print(f"  回答: {result['answer'][:100]}...")
        print(f"  评分: A={scores['accuracy']} R={scores['relevance']} C={scores['completeness']}")

    n = len(test_questions)
    print(f"\n平均分:")
    for k in total_scores:
        print(f"  {k}: {total_scores[k] / n:.1f}/5")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "batch":
        batch_eval()
    else:
        main()
