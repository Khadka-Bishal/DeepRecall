"""Document partitioning using Unstructured API."""

import os
from time import perf_counter
from typing import List, Dict, Any, Tuple
from dotenv import load_dotenv

from unstructured.documents.elements import (
    Text,
    Title,
    NarrativeText,
    Table,
    Image,
    ListItem,
    Header,
    Footer,
    FigureCaption,
    ElementMetadata,
)
from unstructured_client import UnstructuredClient
from unstructured_client.models import operations, shared

from .pdf_preprocessor import PDFPreprocessor

load_dotenv()


class DocumentPartitioner:
    """Partitions documents into structured elements using Unstructured API."""

    TYPE_MAP = {
        "Title": Title,
        "NarrativeText": NarrativeText,
        "Text": Text,
        "Table": Table,
        "Image": Image,
        "ListItem": ListItem,
        "Header": Header,
        "Footer": Footer,
        "FigureCaption": FigureCaption,
    }

    def __init__(self):
        self.preprocessor = PDFPreprocessor()
        self.client = UnstructuredClient(api_key_auth=os.getenv("UNSTRUCTURED_API_KEY"))

    def _convert_api_elements(self, api_elements) -> List[Any]:
        """Convert API response elements to Unstructured element objects."""
        elements = []

        for api_el in api_elements:
            el_type = api_el.get("type", "Text")
            el_text = api_el.get("text", "")
            el_metadata = api_el.get("metadata", {})

            # Get the appropriate element class
            ElementClass = self.TYPE_MAP.get(el_type, Text)

            # Create metadata object
            metadata = ElementMetadata(
                page_number=el_metadata.get("page_number", 1),
                text_as_html=el_metadata.get("text_as_html"),
            )

            # Handle image base64 if present
            if "image_base64" in el_metadata:
                metadata.image_base64 = el_metadata["image_base64"]

            # Create element
            element = ElementClass(text=el_text, metadata=metadata)
            elements.append(element)

        return elements

    def partition(
        self, file_path: str
    ) -> Tuple[List[Any], List[Dict[str, Any]], Dict[str, float]]:
        """Partition a document into structured elements.

        Returns:
            Tuple of (elements, preview_data, timing_stats)
        """
        t0 = perf_counter()

        preprocessed_path = self.preprocessor.preprocess(file_path)
        cleanup_required = preprocessed_path != file_path
        preprocess_duration = perf_counter() - t0

        api_start = perf_counter()
        api_end = api_start

        try:
            with open(preprocessed_path, "rb") as f:
                file_content = f.read()

            req = operations.PartitionRequest(
                partition_parameters=shared.PartitionParameters(
                    files=shared.Files(
                        content=file_content,
                        file_name=os.path.basename(file_path),
                    ),
                    strategy=shared.Strategy.HI_RES,
                    extract_image_block_types=["Image", "Table"],
                ),
            )

            res = self.client.general.partition(request=req)
            api_elements = res.elements
            api_end = perf_counter()
        finally:
            if cleanup_required and os.path.exists(preprocessed_path):
                try:
                    os.remove(preprocessed_path)
                except OSError:
                    pass

        elements = self._convert_api_elements(api_elements)

        # Build preview data
        preview = []
        for el in elements:
            el_type = str(type(el).__name__)
            prob = getattr(el.metadata, "detection_class_prob", 0.95)
            text = str(el) if el_type != "Image" else "[Image]"

            preview.append(
                {
                    "type": el_type,
                    "text": text,
                    "page": (
                        el.metadata.page_number
                        if hasattr(el.metadata, "page_number")
                        else 1
                    ),
                    "prob": prob,
                }
            )

        total_duration = perf_counter() - t0
        stats = {
            "preprocess_seconds": round(preprocess_duration, 3),
            "api_seconds": round(api_end - api_start, 3),
            "total_seconds": round(total_duration, 3),
        }
        print(f"[partition] {len(elements)} elements in {total_duration:.1f}s")
        return elements, preview, stats
