"""AI-powered content summarization for complex content."""

import asyncio
from typing import List
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage


class ContentSummarizer:
    """Generates searchable summaries for document content with tables/images."""

    def __init__(self, llm: ChatOpenAI):
        self.llm = llm

    def summarize(self, text: str, tables: List[str], images: List[str]) -> str:
        """Create an AI-enhanced summary for complex content."""
        try:
            prompt_text = f"""You are creating a searchable description for document content retrieval.

STRICT RULES:
1. ONLY describe what is explicitly present in the provided content
2. DO NOT add external knowledge, context, or information not in the content
3. DO NOT make assumptions or inferences beyond what is stated
4. If an image shows something, describe ONLY what is visibly shown
5. Preserve exact numbers, names, and data from the original content

CONTENT TO ANALYZE:
TEXT CONTENT:
{text}
"""

            if tables:
                prompt_text += "TABLES:\n"
                for i, table in enumerate(tables):
                    prompt_text += f"Table {i+1}:\n{table}\n\n"

            prompt_text += """
YOUR TASK:
Extract and list ONLY information that appears in the content above:
1. Exact facts, numbers, and data points from the text/tables
2. Main topics mentioned (not implied)
3. For images: describe ONLY what is visually present

DO NOT add any information not explicitly present in the content.
DESCRIPTION:"""

            message_content = [{"type": "text", "text": prompt_text}]

            for image_base64 in images:
                message_content.append(
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"},
                    }
                )

            message = HumanMessage(content=message_content)
            response = self.llm.invoke([message])
            return response.content

        except Exception:
            return text

    async def asummarize(self, text: str, tables: List[str], images: List[str]) -> str:
        """Async version of summarize."""
        try:
            prompt_text = f"""You are creating a searchable description for document content retrieval.

STRICT RULES:
1. ONLY describe what is explicitly present in the provided content
2. DO NOT add external knowledge, context, or information not in the content
3. DO NOT make assumptions or inferences beyond what is stated
4. If an image shows something, describe ONLY what is visibly shown
5. Preserve exact numbers, names, and data from the original content

CONTENT TO ANALYZE:
TEXT CONTENT:
{text}
"""

            if tables:
                prompt_text += "TABLES:\n"
                for i, table in enumerate(tables):
                    prompt_text += f"Table {i+1}:\n{table}\n\n"

            prompt_text += """
YOUR TASK:
Extract and list ONLY information that appears in the content above:
1. Exact facts, numbers, and data points from the text/tables
2. Main topics mentioned (not implied)
3. For images: describe ONLY what is visually present

DO NOT add any information not explicitly present in the content.
DESCRIPTION:"""

            message_content = [{"type": "text", "text": prompt_text}]

            for img_b64 in images:
                message_content.append(
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"},
                    }
                )

            response = await self.llm.ainvoke([HumanMessage(content=message_content)])
            return response.content

        except Exception:
            return text
