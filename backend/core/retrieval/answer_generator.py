"""Answer generation from retrieved document chunks."""

import json
import logging
from typing import List, Dict, AsyncIterator

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

log = logging.getLogger(__name__)


class AnswerGenerator:
    """Generates answers from retrieved document chunks.
    
    Uses the LLM to synthesize comprehensive answers based only on
    the provided document context, avoiding external knowledge.
    """
    
    def __init__(self, llm: ChatOpenAI):
        """Initialize the answer generator.
        
        Args:
            llm: LangChain ChatOpenAI instance to use for generation.
        """
        self.llm = llm

    def _build_prompt_content(
        self, query: str, chunks: List[Dict]
    ) -> List[Dict]:
        """Build the multimodal prompt content from chunks.
        
        Args:
            query: The user's question.
            chunks: List of chunk dicts with 'document' key.
            
        Returns:
            List of content blocks for LangChain message.
        """
        txt = """Answer using ONLY the documents below. Do NOT add external knowledge.

QUESTION: {query}

DOCUMENTS:
""".format(query=query)
        
        content = []
        
        for i, item in enumerate(chunks):
            doc = item["document"]
            
            text_content = ""
            
            # 1. Try metadata 'original_content'
            if "original_content" in doc.metadata:
                try:
                    orig = json.loads(doc.metadata["original_content"])
                    text_content = orig.get("raw_text", "")
                    
                    # Add base64 images if present
                    for img in orig.get("images_base64", []):
                        content.append({
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{img}"},
                        })
                except (json.JSONDecodeError, TypeError):
                    pass
            
            # 2. Fallback to page_content
            if not text_content.strip():
                text_content = doc.page_content
                
            # 3. Add to prompt if valid
            if text_content.strip():
                txt += f"--- Doc {i+1} ---\n{text_content}\n\n"

        txt += "\nANSWER:"
        content.insert(0, {"type": "text", "text": txt})
        
        return content

    def generate_answer(self, query: str, chunks: List[Dict]) -> str:
        """Generate an answer from retrieved chunks.
        
        Args:
            query: The user's question.
            chunks: List of chunk dicts with 'document' key.
            
        Returns:
            Generated answer string.
        """
        content = self._build_prompt_content(query, chunks)
        return self.llm.invoke([HumanMessage(content=content)]).content

    async def agenerate_answer(self, query: str, chunks: List[Dict]) -> str:
        """Async version of generate_answer.
        
        Args:
            query: The user's question.
            chunks: List of chunk dicts with 'document' key.
            
        Returns:
            Generated answer string.
        """
        content = self._build_prompt_content(query, chunks)
        response = await self.llm.ainvoke([HumanMessage(content=content)])
        return response.content

    async def agenerate_answer_stream(
        self, query: str, chunks: List[Dict]
    ) -> AsyncIterator[str]:
        """Stream the answer generation token by token.
        
        Args:
            query: The user's question.
            chunks: List of chunk dicts with 'document' key.
            
        Yields:
            Answer tokens as they are generated.
        """
        content = self._build_prompt_content(query, chunks)
        
        async for chunk in self.llm.astream([HumanMessage(content=content)]):
            if chunk.content:
                yield chunk.content
