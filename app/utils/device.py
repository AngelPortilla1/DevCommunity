import hashlib
import re

def parse_user_agent(ua: str) -> dict:
    os_name = "Unknown OS"
    if "Windows" in ua: os_name = "Windows"
    elif "Mac OS X" in ua: os_name = "Mac OS"
    elif "Linux" in ua: os_name = "Linux"
    elif "Android" in ua: os_name = "Android"
    elif "iPhone" in ua or "iPad" in ua: os_name = "iOS"

    browser = "Unknown Browser"
    if "Chrome" in ua and "Edg" not in ua: browser = "Chrome"
    elif "Safari" in ua and "Chrome" not in ua: browser = "Safari"
    elif "Firefox" in ua: browser = "Firefox"
    elif "Edg" in ua: browser = "Edge"
    
    return {"os": os_name, "browser": browser}

def extract_ip(request) -> str:
    """
    Obtiene la IP real del cliente de forma segura contra IP Spoofing.

    X-Forwarded-For SOLO se acepta si la conexión directa proviene de un proxy
    o load-balancer cuya IP esté listada en settings.TRUSTED_PROXIES.
    De lo contrario, se usa siempre request.client.host (IP del socket TCP real),
    que el cliente jamás puede falsificar.

    Configura los proxies de confianza con la variable de entorno:
        TRUSTED_PROXIES="10.0.0.1,10.0.0.2"
    """
    from app.core.config import settings  # import local para evitar ciclos

    direct_ip: str = request.client.host if request.client else "127.0.0.1"

    if direct_ip in settings.TRUSTED_PROXIES:
        # El request viene de un proxy conocido → es seguro leer el header.
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # El header puede tener una cadena de IPs: "client, proxy1, proxy2".
            # La IP más a la izquierda es la del cliente original.
            return forwarded.split(",")[0].strip()

    # Sin proxy de confianza en la cadena → ignoramos el header por completo.
    return direct_ip

def extract_user_agent(request):
    return request.headers.get("User-Agent", "unknown")

def extract_device_id_frontend(request) -> str | None:
    return request.headers.get("X-Device-ID")

def generate_device_id(request) -> str:
    """
    Genera un ID único. 
    Acepta fingerprint del front si existe (X-Device-ID).
    Si no, une OS, navegador e IP para entropía mejorada.
    """
    front_id = extract_device_id_frontend(request)
    if front_id:
        return front_id

    ua = extract_user_agent(request)
    ip = extract_ip(request)
    parsed = parse_user_agent(ua)
    
    # Usamos OS, Navegador, IP y el UA completo para máxima entropía.
    # Esto evita colisiones entre distintos navegadores (Chrome/Firefox) en la misma máquina.
    raw = f"{parsed['os']}-{parsed['browser']}-{ip}-{ua}"
    return hashlib.sha256(raw.encode()).hexdigest()