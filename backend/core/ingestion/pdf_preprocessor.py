"""PDF preprocessing utilities."""

import tempfile
import uuid
from pathlib import Path
from pypdf import PdfReader, PdfWriter
import pikepdf


class PDFPreprocessor:
    """Handles PDF normalization and compression."""

    @staticmethod
    def preprocess(file_path: str) -> str:
        """Normalize PDF rotation and compress.

        Returns the path to the preprocessed file (may be same as input if no changes needed).
        """
        temp_path = Path(tempfile.gettempdir()) / f"normalized_{uuid.uuid4().hex}.pdf"

        try:
            reader = PdfReader(file_path)
            writer = PdfWriter()

            for page in reader.pages:
                rotation = page.get("/Rotate", 0) or 0
                if rotation:
                    page.rotate(-rotation)
                writer.add_page(page)

            writer.add_metadata({})
            with open(temp_path, "wb") as buffer:
                try:
                    writer.write(buffer, compress_streams=True)
                except TypeError:
                    writer.write(buffer)
        except Exception:
            return file_path

        try:
            with pikepdf.open(temp_path, allow_overwriting_input=True) as pdf:
                pdf.remove_unreferenced_resources()
                pdf.save(
                    temp_path,
                    linearize=True,
                    compress_streams=True,
                    object_stream_mode=pikepdf.ObjectStreamMode.generate,
                )
        except Exception:
            pass

        return str(temp_path)
