
from fastapi import (
    FastAPI,
    Depends,
    HTTPException,
    UploadFile,
    File,
    Form
)
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import engine, Base, get_db
from models import User, MedicalDocument,DocumentExtraction
from schemas import (
    UserRegister,
    UserLogin,
    UserResponse,
    LoginResponse,
    UserUpdate,
    DocumentResponse,
    PDFExtractionResponse,
    OCRExtractionResponse,
    DocumentProcessingResponse
)
from security import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user
)

from services.pdf_processor import extract_text_from_pdf
from services.ocr_processor import extract_text_using_ocr
from services.document_processor import process_medical_document
import os
import uuid
import json
from pathlib import Path
import pytesseract
import traceback

# Create database tables
Base.metadata.create_all(bind=engine)
# Secure local storage for uploaded medical documents
UPLOAD_DIR = Path(__file__).resolve().parent / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".jpg",
    ".jpeg",
    ".png"
}

app = FastAPI(
    title="AI-Driven Healthcare Assistance Platform",
    description="A multilingual healthcare assistance platform for rural communities.",
    version="2.0.0"
)


# Allow the local frontend to communicate with this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {
        "message": "Healthcare Assistance Platform API is running",
        "status": "success"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "application": "Healthcare Assistance Platform"
    }


# Patient and healthcare worker registration
@app.post("/auth/register", response_model=UserResponse)
def register_user(user_data: UserRegister, db: Session = Depends(get_db)):

    email = user_data.email.strip().lower()

    if user_data.role not in ["Patient", "Healthcare Worker"]:
        raise HTTPException(
            status_code=400,
            detail="Role must be Patient or Healthcare Worker"
        )

    if user_data.preferred_language not in ["English", "Telugu"]:
        raise HTTPException(
            status_code=400,
            detail="Currently supported languages are English and Telugu"
        )

    existing_user = db.query(User).filter(User.email == email).first()

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="An account with this email already exists"
        )

    new_user = User(
        full_name=user_data.full_name.strip(),
        email=email,
        phone=user_data.phone,
        password_hash=hash_password(user_data.password),
        role=user_data.role,
        preferred_language=user_data.preferred_language
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


# User login
@app.post("/auth/login", response_model=LoginResponse)
def login_user(login_data: UserLogin, db: Session = Depends(get_db)):

    email = login_data.email.strip().lower()

    user = db.query(User).filter(User.email == email).first()

    if not user or not verify_password(
        login_data.password,
        user.password_hash
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    token = create_access_token(user.id)

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user
    }


# View a user profile by ID

# Get the profile of the currently logged-in user
@app.get("/users/me", response_model=UserResponse)
def get_my_profile(
    current_user: User = Depends(get_current_user)
):
    return current_user


# Update the currently logged-in user's profile
@app.patch("/users/me", response_model=UserResponse)
def update_my_profile(
    update_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    update_fields = update_data.model_dump(
        exclude_unset=True
    )

    if "full_name" in update_fields:
        if update_fields["full_name"] is not None:
            cleaned_name = update_fields["full_name"].strip()

            if len(cleaned_name) < 2:
                raise HTTPException(
                    status_code=400,
                    detail="Name must contain at least 2 characters"
                )

            current_user.full_name = cleaned_name

    if "phone" in update_fields:
        current_user.phone = update_fields["phone"]

    if "preferred_language" in update_fields:
        if update_fields["preferred_language"] is not None:
            current_user.preferred_language = (
                update_fields["preferred_language"]
            )

    db.commit()
    db.refresh(current_user)

    return current_user

# Upload a medical document
@app.post("/documents/upload", response_model=DocumentResponse)
async def upload_document(
    document_type: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    # Validate document category
    allowed_categories = [
        "Prescription",
        "Discharge Summary",
        "Medical Report",
        "Other"
    ]

    if document_type not in allowed_categories:
        raise HTTPException(
            status_code=400,
            detail="Invalid document category"
        )

    # Validate original filename and extension
    original_name = Path(file.filename or "").name

    if not original_name:
        raise HTTPException(
            status_code=400,
            detail="Please select a file"
        )

    extension = Path(original_name).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Only PDF, JPG, JPEG and PNG files are allowed"
        )

    # Read no more than 5 MB plus one byte
    file_content = await file.read(MAX_FILE_SIZE + 1)

    if not file_content:
        raise HTTPException(
            status_code=400,
            detail="The selected file is empty"
        )

    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="File size must not exceed 5 MB"
        )

    # Check file signature instead of trusting the extension alone
    valid_file = False

    if extension == ".pdf":
        valid_file = file_content.startswith(b"%PDF-")

    elif extension in [".jpg", ".jpeg"]:
        valid_file = file_content.startswith(b"\xff\xd8\xff")

    elif extension == ".png":
        valid_file = file_content.startswith(
            b"\x89PNG\r\n\x1a\n"
        )

    if not valid_file:
        raise HTTPException(
            status_code=400,
            detail="File content does not match its extension"
        )

    # Generate a unique filename to avoid collisions
    stored_filename = f"{uuid.uuid4().hex}{extension}"
    stored_path = UPLOAD_DIR / stored_filename

    try:
        with open(stored_path, "wb") as destination:
            destination.write(file_content)

        new_document = MedicalDocument(
            user_id=current_user.id,
            document_name=original_name,
            document_type=document_type,
            file_path=stored_filename
        )

        db.add(new_document)
        db.commit()
        db.refresh(new_document)

        return new_document

    except Exception:
        db.rollback()

        if stored_path.exists():
            stored_path.unlink()

        raise HTTPException(
            status_code=500,
            detail="Unable to save the document"
        )

    finally:
        await file.close()


# Get documents belonging only to the logged-in user
@app.get("/documents", response_model=list[DocumentResponse])
def get_my_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    documents = db.query(MedicalDocument).filter(
        MedicalDocument.user_id == current_user.id
    ).order_by(
        MedicalDocument.uploaded_at.desc()
    ).all()

    return documents


# Delete a document belonging to the logged-in user
@app.delete("/documents/{document_id}")
def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    document = db.query(MedicalDocument).filter(
        MedicalDocument.id == document_id,
        MedicalDocument.user_id == current_user.id
    ).first()

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    stored_filename = Path(document.file_path).name
    stored_path = UPLOAD_DIR / stored_filename

    try:
        if stored_path.exists():
            stored_path.unlink()

        db.delete(document)
        db.commit()

        return {
            "message": "Document deleted successfully"
        }

    except Exception:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Unable to delete the document"
        )

