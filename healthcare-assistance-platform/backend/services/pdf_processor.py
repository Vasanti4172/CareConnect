
import fitz
from pathlib import Path


MAX_PDF_PAGES = 50


def extract_text_from_pdf(file_path: str) -> dict:
    """
    Extract selectable text from a digital PDF.

    This function does not perform OCR.
    Scanned image-only PDFs will be handled in Step 3.3.
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError("PDF file not found.")

    if path.suffix.lower() != ".pdf":
        raise ValueError("Only PDF documents are supported.")

    extracted_pages = []

    try:
        with fitz.open(path) as pdf:

            if pdf.is_encrypted:
                raise ValueError(
                    "Password-protected PDFs are not supported."
                )

            total_pages = len(pdf)

            if total_pages == 0:
                raise ValueError("The PDF contains no pages.")

            if total_pages > MAX_PDF_PAGES:
                raise ValueError(
                    f"PDF exceeds the {MAX_PDF_PAGES}-page limit."
                )

            for page_number, page in enumerate(pdf, start=1):

                page_text = page.get_text("text").strip()

                extracted_pages.append({
                    "page_number": page_number,
                    "text": page_text
                })

    except fitz.FileDataError:
        raise ValueError("The PDF file is damaged or invalid.")

    combined_text = "\n\n".join(
        page["text"]
        for page in extracted_pages
        if page["text"]
    )

    return {
        "total_pages": total_pages,
        "pages": extracted_pages,
        "extracted_text": combined_text,
        "character_count": len(combined_text),
        "has_extractable_text": bool(combined_text.strip())
    }
