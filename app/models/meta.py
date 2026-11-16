"""MODELO (MVC): descripción declarativa de las entidades administrables.

Cada ``Entidad`` describe una tabla, sus campos de formulario y cómo listarla.
Agregar una entidad nueva = declarar otra ``Entidad`` en ``catalogo.py`` (abierto/cerrado).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable


@dataclass(frozen=True)
class RelRef:
    """N:1 resuelta por nombre (ej. libro.editorial): se busca/crea por texto."""
    tabla_remota: str
    pk_remota: str
    col_nombre: str


@dataclass(frozen=True)
class RelMuchos:
    """M:N mediante tabla de enlace (ej. pelicula_genero, libro_autor)."""
    tabla_enlace: str
    col_local: str
    col_remota: str
    tabla_remota: str
    pk_remota: str
    col_nombre: str
    con_orden: bool = False


@dataclass(frozen=True)
class Campo:
    nombre: str
    etiqueta: str
    tipo: str = "texto"            # texto | entero | decimal | fecha | fk | ref_texto | lista_texto | multi
    requerido: bool = True
    max_len: int | None = None
    minimo: float | None = None
    maximo: float | None = None
    columna: str | None = None     # columna real si difiere del nombre del campo
    opciones_sql: str | None = None   # fk / multi: SELECT valor, etiqueta
    valor_texto: bool = False      # fk cuyo valor es texto (ej. código de idioma)
    rel: RelRef | RelMuchos | None = None
    lectura_sql: str | None = None   # subconsulta (alias t) para precargar campos virtuales
    inmutable: bool = False        # no editable después de crear (ej. código de empleado)
    ayuda: str = ""
    paso: str = ""                 # atributo step para decimales

    @property
    def col(self) -> str:
        return self.columna or self.nombre

    @property
    def es_virtual(self) -> bool:
        return self.tipo in ("lista_texto", "multi")


@dataclass(frozen=True)
class Entidad:
    slug: str
    titulo: str
    singular: str
    tabla: str
    pk: str
    lista_sql: str
    columnas: tuple[tuple[str, str], ...]        # (columna, etiqueta) visibles en la lista
    campos: tuple[Campo, ...]
    buscar: tuple[str, ...]
    orden: str
    grupo: str = "Nómina"
    pk_auto: bool = True
    validadores: tuple[Callable[[dict], dict[str, str]], ...] = field(default_factory=tuple)

    def campo(self, nombre: str) -> Campo | None:
        return next((c for c in self.campos if c.nombre == nombre), None)
