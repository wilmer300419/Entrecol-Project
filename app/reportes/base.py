"""Infraestructura de reportes (Abierto/Cerrado): un reporte nuevo = una clase nueva."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Mapping

from ..models.informe import Informe, Parametro, Tabla
from ..repositories.reportes import RepositorioReportes
from ..utils.fechas import parsear_mes_anio

ORDEN = Parametro("orden", "Orden de los nombres", "select", "asc", (("asc", "Ascendente (A-Z)"), ("desc", "Descendente (Z-A)")))


class Reporte(ABC):
    slug: str
    titulo: str
    descripcion: str
    icono: str = "chart"

    def __init__(self, repo: RepositorioReportes, filas_max: int = 5000):
        self._repo, self._filas_max = repo, filas_max

    @abstractmethod
    def parametros(self) -> list[Parametro]: ...

    @abstractmethod
    def generar(self, p: dict) -> Informe: ...

    # ----------------------------------------------------------------- común
    def validar(self, crudo: Mapping[str, str]) -> tuple[dict, dict[str, str]]:
        valores, errores = {}, {}
        for prm in self.parametros():
            texto = str(crudo.get(prm.nombre, "") if prm.nombre in crudo else prm.por_defecto).strip()
            try:
                valores[prm.nombre] = self._convertir(prm, texto)
            except ValueError as exc:
                errores[prm.nombre] = str(exc)
        return valores, errores

    @staticmethod
    def _convertir(prm: Parametro, texto: str):
        if not texto:
            if prm.requerido:
                raise ValueError("Este campo es obligatorio.")
            return None
        if prm.tipo == "entero":
            try:
                n = int(texto)
            except ValueError:
                raise ValueError("Ingrese un número entero.")
            if prm.minimo is not None and n < prm.minimo:
                raise ValueError(f"El mínimo es {prm.minimo}.")
            if prm.maximo is not None and n > prm.maximo:
                raise ValueError(f"El máximo es {prm.maximo}.")
            return n
        if prm.tipo == "select":
            if texto not in {v for v, _ in prm.opciones}:
                raise ValueError("Opción no válida.")
            return texto
        if prm.tipo == "mesanio":
            if (d := parsear_mes_anio(texto)) is None:
                raise ValueError("Use el formato MM/AAAA (por ejemplo 03/2022).")
            return d
        return texto[:100]

    def etiquetas_parametros(self, valores: dict) -> list[tuple[str, str]]:
        salida = []
        for prm in self.parametros():
            v = valores.get(prm.nombre)
            if prm.tipo == "select":
                v = dict(prm.opciones).get(v, v)
            elif prm.tipo == "mesanio" and v:
                v = v.strftime("%m/%Y")
            salida.append((prm.etiqueta, "—" if v in (None, "") else str(v)))
        return salida

    def tabla(self, titulo: str, columnas: list[str], filas: list[list]) -> Tabla:
        total = len(filas)
        t = Tabla(titulo, columnas, filas[: self._filas_max], total=total)
        if total > self._filas_max:
            t.nota = f"Se muestran {self._filas_max} de {total} filas."
        return t
