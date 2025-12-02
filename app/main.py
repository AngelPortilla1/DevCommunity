from fastapi import FastAPI
from app.api import routes_test
from app.auth import auth_routes
from app.core.database import Base, engine
from app.models import user, post, coments, like, follows
from app.routes import post_routes


app = FastAPI(title="DevCommunity API", version="0.1.0")

# Crear tablas en la base de datos
Base.metadata.create_all(bind=engine)

# Rutas
app.include_router(routes_test.router)
app.include_router(auth_routes.router)
app.include_router(post_routes.router)

@app.get("/")
def root():
    return {"message": "Welcome to DevCommunity API!"}
