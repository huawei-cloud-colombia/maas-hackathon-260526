"""Chat asistente de Universidad Nova Andes con harness para becas (Flet/Flutter)."""
from __future__ import annotations

import threading
import time
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import flet as ft

from matcher import cargar_csvs, top_matches, Match
from llm import MaaSClient

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
BECAS_CSV = AQUI / "becas.csv"
ESTUDIANTES_CSV = AQUI / "estudiantes.csv"

UNIVERSIDAD = "Universidad Nova Andes"

PRIMARY = "#7C5CFF"
PRIMARY_SOFT = "#A38BFF"
ACCENT = "#22D3EE"
BG_TOP = "#0B1020"
BG_BOTTOM = "#161A36"
USER_BUBBLE = "#7C5CFF"
BOT_BUBBLE = "#12FFFFFF"
BOT_BORDER = "#1FFFFFFF"
TEXT_MAIN = "#F5F7FF"
TEXT_DIM = "#B3B8D9"
OK = "#34D399"
WARN = "#F59E0B"
DANGER = "#F87171"


# ---------------------------------------------------------------- HARNESS ----
class Harness:
    """Capa que el asistente puede invocar como 'tools' para ejecutar acciones."""

    def __init__(self):
        self.becas, self.estudiantes = cargar_csvs(str(BECAS_CSV), str(ESTUDIANTES_CSV))
        self.cliente = None
        self.cache_llm: dict[tuple, dict] = {}

    def _get_client(self) -> MaaSClient:
        if self.cliente is None:
            self.cliente = MaaSClient()
        return self.cliente

    def listar_estudiantes(self) -> list[dict]:
        return self.estudiantes

    def buscar_estudiante(self, query: str) -> dict | None:
        q = query.lower().strip()
        for e in self.estudiantes:
            if q in e["nombre"].lower() or q == e["id_estudiante"]:
                return e
        return None

    def buscar_becas(self, estudiante: dict, k: int = 3) -> list[Match]:
        return top_matches(estudiante, self.becas, k=k)

    def explicar(self, estudiante: dict, match: Match) -> dict:
        key = (estudiante["id_estudiante"], match.beca["id_beca"])
        if key in self.cache_llm:
            return self.cache_llm[key]
        try:
            info = self._get_client().explicar_match(estudiante, match)
        except Exception as exc:  # noqa: BLE001
            info = {"explicacion": f"No pude consultar el MaaS ahora ({exc}).", "fit_score": "-"}
        self.cache_llm[key] = info
        return info

    def generar_reporte(self) -> tuple[Path, Path]:
        """Ejecuta main.py para producir TXT + PDF; devuelve rutas."""
        env_check = subprocess.run(
            [sys.executable, str(AQUI / "main.py"), "--solo-txt"],
            capture_output=True, text=True,
        )
        txt = RAIZ / "reporte_becas.txt"
        pdf = RAIZ / "reporte_becas.pdf"
        subprocess.run([sys.executable, str(AQUI / "main.py")], capture_output=True, text=True)
        return txt, pdf


# ---------------------------------------------------------------- WIDGETS ----
def hora_actual() -> str:
    return datetime.now().strftime("%H:%M")


def avatar(initials: str, color: str = PRIMARY, size: int = 36) -> ft.Container:
    return ft.Container(
        content=ft.Text(initials, color=TEXT_MAIN, weight=ft.FontWeight.BOLD, size=int(size * 0.4)),
        width=size,
        height=size,
        border_radius=size // 2,
        gradient=ft.LinearGradient(
            begin=ft.Alignment.TOP_LEFT,
            end=ft.Alignment.BOTTOM_RIGHT,
            colors=[PRIMARY, ACCENT],
        ),
        alignment=ft.Alignment.CENTER,
    )


