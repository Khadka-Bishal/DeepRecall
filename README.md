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
    subgraph "Client & Backend Tier"
        direction LR
        C["React + Vite Frontend"] <-->|REST / WebSocket| B["FastAPI Backend"]
        B <-->|Query| P["Pinecone Vector DB"]
    end

    subgraph "AWS Serverless (Managed by Terraform)"
        direction LR
        S["S3 Buckets"] -->|"Event Notification"| SQS["SQS Queue"] -->|"Async Trigger"| L["ADE Processor Lambda"]
    end

    B -->|"Secure Upload"| S
    L -->|"Semantic Chunking"| P
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
    subgraph Ingest ["Ingestion: PDF -> S3 -> Lambda -> DB"]
        direction LR
        PDF[File] --> S3[S3 Input] --> L[Lambda]
        L --> P[ADE Parser] --> C[Chunker] --> E[Embedding]
        E --> DB[(Pinecone)]
        E --> Out[S3 Out]
    end
```

### Retrieval Pipeline (Read Path)

DeepRecall employs a "Fusion Retrieval" strategy to ensure high recall and precision:

```mermaid
graph TD
    subgraph Retrieval ["Read Path: Query -> Hybrid Search -> Rerank -> LLM"]
        direction LR
        Q[Query] --> ME[Expansion] --> P[Parallel]
        P --> V[Vector Search] & K[BM25 Search] -->|"Top N Chunks"| RRF[Fusion]
        RRF -->|"Top N"| CE[Rerank] -->|"Top K"| LLM[Generate] --> A[Stream]
    end
```

## Quick Start
1.  **Backend**: `pip install -r backend/requirements.txt` && `python backend/server.py`
2.  **Frontend**: `npm install` && `npm run dev`

## Observability
Integrated with LangSmith (LLM tracing) and Weights & Biases (performance metrics).

