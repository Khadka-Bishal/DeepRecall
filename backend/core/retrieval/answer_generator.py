import json
import asyncio
import concurrent.futures
from typing import List, Dict
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

_executor = concurrent.futures.ThreadPoolExecutor(max_workers=8)


class AnswerGenerator:
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm

    def generate_answer(self, query: str, chunks: List[Dict]) -> str:
        txt = f"""Answer using ONLY the documents below. Do NOT add external knowledge.

QUESTION: {query}

DOCUMENTS:
"""
        content = []
        for i, item in enumerate(chunks):
            doc = item["document"]
            if "original_content" in doc.metadata:
                orig = json.loads(doc.metadata["original_content"])
                txt += f"--- Doc {i+1} ---\n{orig.get('raw_text', '')}\n\n"
                for img in orig.get("images_base64", []):
                    content.append(
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{img}"},
                        }
                    )

        txt += "\nANSWER:"
        content.insert(0, {"type": "text", "text": txt})
        return self.llm.invoke([HumanMessage(content=content)]).content

    async def agenerate_answer(self, query: str, chunks: List[Dict]) -> str:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            _executor, self.generate_answer, query, chunks
        )

    async def agenerate_answer_stream(self, query: str, chunks: List[Dict]):
        txt = f"""Answer using ONLY the documents below. Do NOT add external knowledge.

QUESTION: {query}

DOCUMENTS:
"""
        content = []
        for i, item in enumerate(chunks):
            doc = item["document"]
            if "original_content" in doc.metadata:
                orig = json.loads(doc.metadata["original_content"])
                txt += f"--- Doc {i+1} ---\n{orig.get('raw_text', '')}\n\n"
                for img in orig.get("images_base64", []):
                    content.append(
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{img}"},
                        }
                    )

        txt += "\nANSWER:"
        content.insert(0, {"type": "text", "text": txt})

        async for chunk in self.llm.astream([HumanMessage(content=content)]):
            if chunk.content:
                yield chunk.content
