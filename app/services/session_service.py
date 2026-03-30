from typing import Optional
from datetime import datetime
import json
from fastapi import HTTPException, status
from app.utils.device import parse_user_agent


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

        # 4.4 Etiquetado Semántico
        parsed = parse_user_agent(user_agent)
        os_name = parsed["os"]
        browser = parsed["browser"]
        
        device_type = self._calculate_device_type(os_name, browser)
        trust_level = self._calculate_trust_level(ip)

        session_data = {
            "session_id": f"{user_id}:{device_id}",
            "user_id": user_id,
            "device_id": device_id,
            "jti": jti,
            "os": os_name,
            "browser": browser,
            "device_type": device_type,
            "trust_level": trust_level,
            "initial_ip": ip,
            "initial_user_agent": user_agent,
            "last_ip": ip,
            "last_user_agent": user_agent,
            "last_access": now,
            
            # --- Fase 5 (Métricas extendidas) ---
            "first_refresh_at": None,
            "last_refresh_at": None,
            "refresh_count": 0,
            "failed_refresh_attempts": 0,
            "country": "Unknown",
            "city": "Unknown",
            "login_method": "password",
            "device_trust_score": 100 if trust_level == "high" else 50,
            "session_quality_score": 100,
            
            "created_at": now,
            "expires_at": expires_at.isoformat(),
        }

        ttl = int((expires_at - datetime.utcnow()).total_seconds())
        if ttl <= 0: return None

        self.redis.set(key, json.dumps(session_data), ex=ttl)
        self.redis.set(self._jti_key(jti), device_id, ex=ttl)

        return session_data

    # -----------------------------
    # 4.4 - Helper Semantic Labels
    # -----------------------------
    def _calculate_device_type(self, os_name: str, browser: str) -> str:
        mobile_os = ["Android", "iOS"]
        if os_name in mobile_os:
            return "mobile"
        if os_name in ["Windows", "Mac OS", "Linux", "Mac OS X"]:
            return "desktop"
        return "unknown"

    def _calculate_trust_level(self, ip: str, is_known_ip: bool = False) -> str:
        """
        Calcula trust_level alto si la IP se encuentra en las 3 más frecuentes/recientes,
        'medium' si no. (Mockup funcional preparatorio).
        """
        return "high" if is_known_ip else "medium"

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

        # 2. Verificar correspondencia de JTI (Token replay)
        if session.get("jti") != jti:
            session["failed_refresh_attempts"] = session.get("failed_refresh_attempts", 0) + 1
            session["session_quality_score"] = max(0, session.get("session_quality_score", 100) - 50)
            self._save_session_changes(key, session)
            self.delete_session(user_id, device_id)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token comprometido o previamente usado. Sesión terminada por seguridad."
            )

        # 3. Detección de anomalías en rotación
        changes_detected = False
        if session.get("last_ip") != ip:
            session["session_quality_score"] = max(0, session.get("session_quality_score", 100) - 20)
            session["failed_refresh_attempts"] = session.get("failed_refresh_attempts", 0) + 1
            changes_detected = True

        if session.get("last_user_agent") != user_agent:
            session["session_quality_score"] = max(0, session.get("session_quality_score", 100) - 40)
            session["failed_refresh_attempts"] = session.get("failed_refresh_attempts", 0) + 1
            changes_detected = True

        if changes_detected:
            self._save_session_changes(key, session)

        return session

    def _save_session_changes(self, key: str, session_data: dict):
        """Helper para reguardar sesión cuando la mutamos durante validación."""
        ttl = self.redis.ttl(key)
        if ttl > 0:
            self.redis.set(key, json.dumps(session_data), ex=ttl)

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
        
        now = datetime.utcnow().isoformat()
        session["last_access"] = now
        session["last_ip"] = current_ip
        session["last_user_agent"] = current_user_agent
        
        # Auditoría 5.1
        if not session.get("first_refresh_at"):
            session["first_refresh_at"] = now
        session["last_refresh_at"] = now
        session["refresh_count"] = session.get("refresh_count", 0) + 1

        ttl = int((new_expires_at - datetime.utcnow()).total_seconds())
        if ttl <= 0: return False

        self.redis.set(key, json.dumps(session), ex=ttl)

        # Borrar JTI viejo y guardar el nuevo
        self.redis.delete(self._jti_key(old_jti))
        self.redis.set(self._jti_key(new_jti), device_id, ex=ttl)

        return True

    # -----------------------------
    # Fase 5 - Auditoría y Métricas Empresariales
    # -----------------------------
    def get_metrics_for_user(self, user_id: int) -> dict:
        """
        Retorna un hash comprensible con toda la analítica consolidada de las sesiones
        del usuario. Cumple la funcionalidad de Fase 5 para el dashboard de auditoría y admin.
        """
        sessions = self.get_sessions(user_id)
        
        metrics = {
            "active_sessions_count": len(sessions),
            "total_refreshes": 0,
            "failed_refresh_attempts": 0,
            "top_browsers": {},
            "top_os": {},
            "locations": {},
            "suspicious_sessions": []
        }

        for s in sessions:
            metrics["total_refreshes"] += s.get("refresh_count", 0)
            metrics["failed_refresh_attempts"] += s.get("failed_refresh_attempts", 0)
            
            browser = s.get("browser", "Unknown")
            metrics["top_browsers"][browser] = metrics["top_browsers"].get(browser, 0) + 1
            
            os = s.get("os", "Unknown")
            metrics["top_os"][os] = metrics["top_os"].get(os, 0) + 1
            
            loc = s.get("country", "Unknown")
            metrics["locations"][loc] = metrics["locations"].get(loc, 0) + 1
            
            # --- 5.3 Regla de Sesiones Sospechosas ---
            reasons = []
            if s.get("failed_refresh_attempts", 0) >= 3:
                reasons.append("many_failed_refresh")
            if s.get("device_trust_score", 100) <= 30:
                reasons.append("low_trust_score")
            if s.get("session_quality_score", 100) <= 40:
                reasons.append("low_quality_score")
            
            if s.get("initial_ip") != s.get("last_ip"):
                reasons.append("ip_changed_across_refreshes")
            if s.get("initial_user_agent") != s.get("last_user_agent"):
                reasons.append("user_agent_changed")
                
            # Flooding temporal (Ej: más de 20 refreshes en los primeros 10 minutos de vida)
            created_at = datetime.fromisoformat(s.get("created_at"))
            minutes_alive = max(1.0, (datetime.utcnow() - created_at).total_seconds() / 60.0)
            refresh_rate = s.get("refresh_count", 0) / minutes_alive
            if refresh_rate > 2.0:  # arbitrary threshold
                reasons.append("high_token_refresh_rate (token-flood)")

            if reasons:
                metrics["suspicious_sessions"].append({
                    "device_id": s.get("device_id"),
                    "reasons": reasons
                })
                
        return metrics