from app.exceptions.post_exceptions import ForbiddenAction, PostNotFound
from fastapi import FastAPI, Request
from app.api import routes_test
from app.auth import auth_routes
from app.core.database import Base, engine
from app.models import user, post, coments, like, follows
from app.routers import post_router, comment_router, like_router, follower_router
from app.exceptions.base import AppException
from app.core.exceptions_handlers import app_exception_handler
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="DevCommunity API", version="0.1.0")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://localhost:4201"],  # Puertos del frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(PostNotFound)
async def post_not_found_handler(request: Request, exc: PostNotFound):
    return JSONResponse(
        status_code=404,
        content={"detail": exc.message},
    )

@app.exception_handler(ForbiddenAction)
async def forbidden_action_handler(request: Request, exc: ForbiddenAction):
    return JSONResponse(
        status_code=403,
        content={"detail": exc.message},
    )

# Crear tablas en la base de datos
Base.metadata.create_all(bind=engine)

app.add_exception_handler(AppException, app_exception_handler)

# Rutas
app.include_router(routes_test.router)
app.include_router(auth_routes.router)
app.include_router(post_router.router)
app.include_router(comment_router.router)
app.include_router(like_router.router)
app.include_router(follower_router.router)

@app.get("/")
def root():
    return {"message": "Welcome to DevCommunity API!"}
