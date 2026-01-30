DeepRecall is a hybrid Retrieval-Augmented Generation (RAG) system that uses AWS Lambda for document processing. It separates the "Write Path" (heavy lifting) from the "Read Path" (latency-sensitive chat).

## Technical Overview

-   **Hybrid Search**: Combines BM25 (keyword) and Dense Vector search with Reciprocal Rank Fusion (RRF).
-   **Architecture**:
    -   **Ingestion (Write)**: Event-driven AWS Pipeline (S3 → Lambda → Pinecone).
    -   **Retrieval (Read)**: FastAPI backend querying Pinecone directly.
-   **Infrastructure as Code**: Fully provisioned AWS environment (IAM, S3, Lambda, SQS) using Terraform modules.

## System Architecture

### High-Level Architecture

The system is deployed across a hybrid environment, with infrastructure managed via **Terraform**.

```mermaid
graph TD
    subgraph Client ["Client Side"]
        UI[React Frontend]
    end

    subgraph Backend ["Orchestration"]
        API[FastAPI Server]
    end

    subgraph AWS ["AWS Serverless (Terraform)"]
        S3[S3 Input] --> SQS[SQS Queue] --> Lambda[ADE Processor]
    end

    subgraph KB ["Knowledge Base"]
        Pinecone[(Pinecone DB)]
    end

    UI <-->|REST/WS| API
    API <-->|Query| Pinecone
    API -->|Upload| S3
    Lambda -->|Vectors| Pinecone
```

### Detailed Data Flow

The system implements an **Asynchronous Write Path** (Upload -> S3 -> Lambda -> Pinecone) and a **Synchronous Read Path** (User -> API -> Pinecone).

<details>
<summary>View Sequence Diagram</summary>

```mermaid
sequenceDiagram
    participant U as User
    participant B as Backend
    participant S3 as AWS S3
    participant L as Lambda (ADE)
    participant P as Pinecone

    Note over U, P: 1. Write Path (Ingestion)
    U->>B: Upload PDF
    B->>S3: Upload File
    S3->>L: Trigger Processing
    L->>P: Index Vectors
    B->>S3: Poll Status
    
    Note over U, P: 2. Read Path (Retrieval)
    U->>B: Query
    B->>P: Hybrid Search
    P-->>B: Relvant Chunks
    B->>U: Stream Answer
```
</details>


### Ingestion Pipeline (Write Path)

Handles high-scale document processing using an event-driven serverless architecture:

```mermaid
graph TD
    PDF[PDF File] -->|Upload| S3[S3 Input]
    S3 -->|Trigger| L[Lambda Processor]
    
    subgraph Processing ["Processing Logic"]
        L --> P[ADE Parser]
        P --> C[Semantic Chunker]
        C --> E[Embedding Model]
    end
    
    E --> DB[(Pinecone Vector DB)]
    E --> Out[S3 Output JSON]
```

### Retrieval Pipeline (Read Path)

DeepRecall employs a "Fusion Retrieval" strategy to ensure high recall and precision:

```mermaid
graph TD
    Q[User Query] --> ME[Multi-Query Expansion]
    ME --> P[Parallel Search]
    
    subgraph Hybrid ["Hybrid Retrieval"]
        P --> Dense["Dense Vector Search"]
        P --> BM25["Keyword Search (BM25)"]
    end
    
    Dense --> RRF[RRF Fusion]
    BM25 --> RRF
    
    RRF --> CE[Cross-Encoder Reranking]
    CE --> LLM[LLM Generation]
    LLM --> A[Streamed Answer]
```

## Quick Start
1.  **Backend**: `pip install -r backend/requirements.txt` && `python backend/server.py`
2.  **Frontend**: `npm install` && `npm run dev`

## Observability
Integrated with LangSmith (LLM tracing) and Weights & Biases (performance metrics).

