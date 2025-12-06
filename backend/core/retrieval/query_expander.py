"""Multi-query expansion for improved retrieval recall."""

from time import perf_counter
from typing import List
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage


class MultiQueryExpander:
    """LLM-based query expansion for improved recall."""

    def __init__(self, llm: ChatOpenAI, num_queries: int = 3):
        self.llm = llm
        self.num_queries = num_queries

    def expand_query(self, query: str) -> List[str]:
        t0 = perf_counter()

        system_prompt = """You are a query expansion expert. Given a user question, generate alternative versions 
that capture different aspects or phrasings of the same information need.

Rules:
1. Each query should approach the question from a different angle
2. Use different keywords and terminology (synonyms, related terms)
3. Keep queries concise and search-friendly
4. Output ONLY the queries, one per line, no numbering or bullets"""

        user_prompt = f"""Generate {self.num_queries - 1} alternative search queries for:

"{query}"

Output {self.num_queries - 1} queries, one per line:"""

        response = self.llm.invoke(
            [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
        )

        # Parse response into list of queries, strip quotes
        expanded = [
            q.strip().strip('"').strip("'")
            for q in response.content.strip().split("\n")
            if q.strip()
        ]

        all_queries = [query] + expanded[: self.num_queries - 1]
        print(f"[expand] {len(all_queries)} queries ({(perf_counter()-t0)*1000:.0f}ms)")
        return all_queries

    async def aexpand_query(self, query: str) -> List[str]:
        t0 = perf_counter()

        system_prompt = """You are a query expansion expert. Given a user question, generate alternative versions 
that capture different aspects or phrasings of the same information need.

Rules:
1. Each query should approach the question from a different angle
2. Use different keywords and terminology (synonyms, related terms)
3. Keep queries concise and search-friendly
4. Output ONLY the queries, one per line, no numbering or bullets"""

        user_prompt = f"""Generate {self.num_queries - 1} alternative search queries for:

"{query}"

Output {self.num_queries - 1} queries, one per line:"""

        response = await self.llm.ainvoke(
            [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
        )

        # Parse response into list of queries, strip quotes
        expanded = [
            q.strip().strip('"').strip("'")
            for q in response.content.strip().split("\n")
            if q.strip()
        ]

        all_queries = [query] + expanded[: self.num_queries - 1]
        print(f"[expand] {len(all_queries)} queries ({(perf_counter()-t0)*1000:.0f}ms)")
        return all_queries
