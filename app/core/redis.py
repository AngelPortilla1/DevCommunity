import redis
from app.core.config import settings

# Create a single Redis client instance
redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
