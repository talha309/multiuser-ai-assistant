from pydantic import BaseModel, EmailStr
from typing import List

# --------- Auth Schemas ---------

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    class Config:
        orm_mode = True

class UpdatePassword(BaseModel):
    email: EmailStr
    new_password: str

# --------- Thread + Message ---------

class MessageBase(BaseModel):
    role: str
    content: str

class MessageCreate(BaseModel):
    content: str  # only user sends content

class MessageResponse(MessageBase):
    id: int
    class Config:
        orm_mode = True

class ThreadResponse(BaseModel):
    id: int
    title: str
    messages: List[MessageResponse] = []
    class Config:
        orm_mode = True
