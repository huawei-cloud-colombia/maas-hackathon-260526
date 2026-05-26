"""Generador de reporte PDF estilizado con logo vectorial de Universidad Nova Andes."""
from __future__ import annotations

from datetime import date
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

UNIVERSIDAD = "Universidad Nova Andes"
SUBTITULO = "Oficina de Relaciones Internacionales"

PRIMARY = colors.HexColor("#7C5CFF")
PRIMARY_SOFT = colors.HexColor("#A38BFF")
ACCENT = colors.HexColor("#22D3EE")
INK = colors.HexColor("#0B1020")
INK_SOFT = colors.HexColor("#3A4170")
MUTED = colors.HexColor("#5B6BA0")
OK = colors.HexColor("#15803D")
WARN = colors.HexColor("#B45309")
BG_SOFT = colors.HexColor("#F5F7FF")
BORDER = colors.HexColor("#E2E6F4")


def _dibujar_logo(c: canvas.Canvas, x: float, y: float, escala: float = 1.0) -> None:
    """Dibuja el logo Nova Andes (réplica del SVG) usando primitivas reportlab."""
    s = escala
    # Tres picos
    c.saveState()
    c.translate(x, y)
    # pico izquierdo
    p = c.beginPath()
    p.moveTo(0 * s, 0 * s)
    p.lineTo(18 * s, 42 * s)
    p.lineTo(36 * s, 0 * s)
    p.close()
    c.setFillColor(PRIMARY_SOFT)
    c.setFillAlpha(0.85)
    c.drawPath(p, fill=1, stroke=0)
    # pico central
    p2 = c.beginPath()
    p2.moveTo(12 * s, 0)
    p2.lineTo(34 * s, 54 * s)
    p2.lineTo(56 * s, 0)
    p2.close()
    c.setFillColor(PRIMARY)
    c.setFillAlpha(1.0)
    c.drawPath(p2, fill=1, stroke=0)
    # pico derecho
    p3 = c.beginPath()
    p3.moveTo(30 * s, 0)
    p3.lineTo(48 * s, 38 * s)
    p3.lineTo(64 * s, 0)
    p3.close()
    c.setFillColor(PRIMARY_SOFT)
    c.setFillAlpha(0.65)
    c.drawPath(p3, fill=1, stroke=0)
    # nieve del pico central
    p4 = c.beginPath()
    p4.moveTo(28 * s, 42 * s)
    p4.lineTo(34 * s, 54 * s)
    p4.lineTo(40 * s, 42 * s)
    p4.lineTo(36 * s, 38 * s)
    p4.lineTo(32 * s, 38 * s)
    p4.close()
    c.setFillColor(colors.HexColor("#F5F7FF"))
    c.setFillAlpha(1.0)
    c.drawPath(p4, fill=1, stroke=0)
    # estrella sobre el pico (halo + estrella)
    c.setFillColor(ACCENT)
    c.setFillAlpha(0.25)
    c.circle(34 * s, 64 * s, 6.5 * s, fill=1, stroke=0)
    c.setFillAlpha(1.0)
    star = c.beginPath()
    cx, cy = 34 * s, 64 * s
    puntos = [
        (0, 4), (1.2, 1.2), (4, 1.2), (1.8, -0.6),
        (2.6, -3.4), (0, -1.8), (-2.6, -3.4), (-1.8, -0.6),
        (-4, 1.2), (-1.2, 1.2),
    ]
    star.moveTo(cx + puntos[0][0] * s, cy + puntos[0][1] * s)
    for px, py in puntos[1:]:
        star.lineTo(cx + px * s, cy + py * s)
    star.close()
    c.drawPath(star, fill=1, stroke=0)
    # línea base
    c.setStrokeColor(PRIMARY)
    c.setLineWidth(1.6 * s)
    c.setStrokeAlpha(0.55)
    c.line(-4 * s, -2 * s, 68 * s, -2 * s)
    c.setStrokeAlpha(1.0)
    c.restoreState()


def _header(c: canvas.Canvas, width: float, height: float, fecha: date) -> None:
    # Banda superior
    c.setFillColor(BG_SOFT)
    c.rect(0, height - 36 * mm, width, 36 * mm, stroke=0, fill=1)
    # Logo
    _dibujar_logo(c, 18 * mm, height - 28 * mm, escala=0.32)
    # Texto del logotipo
    c.setFont("Helvetica-Bold", 16)
    c.setFillColor(INK)
    c.drawString(46 * mm, height - 16 * mm, "Universidad")
    c.setFont("Helvetica-Bold", 18)
    c.setFillColor(PRIMARY)
    c.drawString(46 * mm, height - 22 * mm, "Nova")
    c.setFillColor(ACCENT)
    c.drawString(46 * mm + c.stringWidth("Nova ", "Helvetica-Bold", 18), height - 22 * mm, " Andes")
    c.setFont("Helvetica", 7)
    c.setFillColor(MUTED)
    c.drawString(46 * mm, height - 27 * mm, "OFICINA DE RELACIONES INTERNACIONALES")

    # Sello a la derecha
    c.setStrokeColor(PRIMARY)
    c.setLineWidth(0.8)
    c.roundRect(width - 70 * mm, height - 27 * mm, 52 * mm, 14 * mm, 3 * mm, stroke=1, fill=0)
    c.setFont("Helvetica-Bold", 7)
    c.setFillColor(PRIMARY)
    c.drawString(width - 67 * mm, height - 17 * mm, "REPORTE OFICIAL")
    c.setFont("Helvetica", 7)
    c.setFillColor(INK_SOFT)
    c.drawString(width - 67 * mm, height - 21 * mm, f"Fecha: {fecha.isoformat()}")
    c.drawString(width - 67 * mm, height - 25 * mm, "Sistema MaaS · DeepSeek-V4-Flash")

    # Línea divisoria
    c.setStrokeColor(PRIMARY)
    c.setLineWidth(1.2)
    c.line(18 * mm, height - 38 * mm, width - 18 * mm, height - 38 * mm)


def _footer(c: canvas.Canvas, width: float, page_num: int) -> None:
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 7)
    c.drawString(18 * mm, 12 * mm, "Universidad Nova Andes · Oficina de Relaciones Internacionales")
    c.drawRightString(width - 18 * mm, 12 * mm, f"Página {page_num}")
    c.setStrokeColor(BORDER)
    c.setLineWidth(0.4)
    c.line(18 * mm, 15 * mm, width - 18 * mm, 15 * mm)


def _wrap(text: str, c: canvas.Canvas, font: str, size: float, max_width: float) -> list[str]:
    palabras = text.split()
    lineas: list[str] = []
    actual = ""
    for w in palabras:
        prueba = (actual + " " + w).strip()
        if c.stringWidth(prueba, font, size) <= max_width:
            actual = prueba
        else:
            if actual:
                lineas.append(actual)
            actual = w
    if actual:
        lineas.append(actual)
    return lineas


