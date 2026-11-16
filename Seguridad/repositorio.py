"""Acceso a datos de seguridad (SQL parametrizado, sin concatenar valores)."""
from __future__ import annotations

from datetime import datetime

from .contratos import EjecutorSQL
from .modelos import Rol, Usuario

_BASE = """SELECT u.id_usuario, u.nombre_usuario, u.nombre_visible, u.password_hash, u.activo,
                  u.bloqueado_hasta, u.intentos_fallidos, u.creado_en, u.ultimo_acceso, r.nombre AS rol
           FROM usuario u JOIN rol r ON r.id_rol = u.id_rol"""


class RepositorioUsuarios:
    def __init__(self, db: EjecutorSQL):
        self._db = db

    def buscar_por_nombre(self, nombre: str) -> Usuario | None:
        f = self._db.fetch_one(_BASE + " WHERE u.nombre_usuario = %s", (nombre,))
        return Usuario.desde_fila(f) if f else None

    def buscar_por_id(self, id_usuario: int) -> Usuario | None:
        f = self._db.fetch_one(_BASE + " WHERE u.id_usuario = %s", (id_usuario,))
        return Usuario.desde_fila(f) if f else None

    def buscar_con_sesion(self, id_usuario: int, jti: str) -> tuple[Usuario | None, dict | None]:
        """Usuario + su sesión JWT (una sola consulta por petición). None si el token no tiene sesión registrada."""
        f = self._db.fetch_one(
            _BASE.replace("SELECT u.id_usuario", "SELECT s.agente_hash, s.revocado_en, s.expira_en AS sesion_expira, u.id_usuario")
            + " JOIN sesion_jwt s ON s.id_usuario = u.id_usuario AND s.jti = %s WHERE u.id_usuario = %s", (jti, id_usuario))
        return (Usuario.desde_fila(f), f) if f else (None, None)

    def listar(self) -> list[dict]:
        return self._db.fetch_all(_BASE + " ORDER BY u.nombre_usuario")

    def crear(self, nombre: str, visible: str, hash_: str, rol: Rol) -> int:
        f = self._db.fetch_one(
            "INSERT INTO usuario (nombre_usuario, nombre_visible, password_hash, id_rol) "
            "SELECT %s, %s, %s, id_rol FROM rol WHERE nombre = %s RETURNING id_usuario",
            (nombre, visible, hash_, rol.value))
        return f["id_usuario"]

    def actualizar(self, id_usuario: int, visible: str, rol: Rol, activo: bool) -> None:
        self._db.execute("UPDATE usuario SET nombre_visible=%s, activo=%s, id_rol=(SELECT id_rol FROM rol WHERE nombre=%s) "
                         "WHERE id_usuario=%s", (visible, activo, rol.value, id_usuario))

    def cambiar_password(self, id_usuario: int, hash_: str) -> None:
        self._db.execute("UPDATE usuario SET password_hash=%s, intentos_fallidos=0, bloqueado_hasta=NULL WHERE id_usuario=%s",
                         (hash_, id_usuario))

    def registrar_fallo(self, id_usuario: int, max_intentos: int, bloqueo_min: int) -> None:
        self._db.execute(
            """UPDATE usuario SET
                 intentos_fallidos = CASE WHEN intentos_fallidos + 1 >= %(m)s THEN 0 ELSE intentos_fallidos + 1 END,
                 bloqueado_hasta   = CASE WHEN intentos_fallidos + 1 >= %(m)s THEN now() + make_interval(mins => %(b)s)
                                          ELSE bloqueado_hasta END
               WHERE id_usuario = %(i)s""", {"m": max_intentos, "b": bloqueo_min, "i": id_usuario})

    def registrar_acceso(self, id_usuario: int) -> None:
        self._db.execute("UPDATE usuario SET intentos_fallidos=0, bloqueado_hasta=NULL, ultimo_acceso=now() WHERE id_usuario=%s",
                         (id_usuario,))

    # ------------------------------------------------------------ sesiones JWT
    def crear_sesion(self, jti: str, id_usuario: int, expira_en: datetime, ip: str | None, agente_hash: str) -> None:
        self._db.execute("INSERT INTO sesion_jwt (jti, id_usuario, expira_en, ip, agente_hash) VALUES (%s,%s,%s,%s,%s)",
                         (jti, id_usuario, expira_en, ip, agente_hash))
        self._db.execute("DELETE FROM sesion_jwt WHERE expira_en < now() - INTERVAL '1 day'")        # purga de sesiones viejas

    def revocar_sesion(self, jti: str, id_usuario: int, motivo: str) -> bool:
        """Revoca UNA sesión activa del usuario. False si no existe, no es suya o ya estaba revocada/vencida."""
        return self._db.execute(
            "UPDATE sesion_jwt SET revocado_en = now(), motivo_revocacion = %s "
            "WHERE jti = %s AND id_usuario = %s AND revocado_en IS NULL AND expira_en > now()", (motivo, jti, id_usuario)) == 1

    def revocar_sesiones_usuario(self, id_usuario: int, motivo: str, excepto_jti: str | None = None) -> int:
        return self._db.execute(
            "UPDATE sesion_jwt SET revocado_en = now(), motivo_revocacion = %s "
            "WHERE id_usuario = %s AND revocado_en IS NULL AND expira_en > now() AND jti <> COALESCE(%s, '')",
            (motivo, id_usuario, excepto_jti))

    def sesiones_activas(self, id_usuario: int) -> list[dict]:
        return self._db.fetch_all("SELECT jti, emitido_en, expira_en, ip FROM sesion_jwt WHERE id_usuario = %s "
                                  "AND revocado_en IS NULL AND expira_en > now() ORDER BY emitido_en DESC", (id_usuario,))


class RepositorioAuditoria:
    def __init__(self, db: EjecutorSQL):
        self._db = db

    def registrar(self, id_usuario: int | None, nombre: str | None, accion: str,
                  entidad: str | None = None, detalle: str | None = None, ip: str | None = None) -> None:
        self._db.execute("INSERT INTO auditoria (id_usuario, nombre_usuario, accion, entidad, detalle, ip) VALUES (%s,%s,%s,%s,%s,%s)",
                         (id_usuario, (nombre or "")[:40] or None, accion, entidad, (detalle or "")[:500] or None, ip))

    def listar(self, accion: str = "", usuario: str = "", limite: int = 50, desplazamiento: int = 0) -> tuple[list[dict], int]:
        filtros, params = ["TRUE"], []
        if accion:
            filtros.append("accion = %s"); params.append(accion)
        if usuario:
            filtros.append("nombre_usuario ILIKE %s"); params.append(f"%{usuario}%")
        donde = " AND ".join(filtros)
        total = self._db.fetch_one(f"SELECT COUNT(*) AS n FROM auditoria WHERE {donde}", params)["n"]
        filas = self._db.fetch_all(f"SELECT * FROM auditoria WHERE {donde} ORDER BY fecha DESC LIMIT %s OFFSET %s",
                                   [*params, limite, desplazamiento])
        return filas, total

    def acciones(self) -> list[str]:
        return [f["accion"] for f in self._db.fetch_all("SELECT DISTINCT accion FROM auditoria ORDER BY 1")]
