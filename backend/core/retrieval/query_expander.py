"""Multi-query expansion for improved retrieval recall."""

import logging
from time import perf_counter
from typing import List

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from core.prompts import QUERY_EXPANSION_SYSTEM, get_query_expansion_user_prompt

log = logging.getLogger(__name__)


class MultiQueryExpander:
    """LLM-based query expansion for improved recall.
    
    Generates alternative phrasings of a user query to improve
    retrieval coverage across different terminology.
    """

    def __init__(self, llm: ChatOpenAI, num_queries: int = 3):
        """Initialize the query expander.
        
        Args:
            llm: LangChain ChatOpenAI instance to use for expansion.
            num_queries: Total number of queries to return (original + generated).
        """
        self.llm = llm
        self.num_queries = num_queries

    def _parse_response(self, response_content: str) -> List[str]:
        """Parse LLM response into list of queries.
        
        Args:
            response_content: Raw response content from LLM.
            
        Returns:
            List of cleaned query strings.
        """
        return [
            q.strip().strip('"').strip("'")
            for q in response_content.strip().split("\n")
            if q.strip()
        ]

    def expand_query(self, query: str) -> List[str]:
        """Expand a query into multiple alternative phrasings.
        
        Args:
            query: The original user query.
            
        Returns:
            List of queries starting with original, followed by alternatives.
        """
        t0 = perf_counter()
        num_alternatives = self.num_queries - 1
        
        user_prompt = get_query_expansion_user_prompt(query, num_alternatives)
        
        response = self.llm.invoke([
            SystemMessage(content=QUERY_EXPANSION_SYSTEM),
            HumanMessage(content=user_prompt)
        ])

        expanded = self._parse_response(response.content)
        all_queries = [query] + expanded[:num_alternatives]
        
        elapsed_ms = (perf_counter() - t0) * 1000
        log.info("Expanded to %d queries (%.0fms)", len(all_queries), elapsed_ms)
        
        return all_queries

    async def aexpand_query(self, query: str) -> List[str]:
        """Async version of expand_query.
        
        Args:
            query: The original user query.
            
        Returns:
            List of queries starting with original, followed by alternatives.
        """
        t0 = perf_counter()
        num_alternatives = self.num_queries - 1
        
        user_prompt = get_query_expansion_user_prompt(query, num_alternatives)
        
        response = await self.llm.ainvoke([
            SystemMessage(content=QUERY_EXPANSION_SYSTEM),
            HumanMessage(content=user_prompt)
        ])

        expanded = self._parse_response(response.content)
        all_queries = [query] + expanded[:num_alternatives]
        
        elapsed_ms = (perf_counter() - t0) * 1000
        log.info("Expanded to %d queries (%.0fms)", len(all_queries), elapsed_ms)
        
        return all_queries
