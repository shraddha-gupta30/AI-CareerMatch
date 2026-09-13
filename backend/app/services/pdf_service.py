"""
PDF Text Extraction Service using pure Python pypdf.
"""
from pathlib import Path
from typing import Union
import re
from pypdf import PdfReader
from app.core.exceptions import AppException
from app.core.logging import logger


def extract_text_from_pdf(file_path: Union[Path, str]) -> str:
    """
    Extracts all readable text from a PDF resume.
    
    Raises AppException if the file cannot be parsed or if the PDF
    is image-only/scanned without an extractable text layer.
    """
    path = Path(file_path)
    if not path.exists():
        raise AppException(
            message=f"Resume file not found at: {path.name}",
            status_code=404,
            code="FILE_NOT_FOUND",
        )

    try:
        reader = PdfReader(str(path))
        if len(reader.pages) == 0:
            raise AppException(
                message="Uploaded PDF document contains zero pages.",
                status_code=422,
                code="EMPTY_PDF",
            )

        extracted_parts = []
        for idx, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            if page_text.strip():
                extracted_parts.append(page_text.strip())

        full_text = "\n\n".join(extracted_parts).strip()

        # Check for meaningful text (scanned image detection)
        # We check alphanumeric characters count
        alphanumeric_count = len(re.findall(r"[a-zA-Z0-9]", full_text))
        if alphanumeric_count < 50:
            logger.warning(
                f"PDF text extraction yielded only {alphanumeric_count} alphanumeric chars for {path.name}."
            )
            raise AppException(
                message=(
                    "Scanned or image-only PDF detected. AI CareerMatch requires a text-based PDF resume. "
                    "Please upload a document with selectable text."
                ),
                status_code=422,
                code="SCANNED_PDF_UNSUPPORTED",
            )

        logger.info(
            f"Successfully extracted {len(full_text)} chars ({alphanumeric_count} alphanumeric) from {path.name} across {len(reader.pages)} page(s)."
        )
        return full_text

    except AppException:
        raise
    except Exception as exc:
        logger.error(f"Failed to extract text from PDF {path.name}: {exc}")
        raise AppException(
            message=f"Failed to extract text from the uploaded PDF document: {str(exc)}",
            status_code=422,
            code="PDF_PARSING_ERROR",
        )
