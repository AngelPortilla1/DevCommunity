
import hashlib


def generate_device_id(user_agent: str, ip: str) -> str:
    """
    Genera un ID único basado en user-agent + IP.
    Actúa como un fingerprint simple.
    """
    raw = f"{user_agent}-{ip}"
    return hashlib.sha256(raw.encode()).hexdigest()


def extract_ip(request):
    """
    Obtiene IP real considerando proxies.
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0]
    return request.client.host


def extract_user_agent(request):
    return request.headers.get("User-Agent", "unknown")