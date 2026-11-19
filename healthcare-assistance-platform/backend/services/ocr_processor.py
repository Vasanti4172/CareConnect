
import os
from pathlib import Path

import fitz
import pytesseract

from PIL import Image, UnidentifiedImageError


# Use the default Windows installation path if available.
# Otherwise, pytesseract will look for tesseract in PATH.
DEFAULT_TESSERACT_PATH = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

if os.path.exists(DEFAULT_TESSERACT_PATH):
    pytesseract.pytesseract.tesseract_cmd = (
        DEFAULT_TESSERACT_PATH
    )


MAX_PDF_PAGES = 20
OCR_LANGUAGE = "eng"


def extract_text_using_ocr(file_path: str) -> dict:
    """
    Extract text from scanned PDFs and image documents.

    Supported formats:
    PDF, JPG, JPEG and PNG.

    OCR output must be reviewed before it is used
    for medical explanations.
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError("Document file not found.")

    extension = path.suffix.lower()

    extracted_pages = []

    try:

        # CASE 1: Scanned PDF
        if extension == ".pdf":

            with fitz.open(path) as pdf:

                if pdf.is_encrypted:
                    raise ValueError(
                        "Password-protected PDFs are not supported."
                    )

                total_pages = len(pdf)

                if total_pages == 0:
                    raise ValueError(
                        "The PDF contains no pages."
                    )

                if total_pages > MAX_PDF_PAGES:
                    raise ValueError(
                        f"OCR is limited to {MAX_PDF_PAGES} pages."
                    )

                for page_number, page in enumerate(
                    pdf,
                    start=1
                ):

                    # Convert PDF page into an image
                    pixmap = page.get_pixmap(
                        matrix=fitz.Matrix(2, 2),
                        alpha=False
                    )

                    image = Image.frombytes(
                        "RGB",
                        [pixmap.width, pixmap.height],
                        pixmap.samples
                    )

                    # Recognize English text
                    page_text = pytesseract.image_to_string(
                        image,
                        lang=OCR_LANGUAGE,
                        config="--psm 6"
                    ).strip()

                    extracted_pages.append({
                        "page_number": page_number,
                        "text": page_text
                    })

        # CASE 2: Image document
        elif extension in [".jpg", ".jpeg", ".png"]:

            with Image.open(path) as original_image:

                image = original_image.convert("RGB")

                page_text = pytesseract.image_to_string(
                    image,
                    lang=OCR_LANGUAGE,
                    config="--psm 6"
                ).strip()

                extracted_pages.append({
                    "page_number": 1,
                    "text": page_text
                })

            total_pages = 1

        else:
            raise ValueError(
                "OCR supports PDF, JPG, JPEG and PNG files only."
            )

    except fitz.FileDataError:
        raise ValueError("The PDF file is damaged or invalid.")

    except UnidentifiedImageError:
        raise ValueError("The image file is invalid or unreadable.")

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
        "has_extracted_text": bool(combined_text.strip())
    }
