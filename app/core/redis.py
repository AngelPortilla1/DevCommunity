from redis import Redis
from app.core.config import settings

# Single Redis client instance shared across the application
redis_client = Redis.from_url(settings.REDIS_URL, decode_responses=True)
