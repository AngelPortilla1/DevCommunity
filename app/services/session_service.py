from typing import Optional
from datetime import datetime
import json
from fastapi import HTTPException, status


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
        now = datetime.utcnow().isoformat()

        session_data = {
            "session_id": f"{user_id}:{device_id}",
            "user_id": user_id,
            "device_id": device_id,
            "jti": jti,
            "initial_ip": ip,
            "initial_user_agent": user_agent,
            "last_ip": ip,
            "last_user_agent": user_agent,
            "last_access": now,
            "refresh_count": 0,
            "created_at": now,
            "expires_at": expires_at.isoformat(),
        }

        ttl = int((expires_at - datetime.utcnow()).total_seconds())
        if ttl <= 0: return None

        self.redis.set(key, json.dumps(session_data), ex=ttl)
        self.redis.set(self._jti_key(jti), device_id, ex=ttl)

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
            else:
                # Cleanup huérfanas/expiradas (3.2)
                self.redis.delete(key)

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
    # 5. Validación Obligatoria (3.1, 3.2, 3.6, 3.7)
    # -----------------------------
    def validate_session_for_refresh(self, user_id: int, device_id: str, jti: str, ip: str, user_agent: str):
        key = self._session_key(user_id, device_id)
        raw = self.redis.get(key)

        # 1. Verificar si existe (si no = expirada/revocada) (3.2)
        if not raw:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Sesión expirada o inexistente."
            )

        session = json.loads(raw)

        # 2. Verificar correspondencia de JTI (Token replay) (3.1)
        if session.get("jti") != jti:
            # Posible ataque. Revocamos la sesión comprometida. (3.6)
            self.delete_session(user_id, device_id)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token comprometido o previamente usado. Sesión terminada por seguridad."
            )

        # 3. Detección de robo/fraude de contexto (Cookie theft / Anomalous Refresh) (3.7)
        # Relajado: Podemos auditar o bloquear si el user-agent cambia drásticamente.
        # Por ejemplo, de Windows Chrome a iPhone Safari
        """
        # (Ejemplo de consistencia básica) 
        if session.get("initial_user_agent") != user_agent:
            # En entorno móvil podría cambiar ligeramente. Se puede implementar lógica más tolerante.
            # Aquí lo auditaríamos.
            pass
        """
        return session

    # -----------------------------
    # 6. Actualizar JTI (Token rotation / Auditoría 3.4)
    # -----------------------------
    def update_jti_for_session(
        self,
        user_id: int,
        device_id: str,
        old_jti: str,
        new_jti: str,
        new_expires_at: datetime,
        current_ip: str,
        current_user_agent: str
    ):
        key = self._session_key(user_id, device_id)

        # Usamos try-except por si acaban de revocarla
        try:
            session = self.validate_session_for_refresh(user_id, device_id, old_jti, current_ip, current_user_agent)
        except HTTPException:
            return False

        # Auditoría y actualización (3.4)
        session["jti"] = new_jti
        session["expires_at"] = new_expires_at.isoformat()
        session["last_access"] = datetime.utcnow().isoformat()
        session["last_ip"] = current_ip
        session["last_user_agent"] = current_user_agent
        session["refresh_count"] = session.get("refresh_count", 0) + 1

        ttl = int((new_expires_at - datetime.utcnow()).total_seconds())
        if ttl <= 0: return False

        self.redis.set(key, json.dumps(session), ex=ttl)

        # Borrar JTI viejo y guardar el nuevo
        self.redis.delete(self._jti_key(old_jti))
        self.redis.set(self._jti_key(new_jti), device_id, ex=ttl)

        return True