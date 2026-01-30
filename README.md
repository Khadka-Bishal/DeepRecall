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
    PDF[PDF File] -->|Upload| S3[S3 Input] -->|Trigger| L[Lambda Processor]
    
    subgraph "Processing Logic"
        direction LR
        P[ADE Parser] --> C[Semantic Chunker] --> E[Embedding Model]
    end
    
    L --> P
    E -->|Vectors| DB[(Pinecone)]
    E -->|JSON| Out[S3 Output]
```

### Retrieval Pipeline (Read Path)

DeepRecall employs a "Fusion Retrieval" strategy to ensure high recall and precision:

```mermaid
graph TD
    Q[User Query] --> ME[Multi-Query Expansion] -->|Q1, ..., Qn| P[Parallel Search]
    
    subgraph "Hybrid Retrieval"
        direction LR
        V["Vector Search (Dense)"]
        K["Keyword Search (BM25)"]
        V & K --> RRF[RRF Fusion]
    end
    
    P --> V
    P --> K
    RRF -->|Top 60| CE[Cross-Encoder Reranking] -->|Top 5| LLM[LLM Generation] --> A[Streamed Answer]
```

## Quick Start
1.  **Backend**: `pip install -r backend/requirements.txt` && `python backend/server.py`
2.  **Frontend**: `npm install` && `npm run dev`

## Observability
Integrated with LangSmith (LLM tracing) and Weights & Biases (performance metrics).

