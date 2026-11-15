from pydantic import BaseModel, ConfigDict, Field
from typing import Literal
from datetime import datetime
class UserRegister(BaseModel):
    full_name: str = Field(min_length=2, max_length=100)
    email: str = Field(min_length=5, max_length=150)
    phone: str | None = Field(default=None, max_length=15)
    password: str = Field(min_length=6)
    role: str
    preferred_language: str = "English"


class UserLogin(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: int
    full_name: str
    email: str
    phone: str | None
    role: str
    preferred_language: str

    model_config = ConfigDict(from_attributes=True)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


class UserUpdate(BaseModel):
    full_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=100
    )

    phone: str | None = Field(
        default=None,
        max_length=15
    )

    preferred_language: Literal["English", "Telugu"] | None = None


class DocumentResponse(BaseModel):
    id: int
    document_name: str
    document_type: str
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)
