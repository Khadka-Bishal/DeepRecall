# DeepRecall

DeepRecall is an advanced Retrieval-Augmented Generation (RAG) system that enables intelligent question-answering over PDF documents. Built with production-grade architecture, it combines hybrid search algorithms, streaming responses, and multi-tier caching to deliver fast, accurate, and contextually-aware answers.

## 🆕 What Makes This Different

DeepRecall implements several production-level features that go beyond basic implementations:

- **Hybrid Retrieval with RRF Fusion**: Combines BM25 lexical search and vector similarity using Reciprocal Rank Fusion algorithm and Cross Encoder.
- **Multi-Query Expansion**: LLM generates 3 query variations per request to overcome vocabulary mismatch, improving recall by capturing different phrasings
- **Two-Tier Caching System**: Separate retrieval and answer caches with LRU eviction + TTL.
- **Real-Time Streaming Architecture**: WebSocket-based progressive answer delivery.
- **Transparent UI Observability**: Frontend displays real-time backend operations including query expansion variations, retrieved chunks with similarity scores, and source attributions giving users complete visibility into the RAG pipeline
- **Semantic Chunking**: Uses `chunk_by_title` strategy to preserve document structure instead of naive fixed-size splitting
- **Modular Clean Architecture**: Separation of core domain logic from web layer following SOLID principles, not a monolithic script

## 📐 Architecture
![alt text](image.png)

![alt text](image-1.png)

## Demo

https://github.com/user-attachments/assets/98f42624-295e-41c5-9aae-744205db482d





## 📡 API Reference

**Ingestion**

```
POST /ingest
Content-Type: multipart/form-data
Body: PDF file

Response: { chunks_created, collection_name, status }
```

**Chat (Streaming)**

```
POST /chat/stream
Body: { query, collection_name }

Response: Server-Sent Events (token, done, queries, chunks)
```

**System**

```
GET /health - Health check
GET /cache/stats - Cache performance metrics
POST /cache/clear - Clear all caches
GET /benchmarks - System performance statistics
```

## 🛠 Skills

- **Advanced NLP/ML Systems**: RAG pipelines, embedding models, prompt engineering, retrieval algorithms
- **Distributed Systems**: Caching strategies, async operations, WebSocket management, state consistency
- **API Development**: RESTful design, streaming responses, WebSocket protocols, error handling
- **Performance Optimization**: Multi-tier caching, query expansion, parallel processing, latency reduction
- **Production Engineering**: Observability, monitoring, clean architecture, dependency injection
- **Cloud Deployment**: Render.com deployment, environment management, CORS configuration

## 📊 Observability

Integrated monitoring through:

- **LangSmith**: LLM call tracing and prompt inspection
- **Weights & Biases**: Model performance tracking
- **Custom Benchmarks**: Latency, cache hit rates, error rates

## 🏛️ Other Projects

Check out my other projects [here](https://github.com/Khadka-Bishal).

## 🔗 Connect

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-blue)](https://www.linkedin.com/in/khadka-bishal/)
