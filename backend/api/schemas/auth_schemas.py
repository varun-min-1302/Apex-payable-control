from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr

class LoginRequest(BaseModel):
    email: EmailStr
    password: Optional[str] = "password"  # default password for demo users

class UserOut(BaseModel):
    id: UUID
    tenant_id: UUID
    email: str
    full_name: str
    status: str
    roles: list[str]

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut

class DemoUserOut(BaseModel):
    email: str
    full_name: str
    roles: list[str]
    description: str
