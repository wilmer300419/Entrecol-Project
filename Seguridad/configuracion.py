from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ConfigSeguridad:
    jwt_secreto: str
    jwt_expira_min: int = 120
    jwt_emisor: str = "entrecol-api"
    jwt_audiencia: str = "entrecol-web"
    jwt_algoritmo: str = "HS256"
    cookie_nombre: str = "access_token"
    cookie_segura: bool = False
    captcha_ttl_s: int = 180
    max_intentos: int = 5
    bloqueo_min: int = 15
