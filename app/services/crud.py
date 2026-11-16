"""Servicio CRUD: validación/conversión de formularios + reglas de negocio + auditoría."""
from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Mapping

from psycopg import errors as pgerr

from Seguridad.repositorio import RepositorioAuditoria

from ..core.database import Database
from ..models.meta import Campo, Entidad
from ..repositories.crud import RepositorioCrud
from ..utils.fechas import parsear_fecha


class ErrorDeNegocio(Exception):
    """Mensaje seguro para mostrar al usuario."""


class ServicioCrud:
    def __init__(self, db: Database, auditoria: RepositorioAuditoria):
        self._db, self._auditoria = db, auditoria

    def repo(self, e: Entidad) -> RepositorioCrud:
        return RepositorioCrud(self._db, e)

    # ----------------------------------------------------------- validación
    def validar(self, e: Entidad, form: Mapping, getlist=None, editando: bool = False) -> tuple[dict, dict[str, str]]:
        datos: dict = {}
        errores: dict[str, str] = {}
        for c in e.campos:
            if editando and c.inmutable:
                continue
            try:
                datos[c.nombre] = self._convertir(c, form, getlist)
            except ValueError as exc:
                errores[c.nombre] = str(exc)
        if not errores:
            for validador in e.validadores:
                errores.update(validador(datos))
        return datos, errores

    @staticmethod
    def _convertir(c: Campo, form: Mapping, getlist):
        if c.tipo == "multi":
            return [int(v) for v in (getlist(c.nombre) if getlist else []) if str(v).strip().isdigit()]
        bruto = (form.get(c.nombre) or "").strip()
        if c.tipo == "lista_texto":
            return [p.strip() for p in bruto.split("/") if p.strip()][:20]
        if not bruto:
            if c.requerido:
                raise ValueError("Este campo es obligatorio.")
            return None
        if c.max_len and len(bruto) > c.max_len:
            raise ValueError(f"Máximo {c.max_len} caracteres.")
        if c.tipo in ("texto", "ref_texto"):
            return bruto
        if c.tipo == "fk":
            return bruto if c.valor_texto else _entero(bruto)
        if c.tipo == "entero":
            valor: int | Decimal = _entero(bruto)
        elif c.tipo == "decimal":
            try:
                valor = Decimal(bruto.replace(",", "."))
            except InvalidOperation:
                raise ValueError("Ingrese un número válido.")
        elif c.tipo == "fecha":
            d = parsear_fecha(bruto)
            if d is None:
                raise ValueError("Ingrese una fecha válida.")
            return d
        else:
            return bruto
        if c.minimo is not None and valor < c.minimo:
            raise ValueError(f"El valor mínimo es {c.minimo:g}.")
        if c.maximo is not None and valor > c.maximo:
            raise ValueError(f"El valor máximo es {c.maximo:g}.")
        return valor

    # ------------------------------------------------------------ operaciones
    def crear(self, e: Entidad, datos: dict, usuario, ip: str | None) -> object:
        pk = self._proteger(lambda: self.repo(e).crear(datos), e)
        self._auditoria.registrar(usuario.id, usuario.nombre_usuario, "CREAR", e.slug, f"{e.pk}={pk}", ip)
        return pk

    def actualizar(self, e: Entidad, pk, datos: dict, usuario, ip: str | None) -> None:
        if not self._proteger(lambda: self.repo(e).actualizar(pk, datos), e):
            raise ErrorDeNegocio("El registro ya no existe.")
        self._auditoria.registrar(usuario.id, usuario.nombre_usuario, "ACTUALIZAR", e.slug, f"{e.pk}={pk}", ip)

    def eliminar(self, e: Entidad, pk, usuario, ip: str | None) -> None:
        if not self._proteger(lambda: self.repo(e).eliminar(pk), e):
            raise ErrorDeNegocio("El registro ya no existe.")
        self._auditoria.registrar(usuario.id, usuario.nombre_usuario, "ELIMINAR", e.slug, f"{e.pk}={pk}", ip)

    @staticmethod
    def _proteger(accion, e: Entidad):
        try:
            return accion()
        except pgerr.UniqueViolation:
            raise ErrorDeNegocio(f"Ya existe un registro de {e.singular} con esos datos.")
        except pgerr.ForeignKeyViolation:
            raise ErrorDeNegocio("No se puede completar: el registro está relacionado con otros datos "
                                 "(o hace referencia a un valor que no existe).")
        except pgerr.CheckViolation:
            raise ErrorDeNegocio("Algún valor no cumple las reglas de validación de la base de datos.")
        except pgerr.NumericValueOutOfRange:
            raise ErrorDeNegocio("Un número excede el tamaño permitido.")


def _entero(texto: str) -> int:
    try:
        return int(texto)
    except ValueError:
        raise ValueError("Ingrese un número entero.")
