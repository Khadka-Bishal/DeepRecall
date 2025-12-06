from typing import List, Dict, Any, Tuple
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_chroma import Chroma
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document

from .query_expander import MultiQueryExpander
from .rrf_retriever import ReciprocalRankFusionRetriever
from .answer_generator import AnswerGenerator


class HybridRetrieverSystem:
    def __init__(self, persist_directory=None, enable_multi_query: bool = True):
        self.persist_directory = persist_directory
        self.embedding_model = OpenAIEmbeddings(model="text-embedding-3-small")
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        self.vectorstore = None
        self.retriever = None
        self.enable_multi_query = enable_multi_query
        self.multi_query_expander = (
            MultiQueryExpander(llm=self.llm, num_queries=3)
            if enable_multi_query
            else None
        )
        self.answer_generator = AnswerGenerator(llm=self.llm)

    def initialize_vector_store(self, documents: List[Document]):
        kwargs = {
            "documents": documents,
            "embedding": self.embedding_model,
            "collection_metadata": {"hnsw:space": "cosine"},
        }
        if self.persist_directory:
            kwargs["persist_directory"] = self.persist_directory

        self.vectorstore = Chroma.from_documents(**kwargs)

        bm25_retriever = BM25Retriever.from_documents(documents)
        bm25_retriever.k = 5

        self.retriever = ReciprocalRankFusionRetriever(
            vector_retriever=self.vectorstore.as_retriever(search_kwargs={"k": 5}),
            bm25_retriever=bm25_retriever,
            vectorstore=self.vectorstore,
            multi_query_expander=self.multi_query_expander,
            top_n=3,
        )
        print(f"[vectorstore] indexed {len(documents)} docs")
        return self.vectorstore

    async def aretrieve_with_details(
        self, query: str
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """Retrieve documents with detailed scores."""
        if not self.retriever:
            raise ValueError("Retriever not initialized")
        return await self.retriever.ainvoke_with_scores(query)

    def generate_answer(self, query: str, chunks_with_scores: List[Dict]) -> str:
        """Generate an answer from retrieved chunks."""
        return self.answer_generator.generate_answer(query, chunks_with_scores)

    async def agenerate_answer(self, query: str, chunks_with_scores: List[Dict]) -> str:
        """Async version of generate_answer."""
        return await self.answer_generator.agenerate_answer(query, chunks_with_scores)

    async def agenerate_answer_stream(self, query: str, chunks_with_scores: List[Dict]):
        """Stream the answer generation."""
        async for chunk in self.answer_generator.agenerate_answer_stream(
            query, chunks_with_scores
        ):
            yield chunk
