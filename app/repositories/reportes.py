"""Consultas de los reportes. Leen de las VISTAS de PostgreSQL (V004) y siempre parametrizan."""
from __future__ import annotations

from datetime import date

from psycopg import sql

from ..core.database import Database


def _dir(orden: str) -> sql.SQL:
    return sql.SQL("DESC") if orden == "desc" else sql.SQL("ASC")


class RepositorioReportes:
    def __init__(self, db: Database):
        self._db = db

    # ------------------------------------------------------------- nómina
    def empleados(self, orden: str) -> list[dict]:
        return self._db.fetch_all(sql.SQL("SELECT codigo, nombre_completo, dependencia, cargo FROM v_empleado_detalle "
                                          "ORDER BY nombre_completo {}, codigo").format(_dir(orden)))

    def frecuencia_dependencia(self) -> list[dict]:
        return self._db.fetch_all("SELECT dependencia, cantidad FROM v_frecuencia_dependencia ORDER BY dependencia")

    def frecuencia_dependencia_cargo(self) -> list[dict]:
        return self._db.fetch_all("SELECT dependencia, cargo, cantidad FROM v_frecuencia_dependencia_cargo ORDER BY dependencia, cargo")

    # --------------------------------------------------- información personal
    def informacion_personal(self, codigo: int | None, orden: str) -> list[dict]:
        consulta = sql.SQL("""
            SELECT v.codigo, v.nombre_completo, v.dependencia, v.cargo, v.fecha_ingreso, v.eps, v.pension, v.salario,
                   COALESCE((SELECT string_agg(n.tipo || ' ' || to_char(n.fecha_inicio, 'DD/MM/YYYY') || ' al ' ||
                             to_char(n.fecha_fin, 'DD/MM/YYYY') || ' (' || n.dias || ' d)', E'\\n' ORDER BY n.fecha_inicio)
                             FROM v_novedad_detalle n WHERE n.codigo = v.codigo), 'Sin novedades') AS novedades
            FROM v_empleado_detalle v {} ORDER BY v.nombre_completo {}, v.codigo""")
        if codigo is None:
            return self._db.fetch_all(consulta.format(sql.SQL(""), _dir(orden)))
        return self._db.fetch_all(consulta.format(sql.SQL("WHERE v.codigo = %s"), _dir(orden)), (codigo,))

    # ------------------------------------------------------ salud y pensión
    def frecuencia(self, vista: str, columna: str) -> list[dict]:
        permitidas = {("v_frecuencia_eps", "eps"), ("v_frecuencia_pension", "pension")}
        if (vista, columna) not in permitidas:
            raise ValueError("vista no permitida")
        return self._db.fetch_all(sql.SQL("SELECT {c} AS etiqueta, cantidad FROM {v} ORDER BY {c}").format(
            c=sql.Identifier(columna), v=sql.Identifier(vista)))

    def frecuencia_por_dependencia(self, columna: str) -> list[dict]:
        vista = {"eps": "v_frecuencia_eps_dependencia", "pension": "v_frecuencia_pension_dependencia"}[columna]
        return self._db.fetch_all(sql.SQL("SELECT dependencia, {c} AS etiqueta, cantidad FROM {v} ORDER BY dependencia, {c}").format(
            c=sql.Identifier(columna), v=sql.Identifier(vista)))

    def empleados_por_cargo_y(self, columna: str, orden: str) -> list[dict]:
        col = {"eps": "eps", "pension": "pension"}[columna]
        return self._db.fetch_all(sql.SQL("SELECT cargo, {c} AS grupo, codigo, nombre_completo FROM v_empleado_detalle "
                                          "ORDER BY cargo, {c}, nombre_completo {d}, codigo").format(c=sql.Identifier(col), d=_dir(orden)))

    # ------------------------------------------------------------ novedades
    def rango_novedades(self) -> tuple[date, date] | None:
        f = self._db.fetch_one("SELECT MIN(periodo) AS d, MAX(periodo) AS h FROM v_novedad_detalle")
        return (f["d"], f["h"]) if f and f["d"] else None

    def novedades(self, desde: date, hasta: date, orden: str) -> list[dict]:
        return self._db.fetch_all(sql.SQL("""SELECT codigo, nombre_completo, dependencia, cargo, tipo, fecha_inicio, fecha_fin, dias
              FROM v_novedad_detalle WHERE periodo BETWEEN %s AND %s ORDER BY nombre_completo {}, fecha_inicio""").format(_dir(orden)),
                                  (desde, hasta))

    def novedades_conteo(self, desde: date, hasta: date) -> list[dict]:
        return self._db.fetch_all("""SELECT dependencia, cargo, COUNT(DISTINCT codigo)::int AS empleados, COUNT(*)::int AS novedades
              FROM v_novedad_detalle WHERE periodo BETWEEN %s AND %s GROUP BY dependencia, cargo ORDER BY dependencia, cargo""",
                                  (desde, hasta))

    # --------------------------------------------------------- entretenimiento
    def generos(self) -> list[str]:
        return [f["nombre"] for f in self._db.fetch_all("SELECT nombre FROM genero ORDER BY nombre")]

    def peliculas_por_genero(self, desde: int, hasta: int, genero: str, orden: str) -> list[dict]:
        filtro, params = (sql.SQL(" AND genero = %s"), [desde, hasta, genero]) if genero else (sql.SQL(""), [desde, hasta])
        return self._db.fetch_all(sql.SQL("SELECT genero, titulo, anio_estreno FROM v_pelicula_por_genero "
                                          "WHERE anio_estreno BETWEEN %s AND %s{} ORDER BY genero, titulo {}, id_pelicula").format(filtro, _dir(orden)), params)

    def top_libros(self, n: int, orden: str, min_votos: int) -> list[dict]:
        return self._db.fetch_all(sql.SQL("""SELECT titulo, autores, anio_publicacion, calificacion_promedio, cantidad_calificaciones
              FROM v_libro_detalle WHERE cantidad_calificaciones >= %s
              ORDER BY calificacion_promedio DESC, cantidad_calificaciones DESC, titulo {}, id_libro LIMIT %s""").format(_dir(orden)),
                                  (min_votos, n))

    def libros_extremos_por_anio(self, desde: int, hasta: int, min_votos: int, mejores: bool, orden: str, tope: int = 5) -> list[dict]:
        sentido = sql.SQL("DESC") if mejores else sql.SQL("ASC")
        return self._db.fetch_all(sql.SQL("""
            WITH base AS (SELECT * FROM v_libro_detalle WHERE anio_publicacion BETWEEN %s AND %s AND cantidad_calificaciones >= %s),
            pos AS (SELECT *, ROW_NUMBER() OVER (PARTITION BY anio_publicacion
                                ORDER BY calificacion_promedio {s}, cantidad_calificaciones DESC, titulo, id_libro) AS puesto FROM base)
            SELECT anio_publicacion, puesto, titulo, autores, calificacion_promedio, cantidad_calificaciones
            FROM pos WHERE puesto <= %s ORDER BY anio_publicacion, calificacion_promedio {s}, titulo {d}""").format(s=sentido, d=_dir(orden)),
                                  (desde, hasta, min_votos, tope))

    def peliculas_con_n_generos(self, n: int, orden: str) -> list[dict]:
        return self._db.fetch_all(sql.SQL("SELECT titulo, anio_estreno, generos FROM v_pelicula_detalle "
                                          "WHERE num_generos = %s ORDER BY titulo {}, id_pelicula").format(_dir(orden)), (n,))

    def frecuencia_pelicula_genero(self) -> list[dict]:
        return self._db.fetch_all("SELECT genero, cantidad FROM v_frecuencia_pelicula_genero ORDER BY genero")

    def frecuencia_libros_anio(self, desde: int, hasta: int) -> list[dict]:
        return self._db.fetch_all("SELECT anio, cantidad FROM v_frecuencia_libro_anio WHERE anio BETWEEN %s AND %s ORDER BY anio", (desde, hasta))

    def rango_anios_libros(self) -> tuple[int, int]:
        f = self._db.fetch_one("SELECT MIN(anio) AS d, MAX(anio) AS h FROM v_frecuencia_libro_anio")
        return (f["d"] or 2000, f["h"] or 2000)
