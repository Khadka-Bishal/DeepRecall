"""Document chunking utilities."""

from typing import List, Dict, Any, Tuple
from unstructured.chunking.title import chunk_by_title


class DocumentChunker:
    """Chunks document elements into semantic units."""

    def __init__(
        self,
        max_characters: int = 3000,
        new_after_n_chars: int = 2400,
        combine_text_under_n_chars: int = 500,
    ):
        self.max_characters = max_characters
        self.new_after_n_chars = new_after_n_chars
        self.combine_text_under_n_chars = combine_text_under_n_chars

    def chunk(self, elements: List[Any]) -> Tuple[List[Any], List[Dict[str, Any]]]:
        """Chunk elements into semantic units.

        Returns:
            Tuple of (chunks, preview_data)
        """
        chunks = chunk_by_title(
            elements,
            max_characters=self.max_characters,
            new_after_n_chars=self.new_after_n_chars,
            combine_text_under_n_chars=self.combine_text_under_n_chars,
        )

        preview = []
        for i, chunk in enumerate(chunks):
            page = 1
            images = []
            tables = []
            if hasattr(chunk, "metadata"):
                page = getattr(chunk.metadata, "page_number", 1)
                if hasattr(chunk.metadata, "orig_elements"):
                    for el in chunk.metadata.orig_elements:
                        el_type = type(el).__name__
                        if el_type == "Table":
                            tables.append(getattr(el.metadata, "text_as_html", el.text))
                        elif el_type == "Image" and hasattr(
                            el.metadata, "image_base64"
                        ):
                            images.append(el.metadata.image_base64)

            preview.append(
                {
                    "id": f"chk_{i}",
                    "content": chunk.text,
                    "length": len(chunk.text),
                    "page": page,
                    "images": images,
                    "tables": tables,
                }
            )

        print(f"[chunk] {len(chunks)} chunks")
        return chunks, preview

    @staticmethod
    def separate_content_types(chunk) -> Dict[str, Any]:
        """Separate text, tables, and images from a chunk."""
        content_data = {
            "text": chunk.text,
            "tables": [],
            "images": [],
            "types": ["text"],
        }

        if hasattr(chunk, "metadata") and hasattr(chunk.metadata, "orig_elements"):
            for el in chunk.metadata.orig_elements:
                el_type = type(el).__name__
                if el_type == "Table":
                    content_data["types"].append("table")
                    content_data["tables"].append(
                        getattr(el.metadata, "text_as_html", el.text)
                    )
                elif el_type == "Image" and hasattr(el.metadata, "image_base64"):
                    content_data["types"].append("image")
                    content_data["images"].append(el.metadata.image_base64)

        content_data["types"] = list(set(content_data["types"]))
        return content_data

    @staticmethod
    def has_complex_content(chunk) -> bool:
        """Check if a chunk contains tables or images."""
        if hasattr(chunk, "metadata") and hasattr(chunk.metadata, "orig_elements"):
            for element in chunk.metadata.orig_elements or []:
                element_type = type(element).__name__
                if element_type in {"Table", "Image"}:
                    return True
        return False