class PDFBuilder:
    def __init__(self, path: Path, fecha: date | None = None):
        self.path = path
        self.fecha = fecha or date.today()
        self.c = canvas.Canvas(str(path), pagesize=A4)
        self.width, self.height = A4
        self.page_num = 1
        self.y = self.height - 44 * mm

    def _check_break(self, needed: float) -> None:
        if self.y - needed < 24 * mm:
            _footer(self.c, self.width, self.page_num)
            self.c.showPage()
            self.page_num += 1
            _header(self.c, self.width, self.height, self.fecha)
            self.y = self.height - 44 * mm

    def empezar(self) -> None:
        _header(self.c, self.width, self.height, self.fecha)
        # Título principal
        self.c.setFont("Helvetica-Bold", 22)
        self.c.setFillColor(INK)
        self.c.drawString(18 * mm, self.y, "Recomendaciones de Becas")
        self.y -= 8 * mm
        self.c.setFont("Helvetica", 10)
        self.c.setFillColor(INK_SOFT)
        self.c.drawString(
            18 * mm,
            self.y,
            "Sistema personalizado con IA · Filtros deterministas + Huawei MaaS",
        )
        self.y -= 10 * mm

    def resumen(self, n_estudiantes: int, n_becas: int) -> None:
        self.c.setFillColor(BG_SOFT)
        self.c.roundRect(18 * mm, self.y - 14 * mm, self.width - 36 * mm, 14 * mm, 2 * mm, stroke=0, fill=1)
        self.c.setFont("Helvetica-Bold", 10)
        self.c.setFillColor(PRIMARY)
        self.c.drawString(22 * mm, self.y - 6 * mm, "RESUMEN")
        self.c.setFont("Helvetica", 10)
        self.c.setFillColor(INK_SOFT)
        self.c.drawString(
            22 * mm,
            self.y - 11 * mm,
            f"{n_estudiantes} estudiantes analizados   ·   {n_becas} becas en catálogo   ·   Top 3 por estudiante",
        )
        self.y -= 22 * mm

    def estudiante(self, est: dict) -> None:
        self._check_break(30 * mm)
        # Tarjeta de estudiante
        self.c.setFillColor(PRIMARY)
        self.c.roundRect(18 * mm, self.y - 22 * mm, self.width - 36 * mm, 22 * mm, 3 * mm, stroke=0, fill=1)
        # Avatar
        initials = "".join(p[0] for p in est["nombre"].split()[:2]).upper()
        self.c.setFillColor(colors.white)
        self.c.setFillAlpha(0.18)
        self.c.circle(28 * mm, self.y - 11 * mm, 7 * mm, stroke=0, fill=1)
        self.c.setFillAlpha(1.0)
        self.c.setFont("Helvetica-Bold", 12)
        self.c.setFillColor(colors.white)
        self.c.drawCentredString(28 * mm, self.y - 13 * mm, initials)

        self.c.setFont("Helvetica-Bold", 14)
        self.c.drawString(40 * mm, self.y - 8 * mm, est["nombre"])
        self.c.setFont("Helvetica", 9)
        self.c.setFillColor(colors.HexColor("#E0E5FF"))
        self.c.drawString(
            40 * mm,
            self.y - 13 * mm,
            f"{est['carrera']}   ·   GPA {est['gpa']}   ·   Situación EC: {est['situacion_economica']}",
        )
        self.c.drawString(40 * mm, self.y - 18 * mm, f"Idiomas: {est['idiomas']}")
        self.c.drawString(120 * mm, self.y - 18 * mm, f"Países: {est['pais_interes']}")
        self.y -= 28 * mm

    def beca(self, idx: int, match, llm_info: dict | None) -> None:
        llm_info = llm_info or {}
        beca = match.beca
        vigente = not any("cerrada" in a.lower() for a in match.advertencias)
        estado_color = OK if vigente else WARN
        estado_txt = "VIGENTE" if vigente else "VENCIDA"

        # Estimar altura: header + chips + razones + advertencias + explicacion
        razones_lines = max(1, len(match.razones))
        adv_lines = len(match.advertencias)
        explic_lines = len(_wrap(llm_info.get("explicacion", ""), self.c, "Helvetica", 9, self.width - 60 * mm))
        sig_lines = len(_wrap(llm_info.get("siguientes_pasos", ""), self.c, "Helvetica-Oblique", 9, self.width - 60 * mm))
        altura = 22 + razones_lines * 4.2 + (adv_lines * 4.2 + 4 if adv_lines else 0) + (explic_lines * 4.2 + sig_lines * 4.2 + 8 if explic_lines else 0)
        self._check_break(altura * mm + 6 * mm)

        x0 = 18 * mm
        x1 = self.width - 18 * mm
        top = self.y
        bottom = self.y - altura * mm

        # Tarjeta
        self.c.setFillColor(colors.white)
        self.c.setStrokeColor(BORDER)
        self.c.setLineWidth(0.6)
        self.c.roundRect(x0, bottom, x1 - x0, altura * mm, 3 * mm, stroke=1, fill=1)

        # Cinta lateral con número
        self.c.setFillColor(PRIMARY)
        self.c.roundRect(x0, bottom, 8 * mm, altura * mm, 3 * mm, stroke=0, fill=1)
        self.c.setFillColor(colors.white)
        self.c.setFont("Helvetica-Bold", 14)
        self.c.drawCentredString(x0 + 4 * mm, top - 8 * mm, f"#{idx}")

        # Título beca
        self.c.setFont("Helvetica-Bold", 12)
        self.c.setFillColor(INK)
        self.c.drawString(x0 + 14 * mm, top - 7 * mm, beca["nombre_beca"])
        self.c.setFont("Helvetica", 8.5)
        self.c.setFillColor(INK_SOFT)
        self.c.drawString(
            x0 + 14 * mm,
            top - 11.5 * mm,
            f"{beca['pais']}   ·   USD {beca['monto']}   ·   Cierre {beca['fecha_cierre']}   ·   GPA mín {beca['gpa_minimo']}   ·   {beca['idioma_requerido']}",
        )

        # Badge estado
        self.c.setFillColor(estado_color)
        self.c.roundRect(x1 - 26 * mm, top - 10 * mm, 22 * mm, 5 * mm, 1 * mm, stroke=0, fill=1)
        self.c.setFillColor(colors.white)
        self.c.setFont("Helvetica-Bold", 7)
        self.c.drawCentredString(x1 - 15 * mm, top - 6.5 * mm, estado_txt)

        # Scores
        fit = llm_info.get("fit_score", "-")
        self.c.setFont("Helvetica", 7)
        self.c.setFillColor(MUTED)
        self.c.drawRightString(x1 - 4 * mm, top - 14 * mm, f"Score interno {match.score}   ·   Fit LLM {fit}/100")

        cursor_y = top - 17 * mm
        # Razones
        self.c.setFont("Helvetica-Bold", 8)
        self.c.setFillColor(OK)
        self.c.drawString(x0 + 14 * mm, cursor_y, "Por qué encaja")
        cursor_y -= 3.4 * mm
        self.c.setFont("Helvetica", 8.5)
        self.c.setFillColor(INK_SOFT)
        for r in match.razones:
            self.c.drawString(x0 + 14 * mm, cursor_y, f"•  {r}")
            cursor_y -= 4.2 * mm

        # Advertencias
        if match.advertencias:
            cursor_y -= 1 * mm
            self.c.setFont("Helvetica-Bold", 8)
            self.c.setFillColor(WARN)
            self.c.drawString(x0 + 14 * mm, cursor_y, "Advertencias")
            cursor_y -= 3.4 * mm
            self.c.setFont("Helvetica", 8.5)
            self.c.setFillColor(WARN)
            for a in match.advertencias:
                self.c.drawString(x0 + 14 * mm, cursor_y, f"!  {a}")
                cursor_y -= 4.2 * mm

        # Recomendación LLM
        explic = llm_info.get("explicacion", "")
        siguientes = llm_info.get("siguientes_pasos", "")
        if explic:
            cursor_y -= 2 * mm
            self.c.setFont("Helvetica-Bold", 8)
            self.c.setFillColor(PRIMARY)
            self.c.drawString(x0 + 14 * mm, cursor_y, "Asesor IA")
            cursor_y -= 3.4 * mm
            self.c.setFont("Helvetica", 9)
            self.c.setFillColor(INK)
            for ln in _wrap(explic, self.c, "Helvetica", 9, x1 - x0 - 18 * mm):
                self.c.drawString(x0 + 14 * mm, cursor_y, ln)
                cursor_y -= 4.2 * mm
            if siguientes:
                self.c.setFont("Helvetica-Oblique", 9)
                self.c.setFillColor(ACCENT)
                for ln in _wrap("→ " + siguientes, self.c, "Helvetica-Oblique", 9, x1 - x0 - 18 * mm):
                    self.c.drawString(x0 + 14 * mm, cursor_y, ln)
                    cursor_y -= 4.2 * mm

        self.y = bottom - 5 * mm

    def cerrar(self) -> None:
        _footer(self.c, self.width, self.page_num)
        self.c.save()


def generar_pdf(
    salida: Path,
    estudiantes: list[dict],
    becas: list[dict],
    resultados: list[tuple[dict, list[tuple]]],
    fecha: date | None = None,
) -> None:
    """resultados = [(estudiante, [(match, llm_info_dict), ...]), ...]"""
    pdf = PDFBuilder(salida, fecha=fecha)
    pdf.empezar()
    pdf.resumen(len(estudiantes), len(becas))
    for est, items in resultados:
        pdf.estudiante(est)
        for i, (m, llm_info) in enumerate(items, start=1):
            pdf.beca(i, m, llm_info)
    pdf.cerrar()
