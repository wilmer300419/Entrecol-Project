"""Emisión y verificación de JWT con datos NO sensibles.

Claims incluidos:  sub (id numérico), usr (nombre de usuario), rol, jti, iat, exp, iss, aud.
Nunca se incluyen contraseñas, correos, datos de empleados ni salarios."""
from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import jwt

from .configuracion import ConfigSeguridad
from .modelos import Usuario


class TokenInvalido(Exception):
    pass


@dataclass(frozen=True)
class ClaimsToken:
    sub: int
    usr: str
    rol: str
    jti: str
    exp: datetime


class ServicioJWT:
    def __init__(self, cfg: ConfigSeguridad):
        self._cfg = cfg

    def emitir(self, u: Usuario) -> tuple[str, ClaimsToken]:
        ahora = datetime.now(timezone.utc)
        exp = ahora + timedelta(minutes=self._cfg.jwt_expira_min)
        jti = secrets.token_hex(16)
        carga = {"sub": str(u.id), "usr": u.nombre_usuario, "rol": u.rol.value, "jti": jti,
                 "iat": ahora, "exp": exp, "iss": self._cfg.jwt_emisor, "aud": self._cfg.jwt_audiencia}
        token = jwt.encode(carga, self._cfg.jwt_secreto, algorithm=self._cfg.jwt_algoritmo)
        return token, ClaimsToken(u.id, u.nombre_usuario, u.rol.value, jti, exp)

    def verificar(self, token: str) -> ClaimsToken:
        try:
            d = jwt.decode(token, self._cfg.jwt_secreto, algorithms=[self._cfg.jwt_algoritmo],   # algoritmo fijado
                           audience=self._cfg.jwt_audiencia, issuer=self._cfg.jwt_emisor,
                           options={"require": ["exp", "iat", "sub", "jti", "iss", "aud"]})
            return ClaimsToken(int(d["sub"]), d["usr"], d["rol"], d["jti"],
                               datetime.fromtimestamp(d["exp"], timezone.utc))
        except (jwt.PyJWTError, KeyError, ValueError) as exc:
            raise TokenInvalido("Token inválido o expirado") from exc
