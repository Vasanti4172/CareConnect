
from pathlib import Path

from services.pdf_processor import extract_text_from_pdf
from services.ocr_processor import extract_text_using_ocr
from services.text_preprocessor import clean_extracted_text
from services.medical_entity_extractor import extract_medical_entities


def process_medical_document(file_path: str) -> dict:
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError("Document file not found.")

    extension = path.suffix.lower()

    # Step 1: Extract raw text.
    if extension == ".pdf":
        pdf_result = extract_text_from_pdf(str(path))

        if pdf_result["has_extractable_text"]:
            raw_text = pdf_result["extracted_text"]
            extraction_method = "digital_pdf"
        else:
            ocr_result = extract_text_using_ocr(str(path))
            raw_text = ocr_result["extracted_text"]
            extraction_method = "ocr"

    elif extension in [".jpg", ".jpeg", ".png"]:
        ocr_result = extract_text_using_ocr(str(path))
        raw_text = ocr_result["extracted_text"]
        extraction_method = "ocr"

    else:
        raise ValueError("Unsupported document format.")

    # Step 2: Clean text without modifying the raw version.
    preprocessing_result = clean_extracted_text(raw_text)
    cleaned_text = preprocessing_result["cleaned_text"]

    # Step 3: Identify clearly labelled medical information.
    entity_result = extract_medical_entities(cleaned_text)

    # Step 4: Return the complete processing result.
    return {
        "raw_text": raw_text,
        "cleaned_text": cleaned_text,
        "entities": entity_result["entities"],
        "extraction_method": extraction_method,
        "extraction_status": (
            "success" if cleaned_text else "no_text_detected"
        ),
        "requires_human_verification": True
    }
