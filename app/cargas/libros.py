from __future__ import annotations

import json

from ..utils.fechas import parsear_fecha
from ..utils.textos import a_decimal, a_entero, limpiar
from .base import Cargador, ErrorCarga, ResultadoCarga

_ORDEN = ["bookID", "title", "authors", "average_rating", "isbn", "isbn13", "language_code",
          "num_pages", "ratings_count", "text_reviews_count", "publication_date", "publisher"]


def _es_numero(valor) -> bool:
    return a_decimal(valor) is not None


def alinear(registro: dict) -> list:
    """Repara filas cuyo campo 'authors' trae una coma sin escapar.

    En Books.json hay registros como ``"authors": "Sam Bass Warner"`` y
    ``"average_rating": " Jr./Sam B. Warner"``: el nombre del autor se partió en dos
    y todas las columnas siguientes quedaron corridas una posición a la derecha.
    """
    v = [registro.get(k, "") for k in _ORDEN + ["FIELD13"]]
    if not _es_numero(v[3]) and _es_numero(v[4]):
        v = v[:2] + [f"{v[2]},{v[3]}"] + v[4:]
    return v[:12]


class CargadorLibros(Cargador):
    clave, titulo, extensiones = "libros", "Libros (.json)", (".json",)

    def cargar(self, contenido: bytes, **_) -> ResultadoCarga:
        try:
            datos = json.loads(contenido.decode("utf-8-sig"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ErrorCarga("El archivo no es un JSON válido.") from exc
        if not isinstance(datos, list) or not all(isinstance(d, dict) for d in datos):
            raise ErrorCarga("Se esperaba una lista de objetos JSON (uno por libro).")
        res = ResultadoCarga("Libros")
        libros: dict[int, dict] = {}
        isbn13_vistos: set[str] = set()
        reparados = fechas_nulas = 0
        for n, reg in enumerate(datos, start=1):
            v = alinear(reg)
            if v != [reg.get(k, "") for k in _ORDEN]:
                reparados += 1
            id_libro, titulo = a_entero(v[0]), limpiar(v[1])
            rating = a_decimal(v[3])
            if not id_libro or id_libro <= 0 or not titulo or rating is None or not 0 <= rating <= 5:
                res.rechazados += 1
                res.advertir(f"Registro {n} (bookID={v[0]}): id, título o calificación inválidos.")
                continue
            isbn13 = limpiar(v[5])[:13] or None
            if isbn13 in isbn13_vistos:
                res.advertir(f"bookID={id_libro}: ISBN-13 repetido ({isbn13}); se guardó sin ISBN-13.")
                isbn13 = None
            if isbn13:
                isbn13_vistos.add(isbn13)
            fecha = parsear_fecha(v[10])
            fechas_nulas += fecha is None
            libros[id_libro] = {
                "id": id_libro, "titulo": titulo[:600],
                "autores": list(dict.fromkeys(a.strip()[:400] for a in str(v[2]).split("/") if a.strip())),
                "rating": round(rating, 2), "isbn": limpiar(v[4])[:10] or None, "isbn13": isbn13,
                "idioma": limpiar(v[6])[:10] or None, "paginas": max(0, a_entero(v[7], 0) or 0),
                "calificaciones": max(0, a_entero(v[8], 0) or 0), "resenas": max(0, a_entero(v[9], 0) or 0),
                "fecha": fecha, "editorial": limpiar(v[11])[:300] or None}
        if not libros:
            raise ErrorCarga("No se encontró ningún libro válido en el archivo.")
        ids = list(libros)
        autores = sorted({a for b in libros.values() for a in b["autores"]})
        editoriales = sorted({b["editorial"] for b in libros.values() if b["editorial"]})
        idiomas = sorted({b["idioma"] for b in libros.values() if b["idioma"]})
        with self._db.transaccion() as conn:
            existentes = {f["id_libro"] for f in conn.execute("SELECT id_libro FROM libro WHERE id_libro = ANY(%s)", (ids,)).fetchall()}
            conn.execute("INSERT INTO autor (nombre) SELECT unnest(%s::text[]) ON CONFLICT (nombre) DO NOTHING", (autores,))
            conn.execute("INSERT INTO editorial (nombre) SELECT unnest(%s::text[]) ON CONFLICT (nombre) DO NOTHING", (editoriales,))
            conn.execute("INSERT INTO idioma (codigo_idioma) SELECT unnest(%s::text[]) ON CONFLICT DO NOTHING", (idiomas,))
            id_autor = {f["nombre"]: f["id_autor"] for f in conn.execute("SELECT id_autor, nombre FROM autor WHERE nombre = ANY(%s)", (autores,)).fetchall()}
            id_editorial = {f["nombre"]: f["id_editorial"] for f in conn.execute("SELECT id_editorial, nombre FROM editorial WHERE nombre = ANY(%s)", (editoriales,)).fetchall()}
            with conn.cursor() as cur:
                cur.executemany(
                    """INSERT INTO libro (id_libro, titulo, isbn, isbn13, codigo_idioma, id_editorial, num_paginas,
                                          calificacion_promedio, cantidad_calificaciones, cantidad_resenas, fecha_publicacion)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                       ON CONFLICT (id_libro) DO UPDATE SET titulo=EXCLUDED.titulo, isbn=EXCLUDED.isbn, isbn13=EXCLUDED.isbn13,
                         codigo_idioma=EXCLUDED.codigo_idioma, id_editorial=EXCLUDED.id_editorial, num_paginas=EXCLUDED.num_paginas,
                         calificacion_promedio=EXCLUDED.calificacion_promedio, cantidad_calificaciones=EXCLUDED.cantidad_calificaciones,
                         cantidad_resenas=EXCLUDED.cantidad_resenas, fecha_publicacion=EXCLUDED.fecha_publicacion""",
                    [(b["id"], b["titulo"], b["isbn"], b["isbn13"], b["idioma"], id_editorial.get(b["editorial"]), b["paginas"],
                      b["rating"], b["calificaciones"], b["resenas"], b["fecha"]) for b in libros.values()])
                cur.execute("DELETE FROM libro_autor WHERE id_libro = ANY(%s)", (ids,))
                cur.executemany("INSERT INTO libro_autor (id_libro, id_autor, orden) VALUES (%s,%s,%s)",
                                [(b["id"], id_autor[a], i) for b in libros.values() for i, a in enumerate(b["autores"], start=1)])
            conn.execute("SELECT setval(pg_get_serial_sequence('libro','id_libro'), (SELECT MAX(id_libro) FROM libro))")
        res.actualizados = len(existentes)
        res.insertados = len(libros) - len(existentes)
        res.detalle.update({"autores distintos": len(autores), "editoriales": len(editoriales)})
        if reparados:
            res.detalle["filas reparadas (autor con coma)"] = reparados
        if fechas_nulas:
            res.advertir(f"{fechas_nulas} libro(s) con fecha de publicación inválida o vacía: se guardaron sin fecha.")
        return res
