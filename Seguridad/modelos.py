from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class Rol(str, Enum):
    ADMIN = "ADMIN"
    ANALISTA = "ANALISTA"
    CONSULTA = "CONSULTA"


@dataclass(frozen=True)
class Usuario:
    id: int
    nombre_usuario: str
    nombre_visible: str
    rol: Rol
    activo: bool = True
    password_hash: str = ""
    bloqueado_hasta: datetime | None = None

    @property
    def es_admin(self) -> bool:
        return self.rol is Rol.ADMIN

    @property
    def puede_escribir(self) -> bool:
        return self.rol in (Rol.ADMIN, Rol.ANALISTA)

    @classmethod
    def desde_fila(cls, f: dict) -> "Usuario":
        return cls(f["id_usuario"], f["nombre_usuario"], f["nombre_visible"], Rol(f["rol"]),
                   f["activo"], f.get("password_hash", ""), f.get("bloqueado_hasta"))
