from typing import Optional
from datetime import datetime
import json


class SessionService:

    def __init__(self, redis_client):
        self.redis = redis_client

    # -----------------------------
    # Helper para generar las keys
    # -----------------------------
    def _session_key(self, user_id: int, device_id: str) -> str:
        return f"session:{user_id}:{device_id}"

    def _jti_key(self, jti: str) -> str:
        return f"refresh_jti:{jti}"

    # -----------------------------
    # 1. Crear Sesión
    # -----------------------------
    def create_session(
        self,
        user_id: int,
        device_id: str,
        jti: str,
        ip: str,
        user_agent: str,
        expires_at: datetime
    ):
        key = self._session_key(user_id, device_id)

        session_data = {
            "session_id": f"{user_id}:{device_id}",
            "user_id": user_id,
            "device_id": device_id,
            "jti": jti,
            "ip": ip,
            "user_agent": user_agent,
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": expires_at.isoformat(),
        }

        # Guardamos sesión como JSON
        self.redis.set(
            key,
            json.dumps(session_data),
            ex=int((expires_at - datetime.utcnow()).total_seconds())
        )

        # También guardamos jti -> device_id
        self.redis.set(
            self._jti_key(jti),
            device_id,
            ex=int((expires_at - datetime.utcnow()).total_seconds())
        )

        return session_data

    # -----------------------------
    # 2. Obtener todas las sesiones de un usuario
    # -----------------------------
    def get_sessions(self, user_id: int):
        pattern = f"session:{user_id}:*"
        keys = self.redis.keys(pattern)

        sessions = []

        for key in keys:
            raw = self.redis.get(key)
            if raw:
                sessions.append(json.loads(raw))

        return sessions

    # -----------------------------
    # 3. Eliminar una sesión
    # -----------------------------
    def delete_session(self, user_id: int, device_id: str):
        key = self._session_key(user_id, device_id)

        raw = self.redis.get(key)
        if not raw:
            return False

        session = json.loads(raw)
        jti = session.get("jti")

        # Borrar sesión y refresh token asociado
        self.redis.delete(key)
        if jti:
            self.redis.delete(self._jti_key(jti))

        return True

    # -----------------------------
    # 4. Eliminar todas las sesiones excepto la actual
    # -----------------------------
    def delete_all_except(self, user_id: int, keep_device_id: str):
        pattern = f"session:{user_id}:*"
        keys = self.redis.keys(pattern)

        deleted = []

        for key in keys:
            # En redis sincronizado, si no usa decode_responses, las llaves podrian ser bytes
            k_str = key if isinstance(key, str) else key.decode()
            
            if k_str.endswith(f":{keep_device_id}"):
                continue

            raw = self.redis.get(key)
            if raw:
                session = json.loads(raw)
                jti = session.get("jti")

                self.redis.delete(key)
                if jti:
                    self.redis.delete(self._jti_key(jti))

                deleted.append(session["device_id"])

        return deleted

    # -----------------------------
    # 5. Actualizar JTI (token rotation)
    # -----------------------------
    def update_jti_for_session(
        self,
        user_id: int,
        device_id: str,
        old_jti: str,
        new_jti: str,
        new_expires_at: datetime
    ):
        key = self._session_key(user_id, device_id)

        raw = self.redis.get(key)
        if not raw:
            return False

        session = json.loads(raw)
        session["jti"] = new_jti
        session["expires_at"] = new_expires_at.isoformat()

        # Guardamos nuevamente con TTL actualizado
        self.redis.set(
            key,
            json.dumps(session),
            ex=int((new_expires_at - datetime.utcnow()).total_seconds())
        )

        # Borrar JTI viejo
        self.redis.delete(self._jti_key(old_jti))

        # Guardar JTI nuevo
        self.redis.set(
            self._jti_key(new_jti),
            device_id,
            ex=int((new_expires_at - datetime.utcnow()).total_seconds())
        )

        return True