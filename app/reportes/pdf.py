"""VISTA (MVC) en PDF: convierte un ``Informe`` en un documento con ReportLab."""
from __future__ import annotations

import math
from datetime import datetime
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.graphics.charts.barcharts import HorizontalBarChart, VerticalBarChart
from reportlab.graphics.charts.legends import Legend
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.shapes import Drawing, String
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from ..models.informe import Grafico, Informe, Tabla
from ..utils.formatos import celda

_FUENTES = Path(__file__).resolve().parent.parent / "static" / "fonts"
PALETA = ["#4f46e5", "#0ea5e9", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#14b8a6", "#f97316", "#64748b", "#ec4899", "#84cc16", "#06b6d4"]
COLOR_MARCA, COLOR_TEXTO = colors.HexColor("#3730a3"), colors.HexColor("#1b1f2a")
_registradas = False


def _registrar_fuentes() -> None:
    global _registradas
    if not _registradas:
        pdfmetrics.registerFont(TTFont("DejaVu", str(_FUENTES / "DejaVuSans.ttf")))
        pdfmetrics.registerFont(TTFont("DejaVu-Bold", str(_FUENTES / "DejaVuSans-Bold.ttf")))
        pdfmetrics.registerFontFamily("DejaVu", normal="DejaVu", bold="DejaVu-Bold", italic="DejaVu", boldItalic="DejaVu-Bold")
        _registradas = True


def _texto(valor) -> str:
    """Texto seguro para Paragraph: escapa XML y reemplaza glifos que la fuente no tiene."""
    glifos = pdfmetrics.getFont("DejaVu").face.charToGlyph
    return escape("".join(c if (ord(c) in glifos or c in "\n\t") else "?" for c in celda(valor))).replace("\n", "<br/>")


class _LienzoNumerado(canvas.Canvas):
    """Canvas en dos pasadas para poder escribir 'Página X de Y'."""
    encabezado = ("", "")

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self._paginas: list[dict] = []

    def showPage(self):
        self._paginas.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._paginas)
        for estado in self._paginas:
            self.__dict__.update(estado)
            ancho, alto = self._pagesize
            self.setFont("DejaVu", 7.5)
            self.setFillColor(colors.HexColor("#5b6275"))
            self.drawString(15 * mm, 10 * mm, self.encabezado[1])
            self.drawRightString(ancho - 15 * mm, 10 * mm, f"Página {self._pageNumber} de {total}")
            self.setStrokeColor(colors.HexColor("#d5d9e5"))
            self.line(15 * mm, alto - 14 * mm, ancho - 15 * mm, alto - 14 * mm)
            self.setFont("DejaVu-Bold", 8.5)
            self.setFillColor(COLOR_MARCA)
            self.drawString(15 * mm, alto - 11 * mm, "EntreCOL+  ·  Sistema de Información")
            self.setFont("DejaVu", 7.5)
            self.setFillColor(colors.HexColor("#5b6275"))
            self.drawRightString(ancho - 15 * mm, alto - 11 * mm, self.encabezado[0])
            super().showPage()
        super().save()


def _estilos() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()["Normal"]
    return {
        "titulo": ParagraphStyle("t", parent=base, fontName="DejaVu-Bold", fontSize=17, leading=21, textColor=COLOR_MARCA, spaceAfter=2),
        "sub": ParagraphStyle("s", parent=base, fontName="DejaVu", fontSize=10, leading=13, textColor=colors.HexColor("#3c4256"), spaceAfter=6),
        "h2": ParagraphStyle("h", parent=base, fontName="DejaVu-Bold", fontSize=10.5, leading=13, textColor=COLOR_TEXTO, spaceBefore=10, spaceAfter=4),
        "celda": ParagraphStyle("c", parent=base, fontName="DejaVu", fontSize=7.8, leading=9.6, textColor=COLOR_TEXTO),
        "cab": ParagraphStyle("ch", parent=base, fontName="DejaVu-Bold", fontSize=7.8, leading=9.6, textColor=colors.white),
        "nota": ParagraphStyle("n", parent=base, fontName="DejaVu", fontSize=7.5, leading=9.5, textColor=colors.HexColor("#8a4b00"), spaceBefore=2),
    }


