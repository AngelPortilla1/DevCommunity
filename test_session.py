import datetime
import json
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.redis import redis_client
from app.services.session_service import SessionService

def main():
    service = SessionService(redis_client)
    user_id = 999
    device_id = "test-device-123"
    jti = "test-jti-456"
    ip = "127.0.0.1"
    user_agent = "TestAgent/1.0"
    expires_at = datetime.datetime.utcnow() + datetime.timedelta(minutes=10)

    try:
        print("Testing create_session...")
        session = service.create_session(
            user_id, device_id, jti, ip, user_agent, expires_at
        )
        print("create_session ok!", session)
    except Exception as e:
        print("Error en create_session:", e)

    try:
        print("Testing get_sessions...")
        sessions = service.get_sessions(user_id)
        print("get_sessions ok!", sessions)
    except Exception as e:
        print("Error en get_sessions:", e)

if __name__ == "__main__":
    main()
