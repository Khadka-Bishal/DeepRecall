"""Main ingestion pipeline orchestrator."""

import json
import asyncio
from typing import List, Dict, Any, Tuple
from time import perf_counter
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from .partitioner import DocumentPartitioner
from .chunker import DocumentChunker
from .summarizer import ContentSummarizer


class IngestionReport:
    """Report containing ingestion statistics."""

    def __init__(self):
        self.elements_found = 0
        self.chunks_created = 0
        self.preview_elements = []
        self.preview_chunks = []
        self.summary_stats = {}


class IngestionPipeline:
    """Main pipeline for document ingestion."""

    def __init__(self, retriever_system=None):
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        self.embedding_model = OpenAIEmbeddings(model="text-embedding-3-small")
        self.retriever_system = retriever_system

        # Initialize components
        self.partitioner = DocumentPartitioner()
        self.chunker = DocumentChunker()
        self.summarizer = ContentSummarizer(llm=self.llm)

    def partition_document(
        self, file_path: str
    ) -> Tuple[List[Any], List[Dict[str, Any]], Dict[str, float]]:
        """Partition a document into elements."""
        return self.partitioner.partition(file_path)

    def create_chunks(
        self, elements: List[Any]
    ) -> Tuple[List[Any], List[Dict[str, Any]]]:
        """Create chunks from elements."""
        return self.chunker.chunk(elements)

    def separate_content_types(self, chunk) -> Dict[str, Any]:
        """Separate content types from a chunk."""
        return self.chunker.separate_content_types(chunk)

    def create_ai_enhanced_summary(
        self, text: str, tables: List[str], images: List[str]
    ) -> str:
        """Create AI-enhanced summary."""
        return self.summarizer.summarize(text, tables, images)

    def _create_text_documents(self, chunks: List[Any]) -> List[Document]:
        """Create plain text documents when no complex content is detected."""
        documents = []
        for i, chunk in enumerate(chunks):
            content_data = self.separate_content_types(chunk)
            doc = Document(
                page_content=content_data["text"],
                metadata={
                    "chunk_id": str(i),
                    "original_content": json.dumps(
                        {
                            "raw_text": content_data["text"],
                            "tables_html": content_data["tables"],
                            "images_base64": content_data["images"],
                        }
                    ),
                },
            )
            documents.append(doc)
        return documents

    async def process_and_summarize_async(self, chunks: List[Any]) -> List[Document]:
        """Process chunks and create AI summaries for complex content."""
        t0 = perf_counter()
        ai_tasks = []
        text_only = []

        for i, chunk in enumerate(chunks):
            data = self.separate_content_types(chunk)
            if data["tables"] or data["images"]:
                ai_tasks.append((i, data))
            else:
                text_only.append((i, data))

        results = {}
        for i, data in text_only:
            results[i] = Document(
                page_content=data["text"],
                metadata={
                    "chunk_id": str(i),
                    "original_content": json.dumps(
                        {
                            "raw_text": data["text"],
                            "tables_html": data["tables"],
                            "images_base64": data["images"],
                        }
                    ),
                },
            )

        if ai_tasks:

            async def process_ai_chunk(idx: int, d: dict) -> Tuple[int, Document]:
                enhanced = await self.summarizer.asummarize(
                    d["text"], d["tables"], d["images"]
                )
                return idx, Document(
                    page_content=enhanced,
                    metadata={
                        "chunk_id": str(idx),
                        "original_content": json.dumps(
                            {
                                "raw_text": d["text"],
                                "tables_html": d["tables"],
                                "images_base64": d["images"],
                            }
                        ),
                    },
                )

            ai_results = await asyncio.gather(
                *[process_ai_chunk(i, d) for i, d in ai_tasks]
            )
            for idx, doc in ai_results:
                results[idx] = doc

        docs = [results[i] for i in sorted(results.keys())]
        print(f"[summarize] {len(chunks)} chunks in {perf_counter()-t0:.1f}s")
        return docs

    async def run(self, file_path: str, manager=None) -> Dict[str, Any]:
        """Run the full ingestion pipeline."""
        loop = asyncio.get_event_loop()

        # Partition
        elements, el_preview, partition_stats = await loop.run_in_executor(
            None, self.partition_document, file_path
        )

        if manager:
            await manager.broadcast(
                {
                    "type": "pipeline",
                    "stage": "PARTITIONING",
                    "status": "complete",
                    "count": len(elements),
                    "meta": partition_stats,
                }
            )
            await manager.broadcast(
                {"type": "pipeline", "stage": "CHUNKING", "status": "active"}
            )

        # Chunk
        chunks, chk_preview = await loop.run_in_executor(
            None, self.create_chunks, elements
        )

        if manager:
            await manager.broadcast(
                {
                    "type": "pipeline",
                    "stage": "CHUNKING",
                    "status": "complete",
                    "count": len(chunks),
                }
            )

        # Check if AI summarization needed
        needs_ai = any(self.chunker.has_complex_content(chunk) for chunk in chunks)

        if needs_ai:
            if manager:
                await manager.broadcast(
                    {"type": "pipeline", "stage": "SUMMARIZING", "status": "active"}
                )
            processed_docs = await self.process_and_summarize_async(chunks)
            if manager:
                await manager.broadcast(
                    {"type": "pipeline", "stage": "SUMMARIZING", "status": "complete"}
                )
        else:
            if manager:
                await manager.broadcast(
                    {"type": "pipeline", "stage": "SUMMARIZING", "status": "skipped"}
                )
            processed_docs = self._create_text_documents(chunks)

        # Filter empty documents
        processed_docs = [
            doc
            for doc in processed_docs
            if doc.page_content and doc.page_content.strip()
        ]

        if not processed_docs:
            raise ValueError("No valid content extracted from document.")

        # Count totals
        total_images = sum(
            len(
                json.loads(d.metadata.get("original_content", "{}")).get(
                    "images_base64", []
                )
            )
            for d in processed_docs
        )
        total_tables = sum(
            len(
                json.loads(d.metadata.get("original_content", "{}")).get(
                    "tables_html", []
                )
            )
            for d in processed_docs
        )

        # Vectorize
        if manager:
            await manager.broadcast(
                {"type": "pipeline", "stage": "VECTORIZING", "status": "active"}
            )

        if self.retriever_system:
            await loop.run_in_executor(
                None, self.retriever_system.initialize_vector_store, processed_docs
            )

        if manager:
            await manager.broadcast(
                {"type": "pipeline", "stage": "VECTORIZING", "status": "complete"}
            )

        print(f"[pipeline] {len(processed_docs)} docs indexed")

        # Build final preview
        final_chunk_preview = []
        for doc in processed_docs:
            orig = json.loads(doc.metadata.get("original_content", "{}"))
            final_chunk_preview.append(
                {
                    "id": f"chk_{doc.metadata.get('chunk_id', '0')}",
                    "content": orig.get("raw_text", doc.page_content),
                    "length": len(orig.get("raw_text", doc.page_content)),
                    "page": doc.metadata.get("page_number", 1),
                    "images": orig.get("images_base64", []),
                    "tables": orig.get("tables_html", []),
                }
            )

        return {
            "documents": processed_docs,
            "report": {
                "elements": el_preview,
                "chunks": final_chunk_preview,
                "total_elements": len(elements),
                "total_chunks": len(chunks),
                "total_images": total_images,
                "total_tables": total_tables,
            },
        }