# Extract readable text from a patient's uploaded PDF
@app.post(
    "/documents/{document_id}/extract-text",
    response_model=PDFExtractionResponse
)
def extract_document_text(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    # Find only a document owned by the logged-in user
    document = db.query(MedicalDocument).filter(
        MedicalDocument.id == document_id,
        MedicalDocument.user_id == current_user.id
    ).first()

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    # This extraction endpoint currently supports PDF files only
    if Path(document.file_path).suffix.lower() != ".pdf":
        raise HTTPException(
            status_code=400,
            detail="Text extraction currently supports PDF files only"
        )

    # Resolve the stored filename inside the uploads directory
    stored_filename = Path(document.file_path).name
    stored_path = UPLOAD_DIR / stored_filename

    try:

        result = extract_text_from_pdf(str(stored_path))

        if not result["has_extractable_text"]:

            return {
                "document_id": document.id,
                "document_name": document.document_name,
                "total_pages": result["total_pages"],
                "extracted_text": "",
                "character_count": 0,
                "extraction_status": "ocr_required",
                "message": (
                    "No selectable text found. "
                    "OCR processing will be required."
                )
            }

        return {
            "document_id": document.id,
            "document_name": document.document_name,
            "total_pages": result["total_pages"],
            "extracted_text": result["extracted_text"],
            "character_count": result["character_count"],
            "extraction_status": "success",
            "message": "PDF text extracted successfully."
        }

    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Stored PDF file not found"
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to process this PDF document"
        )

