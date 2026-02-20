from pydantic import BaseModel, EmailStr, Field, ConfigDict

class UserCreate(BaseModel):
    """Esquema para la creación de un nuevo usuario."""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=72)
    
class UserLogin(BaseModel):
    """Esquema para la autenticación de usuario."""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=72)
    
class UserResponse(BaseModel):
    """Esquema para la respuesta de la API al devolver datos de usuario."""
    id: int
    username: str
    email: EmailStr
    
    model_config = ConfigDict(from_attributes=True)

class UserPublicResponse(BaseModel):
    id: int
    username: str
    email: str

    model_config = ConfigDict(from_attributes=True)
