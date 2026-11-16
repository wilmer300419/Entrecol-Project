"""Utilería de texto."""
from __future__ import annotations

import re
import unicodedata


def sin_tildes(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")


def normalizar_encabezado(texto) -> str:
    """'NÚMERO  DE DÍAS' -> 'numero de dias' (para reconocer columnas de Excel)."""
    return re.sub(r"\s+", " ", sin_tildes(str(texto or "")).strip().lower())


def limpiar(texto) -> str:
    return re.sub(r"\s+", " ", str(texto or "")).strip()


def separar_nombre(nombre_completo: str) -> tuple[str, str]:
    """Convención colombiana del archivo de nómina: APELLIDO1 APELLIDO2 NOMBRE1 [NOMBRE2].

    'AGUDELO ESCOBAR EDWAR DAVID' -> ('AGUDELO ESCOBAR', 'EDWAR DAVID')
    'GIRALDO BRICEÑO SANTIAGO'    -> ('GIRALDO BRICEÑO', 'SANTIAGO')
    """
    partes = limpiar(nombre_completo).split(" ")
    if len(partes) < 3:
        return (partes[0], " ".join(partes[1:]) or "-") if partes and partes[0] else ("-", "-")
    return " ".join(partes[:2]), " ".join(partes[2:])


def a_entero(valor, por_defecto: int | None = None) -> int | None:
    try:
        return int(float(str(valor).strip()))
    except (TypeError, ValueError):
        return por_defecto


def a_decimal(valor) -> float | None:
    try:
        return float(str(valor).strip().replace(",", "."))
    except (TypeError, ValueError):
        return None
