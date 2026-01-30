"""Prompt templates for LLM interactions in DeepRecall.

Centralizes all prompt templates to avoid duplication and ensure consistency.
"""

# Query Expansion Prompts
QUERY_EXPANSION_SYSTEM = """You are a query expansion expert. Given a user question, generate alternative versions 
that capture different aspects or phrasings of the same information need.

Rules:
1. Each query should approach the question from a different angle
2. Use different keywords and terminology (synonyms, related terms)
3. Keep queries concise and search-friendly
4. Output ONLY the queries, one per line, no numbering or bullets"""


def get_query_expansion_user_prompt(query: str, num_alternatives: int) -> str:
    """Generate the user prompt for query expansion.
    
    Args:
        query: The original user query to expand.
        num_alternatives: Number of alternative queries to generate.
        
    Returns:
        Formatted user prompt string.
    """
    return f"""Generate {num_alternatives} alternative search queries for:

"{query}"

Output {num_alternatives} queries, one per line:"""


# Answer Generation Prompts
ANSWER_GENERATION_SYSTEM = """Answer using ONLY the documents below. Do NOT add external knowledge."""


def format_answer_prompt(query: str, documents: list) -> str:
    """Format the full answer generation prompt.
    
    Args:
        query: The user's question.
        documents: List of document texts to include as context.
        
    Returns:
        Formatted prompt string.
    """
    docs_text = ""
    for i, doc_text in enumerate(documents):
        docs_text += f"--- Doc {i+1} ---\n{doc_text}\n\n"
    
    return f"""{ANSWER_GENERATION_SYSTEM}

QUESTION: {query}

DOCUMENTS:
{docs_text}
ANSWER:"""
