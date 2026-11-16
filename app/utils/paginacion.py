from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Pagina:
    numero: int
    tamano: int
    total: int

    @property
    def paginas(self) -> int:
        return max(1, -(-self.total // self.tamano))

    @property
    def desplazamiento(self) -> int:
        return (self.numero - 1) * self.tamano

    @property
    def hay_anterior(self) -> bool:
        return self.numero > 1

    @property
    def hay_siguiente(self) -> bool:
        return self.numero < self.paginas
