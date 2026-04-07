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

def extract_ip(request):
    """
    Obtiene IP real considerando proxies.
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"

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