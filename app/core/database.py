"""Acceso a PostgreSQL mediante un pool de conexiones (psycopg 3).

Es la única clase que conoce el driver; el resto del sistema depende de sus
métodos (fetch_all / fetch_one / execute / transaccion), no del driver.
"""
from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator, Sequence

from psycopg import Connection
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool


class Database:
    def __init__(self, dsn: str, min_size: int = 1, max_size: int = 10):
        self._pool = ConnectionPool(dsn, min_size=min_size, max_size=max_size,
                                    kwargs={"row_factory": dict_row}, open=False)

    def abrir(self) -> None:
        self._pool.open(wait=True, timeout=15)

    def cerrar(self) -> None:
        self._pool.close()

    @contextmanager
    def transaccion(self) -> Iterator[Connection]:
        """Conexión con commit al salir y rollback ante cualquier excepción."""
        with self._pool.connection() as conn:
            yield conn

    def fetch_all(self, sql: Any, params: Sequence | dict | None = None) -> list[dict]:
        with self.transaccion() as conn:
            return conn.execute(sql, params).fetchall()

    def fetch_one(self, sql: Any, params: Sequence | dict | None = None) -> dict | None:
        with self.transaccion() as conn:
            return conn.execute(sql, params).fetchone()

    def execute(self, sql: Any, params: Sequence | dict | None = None) -> int:
        with self.transaccion() as conn:
            return conn.execute(sql, params).rowcount
