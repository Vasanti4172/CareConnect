
from sqlalchemy import Column, Text,Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    phone = Column(String(15), nullable=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(30), nullable=False)
    preferred_language = Column(String(30), default="English")
    created_at = Column(DateTime(timezone=True), server_default=func.now())



class MedicalDocument(Base):
    __tablename__ = "medical_documents"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    document_name = Column(
        String(255),
        nullable=False
    )

    document_type = Column(
        String(100),
        nullable=False
    )

    file_path = Column(
        String(500),
        nullable=False
    )

    uploaded_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

class DocumentExtraction(Base):
    __tablename__ = "document_extractions"

    id = Column(Integer, primary_key=True, index=True)

    document_id = Column(
        Integer,
        ForeignKey("medical_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    extraction_method = Column(String(30), nullable=False)

    raw_text = Column(Text, nullable=True)

    cleaned_text = Column(Text, nullable=True)

    entities_json = Column(Text, nullable=True)

    extraction_status = Column(String(50), nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )
