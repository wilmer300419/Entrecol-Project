"""Configuración centralizada: todo viene de variables de entorno (.env)."""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Configuracion:
    entorno: str
    database_url: str
    secret_key: str
    jwt_secret: str
    jwt_expira_min: int
    cookie_segura: bool
    upload_max_mb: int
    filas_html_max: int = 300      # filas por tabla en la vista web (el PDF trae todas)
    filas_pdf_max: int = 5000

    @classmethod
    def desde_entorno(cls) -> "Configuracion":
        def requerido(nombre: str) -> str:
            valor = os.environ.get(nombre, "").strip()
            if not valor:
                raise RuntimeError(f"Falta la variable de entorno {nombre} (revisa .env.example)")
            return valor

        secret, jwt_secret = requerido("SECRET_KEY"), requerido("JWT_SECRET_KEY")
        if len(secret) < 32 or len(jwt_secret) < 32:
            raise RuntimeError("SECRET_KEY y JWT_SECRET_KEY deben tener al menos 32 caracteres")
        return cls(
            entorno=os.environ.get("FLASK_ENV", "production"),
            database_url=requerido("DATABASE_URL"),
            secret_key=secret,
            jwt_secret=jwt_secret,
            jwt_expira_min=int(os.environ.get("JWT_EXPIRA_MINUTOS", "120")),
            cookie_segura=os.environ.get("COOKIE_SEGURA", "false").lower() == "true",
            upload_max_mb=int(os.environ.get("UPLOAD_MAX_MB", "20")),
        )