def bubble_asistente(contenido: ft.Control, hora: str | None = None) -> ft.Row:
    hora = hora or hora_actual()
    burbuja = ft.Container(
        content=ft.Column(
            [
                contenido,
                ft.Row(
                    [ft.Text(hora, color=TEXT_DIM, size=10)],
                    alignment=ft.MainAxisAlignment.END,
                ),
            ],
            spacing=4,
            tight=True,
        ),
        padding=ft.Padding.symmetric(horizontal=14, vertical=10),
        bgcolor=BOT_BUBBLE,
        border=ft.Border.all(1, BOT_BORDER),
        border_radius=ft.BorderRadius.only(top_left=4, top_right=18, bottom_left=18, bottom_right=18),
        animate_opacity=400,
        animate_offset=ft.Animation(400, ft.AnimationCurve.EASE_OUT),
        offset=ft.Offset(0, 0),
        opacity=1,
        shadow=ft.BoxShadow(blur_radius=18, color="#40000000", offset=ft.Offset(0, 4)),
    )
    fila = ft.Row(
        [avatar("NA"), ft.Container(burbuja, expand=True)],
        spacing=10,
        vertical_alignment=ft.CrossAxisAlignment.START,
    )
    return ft.Container(
        content=fila,
        padding=ft.Padding(left=0, right=60, top=0, bottom=0),
        animate_opacity=400,
    )


def bubble_usuario(texto: str, hora: str | None = None) -> ft.Container:
    hora = hora or hora_actual()
    burbuja = ft.Container(
        content=ft.Column(
            [
                ft.Text(texto, color=TEXT_MAIN, size=14, weight=ft.FontWeight.W_500),
                ft.Row(
                    [
                        ft.Text(hora, color="#E0E5FF", size=10),
                        ft.Icon(ft.Icons.DONE_ALL_ROUNDED, color="#E0E5FF", size=12),
                    ],
                    alignment=ft.MainAxisAlignment.END,
                    spacing=4,
                ),
            ],
            spacing=4,
            tight=True,
        ),
        padding=ft.Padding.symmetric(horizontal=14, vertical=10),
        gradient=ft.LinearGradient(begin=ft.Alignment.TOP_LEFT, end=ft.Alignment.BOTTOM_RIGHT, colors=[PRIMARY, "#5B3FE5"]),
        border_radius=ft.BorderRadius.only(top_left=18, top_right=4, bottom_left=18, bottom_right=18),
        shadow=ft.BoxShadow(blur_radius=14, color="#557C5CFF", offset=ft.Offset(0, 6)),
    )
    return ft.Container(
        content=ft.Row([burbuja], alignment=ft.MainAxisAlignment.END),
        padding=ft.Padding(left=60, right=0, top=0, bottom=0),
        animate_opacity=400,
    )


def quick_reply(texto: str, on_click, icono: str | None = None, color: str = ACCENT) -> ft.Container:
    contenido = []
    if icono:
        contenido.append(ft.Icon(icono, color=color, size=14))
    contenido.append(ft.Text(texto, color=color, size=12, weight=ft.FontWeight.W_600))
    return ft.Container(
        content=ft.Row(contenido, spacing=6, tight=True),
        padding=ft.Padding.symmetric(horizontal=12, vertical=8),
        border_radius=18,
        bgcolor=f"#14{color[1:]}",
        border=ft.Border.all(1, f"#55{color[1:]}"),
        on_click=on_click,
        ink=True,
        animate=ft.Animation(200, ft.AnimationCurve.EASE_OUT),
    )


