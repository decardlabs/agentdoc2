# Phase 2-04: Agentic RAG

## 从 Pipeline 到 Agent

基础的 RAG 是一个固定 pipeline：

```
query → embed → search → retrieve → generate
```

Agentic RAG 让 **Agent 动态决定检索策略**：

```
query → Agent 分析
         → 需要更多上下文？→ 检索 → 评估结果是否足够 → 不够再检索
         → 需要多源信息？→ 并行检索多个知识库
         → 不够具体？→ 改写查询再检索
         → 够了 → 生成最终回答
```

## 为什么需要 Agentic RAG？

| 场景 | 固定 Pipeline | Agentic RAG |
|------|-------------|-------------|
| "这篇论文用了什么方法？" | 可能检索不到准确段落 | 可以反复调整检索关键词 |
| "对比论文 A 和 B 的方法" | 一次检索只返回一个主题 | 需要从不同角度多次检索 |
| "帮我写个论文总结" | 只回答具体问题，不会规划 | 主动规划需要检索哪些信息 |

## 实现一个简单的 Agentic RAG

```python
class AgenticRAG:
    def __init__(self, collection, llm_client, max_searches=5):
        self.collection = collection
        self.client = llm_client
        self.max_searches = max_searches
        self.search_history = []

    def _should_search(self, question: str, context: list[str], search_count: int) -> tuple[bool, str]:
        """判断是否需要继续检索"""
        context_text = "\n\n".join(context) if context else "尚无上下文"

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": f"""
问题: {question}
已有上下文: {context_text}
已检索次数: {search_count}

基于已有信息，是否能完整回答这个问题？
如果能，输出: NO
如果不能，输出需要进一步搜索的关键词: SEARCH: <关键词>
"""}],
        )

        return response.choices[0].message.content

    def _rewrite_query(self, question: str, context: list[str]) -> str:
        """重写检索查询以获取更准确的结果"""
        context_text = "\n\n".join(context) if context else "尚无上下文"

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": f"""
原始问题: {question}
已有上下文: {context_text}

你需要补充哪些信息？请设计一个更精准的检索查询。
只输出查询关键词，不要其他内容。
"""}],
        )
        return response.choices[0].message.content

    def answer(self, question: str) -> str:
        context = []
        search_count = 0

        while search_count < self.max_searches:
            decision = self._should_search(question, context, search_count)

            if decision.startswith("NO"):
                break

            # 需要检索
            query = self._rewrite_query(question, context) if context else question
            self.search_history.append(query)
            print(f"  [检索 {search_count + 1}] 查询: {query}")

            results = self.collection.query(
                query_texts=[query],
                n_results=3,
            )

            new_chunks = results["documents"][0]
            context.extend(new_chunks)
            search_count += 1

        # 基于全部检索结果生成回答
        final_context = "\n\n---\n\n".join(context)
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": f"""
基于以下资料回答问题。如果资料不足以回答请明确说明。
每次检索的查询: {', '.join(self.search_history)}

资料:
{final_context}
"""},
            {"role": "user", "content": question},
        ])
        return response.choices[0].message.content
```

## Agentic RAG 进阶模式

### 1. 多源并行检索

```python
def parallel_retrieve(question: str, sources: list[str]) -> list[str]:
    """从多个知识源并行检索"""
    from concurrent.futures import ThreadPoolExecutor

    with ThreadPoolExecutor() as executor:
        futures = {
            executor.submit(query_source, source, question): source
            for source in sources
        }
        results = []
        for future in futures:
            results.extend(future.result())
    return results
```

### 2. 检索结果自评估

```python
def evaluate_retrieval_quality(question: str, chunks: list[str]) -> list[str]:
    """让 LLM 评估每个 chunk 的相关性，过滤不相关的"""
    filtered = []
    for chunk in chunks:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": f"""
问题: {question}
段落: {chunk}

这个段落对回答问题有帮助吗？只回答 YES 或 NO。
"""}],
        )
        if response.choices[0].message.content == "YES":
            filtered.append(chunk)
    return filtered
```

## 练习

1. 在实验 3 的基础上，将固定 RAG pipeline 改为 Agentic RAG
2. 实现一个带"检索结果自评估"的 Agentic RAG
3. 对比 Agentic RAG 和固定 pipeline 在复杂问题上的效果差异

## 检查清单

- [ ] 理解 Agentic RAG 和固定 pipeline RAG 的区别
- [ ] 能实现带自适应检索的 RAG Agent
- [ ] 能实现查询重写
- [ ] 能对比两种方案在不同场景下的优劣
