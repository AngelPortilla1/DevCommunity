from datetime import datetime
from typing import Optional

# Importamos ConfigDict para la configuración nativa de Pydantic V2
from pydantic import BaseModel, EmailStr, Field, ConfigDict

# --- ESQUEMAS DE USUARIO ---

class UserCreate(BaseModel):
    """Esquema para la creación de un nuevo usuario."""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    # El límite de 72 bytes es una buena práctica para hashes bcrypt
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
    
    # CONFIGURACIÓN PYDANTIC V2
    # Usamos model_config en lugar de class Config para asegurar compatibilidad total
    model_config = ConfigDict(from_attributes=True)

# --- ESQUEMAS DE POST ---

class PostCreate(BaseModel):
    """Esquema para la creación de un nuevo post (datos de entrada)."""
    title: str
    content: str
    
class PostResponse(BaseModel):
    """
    Esquema para la respuesta de la API al devolver un post.
    """
    id: int
    title: str
    content: str
    author: UserResponse
    created_at: datetime
    likes_count: int
    liked_by_me: bool
    
    # Relación opcional: Evita errores 500 si SQLAlchemy no carga el autor inmediatamente
    author: Optional[UserResponse] = None 
    
    # CONFIGURACIÓN PYDANTIC V2
    model_config = ConfigDict(from_attributes=True)


# ------- User Public Schema -------

class UserPublicResponse(BaseModel):
    id: int
    username: str
    email: str

    model_config = ConfigDict(from_attributes=True)

    
    # ------- Comment Schemas -------

class CommentCreate(BaseModel):
    content: str

class CommentResponse(BaseModel):
    id: int
    content: str
    author: UserPublicResponse
    post_id: int
    created_at: datetime | None = None
    updated_at: datetime | None = None

    # CONFIGURACIÓN PYDANTIC V2
    model_config = ConfigDict(from_attributes=True)
        
        
        
class PaginatedPosts(BaseModel):
    page: int
    limit: int
    total: int
    data: list[PostResponse]

    # CONFIGURACIÓN PYDANTIC V2
    model_config = ConfigDict(from_attributes=True)
