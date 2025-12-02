from pydantic import BaseModel, EmailStr, Field

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=72)  # bcrypt tiene un límite de 72 bytes
    

class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=72)
    
    
class PostCreate(BaseModel):
    title: str
    content: str
    
class PostResponse(BaseModel):
    id: int
    title: str
    content: str
    author_id: int

    class Config:
        orm_mode = True
