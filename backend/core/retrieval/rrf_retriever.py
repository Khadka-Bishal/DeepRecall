"""Reciprocal Rank Fusion retriever combining BM25 and vector search."""

import asyncio
import concurrent.futures
from time import perf_counter
from typing import List, Dict, Any, Tuple
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_core.callbacks import CallbackManagerForRetrieverRun

_executor = concurrent.futures.ThreadPoolExecutor(max_workers=8)


class ReciprocalRankFusionRetriever(BaseRetriever):
    """Hybrid BM25+vector retriever with RRF fusion."""

    vector_retriever: Any
    bm25_retriever: Any
    vectorstore: Any = None
    multi_query_expander: Any = None
    k: int = 60
    top_n: int = 5

    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun = None
    ) -> List[Document]:
        return [item["document"] for item in self.invoke_with_scores(query)]

    def _bm25_search(self, query: str) -> List[Document]:
        return self.bm25_retriever.invoke(query)

    def _vector_search(self, query: str, k: int) -> List[Tuple[Document, float]]:
        return self.vectorstore.similarity_search_with_score(query, k=k)

    def invoke_with_scores(self, query: str) -> List[Dict[str, Any]]:
        t0 = perf_counter()

        queries = (
            self.multi_query_expander.expand_query(query)
            if self.multi_query_expander
            else [query]
        )

        bm25_futures = [_executor.submit(self._bm25_search, q) for q in queries]
        vector_futures = [_executor.submit(self._vector_search, q, 5) for q in queries]

        sparse = []
        dense = []
        for f in bm25_futures:
            sparse.extend(f.result())
        for f in vector_futures:
            dense.extend(f.result())

        print(
            f"[retrieve] {len(queries)}q -> {len(sparse)}bm25+{len(dense)}vec ({(perf_counter()-t0)*1000:.0f}ms)"
        )

        fused = self._fuse_results(sparse, dense, top_n=self.top_n)
        return fused

    async def ainvoke_with_scores(
        self, query: str
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        loop = asyncio.get_event_loop()
        t0 = perf_counter()

        queries = (
            await self.multi_query_expander.aexpand_query(query)
            if self.multi_query_expander
            else [query]
        )

        bm25_tasks = [
            loop.run_in_executor(_executor, self._bm25_search, q) for q in queries
        ]
        vec_tasks = [
            loop.run_in_executor(_executor, self._vector_search, q, 5) for q in queries
        ]

        all_results = await asyncio.gather(*bm25_tasks, *vec_tasks)
        bm25_results = all_results[: len(queries)]
        vec_results = all_results[len(queries) :]

        sparse = [doc for r in bm25_results for doc in r]
        dense = [doc for r in vec_results for doc in r]

        print(
            f"[retrieve] {len(queries)}q -> {len(sparse)}bm25+{len(dense)}vec ({(perf_counter()-t0)*1000:.0f}ms)"
        )

        fused = self._fuse_results(sparse, dense, top_n=self.top_n)
        return fused, queries

    def _fuse_results(
        self,
        sparse_docs: List[Document],
        dense_results: List[Tuple[Document, float]],
        top_n: int = None,
    ) -> List[Dict[str, Any]]:
        """Apply Reciprocal Rank Fusion to combine results."""
        if top_n is None:
            top_n = self.top_n

        rrf_scores = {}
        doc_metadata_map = {}
        raw_scores_map = {}

        # Process Sparse Results (BM25)
        for rank, doc in enumerate(sparse_docs):
            doc_id = doc.metadata.get("chunk_id")
            if doc_id not in rrf_scores:
                rrf_scores[doc_id] = 0.0
                doc_metadata_map[doc_id] = doc
                raw_scores_map[doc_id] = {"bm25": 0.0, "vector": 0.0}

            score = 1.0 / (self.k + rank + 1)
            rrf_scores[doc_id] += score
            raw_scores_map[doc_id]["bm25"] = 1.0 - (rank / max(len(sparse_docs), 1))

        # Process Dense Results (Vector)
        for rank, (doc, sim_score) in enumerate(dense_results):
            doc_id = doc.metadata.get("chunk_id")
            if doc_id not in rrf_scores:
                rrf_scores[doc_id] = 0.0
                doc_metadata_map[doc_id] = doc
                raw_scores_map[doc_id] = {"bm25": 0.0, "vector": 0.0}

            score = 1.0 / (self.k + rank + 1)
            rrf_scores[doc_id] += score
            raw_scores_map[doc_id]["vector"] = float(sim_score)

        # Sort by Final RRF Score
        sorted_doc_ids = sorted(rrf_scores, key=rrf_scores.get, reverse=True)[:top_n]

        # Construct Final Results (ensure all scores are Python floats for JSON)
        return [
            {
                "document": doc_metadata_map[doc_id],
                "score": float(rrf_scores[doc_id]),
                "scores": {k: float(v) for k, v in raw_scores_map[doc_id].items()},
            }
            for doc_id in sorted_doc_ids
        ]
