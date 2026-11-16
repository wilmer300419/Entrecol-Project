"""Repositorio CRUD genérico dirigido por metadatos (consultas dinámicas y seguras).

Los identificadores (tablas/columnas) vienen SIEMPRE del catálogo y se componen con
``psycopg.sql.Identifier``; los valores viajan siempre como parámetros.
"""
from __future__ import annotations

from psycopg import sql

from ..core.database import Database
from ..models.meta import Campo, Entidad, RelMuchos, RelRef


class RepositorioCrud:
    def __init__(self, db: Database, entidad: Entidad):
        self._db, self._e = db, entidad

    # ------------------------------------------------------------- lectura
    def listar(self, q: str = "", filtros: dict[str, str] | None = None, orden: str = "", direccion: str = "asc",
               limite: int = 15, desplazamiento: int = 0) -> tuple[list[dict], int]:
        e = self._e
        visibles = [c for c, _ in e.columnas]
        base = sql.SQL("FROM ({}) AS t").format(sql.SQL(e.lista_sql))
        condiciones, params = [], []
        if q:
            condiciones.append(sql.SQL("(") + sql.SQL(" OR ").join(
                sql.SQL("{}::text ILIKE %s").format(sql.Identifier(c)) for c in e.buscar) + sql.SQL(")"))
            params += [f"%{q}%"] * len(e.buscar)
        for col, valor in (filtros or {}).items():          # filtros dinámicos por columna (lista blanca)
            if col in visibles and valor:
                condiciones.append(sql.SQL("{}::text ILIKE %s").format(sql.Identifier(col)))
                params.append(f"%{valor}%")
        donde = sql.SQL(" WHERE ") + sql.SQL(" AND ").join(condiciones) if condiciones else sql.SQL("")
        col_orden = orden if orden in visibles or orden == e.pk else e.orden
        dir_sql = sql.SQL("DESC") if direccion == "desc" else sql.SQL("ASC")
        total = self._db.fetch_one(sql.SQL("SELECT COUNT(*) AS n ") + base + donde, params)["n"]
        filas = self._db.fetch_all(
            sql.SQL("SELECT * ") + base + donde + sql.SQL(" ORDER BY {} {} NULLS LAST, {} LIMIT %s OFFSET %s").format(
                sql.Identifier(col_orden), dir_sql, sql.Identifier(e.pk)), [*params, limite, desplazamiento])
        return filas, total

    def obtener(self, pk) -> dict | None:
        e = self._e
        extras = [sql.SQL("{} AS {}").format(sql.SQL(c.lectura_sql), sql.Identifier(c.nombre))
                  for c in e.campos if c.lectura_sql]
        columnas = sql.SQL("t.*") + (sql.SQL(", ") + sql.SQL(", ").join(extras) if extras else sql.SQL(""))
        return self._db.fetch_one(sql.SQL("SELECT {} FROM {} t WHERE t.{} = %s").format(
            columnas, sql.Identifier(e.tabla), sql.Identifier(e.pk)), (pk,))

    def opciones(self, campo: Campo) -> list[tuple]:
        return [(f["valor"], f["etiqueta"]) for f in self._db.fetch_all(sql.SQL(campo.opciones_sql))]

    # ------------------------------------------------------------ escritura
    def crear(self, datos: dict):
        e = self._e
        with self._db.transaccion() as conn:
            columnas, valores = [], []
            for c in e.campos:
                if c.es_virtual:
                    continue
                if c.nombre == e.pk and e.pk_auto:
                    continue
                columnas.append(sql.Identifier(c.col))
                valores.append(self._valor_columna(conn, c, datos.get(c.nombre)))
            consulta = sql.SQL("INSERT INTO {} ({}) VALUES ({}) RETURNING {}").format(
                sql.Identifier(e.tabla), sql.SQL(", ").join(columnas), sql.SQL(", ").join(sql.Placeholder() * len(valores)),
                sql.Identifier(e.pk))
            pk = conn.execute(consulta, valores).fetchone()[e.pk]
            self._sincronizar_relaciones(conn, pk, datos)
        return pk

    def actualizar(self, pk, datos: dict) -> bool:
        e = self._e
        with self._db.transaccion() as conn:
            asignaciones, valores = [], []
            for c in e.campos:
                if c.es_virtual or c.inmutable:
                    continue
                asignaciones.append(sql.SQL("{} = %s").format(sql.Identifier(c.col)))
                valores.append(self._valor_columna(conn, c, datos.get(c.nombre)))
            n = conn.execute(sql.SQL("UPDATE {} SET {} WHERE {} = %s").format(
                sql.Identifier(e.tabla), sql.SQL(", ").join(asignaciones), sql.Identifier(e.pk)), [*valores, pk]).rowcount
            if n:
                self._sincronizar_relaciones(conn, pk, datos)
        return bool(n)

    def eliminar(self, pk) -> bool:
        e = self._e
        return self._db.execute(sql.SQL("DELETE FROM {} WHERE {} = %s").format(
            sql.Identifier(e.tabla), sql.Identifier(e.pk)), (pk,)) > 0

    # ------------------------------------------------------------- internos
    def _valor_columna(self, conn, c: Campo, valor):
        if c.tipo == "ref_texto":
            return self._resolver_por_nombre(conn, c.rel, valor)
        return valor

    @staticmethod
    def _resolver_por_nombre(conn, rel: RelRef | RelMuchos, nombre: str | None):
        if not nombre:
            return None
        return conn.execute(sql.SQL("INSERT INTO {t} ({n}) VALUES (%s) ON CONFLICT ({n}) DO UPDATE SET {n} = EXCLUDED.{n} RETURNING {pk}").format(
            t=sql.Identifier(rel.tabla_remota), n=sql.Identifier(rel.col_nombre), pk=sql.Identifier(rel.pk_remota)),
            (nombre,)).fetchone()[rel.pk_remota]

    def _sincronizar_relaciones(self, conn, pk, datos: dict) -> None:
        for c in self._e.campos:
            if not c.es_virtual:
                continue
            r: RelMuchos = c.rel
            conn.execute(sql.SQL("DELETE FROM {} WHERE {} = %s").format(sql.Identifier(r.tabla_enlace), sql.Identifier(r.col_local)), (pk,))
            ids: list = []
            for item in datos.get(c.nombre) or []:
                id_remoto = item if c.tipo == "multi" else self._resolver_por_nombre(conn, r, item)
                if id_remoto not in ids:
                    ids.append(id_remoto)
            for orden, id_remoto in enumerate(ids, start=1):
                cols = [r.col_local, r.col_remota] + (["orden"] if r.con_orden else [])
                vals = [pk, id_remoto] + ([orden] if r.con_orden else [])
                conn.execute(sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
                    sql.Identifier(r.tabla_enlace), sql.SQL(", ").join(map(sql.Identifier, cols)),
                    sql.SQL(", ").join(sql.Placeholder() * len(vals))), vals)
