"""Cargadores de archivos (Excel de nómina, películas .dat, libros .json).

Todos implementan ``Cargador`` (Liskov): el servicio/controlador los usa sin saber cuál es."""
from .base import Cargador, ErrorCarga, ResultadoCarga
from .libros import CargadorLibros
from .nomina import CargadorNomina
from .peliculas import CargadorPeliculas

CARGADORES = {"nomina": CargadorNomina, "peliculas": CargadorPeliculas, "libros": CargadorLibros}

__all__ = ["Cargador", "ErrorCarga", "ResultadoCarga", "CARGADORES",
           "CargadorNomina", "CargadorPeliculas", "CargadorLibros"]
