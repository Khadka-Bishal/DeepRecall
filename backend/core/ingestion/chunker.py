
from typing import List, Dict, Any, Tuple



class LandingAIChunk:
    """Internal chunk representation for LandingAI results."""
    def __init__(self, text: str, page_number: int, grounding: Any = None, image_base64: str = None):
        self.text = text
        self.metadata = type('obj', (object,), {
            'page_number': page_number,
            'grounding': grounding,
            'orig_elements': [],
            'image_base64': image_base64
        })

class DocumentChunker:
    """Chunks document elements (LandingAI ParseResponse) into semantic units."""

    def __init__(self, max_characters: int = 3000, new_after_n_chars: int = 2400, combine_text_under_n_chars: int = 500):
        # Parameters kept for compatibility but currently unused with Page-level splitting
        self.max_characters = max_characters

    def chunk(self, elements: List[Any]) -> Tuple[List[Any], List[Dict[str, Any]]]:
        """Process ParseResponse into Chunks.
        
        Args:
            elements: List containing a single ParseResponse object
        """
        if not elements:
            return [], []
            
        # Unwrap the ParseResponse (it's actually [LandingAIPage] list now from partitioner)
        # partitioner returns [LandingAIPage, LandingAIPage...]
        # My previous chunker implementation expected ParseResponse inside elements[0]
        # But wait, partitioner returns `pages` list directly if I look at 1749 code.
        # "return pages, preview, stats"
        # So elements IS the list of pages.
        
        chunks = []
        preview = []
        
        # Strategy: One chunk per page (as per tutorial split="page")
        for i, page_obj in enumerate(elements):
            
            chunk = LandingAIChunk(
                text=page_obj.text,
                page_number=page_obj.metadata.page_number,
                grounding=page_obj.metadata.grounding,
                image_base64=page_obj.metadata.image_base64
            )
            chunks.append(chunk)

            preview.append({
                "id": f"chk_{i}",
                "content": page_obj.text,
                "length": len(page_obj.text),
                "page": page_obj.metadata.page_number,
                "images": ["Page Image"] if page_obj.metadata.image_base64 else [],
                "tables": [],
            })

        print(f"[chunk] Created {len(chunks)} chunks from LandingAI pages")
        return chunks, preview

    @staticmethod
    def separate_content_types(chunk) -> Dict[str, Any]:
        """Separate text and grounding. Complex types (images/tables) pending implementation."""
        images = []
        if getattr(chunk.metadata, "image_base64", None):
            images.append(chunk.metadata.image_base64)

        return {
            "text": chunk.text,
            "tables": [],
            "images": images,
            "types": ["text", "image"] if images else ["text"],
            "grounding": getattr(chunk.metadata, "grounding", None)
        }

    @staticmethod
    def has_complex_content(chunk) -> bool:
        """Check if a chunk contains tables or images."""
        return False
