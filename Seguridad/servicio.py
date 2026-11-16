"""Casos de uso de autenticación (sin Flask: se puede probar de forma aislada)."""
from __future__ import annotations

import hashlib
import hmac
import re
from datetime import datetime, timezone

from .captcha import ServicioCaptcha
from .configuracion import ConfigSeguridad
from .contrasenas import HasherContrasena, PoliticaContrasena
from .modelos import Rol, Usuario
from .repositorio import RepositorioAuditoria, RepositorioUsuarios
from .tokens import ClaimsToken, ServicioJWT, TokenInvalido


class ErrorAutenticacion(Exception):
    """El mensaje es seguro para mostrar al usuario."""


class CredencialesInvalidas(ErrorAutenticacion):
    pass


class CuentaBloqueada(ErrorAutenticacion):
    pass


class CaptchaInvalido(ErrorAutenticacion):
    pass


class DatosUsuarioInvalidos(Exception):
    def __init__(self, errores: dict[str, list[str]]):
        super().__init__("Datos de usuario inválidos")
        self.errores = errores


class ServicioAutenticacion:
    def __init__(self, usuarios: RepositorioUsuarios, auditoria: RepositorioAuditoria, jwt: ServicioJWT,
                 captcha: ServicioCaptcha, hasher: HasherContrasena, politica: PoliticaContrasena, cfg: ConfigSeguridad):
        self.usuarios, self.auditoria, self.jwt, self.captcha = usuarios, auditoria, jwt, captcha
        self._hasher, self._politica, self._cfg = hasher, politica, cfg

    # ---------------------------------------------------------------- sesión
    def iniciar_sesion(self, nombre: str, clave: str, captcha_token: str, captcha_resp: str,
                       ip: str | None = None, agente: str = "") -> tuple[str, ClaimsToken, Usuario]:
        nombre = (nombre or "").strip().lower()
        if not self.captcha.validar(captcha_token, captcha_resp):
            self.auditoria.registrar(None, nombre, "LOGIN_FALLIDO", "usuario", "captcha incorrecto", ip)
            raise CaptchaInvalido("El código de verificación es incorrecto o expiró.")
        u = self.usuarios.buscar_por_nombre(nombre)
        if u is None:
            self._hasher.verificar_senuelo(clave or "")
            self.auditoria.registrar(None, nombre, "LOGIN_FALLIDO", "usuario", "usuario inexistente", ip)
            raise CredencialesInvalidas("Usuario o contraseña incorrectos.")
        if u.bloqueado_hasta and u.bloqueado_hasta > datetime.now(timezone.utc):
            minutos = max(1, int((u.bloqueado_hasta - datetime.now(timezone.utc)).total_seconds() // 60) + 1)
            self.auditoria.registrar(u.id, nombre, "LOGIN_BLOQUEADO", "usuario", None, ip)
            raise CuentaBloqueada(f"Cuenta bloqueada temporalmente. Intenta de nuevo en {minutos} min.")
        if not self._hasher.verificar(u.password_hash, clave or "") or not u.activo:
            self.usuarios.registrar_fallo(u.id, self._cfg.max_intentos, self._cfg.bloqueo_min)
            self.auditoria.registrar(u.id, nombre, "LOGIN_FALLIDO", "usuario", "clave incorrecta o cuenta inactiva", ip)
            raise CredencialesInvalidas("Usuario o contraseña incorrectos.")
        self.usuarios.registrar_acceso(u.id)
        token, claims = self.jwt.emitir(u)
        self.usuarios.crear_sesion(claims.jti, u.id, claims.exp, ip, self.hash_agente(agente))     # el token queda ligado a una sesión
        self.auditoria.registrar(u.id, nombre, "LOGIN", "usuario", f"sesion={claims.jti[:8]}", ip)
        return token, claims, u

    @staticmethod
    def hash_agente(agente: str) -> str:
        return hashlib.sha256((agente or "")[:300].encode()).hexdigest()

    def cerrar_sesion(self, claims: ClaimsToken, ip: str | None = None) -> None:
        """Cierre de sesión con validación: la sesión debe existir, ser del usuario del token y seguir activa."""
        if not self.usuarios.revocar_sesion(claims.jti, claims.sub, "LOGOUT"):
            raise TokenInvalido("La sesión ya no está activa")
        self.auditoria.registrar(claims.sub, claims.usr, "LOGOUT", "usuario", f"sesion={claims.jti[:8]}", ip)

    def cerrar_todas(self, id_usuario: int, nombre: str, motivo: str = "LOGOUT_TOTAL", ip: str | None = None,
                     excepto_jti: str | None = None) -> int:
        n = self.usuarios.revocar_sesiones_usuario(id_usuario, motivo, excepto_jti)
        self.auditoria.registrar(id_usuario, nombre, "SESIONES_REVOCADAS", "usuario", f"{n} sesion(es) · {motivo}", ip)
        return n

    def autenticar_token(self, token: str, agente: str = "") -> tuple[Usuario, ClaimsToken]:
        """Firma + expiración (JWT) y además la SESIÓN registrada en base de datos."""
        claims = self.jwt.verificar(token)
        u, ses = self.usuarios.buscar_con_sesion(claims.sub, claims.jti)
        if u is None or ses is None or ses["revocado_en"] is not None or not u.activo \
                or ses["sesion_expira"] <= datetime.now(timezone.utc):
            raise TokenInvalido("Sesión no válida")
        if not hmac.compare_digest(ses["agente_hash"], self.hash_agente(agente)):          # token usado desde otro navegador
            self.usuarios.revocar_sesion(claims.jti, claims.sub, "AGENTE_DISTINTO")
            self.auditoria.registrar(claims.sub, claims.usr, "SESION_SOSPECHOSA", "usuario", "agente de usuario distinto", None)
            raise TokenInvalido("Sesión no válida")
        return u, claims

    # -------------------------------------------------------------- usuarios
    def validar_datos(self, nombre: str, visible: str, clave: str | None) -> dict[str, list[str]]:
        errores: dict[str, list[str]] = {}
        if not re.fullmatch(r"[a-z0-9._-]{3,40}", nombre or ""):
            errores["nombre_usuario"] = ["Use 3 a 40 caracteres: minúsculas, números, punto, guion o guion bajo."]
        if not (visible or "").strip() or len(visible) > 80:
            errores["nombre_visible"] = ["El nombre es obligatorio (máximo 80 caracteres)."]
        if clave is not None and (problemas := self._politica.validar(clave, nombre)):
            errores["password"] = problemas
        return errores

    def crear_usuario(self, nombre: str, visible: str, clave: str, rol: Rol) -> int:
        nombre = (nombre or "").strip().lower()
        errores = self.validar_datos(nombre, visible, clave)
        if not errores and self.usuarios.buscar_por_nombre(nombre):
            errores["nombre_usuario"] = ["Ese nombre de usuario ya existe."]
        if errores:
            raise DatosUsuarioInvalidos(errores)
        return self.usuarios.crear(nombre, visible.strip(), self._hasher.cifrar(clave), rol)

    def cambiar_password(self, id_usuario: int, nombre: str, clave: str) -> None:
        if problemas := self._politica.validar(clave, nombre):
            raise DatosUsuarioInvalidos({"password": problemas})
        self.usuarios.cambiar_password(id_usuario, self._hasher.cifrar(clave))
        self.usuarios.revocar_sesiones_usuario(id_usuario, "CAMBIO_CLAVE")          # obliga a ingresar de nuevo
