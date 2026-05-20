# Baseline vs Agent

This sample compares a naive single LLM call against the grounded planner + tools + synthesizer pipeline for the canonical vector database query. The baseline is faster and simpler, but it has no source grounding or tool trace.

## Baseline (raw LLM, no tools)

Command:

```powershell
bot ask "Compare the top 3 open-source vector databases for a startup building RAG products." --baseline
```

Output:

```json
{
  "question": "Compare the top 3 open-source vector databases for a startup building RAG products.",
  "short_answer": "When considering open-source vector databases for a startup building Retrieval-Augmented Generation (RAG) products, three of the top options are **Pinecone**, **Weaviate**, and **Milvus**. Here\u2019s a comparison of these databases based on key features:\n\n### 1. **Weaviate**\n- **Overview**: Weaviate is a cloud-native, modular, real-time vector search engine that is designed to handle large datasets.\n- **Key Features**:\n  - **Hybrid Search**: Combines vector search with traditional keyword search.\n  - **GraphQL API**: Offers a flexible API for querying data.\n  - **Schema-based**: Supports rich data types and relationships.\n  - **Scalability**: Can scale horizontally and is suitable for large-scale applications.\n  - **Integrations**: Supports various machine learning models and can be integrated with popular frameworks.\n- **Use Cases**: Ideal for applications requiring complex queries and relationships, such as recommendation systems and knowledge graphs.\n\n### 2. **Milvus**\n- **Overview**: Milvus is a high-performance vector database designed for managing and searching large-scale vector data.\n- **Key Features**:\n  - **High Throughput**: Optimized for fast insertion and querying of vectors.\n  - **Multiple Indexing Options**: Supports various indexing algorithms (e.g., IVF, HNSW) for efficient searching.\n  - **Distributed Architecture**: Can be deployed in a distributed manner for scalability.\n  - **Integration**: Works well with machine learning frameworks and supports various data types.\n- **Use Cases**: Suitable for applications in AI, image and video search, and recommendation systems where performance is critical.\n\n### 3. **Pinecone**\n- **Overview**: Pinecone is a fully managed vector database that focuses on simplicity and performance, although it has a free tier for development.\n- **Key Features**:\n  - **Managed Service**: Simplifies deployment and management, allowing developers to focus on building applications.\n  - **Real-time Updates**: Supports real-time data updates and querying.\n  - **Scalability**: Automatically scales with your data and query load.\n  - **Easy Integration**: Provides SDKs for various programming languages and integrates well with machine learning pipelines.\n- **Use Cases**: Best for startups looking for a hassle-free, scalable solution without the overhead of managing infrastructure.\n\n### Conclusion\n- **Weaviate** is ideal for applications needing complex queries and relationships.\n- **Milvus** excels in performance and scalability for high-throughput applications.\n- **Pinecone** offers a managed solution that simplifies the development process, making it suitable for startups focused on rapid deployment.\n\nChoosing the right database will depend on your specific use case, performance requirements, and whether you prefer a managed service or an open-source solution that you can host yourself.",
  "key_findings": [
    "Baseline single-LLM-call output. See short_answer."
  ],
  "sources": [],
  "confidence": "low",
  "confidence_rationale": "Baseline single-LLM-call output, no grounding.",
  "limitations": [
    "No tools used. No source grounding. May contain fabrications."
  ],
  "assumptions": [],
  "next_steps": []
}
```

## Agent (planner + tools + grounding)

Short answer:

> The top three open-source vector databases suitable for RAG products are Weaviate, Qdrant, and Redis.

Key findings (with inline citations):

- Weaviate is an open-source vector database that combines vector search with structured filtering, offering scalability and fault tolerance, making it suitable for RAG applications [1]
- Qdrant is highlighted for its efficiency in handling tens of millions of vectors, making it a strong candidate for production-ready RAG systems [2]
- Redis serves as a versatile data structure server and vector query engine, known for its speed and feature richness, which is beneficial for real-time applications in RAG products [3]

Sources:

```json
[
  {
    "url": "https://www.gigaspaces.com/blog/best-vector-database-solutions-for-rag-applications",
    "title": "The 6 Best Vector Database Solutions for RAG Applications | GigaSpaces AI",
    "used_for": ["Comparing vector databases for RAG applications"]
  },
  {
    "url": "https://www.reddit.com/r/LangChain/comments/1mqp585/best_vector_db_for_production_ready_rag/",
    "title": "Best Vector DB for production ready RAG ? : r/LangChain - Reddit",
    "used_for": ["Discussion on vector databases suitable for RAG"]
  },
  {
    "url": "https://github.com/redis/redis",
    "title": "Redis GitHub Repository",
    "used_for": ["Information on Redis as a vector database"]
  },
  {
    "url": "https://github.com/weaviate/weaviate",
    "title": "Weaviate GitHub Repository",
    "used_for": ["Information on Weaviate as a vector database"]
  }
]
```

Confidence: `high`. Limitations: none flagged by the synthesizer for this query.

## Key difference

The baseline lists **Pinecone** as a top *open-source* vector database — but Pinecone is closed-source managed SaaS. The agent's answer doesn't make this mistake because it grounds in actual GitHub repositories (note the `github.com/weaviate/weaviate` and `github.com/redis/redis` URLs in `sources`). Same LLM under the hood — the difference is the grounding loop.

## Honest caveat

The agent's answer is not perfect either. **Redis** appears in the list because `github_search` returned it as a high-star repo with vector-search capabilities — but Redis is primarily a cache, not a purpose-built vector DB. A more rigorous result would have featured Qdrant, Milvus, or Chroma in Redis's slot. Future work: weight `github_search` results by topic relevance rather than star count alone, or have the planner explicitly query for "vector-database" topic tag.

Even with that caveat, the agent's failure mode is *recoverable* (a reviewer can click through to `github.com/redis/redis` and verify the claim themselves), while the baseline's failure mode (calling Pinecone open-source) is *unverifiable* and indistinguishable from confident truth.
