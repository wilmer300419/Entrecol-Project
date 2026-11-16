from __future__ import annotations

from ..repositories.reportes import RepositorioReportes
from .base import Reporte
from .entretenimiento import ReporteEntretenimiento
from .nomina import ReporteNomina, ReportePersonal
from .salud_novedades import ReporteNovedades, ReporteSaludPension

CLASES_REPORTE: tuple[type[Reporte], ...] = (ReporteNomina, ReportePersonal, ReporteSaludPension, ReporteNovedades, ReporteEntretenimiento)


def construir_reportes(repo: RepositorioReportes, filas_max: int) -> dict[str, Reporte]:
    return {c.slug: c(repo, filas_max) for c in CLASES_REPORTE}