def _tabla(t: Tabla, ancho: float, est: dict) -> list:
    n = len(t.columnas)
    muestras = [[len(str(celda(c))) for c in fila] for fila in t.filas[:200]] or [[8] * n]
    pesos = [max(6, min(60, max(m[i] for m in muestras), len(t.columnas[i]) + 2)) for i in range(n)]
    anchos = [ancho * p / sum(pesos) for p in pesos]
    datos = [[Paragraph(_texto(c), est["cab"]) for c in t.columnas]]
    datos += [[Paragraph(_texto(c), est["celda"]) for c in fila] for fila in t.filas] or [[Paragraph("Sin resultados para los filtros elegidos.", est["celda"])] + [""] * (n - 1)]
    tbl = Table(datos, colWidths=anchos, repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_MARCA), ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f3f4fb")]),
        ("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.HexColor("#d5d9e5")),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4)]))
    salida: list = [Paragraph(_texto(t.titulo), est["h2"]), tbl]
    if t.nota:
        salida.append(Paragraph(_texto(t.nota), est["nota"]))
    return salida


def _grafico(g: Grafico, ancho: float, est: dict) -> list:
    datos = [(s.nombre, s.valores) for s in g.series]
    if not g.etiquetas or not any(v for _, vs in datos for v in vs):            # sin datos: no se dibuja (evita errores de ReportLab)
        return [Paragraph(_texto(g.titulo), est["h2"]), Paragraph("Sin datos para graficar.", est["celda"]), Spacer(1, 6)]
    if g.tipo == "pie":
        pares = [(e, v) for e, v in zip(g.etiquetas, g.series[0].valores) if v > 0]
        d = Drawing(ancho, 190)
        pie = Pie()
        pie.x, pie.y, pie.width, pie.height = 15, 15, 160, 160
        pie.data, pie.labels = [v for _, v in pares], None
        pie.slices.strokeColor, pie.slices.strokeWidth = colors.white, 1
        for i in range(len(pares)):
            pie.slices[i].fillColor = colors.HexColor(PALETA[i % len(PALETA)])
        d.add(pie)
        total = sum(v for _, v in pares) or 1
        leyenda = Legend()
        leyenda.x, leyenda.y, leyenda.fontName, leyenda.fontSize, leyenda.dy, leyenda.dx = 200, 150, "DejaVu", 8.5, 8, 8
        leyenda.alignment, leyenda.columnMaximum, leyenda.deltay = "right", 10, 13
        leyenda.colorNamePairs = [(colors.HexColor(PALETA[i % len(PALETA)]), _texto(f"{e}: {v:g} ({v / total:.0%})").replace("<br/>", " "))
                                  for i, (e, v) in enumerate(pares)]
        d.add(leyenda)
    else:
        horizontal = g.tipo == "barh"
        n = len(g.etiquetas)
        alto = max(190, 30 + n * 17) if horizontal else 210
        d = Drawing(ancho, alto + (0 if len(datos) < 2 else 14))
        grafico = HorizontalBarChart() if horizontal else VerticalBarChart()
        margen_izq = min(ancho * 0.5, 14 + 4.3 * max((len(e) for e in g.etiquetas), default=6)) if horizontal else 32
        grafico.x, grafico.y = margen_izq, 22 + (14 if len(datos) > 1 else 0)
        grafico.width, grafico.height = ancho - margen_izq - 24, alto - 40 - (14 if len(datos) > 1 else 0)
        grafico.data = [v for _, v in reversed(datos)] if horizontal else [v for _, v in datos]
        etiquetas = list(reversed(g.etiquetas)) if horizontal else g.etiquetas
        if horizontal:
            grafico.data = [list(reversed(s.valores)) for s in g.series]
        grafico.categoryAxis.categoryNames = [_texto(e).replace("<br/>", " ") for e in etiquetas]
        grafico.categoryAxis.labels.fontName = grafico.valueAxis.labels.fontName = "DejaVu"
        grafico.categoryAxis.labels.fontSize = grafico.valueAxis.labels.fontSize = 7.5
        if not horizontal and n > 5:
            grafico.categoryAxis.labels.angle, grafico.categoryAxis.labels.boxAnchor = 25, "ne"
            grafico.categoryAxis.labels.dy = -2
        maximo = max((max(s.valores, default=0) for s in g.series), default=0)
        paso = max(1, math.ceil(maximo / 6))
        grafico.valueAxis.valueMin, grafico.valueAxis.valueMax, grafico.valueAxis.valueStep = 0, paso * math.ceil((maximo + 0.01) / paso), paso
        grafico.valueAxis.labelTextFormat = "%d"
        grafico.valueAxis.visibleGrid, grafico.valueAxis.gridStrokeColor = True, colors.HexColor("#e3e6ee")
        grafico.groupSpacing, grafico.barSpacing = 6, 1
        if len(datos) == 1:
            grafico.barLabelFormat, grafico.barLabels.fontSize, grafico.barLabels.fontName = "%d", 7, "DejaVu"
            grafico.barLabels.nudge = 7 if not horizontal else 8
        for i in range(len(datos)):
            grafico.bars[i].fillColor = colors.HexColor(PALETA[i % len(PALETA)])
            grafico.bars[i].strokeColor = colors.white
        d.add(grafico)
        if len(datos) > 1:
            leyenda = Legend()
            leyenda.x, leyenda.y, leyenda.fontName, leyenda.fontSize, leyenda.alignment = 20, alto + 8, "DejaVu", 7.5, "right"
            leyenda.columnMaximum, leyenda.dx, leyenda.dy, leyenda.deltax = 1, 7, 7, 80
            leyenda.colorNamePairs = [(colors.HexColor(PALETA[i % len(PALETA)]), _texto(nombre).replace("<br/>", " ")) for i, (nombre, _) in enumerate(datos)]
            d.add(leyenda)
    return [KeepTogether([Paragraph(_texto(g.titulo), est["h2"]), d, Spacer(1, 4)])]


def generar_pdf(informe: Informe, usuario: str = "") -> bytes:
    _registrar_fuentes()
    ancha = informe.horizontal or any(isinstance(b, Tabla) and len(b.columnas) >= 6 for b in informe.bloques)
    pagina = landscape(A4) if ancha else A4
    ancho_util = pagina[0] - 30 * mm
    est = _estilos()
    historia: list = [Paragraph(_texto(informe.titulo), est["titulo"])]
    if informe.subtitulo:
        historia.append(Paragraph(_texto(informe.subtitulo), est["sub"]))
    if informe.parametros:
        par = Table([[Paragraph(f"<b>{_texto(k)}:</b> {_texto(v)}", est["celda"]) for k, v in informe.parametros[i:i + 3]]
                     for i in range(0, len(informe.parametros), 3)], hAlign="LEFT")
        par.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f3f4fb")), ("BOX", (0, 0), (-1, -1), 0.3, colors.HexColor("#d5d9e5")),
                                 ("LEFTPADDING", (0, 0), (-1, -1), 6), ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
        historia += [par, Spacer(1, 4)]
    for bloque in informe.bloques:
        historia += _grafico(bloque, ancho_util, est) if isinstance(bloque, Grafico) else _tabla(bloque, ancho_util, est)
    _LienzoNumerado.encabezado = (datetime.now().strftime("%d/%m/%Y %H:%M"), f"Generado por: {usuario}" if usuario else "")
    buffer = BytesIO()
    SimpleDocTemplate(buffer, pagesize=pagina, leftMargin=15 * mm, rightMargin=15 * mm, topMargin=19 * mm, bottomMargin=17 * mm,
                      title=informe.titulo, author="EntreCOL+").build(historia, canvasmaker=_LienzoNumerado)
    return buffer.getvalue()
