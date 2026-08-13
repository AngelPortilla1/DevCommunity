from fastapi import FastAPI
from app.auth import auth_routes
from app.db.base import Base
from app.db.session import engine
from app.models import user, post, comment, like, follows
from app.routers import post_router, comment_router, like_router, follower_router, admin_routes, notification_router
from app.exceptions.base import AppException
from app.core.exceptions_handlers import app_exception_handler
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="DevCommunity API", version="0.1.0")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://localhost:4201", "http://localhost:52924", "http://127.0.0.1:52924"],  # Puertos del frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Crear tablas en la base de datos
Base.metadata.create_all(bind=engine)

# Handler genérico para todas las AppException y sus subclases (PostNotFound, ForbiddenAction, etc.)
app.add_exception_handler(AppException, app_exception_handler)

# Rutas
app.include_router(auth_routes.router)
app.include_router(post_router.router)
app.include_router(comment_router.router)
app.include_router(like_router.router)
app.include_router(follower_router.router)
app.include_router(admin_routes.router)
app.include_router(notification_router.router)

@app.get("/")
def root():
    return {"message": "Welcome to DevCommunity API!"}
