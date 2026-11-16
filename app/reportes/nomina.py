from __future__ import annotations

from itertools import groupby
from operator import itemgetter

from ..models.informe import Grafico, Informe, Parametro, Serie
from ..utils.fechas import formatear_fecha
from ..utils.formatos import moneda
from .base import ORDEN, Reporte


def agrupar(filas: list[dict], *claves: str):
    """Agrupa filas ya ordenadas por las claves dadas -> [(tupla_clave, [filas])]."""
    llave = itemgetter(*claves)
    return [((k if isinstance(k, tuple) else (k,)), list(g)) for k, g in groupby(filas, key=llave)]


def barras_agrupadas(titulo: str, filas: list[dict], eje: str, serie: str) -> Grafico:
    """filas = [{eje, serie, cantidad}] -> barras comparativas (una serie por valor de *serie*)."""
    categorias = sorted({f[eje] for f in filas})
    nombres = sorted({f[serie] for f in filas})
    cuenta = {(f[eje], f[serie]): f["cantidad"] for f in filas}
    return Grafico(titulo, "bar", categorias, [Serie(n, [cuenta.get((c, n), 0) for c in categorias]) for n in nombres])


class ReporteNomina(Reporte):
    slug, titulo, icono = "nomina", "Reporte de nómina", "users"
    descripcion = "Empleados en total, por dependencia y por cargo, con gráficos de torta y de barras."

    def parametros(self) -> list[Parametro]:
        return [ORDEN]

    def generar(self, p: dict) -> Informe:
        orden = p["orden"]
        emp = self._repo.empleados(orden)
        inf = Informe("Reporte de nómina", f"Total de empleados: {len(emp)}", self.etiquetas_parametros(p))
        por_dep = self._repo.frecuencia_dependencia()
        por_cargo = self._repo.frecuencia_dependencia_cargo()
        inf.bloques += [
            self.tabla("Cantidad de empleados por dependencia", ["Dependencia", "Empleados"],
                       [[f["dependencia"], f["cantidad"]] for f in por_dep] + [["TOTAL", len(emp)]]),
            Grafico("Empleados por dependencia", "pie", [f["dependencia"] for f in por_dep],
                    [Serie("Empleados", [f["cantidad"] for f in por_dep])]),
            Grafico("Empleados por dependencia y cargo", "barh", [f"{f['dependencia']} › {f['cargo']}" for f in por_cargo],
                    [Serie("Empleados", [f["cantidad"] for f in por_cargo])]),
            self.tabla(f"Lista de empleados de la empresa — {len(emp)} en total", ["Código", "Nombre", "Dependencia", "Cargo"],
                       [[f["codigo"], f["nombre_completo"], f["dependencia"], f["cargo"]] for f in emp]),
        ]
        por_dependencia = sorted(emp, key=itemgetter("dependencia"))            # sorted es estable: conserva el orden de nombres
        for (dep,), grupo in agrupar(por_dependencia, "dependencia"):
            inf.bloques.append(self.tabla(f"Dependencia {dep} — {len(grupo)} empleado(s)", ["Código", "Nombre", "Cargo"],
                                          [[f["codigo"], f["nombre_completo"], f["cargo"]] for f in grupo]))
        por_dep_cargo = sorted(emp, key=itemgetter("dependencia", "cargo"))
        for (dep, cargo), grupo in agrupar(por_dep_cargo, "dependencia", "cargo"):
            inf.bloques.append(self.tabla(f"{dep} › {cargo} — {len(grupo)} empleado(s)", ["Código", "Nombre"],
                                          [[f["codigo"], f["nombre_completo"]] for f in grupo]))
        return inf


class ReportePersonal(Reporte):
    slug, titulo, icono = "informacion-personal", "Reporte de información personal", "id"
    descripcion = "Ficha de cada empleado: dependencia, cargo, ingreso, EPS, pensión, salario y novedades."

    def parametros(self) -> list[Parametro]:
        return [Parametro("codigo", "Código del empleado", "entero", "", minimo=1, requerido=False,
                          ayuda="Déjelo vacío para ver todos los empleados."), ORDEN]

    def generar(self, p: dict) -> Informe:
        filas = self._repo.informacion_personal(p["codigo"], p["orden"])
        inf = Informe("Reporte de información personal", f"Empleados incluidos: {len(filas)}", self.etiquetas_parametros(p), horizontal=True)
        inf.bloques.append(self.tabla(
            "Información personal y laboral",
            ["Nombre completo + código", "Dependencia", "Cargo", "Fecha de ingreso", "EPS", "Aporte pensión (fondo)", "Salario", "Discriminación de novedades"],
            [[f"{f['nombre_completo']} ({f['codigo']})", f["dependencia"], f["cargo"], formatear_fecha(f["fecha_ingreso"]),
              f["eps"], f["pension"], moneda(f["salario"]), f["novedades"]] for f in filas]))
        return inf
