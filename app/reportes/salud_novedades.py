from __future__ import annotations

from ..models.informe import Grafico, Informe, Parametro, Serie
from ..utils.fechas import formatear_fecha
from .base import ORDEN, Reporte
from .nomina import agrupar, barras_agrupadas


class ReporteSaludPension(Reporte):
    slug, titulo, icono = "salud-pension", "Reporte de salud y pensión", "heart"
    descripcion = "Frecuencias por EPS y fondo de pensión, por dependencia y por cargo."

    def parametros(self) -> list[Parametro]:
        return [ORDEN]

    def generar(self, p: dict) -> Informe:
        r, orden = self._repo, p["orden"]
        inf = Informe("Reporte de salud y pensión", "", self.etiquetas_parametros(p))
        eps, pension = r.frecuencia("v_frecuencia_eps", "eps"), r.frecuencia("v_frecuencia_pension", "pension")
        inf.subtitulo = f"{sum(f['cantidad'] for f in eps)} empleados afiliados"
        inf.bloques += [
            Grafico("Frecuencia de empleados por EPS", "bar", [f["etiqueta"] for f in eps], [Serie("Empleados", [f["cantidad"] for f in eps])]),
            Grafico("Frecuencia de empleados por fondo de pensión", "bar", [f["etiqueta"] for f in pension],
                    [Serie("Empleados", [f["cantidad"] for f in pension])]),
            barras_agrupadas("EPS por dependencia (barras comparativas)", [{**f, "eps": f["etiqueta"]} for f in r.frecuencia_por_dependencia("eps")], "dependencia", "eps"),
            barras_agrupadas("Fondo de pensión por dependencia (barras comparativas)",
                             [{**f, "pension": f["etiqueta"]} for f in r.frecuencia_por_dependencia("pension")], "dependencia", "pension"),
        ]
        for col, etiqueta in (("eps", "EPS"), ("pension", "pensión")):
            for (cargo, grupo), filas in agrupar(r.empleados_por_cargo_y(col, orden), "cargo", "grupo"):
                inf.bloques.append(self.tabla(f"Cargo {cargo} · {etiqueta} {grupo} — {len(filas)} empleado(s)", ["Código", "Nombre"],
                                              [[f["codigo"], f["nombre_completo"]] for f in filas]))
        return inf


class ReporteNovedades(Reporte):
    slug, titulo, icono = "novedades", "Reporte de novedades", "calendar"
    descripcion = "Empleados con incapacidades o vacaciones entre dos meses, y conteo por dependencia y cargo."

    def parametros(self) -> list[Parametro]:
        rango = self._repo.rango_novedades()
        d, h = (rango[0].strftime("%m/%Y"), rango[1].strftime("%m/%Y")) if rango else ("01/2022", "12/2022")
        return [Parametro("desde", "Desde (MM/AAAA)", "mesanio", d, ayuda="Primer mes del rango, ej. 03/2022"),
                Parametro("hasta", "Hasta (MM/AAAA)", "mesanio", h, ayuda="Último mes incluido, ej. 05/2022"), ORDEN]

    def validar(self, crudo):
        valores, errores = super().validar(crudo)
        if not errores and valores["hasta"] < valores["desde"]:
            errores["hasta"] = "El mes final no puede ser anterior al inicial."
        return valores, errores

    def generar(self, p: dict) -> Informe:
        filas = self._repo.novedades(p["desde"], p["hasta"], p["orden"])
        conteo = self._repo.novedades_conteo(p["desde"], p["hasta"])
        empleados = len({f["codigo"] for f in filas})
        inf = Informe("Reporte de novedades", f"{empleados} empleado(s) con novedades · {len(filas)} novedad(es)", self.etiquetas_parametros(p), horizontal=True)
        inf.bloques += [
            self.tabla("Empleados con novedades en el rango", ["Código", "Nombre", "Dependencia", "Cargo", "Tipo", "Inicio", "Fin", "Días"],
                       [[f["codigo"], f["nombre_completo"], f["dependencia"], f["cargo"], f["tipo"].capitalize(),
                         formatear_fecha(f["fecha_inicio"]), formatear_fecha(f["fecha_fin"]), f["dias"]] for f in filas]),
            self.tabla("Cantidad de empleados con novedades por dependencia y cargo", ["Dependencia", "Cargo", "Empleados", "Novedades"],
                       [[f["dependencia"], f["cargo"], f["empleados"], f["novedades"]] for f in conteo]),
        ]
        return inf
