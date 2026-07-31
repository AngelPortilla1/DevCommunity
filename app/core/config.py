import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME: str = "DevCommunity"
    PROJECT_VERSION: str = "0.1.0"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./devcommunity.db")
    # Clave secreta para firmar JWT.
    # OBLIGATORIA: debe definirse en el .env. Si falta, la app falla de forma visible y segura.
    SECRET_KEY: str = os.environ["SECRET_KEY"]
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    # IPs de proxies/load-balancers de confianza (separadas por coma en la env var).
    # Solo estas IPs pueden propagar X-Forwarded-For de forma válida.
    # Ejemplo: TRUSTED_PROXIES="10.0.0.1,10.0.0.2"
    TRUSTED_PROXIES: frozenset = frozenset(
        ip.strip()
        for ip in os.getenv("TRUSTED_PROXIES", "").split(",")
        if ip.strip()
    )

settings = Settings()
