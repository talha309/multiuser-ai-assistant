from pydantic import BaseModel,EmailStr

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