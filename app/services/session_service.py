from typing import Optional
from datetime import datetime


class SessionService:

    def __init__(self, redis_client):
        self.redis = redis_client

    async def create_session(
        self,
        user_id: int,
        device_id: str,
        jti: str,
        ip: str,
        user_agent: str,
        expires_at: datetime
    ):
        """
        Crear una nueva sesión en Redis.
        """
        pass

    async def get_sessions(self, user_id: int):
        """
        Listar sesiones activas del usuario.
        """
        pass

    async def delete_session(self, user_id: int, device_id: str):
        """
        Eliminar una sesión especifica.
        """
        pass

    async def delete_all_except(self, user_id: int, keep_device_id: str):
        """
        Eliminar todas las sesiones menos la actual.
        """
        pass

    async def update_jti_for_session(
        self,
        user_id: int,
        device_id: str,
        old_jti: str,
        new_jti: str
    ):
        """
        Rotar JTI durante refresh.
        """
        pass