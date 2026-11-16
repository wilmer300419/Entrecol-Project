from __future__ import annotations

import re

from .base import Cargador, ErrorCarga, ResultadoCarga

_ANIO = re.compile(r"\s*\((\d{4})\)\s*$")


def decodificar(contenido: bytes) -> str:
    try:
        return contenido.decode("utf-8-sig")
    except UnicodeDecodeError:
        return contenido.decode("latin-1")


def parsear_linea(linea: str) -> tuple[int, str, int | None, list[str]]:
    """'1::Toy Story (1995)::Adventure|Animation' -> (1, 'Toy Story', 1995, [...])"""
    partes = linea.rstrip("\r\n").split("::")
    if len(partes) != 3:
        raise ValueError("se esperaban 3 campos separados por '::'")
    id_pelicula = int(partes[0])
    titulo = partes[1].strip()
    anio = None
    if m := _ANIO.search(titulo):
        anio, titulo = int(m[1]), titulo[:m.start()].strip()
    if not titulo:
        raise ValueError("título vacío")
    generos = [g.strip() for g in partes[2].split("|") if g.strip() and g.strip() != "(no genres listed)"]
    return id_pelicula, titulo[:300], anio, list(dict.fromkeys(generos))


class CargadorPeliculas(Cargador):
    clave, titulo, extensiones = "peliculas", "Películas (.dat)", (".dat", ".txt")

    def cargar(self, contenido: bytes, **_) -> ResultadoCarga:
        texto = decodificar(contenido)
        if "::" not in texto:
            raise ErrorCarga("El archivo no tiene el formato esperado (id::título (año)::género|género).")
        res = ResultadoCarga("Películas")
        filas: dict[int, tuple] = {}
        for n, linea in enumerate(texto.splitlines(), start=1):
            if not linea.strip():
                continue
            try:
                id_p, titulo, anio, generos = parsear_linea(linea)
                if anio is not None and not 1870 <= anio <= 2100:
                    anio = None
                filas[id_p] = (id_p, titulo, anio, generos)
            except ValueError as exc:
                res.rechazados += 1
                res.advertir(f"Línea {n}: {exc}.")
        if not filas:
            raise ErrorCarga("No se encontró ninguna película válida en el archivo.")
        ids = list(filas)
        nombres = sorted({g for _, _, _, gs in filas.values() for g in gs})
        with self._db.transaccion() as conn:
            existentes = {f["id_pelicula"] for f in conn.execute(
                "SELECT id_pelicula FROM pelicula WHERE id_pelicula = ANY(%s)", (ids,)).fetchall()}
            conn.execute("INSERT INTO genero (nombre) SELECT unnest(%s::text[]) ON CONFLICT (nombre) DO NOTHING", (nombres,))
            id_genero = {f["nombre"]: f["id_genero"] for f in conn.execute(
                "SELECT id_genero, nombre FROM genero WHERE nombre = ANY(%s)", (nombres,)).fetchall()}
            with conn.cursor() as cur:
                cur.executemany(
                    """INSERT INTO pelicula (id_pelicula, titulo, anio_estreno) VALUES (%s,%s,%s)
                       ON CONFLICT (id_pelicula) DO UPDATE SET titulo = EXCLUDED.titulo, anio_estreno = EXCLUDED.anio_estreno""",
                    [(i, t, a) for i, t, a, _ in filas.values()])
                cur.execute("DELETE FROM pelicula_genero WHERE id_pelicula = ANY(%s)", (ids,))
                cur.executemany("INSERT INTO pelicula_genero (id_pelicula, id_genero) VALUES (%s,%s)",
                                [(i, id_genero[g]) for i, _, _, gs in filas.values() for g in gs])
            conn.execute("SELECT setval(pg_get_serial_sequence('pelicula','id_pelicula'), (SELECT MAX(id_pelicula) FROM pelicula))")
        res.actualizados = len(existentes)
        res.insertados = len(filas) - len(existentes)
        res.detalle["géneros distintos"] = len(nombres)
        return res
