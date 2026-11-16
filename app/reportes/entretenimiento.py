from __future__ import annotations

from ..models.informe import Grafico, Informe, Parametro, Serie
from .base import ORDEN, Reporte
from .nomina import agrupar


class ReporteEntretenimiento(Reporte):
    slug, titulo, icono = "entretenimiento", "Reporte de base de entretenimiento", "film"
    descripcion = "Películas por género y año, ranking de libros y gráficos de frecuencia."

    def parametros(self) -> list[Parametro]:
        d, h = self._repo.rango_anios_libros()
        generos = (("", "Todos los géneros"),) + tuple((g, g) for g in self._repo.generos())
        return [
            Parametro("anio_desde", "Películas: año desde (F1)", "entero", 1995, minimo=1870, maximo=2100, ayuda="El archivo de películas solo trae el año de estreno."),
            Parametro("anio_hasta", "Películas: año hasta (F2)", "entero", 1995, minimo=1870, maximo=2100),
            Parametro("genero", "Género de las películas", "select", "", generos, requerido=False),
            Parametro("n_libros", "Top N libros con mejor rating", "entero", 10, minimo=1, maximo=500),
            Parametro("min_votos", "Mínimo de calificaciones por libro", "entero", 1, minimo=0, maximo=100000,
                      ayuda="Con 1 se excluyen los libros que nadie ha calificado."),
            Parametro("libros_desde", "Libros: año desde (F1)", "entero", 2000, minimo=1000, maximo=2100, ayuda=f"Datos disponibles: {d}–{h}."),
            Parametro("libros_hasta", "Libros: año hasta (F2)", "entero", 2006, minimo=1000, maximo=2100),
            Parametro("n_generos", "Películas con N géneros", "entero", 5, minimo=0, maximo=20),
            ORDEN,
        ]

    def validar(self, crudo):
        valores, errores = super().validar(crudo)
        for a, b in (("anio_desde", "anio_hasta"), ("libros_desde", "libros_hasta")):
            if a not in errores and b not in errores and valores[b] < valores[a]:
                errores[b] = "El año final no puede ser menor que el inicial."
        return valores, errores

    def generar(self, p: dict) -> Informe:
        r, orden = self._repo, p["orden"]
        inf = Informe("Reporte de base de entretenimiento", "", self.etiquetas_parametros(p), horizontal=True)
        # 1) Películas por género entre dos años
        pelis = r.peliculas_por_genero(p["anio_desde"], p["anio_hasta"], p["genero"] or "", orden)
        inf.subtitulo = f"{len(pelis)} película(s) listadas por género en {p['anio_desde']}–{p['anio_hasta']}"
        if not pelis:
            inf.bloques.append(self.tabla("Películas por género", ["Título", "Año"], []))
        for (genero,), filas in agrupar(pelis, "genero"):
            inf.bloques.append(self.tabla(f"Películas de {genero} ({p['anio_desde']}–{p['anio_hasta']}) — {len(filas)}",
                                          ["Título", "Año"], [[f["titulo"], f["anio_estreno"]] for f in filas]))
        # 2) Top N libros
        top = r.top_libros(p["n_libros"], orden, p["min_votos"])
        inf.bloques.append(self.tabla(f"Top {p['n_libros']} libros con mejor rating", ["#", "Título", "Autores", "Año", "Rating", "Calificaciones"],
                                      [[i, f["titulo"], f["autores"], f["anio_publicacion"] or "", f["calificacion_promedio"], f["cantidad_calificaciones"]]
                                       for i, f in enumerate(top, 1)]))
        # 3) Top 5 mejores / peores por año
        rango = f"{p['libros_desde']}–{p['libros_hasta']}"
        for mejores, nombre in ((True, "mejor"), (False, "peor")):
            filas = r.libros_extremos_por_anio(p["libros_desde"], p["libros_hasta"], p["min_votos"], mejores, orden)
            inf.bloques.append(self.tabla(f"Top 5 libros con {nombre} rating por año ({rango})", ["Año", "#", "Título", "Autores", "Rating", "Calificaciones"],
                                          [[f["anio_publicacion"], f["puesto"], f["titulo"], f["autores"], f["calificacion_promedio"], f["cantidad_calificaciones"]]
                                           for f in filas]))
        # 4) Películas con N géneros
        con_n = r.peliculas_con_n_generos(p["n_generos"], orden)
        inf.bloques.append(self.tabla(f"Películas con {p['n_generos']} género(s) — {len(con_n)} película(s)", ["Título", "Año", "Géneros"],
                                      [[f["titulo"], f["anio_estreno"] or "", f["generos"]] for f in con_n]))
        # 5) Gráficos
        por_genero = r.frecuencia_pelicula_genero()
        inf.bloques.append(Grafico("Frecuencia de películas por género", "barh", [f["genero"] for f in por_genero],
                                   [Serie("Películas", [f["cantidad"] for f in por_genero])]))
        por_anio = r.frecuencia_libros_anio(p["libros_desde"], p["libros_hasta"])
        inf.bloques.append(Grafico(f"Frecuencia de libros por año de publicación ({rango})", "bar", [str(f["anio"]) for f in por_anio],
                                   [Serie("Libros", [f["cantidad"] for f in por_anio])]))
        return inf