def list_item_whatsapp(titulo: str, subtitulo: str, on_click, trailing: str = "", icono: str = ft.Icons.PERSON) -> ft.Container:
    return ft.Container(
        content=ft.Row(
            [
                ft.Container(
                    content=ft.Icon(icono, color=PRIMARY_SOFT, size=18),
                    width=36, height=36, border_radius=18,
                    bgcolor=f"#22{PRIMARY[1:]}",
                    alignment=ft.Alignment.CENTER,
                ),
                ft.Column(
                    [
                        ft.Text(titulo, color=TEXT_MAIN, size=13, weight=ft.FontWeight.W_600),
                        ft.Text(subtitulo, color=TEXT_DIM, size=11),
                    ],
                    spacing=2,
                    expand=True,
                ),
                ft.Text(trailing, color=TEXT_DIM, size=10) if trailing else ft.Container(),
                ft.Icon(ft.Icons.CHEVRON_RIGHT, color=TEXT_DIM, size=16),
            ],
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=ft.Padding.symmetric(horizontal=10, vertical=8),
        border_radius=10,
        on_click=on_click,
        ink=True,
        bgcolor="#08FFFFFF",
        animate=ft.Animation(200, ft.AnimationCurve.EASE_OUT),
    )


def beca_card_mini(m: Match, idx: int, on_explain, on_detail) -> ft.Container:
    beca = m.beca
    vigente = not any("cerrada" in a.lower() for a in m.advertencias)
    estado_color = OK if vigente else DANGER
    estado_txt = "Vigente" if vigente else "Vencida"
    return ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Container(
                            content=ft.Text(f"#{idx}", color=TEXT_MAIN, size=11, weight=ft.FontWeight.BOLD),
                            width=22, height=22, border_radius=11,
                            bgcolor=PRIMARY, alignment=ft.Alignment.CENTER,
                        ),
                        ft.Text(beca["nombre_beca"], color=TEXT_MAIN, size=13, weight=ft.FontWeight.W_700, expand=True),
                        ft.Container(
                            content=ft.Text(estado_txt, color=TEXT_MAIN, size=9, weight=ft.FontWeight.BOLD),
                            padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                            border_radius=10,
                            bgcolor=estado_color,
                        ),
                    ],
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Text(
                    f"{beca['pais']}  ·  USD {beca['monto']}  ·  Cierre {beca['fecha_cierre']}",
                    color=TEXT_DIM, size=11,
                ),
                ft.Row(
                    [
                        quick_reply("Por qué encaja", on_explain, icono=ft.Icons.AUTO_AWESOME, color=PRIMARY_SOFT),
                        quick_reply("Detalles", on_detail, icono=ft.Icons.INFO_OUTLINE, color=ACCENT),
                    ],
                    wrap=True, spacing=6, run_spacing=6,
                ),
            ],
            spacing=8,
            tight=True,
        ),
        padding=12,
        border_radius=12,
        bgcolor="#0AFFFFFF",
        border=ft.Border.all(1, "#18FFFFFF"),
    )


def typing_indicator() -> ft.Container:
    dot = lambda d: ft.Container(
        width=6, height=6, border_radius=3, bgcolor=PRIMARY_SOFT,
        animate_opacity=ft.Animation(800, ft.AnimationCurve.EASE_IN_OUT),
        opacity=0.3 + d * 0.25,
    )
    return ft.Container(
        content=ft.Row(
            [avatar("NA"), ft.Container(
                content=ft.Row([dot(0), dot(1), dot(2)], spacing=4),
                padding=ft.Padding.symmetric(horizontal=14, vertical=12),
                bgcolor=BOT_BUBBLE,
                border=ft.Border.all(1, BOT_BORDER),
                border_radius=ft.BorderRadius.only(top_left=4, top_right=18, bottom_left=18, bottom_right=18),
            )],
            spacing=10,
        ),
        padding=ft.Padding(left=0, right=60, top=0, bottom=0),
    )


