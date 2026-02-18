import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME: str = "DevCommunity"
    PROJECT_VERSION: str = "0.1.0"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./devcommunity.db")
    # Clave secreta para firmar JWT — cámbiala en producción
    SECRET_KEY: str = os.getenv("SECRET_KEY", "mi_super_clave_ultra_secreta")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

settings = Settings()
