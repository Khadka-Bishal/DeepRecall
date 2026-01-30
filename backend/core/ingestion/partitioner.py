
import os
import fitz  # PyMuPDF
import base64
import requests
import logging
from time import perf_counter
from typing import List, Dict, Any, Tuple
from dotenv import load_dotenv

from ade import Ade

load_dotenv()
logger = logging.getLogger(__name__)

class LandingAIPage:
    """Represents a single parsed page with its visual representation."""
    def __init__(self, markdown: str, grounding: Any, image_base64: str, page_number: int):
        self.text = markdown
        self.metadata = type('obj', (object,), {
            'page_number': page_number,
            'grounding': grounding,
            'image_base64': image_base64, # The full page image
            'orig_elements': []
        })

class DocumentPartitioner:
    """Partitions documents using LandingAI Agentic Document Extraction (ADE)."""

    def __init__(self):
        self.api_key = os.getenv("LANDINGAI_API_KEY")
        self.client = Ade(apikey=self.api_key)

    def partition(
        self, file_path: str
    ) -> Tuple[List[Any], List[Dict[str, Any]], Dict[str, float]]:
        """Partition a document to LandingAIPage objects with images.

        Returns:
            Tuple of ([LandingAIPage], preview_data, timing_stats)
        """
        t0 = perf_counter()
        
        abs_path = os.path.abspath(file_path)
        if not os.path.exists(abs_path):
             raise ValueError(f"File not found: {abs_path}")
        
        size = os.path.getsize(abs_path)
        logger.info(f"Sending {os.path.basename(abs_path)} ({size} bytes) to LandingAI ADE...")
        
        # Ensure we are not sending an empty file
        if size == 0:
             raise ValueError("File is empty.")

        url = "https://api.va.landing.ai/v1/ade/parse"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        with open(abs_path, "rb") as f:
            files = {"document": (os.path.basename(abs_path), f, "application/pdf")}
            data = {"model": "dpt-2-latest"} # Or preferred model
            
            api_start = perf_counter()
            resp = requests.post(url, files=files, data=data, headers=headers)
            if resp.status_code != 200:
                logger.error(f"Error {resp.status_code}: {resp.text}")
                resp.raise_for_status()
            
            parse_result = resp.json()
            api_end = perf_counter()
            logger.debug(f"API Response keys: {list(parse_result.keys())}")
            if "data" in parse_result:
                logger.debug(f"Data length: {len(parse_result['data'])}")

        # Render pages to images
        logger.info(f"Rendering page images with PyMuPDF...")
        doc = fitz.open(abs_path)
        pages = []
        preview = []

        # LandingAI returns 'data' or 'splits' as a list of page/split results
        elements_data = parse_result.get("data") or parse_result.get("splits") or []
        
        # Capture top-level grounding (bounding boxes) - this is where bbox data lives
        top_level_grounding = parse_result.get("grounding", {})
        logger.debug(f"Found {len(top_level_grounding)} grounding entries with bounding boxes")
        
        # If both are missing but we have top-level markdown, wrap it
        if not elements_data and "markdown" in parse_result:
            elements_data = [{
                "markdown": parse_result.get("markdown"),
                "chunks": parse_result.get("chunks", []),
                "metadata": parse_result.get("metadata", {})
            }]
        
        logger.info(f"Found {len(elements_data)} elements/splits")
        
        for i, page_data in enumerate(elements_data):
            # Render page to image
            # Use 2.0 zoom for better resolution if needed, keeping default for speed/size now
            pix = doc.load_page(i).get_pixmap(matrix=fitz.Matrix(1.5, 1.5)) 
            img_data = pix.tobytes("png")
            img_base64 = base64.b64encode(img_data).decode("utf-8")
            
            # Create Page Object - use top-level grounding which contains bbox data
            page_obj = LandingAIPage(
                markdown=page_data.get("markdown") or page_data.get("content") or "",
                grounding=top_level_grounding,  # Pass full grounding dict with bounding boxes
                image_base64=img_base64,
                page_number=i + 1
            )
            pages.append(page_obj)

            preview.append(
                {
                    "type": "Page",
                    "text": f"Page {i+1} Content",
                    "page": i + 1,
                    "prob": 1.0,
                    "image": img_base64[:100] + "..." # Snippet for logs logic if needed
                }
            )
            
        doc.close()

        total_duration = perf_counter() - t0
        stats = {
            "preprocess_seconds": 0.0,
            "api_seconds": round(api_end - t0, 3),
            "total_seconds": round(total_duration, 3),
        }
        logger.info(f"Processed {len(pages)} pages in {total_duration:.1f}s")
        
        return pages, preview, stats
