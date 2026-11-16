"""Utilería de fechas."""
from __future__ import annotations

import calendar
import re
from datetime import date, datetime


def formatear_fecha(valor: date | datetime | None) -> str:
    """DD/MM/AAAA (formato exigido por la guía)."""
    return valor.strftime("%d/%m/%Y") if valor else ""


def parsear_fecha(valor) -> date | None:
    """Acepta date, datetime, 20210311 (int/str), 2021-03-11, 11/03/2021 y M/D/YYYY de Books.json."""
    if valor is None or valor == "":
        return None
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    texto = str(valor).strip()
    if re.fullmatch(r"\d{8}", texto):
        return _seguro(int(texto[:4]), int(texto[4:6]), int(texto[6:]))
    if m := re.fullmatch(r"(\d{4})-(\d{1,2})-(\d{1,2})", texto):
        return _seguro(int(m[1]), int(m[2]), int(m[3]))
    if m := re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})", texto):
        a, b, anio = int(m[1]), int(m[2]), int(m[3])
        return _seguro(anio, a, b)
    return None


def _seguro(anio: int, mes: int, dia: int) -> date | None:
    try:
        return date(anio, mes, dia)
    except ValueError:
        return None


def parsear_mes_anio(texto: str) -> date | None:
    """'03/2022' -> date(2022, 3, 1)."""
    m = re.fullmatch(r"\s*(\d{1,2})\s*/\s*(\d{4})\s*", texto or "")
    return _seguro(int(m[2]), int(m[1]), 1) if m else None


def fin_de_mes(d: date) -> date:
    return d.replace(day=calendar.monthrange(d.year, d.month)[1])