# ---------------------------------------------------------------- ASISTENTE --
class Asistente:
    def __init__(self, page: ft.Page, lista_chat: ft.Column, harness: Harness):
        self.page = page
        self.lista = lista_chat
        self.harness = harness
        self.estudiante: dict | None = None
        self.matches: list[Match] = []

    def _agregar(self, control: ft.Control):
        self.lista.controls.append(control)
        self.page.update()

    def _typing(self, segundos: float = 0.6):
        ti = typing_indicator()
        self.lista.controls.append(ti)
        self.page.update()
        time.sleep(segundos)
        self.lista.controls.remove(ti)

    def usuario_dice(self, texto: str):
        self._agregar(bubble_usuario(texto))

    def bot_dice(self, texto: str, opciones: list[ft.Control] | None = None):
        contenido_items: list[ft.Control] = [ft.Text(texto, color=TEXT_MAIN, size=14)]
        if opciones:
            contenido_items.append(
                ft.Row(opciones, wrap=True, spacing=6, run_spacing=6),
            )
        self._typing()
        self._agregar(bubble_asistente(ft.Column(contenido_items, spacing=10, tight=True)))

    def bot_lista(self, titulo: str, items: list[ft.Control]):
        contenido = ft.Column(
            [
                ft.Text(titulo, color=TEXT_MAIN, size=14),
                ft.Container(
                    content=ft.Column(items, spacing=4, tight=True),
                    padding=ft.Padding.symmetric(vertical=4),
                ),
            ],
            spacing=8,
            tight=True,
        )
        self._typing()
        self._agregar(bubble_asistente(contenido))

    def bot_card(self, titulo: str, cards: list[ft.Control], cierre: str | None = None, opciones: list[ft.Control] | None = None):
        items: list[ft.Control] = [ft.Text(titulo, color=TEXT_MAIN, size=14)]
        items.extend(cards)
        if cierre:
            items.append(ft.Text(cierre, color=TEXT_DIM, size=12))
        if opciones:
            items.append(ft.Row(opciones, wrap=True, spacing=6, run_spacing=6))
        self._typing()
        self._agregar(bubble_asistente(ft.Column(items, spacing=10, tight=True)))

    # -------------------- flujos --------------------
    def _reportes_existen(self) -> bool:
        return (RAIZ / "reporte_becas.txt").exists() and (RAIZ / "reporte_becas.pdf").exists()

    def saludar(self):
        opciones = [
            quick_reply("Buscar mis becas", lambda e: self.flujo_buscar(), icono=ft.Icons.SEARCH, color=ACCENT),
            quick_reply("Generar / regenerar reporte", lambda e: self.flujo_reporte(), icono=ft.Icons.PICTURE_AS_PDF, color=PRIMARY_SOFT),
            quick_reply("Cómo funciona", lambda e: self.flujo_ayuda(), icono=ft.Icons.HELP_OUTLINE, color=OK),
        ]
        if self._reportes_existen():
            opciones.insert(
                0,
                quick_reply("Descargar reportes", lambda e: self.flujo_descargas(), icono=ft.Icons.DOWNLOAD_ROUNDED, color=PRIMARY_SOFT),
            )
        self.bot_dice(
            f"¡Hola! Soy el asistente IA de la Oficina de Relaciones Internacionales de {UNIVERSIDAD}. "
            f"Te puedo ayudar a encontrar becas que encajen con tu perfil.\n\n¿Qué quieres hacer?",
            opciones=opciones,
        )

    def flujo_descargas(self):
        self.usuario_dice("Descargar reportes")
        contenido = ft.Column(
            [
                ft.Row(
                    [
                        ft.Icon(ft.Icons.FOLDER_OPEN, color=PRIMARY_SOFT, size=18),
                        ft.Text("Reportes disponibles", color=TEXT_MAIN, size=14, weight=ft.FontWeight.W_700),
                    ],
                    spacing=6,
                ),
                ft.Text("Toca para abrir/descargar en tu navegador:", color=TEXT_DIM, size=12),
                ft.Row(
                    [
                        quick_reply(
                            "Descargar PDF estilizado",
                            lambda e: self._descargar("/reporte_becas.pdf"),
                            icono=ft.Icons.PICTURE_AS_PDF,
                            color=PRIMARY_SOFT,
                        ),
                        quick_reply(
                            "Descargar TXT oficial",
                            lambda e: self._descargar("/reporte_becas.txt"),
                            icono=ft.Icons.DESCRIPTION_OUTLINED,
                            color=ACCENT,
                        ),
                    ],
                    wrap=True,
                    spacing=6,
                    run_spacing=6,
                ),
            ],
            spacing=8,
            tight=True,
        )
        self._typing(0.3)
        self._agregar(bubble_asistente(contenido))

    def flujo_buscar(self):
        self.usuario_dice("Buscar mis becas")
        items = [
            list_item_whatsapp(
                e["nombre"],
                f"{e['carrera']}  ·  GPA {e['gpa']}",
                lambda ev, est=e: self.seleccionar_estudiante(est),
                trailing=e["pais_interes"].split(",")[0],
            )
            for e in self.harness.listar_estudiantes()
        ]
        self.bot_lista("Selecciona el estudiante:", items)

    def seleccionar_estudiante(self, est: dict):
        self.estudiante = est
        self.usuario_dice(f"Soy {est['nombre']}")
        self.bot_dice(
            f"Perfecto, {est['nombre'].split()[0]} 👋. Veo que estudias {est['carrera']} "
            f"con GPA {est['gpa']} y te interesa {est['pais_interes']}. "
            f"Voy a buscar las 3 becas más afines a tu perfil…"
        )
        threading.Thread(target=self._buscar_y_mostrar, daemon=True).start()

    def _buscar_y_mostrar(self):
        matches = self.harness.buscar_becas(self.estudiante, k=3)
        self.matches = matches
        cards = [
            beca_card_mini(
                m,
                i + 1,
                on_explain=lambda ev, mm=m: self.explicar_beca(mm),
                on_detail=lambda ev, mm=m: self.detalle_beca(mm),
            )
            for i, m in enumerate(matches)
        ]
        self.bot_card(
            f"Estas son tus 3 becas más afines:",
            cards,
            cierre="Toca *Por qué encaja* para que el asesor IA lo explique en lenguaje natural.",
            opciones=[
                quick_reply("Generar mi reporte PDF", lambda e: self.flujo_reporte(), icono=ft.Icons.PICTURE_AS_PDF, color=PRIMARY_SOFT),
                quick_reply("Otro estudiante", lambda e: self.flujo_buscar(), icono=ft.Icons.SWITCH_ACCOUNT, color=ACCENT),
            ],
        )

    def detalle_beca(self, m: Match):
        beca = m.beca
        self.usuario_dice(f"Detalles de {beca['nombre_beca']}")
        cuerpo = (
            f"**{beca['nombre_beca']}**\n"
            f"País: {beca['pais']}\n"
            f"Monto: USD {beca['monto']}\n"
            f"Carreras: {beca['carreras_aceptadas']}\n"
            f"GPA mínimo: {beca['gpa_minimo']}\n"
            f"Idioma requerido: {beca['idioma_requerido']}\n"
            f"Fecha de cierre: {beca['fecha_cierre']}\n"
            f"Requiere carta: {beca['requiere_carta']}"
        )
        razones = "\n".join([f"  ✓ {r}" for r in m.razones]) or "  (ninguna)"
        advertencias = "\n".join([f"  ! {a}" for a in m.advertencias])
        texto = cuerpo + "\n\nPor qué encaja:\n" + razones
        if advertencias:
            texto += "\n\nAdvertencias:\n" + advertencias
        self.bot_dice(texto)

    def explicar_beca(self, m: Match):
        beca = m.beca
        self.usuario_dice(f"Por qué encaja {beca['nombre_beca']}")
        threading.Thread(target=self._explicar_async, args=(m,), daemon=True).start()

    def _explicar_async(self, m: Match):
        info = self.harness.explicar(self.estudiante, m)
        explic = info.get("explicacion", "")
        siguientes = info.get("siguientes_pasos", "")
        fit = info.get("fit_score", "-")
        contenido = ft.Column(
            [
                ft.Row(
                    [
                        ft.Icon(ft.Icons.AUTO_AWESOME, color=PRIMARY_SOFT, size=16),
                        ft.Text(f"Asesor IA  ·  Fit {fit}/100", color=PRIMARY_SOFT, size=12, weight=ft.FontWeight.W_600),
                    ],
                    spacing=6,
                ),
                ft.Text(explic, color=TEXT_MAIN, size=13),
                ft.Row(
                    [
                        ft.Icon(ft.Icons.ARROW_FORWARD_ROUNDED, color=ACCENT, size=14),
                        ft.Text(siguientes, color=ACCENT, size=12, weight=ft.FontWeight.W_500, expand=True),
                    ],
                    spacing=6,
                ) if siguientes else ft.Container(),
            ],
            spacing=8,
            tight=True,
        )
        self._typing(0.4)
        self._agregar(bubble_asistente(contenido))

    def flujo_reporte(self):
        self.usuario_dice("Generar reporte PDF")
        self.bot_dice("Ejecutando el motor… esto puede tardar un poco por las llamadas al MaaS.")
        threading.Thread(target=self._generar_reporte_async, daemon=True).start()

    def _descargar(self, ruta_relativa: str):
        # Los reportes viven en arias/ y se sirven desde assets_dir como rutas
        # absolutas de URL. En modo web abre en pestaña; en desktop usa app
        # nativa via launch_url.
        self.page.launch_url(ruta_relativa)

    def _generar_reporte_async(self):
        try:
            txt, pdf = self.harness.generar_reporte()
            self._typing(0.4)
            contenido = ft.Column(
                [
                    ft.Row(
                        [
                            ft.Icon(ft.Icons.CHECK_CIRCLE, color=OK, size=18),
                            ft.Text("Reporte generado", color=OK, size=14, weight=ft.FontWeight.W_700),
                        ],
                        spacing=6,
                    ),
                    ft.Text("Descarga los archivos:", color=TEXT_MAIN, size=13),
                    ft.Row(
                        [
                            quick_reply(
                                "Descargar PDF",
                                lambda e: self._descargar("/reporte_becas.pdf"),
                                icono=ft.Icons.PICTURE_AS_PDF,
                                color=PRIMARY_SOFT,
                            ),
                            quick_reply(
                                "Descargar TXT",
                                lambda e: self._descargar("/reporte_becas.txt"),
                                icono=ft.Icons.DESCRIPTION_OUTLINED,
                                color=ACCENT,
                            ),
                        ],
                        wrap=True,
                        spacing=6,
                        run_spacing=6,
                    ),
                    ft.Text(f"Ruta TXT: {txt}", color=TEXT_DIM, size=10),
                    ft.Text(f"Ruta PDF: {pdf}", color=TEXT_DIM, size=10),
                ],
                spacing=8,
                tight=True,
            )
            self._agregar(bubble_asistente(contenido))
        except Exception as exc:  # noqa: BLE001
            self.bot_dice(f"No pude generar el reporte: {exc}")

    def flujo_ayuda(self):
        self.usuario_dice("Cómo funciona")
        self.bot_dice(
            "Este asistente combina dos cerebros:\n\n"
            "🔍 **Filtros deterministas** — Aplico reglas duras sobre GPA, país, carrera, "
            "idioma, fecha y situación económica. Eso me da las becas elegibles para tu perfil.\n\n"
            "🤖 **Huawei MaaS (DeepSeek-V4-Flash)** — Para las 3 mejores becas, le pido al modelo "
            "que explique en lenguaje natural por qué te encajan y qué siguiente paso te sugiere.\n\n"
            "Así obtienes resultados predecibles (las reglas) y útiles (la explicación IA).",
            opciones=[
                quick_reply("Buscar mis becas", lambda e: self.flujo_buscar(), icono=ft.Icons.SEARCH, color=ACCENT),
            ],
        )


