import redis
from app.core.config import settings
from redis import Redis 
# Create a single Redis client instance
redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)



redis_client = Redis.from_url(
    settings.REDIS_URL,
    decode_responses=True
)