# Extract text from scanned PDFs and medical images using OCR
@app.post(
    "/documents/{document_id}/extract-ocr",
    response_model=OCRExtractionResponse
)
def extract_document_using_ocr(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    # Verify that the document belongs to the logged-in user
    document = db.query(MedicalDocument).filter(
        MedicalDocument.id == document_id,
        MedicalDocument.user_id == current_user.id
    ).first()

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    # Get the stored filename safely
    stored_filename = Path(document.file_path).name
    stored_path = UPLOAD_DIR / stored_filename

    try:

        result = extract_text_using_ocr(
            str(stored_path)
        )

        if not result["has_extracted_text"]:

            return {
                "document_id": document.id,
                "document_name": document.document_name,
                "total_pages": result["total_pages"],
                "extracted_text": "",
                "character_count": 0,
                "extraction_status": "no_text_detected",
                "message": (
                    "OCR could not recognize readable text. "
                    "Please upload a clearer document."
                )
            }

        return {
            "document_id": document.id,
            "document_name": document.document_name,
            "total_pages": result["total_pages"],
            "extracted_text": result["extracted_text"],
            "character_count": result["character_count"],
            "extraction_status": "success",
            "message": (
                "OCR text extraction completed. "
                "Please verify the extracted content."
            )
        }

    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Stored document file not found"
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception as error:

        if isinstance(
            error,
            pytesseract.TesseractNotFoundError
        ):
            raise HTTPException(
                status_code=500,
                detail=(
                    "Tesseract OCR is not installed "
                    "or its executable path is incorrect."
                )
            )

        raise HTTPException(
            status_code=500,
            detail="Unable to process the document using OCR"
        )

@app.post(
    "/documents/{document_id}/process",
    response_model=DocumentProcessingResponse
)
def process_uploaded_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Step 1: Verify document ownership.
    document = db.query(MedicalDocument).filter(
        MedicalDocument.id == document_id,
        MedicalDocument.user_id == current_user.id
    ).first()

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found."
        )

    # Step 2: Resolve the stored file safely.
    stored_filename = Path(document.file_path).name
    stored_path = UPLOAD_DIR / stored_filename

    try:
        # Step 3: Run extraction, cleaning and entity extraction.
        result = process_medical_document(str(stored_path))

        # Step 4: Store the processing result.
        extraction_record = DocumentExtraction(
            document_id=document.id,
            extraction_method=result["extraction_method"],
            raw_text=result["raw_text"],
            cleaned_text=result["cleaned_text"],
            entities_json=json.dumps(
                result["entities"],
                ensure_ascii=False
            ),
            extraction_status=result["extraction_status"]
        )

        db.add(extraction_record)
        db.commit()
        db.refresh(extraction_record)

        # Step 5: Return the saved result.
        return {
            "extraction_id": extraction_record.id,
            "document_id": document.id,
            "document_name": document.document_name,
            "extraction_method": result["extraction_method"],
            "raw_text": result["raw_text"],
            "cleaned_text": result["cleaned_text"],
            "entities": result["entities"],
            "extraction_status": result["extraction_status"],
            "requires_human_verification": True,
            "message": (
                "Document processing completed. "
                "Verify all extracted medical information."
            )
        }

    except FileNotFoundError:
        db.rollback()
        raise HTTPException(
            status_code=404,
            detail="Stored document file not found."
        )

    except ValueError as error:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception as error:
        db.rollback()

        print("\n========== DOCUMENT PROCESSING ERROR ==========")
        traceback.print_exc()
        print("ERROR MESSAGE:", str(error))
        print("================================================\n")

        raise HTTPException(
            status_code=500,
            detail="Unable to process the uploaded document."
    )
@app.get("/documents/{document_id}/extractions")
def get_document_extractions(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify the document belongs to the logged-in user.
    document = db.query(MedicalDocument).filter(
        MedicalDocument.id == document_id,
        MedicalDocument.user_id == current_user.id
    ).first()

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found."
        )

    records = db.query(DocumentExtraction).filter(
        DocumentExtraction.document_id == document.id
    ).order_by(
        DocumentExtraction.created_at.desc()
    ).all()

    return [
        {
            "extraction_id": record.id,
            "document_id": record.document_id,
            "extraction_method": record.extraction_method,
            "raw_text": record.raw_text,
            "cleaned_text": record.cleaned_text,
            "entities": json.loads(record.entities_json or "{}"),
            "extraction_status": record.extraction_status,
            "created_at": record.created_at
        }
        for record in records
    ]