# ---------------------------------------------------------------- LAYOUT -----
def main(page: ft.Page):
    page.title = f"Asistente · {UNIVERSIDAD}"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    page.bgcolor = BG_TOP
    page.window.min_width = 480
    page.window.min_height = 720

    harness = Harness()

    chat = ft.Column(
        spacing=14,
        scroll=ft.ScrollMode.AUTO,
        expand=True,
        auto_scroll=True,
    )

    asistente = Asistente(page, chat, harness)

    input_field = ft.TextField(
        hint_text="Escribe un mensaje…",
        hint_style=ft.TextStyle(color=TEXT_DIM, size=13),
        text_style=ft.TextStyle(color=TEXT_MAIN, size=13),
        border_color=BOT_BORDER,
        focused_border_color=PRIMARY_SOFT,
        bgcolor=BOT_BUBBLE,
        border_radius=24,
        content_padding=ft.Padding.symmetric(horizontal=16, vertical=12),
        expand=True,
        on_submit=lambda e: enviar(),
    )

    def enviar(_=None):
        texto = (input_field.value or "").strip()
        if not texto:
            return
        input_field.value = ""
        page.update()
        asistente.usuario_dice(texto)
        # Comandos simples
        t = texto.lower()
        if "beca" in t or "buscar" in t:
            asistente.flujo_buscar()
        elif "reporte" in t or "pdf" in t:
            asistente.flujo_reporte()
        elif "ayuda" in t or "cómo" in t or "como" in t or "funciona" in t:
            asistente.flujo_ayuda()
        else:
            asistente.bot_dice(
                "Puedo ayudarte con tres cosas:",
                opciones=[
                    quick_reply("Buscar mis becas", lambda e: asistente.flujo_buscar(), icono=ft.Icons.SEARCH, color=ACCENT),
                    quick_reply("Generar reporte PDF", lambda e: asistente.flujo_reporte(), icono=ft.Icons.PICTURE_AS_PDF, color=PRIMARY_SOFT),
                    quick_reply("Cómo funciona", lambda e: asistente.flujo_ayuda(), icono=ft.Icons.HELP_OUTLINE, color=OK),
                ],
            )

    enviar_btn = ft.Container(
        content=ft.Icon(ft.Icons.SEND_ROUNDED, color=TEXT_MAIN, size=18),
        width=44, height=44, border_radius=22,
        gradient=ft.LinearGradient(begin=ft.Alignment.TOP_LEFT, end=ft.Alignment.BOTTOM_RIGHT, colors=[PRIMARY, ACCENT]),
        alignment=ft.Alignment.CENTER,
        on_click=enviar,
        ink=True,
        shadow=ft.BoxShadow(blur_radius=18, color="#667C5CFF", offset=ft.Offset(0, 6)),
    )

    header = ft.Container(
        content=ft.Row(
            [
                avatar("NA", size=42),
                ft.Column(
                    [
                        ft.Text(f"Asistente · {UNIVERSIDAD}", color=TEXT_MAIN, size=15, weight=ft.FontWeight.W_700),
                        ft.Row(
                            [
                                ft.Container(width=8, height=8, border_radius=4, bgcolor=OK),
                                ft.Text("En línea · powered by Huawei MaaS", color=TEXT_DIM, size=11),
                            ],
                            spacing=6,
                        ),
                    ],
                    spacing=2,
                    expand=True,
                ),
                ft.Icon(ft.Icons.MORE_VERT, color=TEXT_DIM),
            ],
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=ft.Padding.symmetric(horizontal=20, vertical=14),
        border=ft.Border(bottom=ft.BorderSide(1, BOT_BORDER)),
        gradient=ft.LinearGradient(begin=ft.Alignment.TOP_LEFT, end=ft.Alignment.BOTTOM_RIGHT, colors=[BG_TOP, BG_BOTTOM]),
    )

    input_bar = ft.Container(
        content=ft.Row(
            [
                ft.Icon(ft.Icons.EMOJI_EMOTIONS_OUTLINED, color=TEXT_DIM, size=22),
                input_field,
                enviar_btn,
            ],
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=ft.Padding.symmetric(horizontal=16, vertical=12),
        border=ft.Border(top=ft.BorderSide(1, BOT_BORDER)),
        bgcolor=BG_BOTTOM,
    )

    chat_area = ft.Container(
        content=chat,
        padding=ft.Padding.symmetric(horizontal=18, vertical=18),
        expand=True,
        gradient=ft.LinearGradient(
            begin=ft.Alignment.TOP_LEFT,
            end=ft.Alignment.BOTTOM_RIGHT,
            colors=[BG_TOP, BG_BOTTOM],
        ),
    )

    page.add(
        ft.Column(
            [header, chat_area, input_bar],
            spacing=0,
            expand=True,
        )
    )

    # Mensaje inicial diferido para que se vea la animación
    threading.Thread(target=lambda: (time.sleep(0.3), asistente.saludar()), daemon=True).start()


if __name__ == "__main__":
    import os
    modo_web = os.environ.get("APP_MODE", "web").lower() == "web"
    # Servimos arias/ como assets para que reporte_becas.pdf / .txt sean
    # descargables vía launch_url("/reporte_becas.pdf") en modo web.
    assets_dir = str(RAIZ)
    if modo_web:
        ft.run(main, view=ft.AppView.WEB_BROWSER, port=8550, assets_dir=assets_dir)
    else:
        ft.run(main, assets_dir=assets_dir)
