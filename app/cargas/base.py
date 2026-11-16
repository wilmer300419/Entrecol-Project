from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from ..core.database import Database


class ErrorCarga(Exception):
    """Archivo inválido o con estructura inesperada (mensaje seguro para el usuario)."""


@dataclass
class ResultadoCarga:
    origen: str
    insertados: int = 0
    actualizados: int = 0
    rechazados: int = 0
    advertencias: list[str] = field(default_factory=list)
    detalle: dict[str, int] = field(default_factory=dict)

    MAX_MENSAJES = 25

    def advertir(self, mensaje: str) -> None:
        if len(self.advertencias) < self.MAX_MENSAJES:
            self.advertencias.append(mensaje)
        elif len(self.advertencias) == self.MAX_MENSAJES:
            self.advertencias.append("… (hay más advertencias, se omiten)")

    def resumen(self) -> str:
        return f"{self.insertados} nuevos, {self.actualizados} actualizados, {self.rechazados} rechazados"


class Cargador(ABC):
    clave: str
    titulo: str
    extensiones: tuple[str, ...]

    def __init__(self, db: Database):
        self._db = db

    @abstractmethod
    def cargar(self, contenido: bytes, **opciones) -> ResultadoCarga: ...
