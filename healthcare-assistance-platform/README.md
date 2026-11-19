
# AI-Driven Healthcare Assistance Platform

## Project Overview

An AI-driven healthcare assistance platform designed to improve access to medical information for rural communities through multilingual medical communication support.

## Week 1 – Frontend Development

- Patient login and registration interface.
- Patient dashboard.
- Medical document upload interface.
- Basic language selection interface.

## Week 2 – Patient and Healthcare Information Management

- Patient registration and authentication.
- Password hashing and JWT authentication.
- User profile management.
- Medical document upload and listing.
- Document ownership validation.
- PostgreSQL database integration.

## Week 3 – Medical Document Processing

### Implemented Features

- Digital PDF text extraction using PyMuPDF.
- OCR extraction using Tesseract OCR.
- Image document processing using Pillow.
- Text cleaning and preprocessing.
- Rule-based medical entity extraction.
- Storage of raw and processed text in PostgreSQL.
- Extraction history retrieval.
- Authenticated document processing APIs.

### Processing Workflow

1. Patient uploads a medical document.
2. System identifies the document format.
3. Digital PDF extraction or OCR is performed.
4. Original extracted text is preserved.
5. Text preprocessing is performed.
6. Clearly labelled medical information is identified.
7. Results are stored in PostgreSQL.
8. Authorized users can retrieve processing history.

## Technology Stack

- Python 3.12
- FastAPI
- PostgreSQL
- SQLAlchemy
- PyMuPDF
- Tesseract OCR
- Pytesseract
- Pillow
- HTML
- CSS
- JavaScript

## Current Limitations

- OCR currently supports English language data.
- Medical entity extraction uses basic rule-based patterns.
- Extracted medical information requires human verification.
- The current system does not provide medical diagnosis.
- Production deployment requires additional privacy and security controls.

## Running the Backend

Activate the virtual environment:

```powershell
.\venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Start the backend:

```powershell
uvicorn main:app --reload
```

Open API documentation:

http://127.0.0.1:8000/docs

## External Software Requirement

Tesseract OCR must be installed separately on the machine running the backend.

Official installation information:

https://github.com/UB-Mannheim/tesseract/wiki
