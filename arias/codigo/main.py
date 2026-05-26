"""Genera el reporte_becas.txt (entregable oficial) y reporte_becas.pdf (estilizado)."""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date
from pathlib import Path

from matcher import cargar_csvs, top_matches
from llm import MaaSClient
from pdf_report import generar_pdf

AQUI = Path(__file__).resolve().parent
RAIZ_ENTREGA = AQUI.parent  # arias/
CACHE_FILE = AQUI / ".llm_cache.json"


def _formatear_match(idx: int, m, llm_data: dict) -> str:
    beca = m.beca
    lineas = [
        f"  {idx}. {beca['nombre_beca']}  ·  {beca['pais']}  ·  USD {beca['monto']}",
        f"     Cierre: {beca['fecha_cierre']}   GPA mín: {beca['gpa_minimo']}   Idioma: {beca['idioma_requerido']}",
        f"     Score interno: {m.score}   Fit LLM: {llm_data.get('fit_score', '-')} / 100",
        "     Por qué te encaja:",
    ]
    for r in m.razones:
        lineas.append(f"        - {r}")
    if m.advertencias:
        lineas.append("     Advertencias:")
        for a in m.advertencias:
            lineas.append(f"        ! {a}")
    lineas.append(f"     Recomendación del asesor IA: {llm_data.get('explicacion', '').strip()}")
    siguientes = llm_data.get("siguientes_pasos", "").strip()
    if siguientes:
        lineas.append(f"     Siguiente paso: {siguientes}")
    return "\n".join(lineas)


def _load_cache() -> dict:
    if CACHE_FILE.exists():
        try:
            return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            return {}
    return {}


def _save_cache(cache: dict) -> None:
    CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")


def generar_reporte(
    becas_path: Path,
    estudiantes_path: Path,
    salida_txt: Path,
    salida_pdf: Path | None = None,
    k: int = 3,
    hoy: date | None = None,
    usar_llm: bool = True,
) -> None:
    becas, estudiantes = cargar_csvs(str(becas_path), str(estudiantes_path))
    cliente = MaaSClient() if usar_llm else None
    hoy = hoy or date.today()
    cache = _load_cache()

    bloques: list[str] = []
    encabezado = [
        "=" * 78,
        "REPORTE DE BECAS RECOMENDADAS",
        "Universidad Nova Andes — Oficina de Relaciones Internacionales",
        "Sistema de recomendación personalizada — Huawei MaaS Hackathon 2026",
        f"Fecha de ejecución: {hoy.isoformat()}",
        f"Total estudiantes analizados: {len(estudiantes)}",
        f"Total becas consideradas: {len(becas)}",
        "=" * 78,
        "",
    ]
    bloques.append("\n".join(encabezado))

    resultados_pdf: list[tuple[dict, list[tuple]]] = []

    for est in estudiantes:
        matches = top_matches(est, becas, k=k, hoy=hoy)
        bloque = [
            "-" * 78,
            f"ESTUDIANTE: {est['nombre']}   (ID {est['id_estudiante']})",
            f"  Carrera: {est['carrera']}   GPA: {est['gpa']}   Situación EC: {est['situacion_economica']}",
            f"  Idiomas: {est['idiomas']}",
            f"  Países de interés: {est['pais_interes']}",
            f"  Email: {est['email']}",
            "",
            f"  Top {k} becas más afines:",
        ]
        bloques.append("\n".join(bloque))

        items_pdf: list[tuple] = []
        for i, m in enumerate(matches, start=1):
            cache_key = f"{est['id_estudiante']}::{m.beca['id_beca']}"
            llm_data: dict = cache.get(cache_key, {})
            if cliente and not llm_data:
                try:
                    llm_data = cliente.explicar_match(est, m)
                    cache[cache_key] = llm_data
                    _save_cache(cache)
                except Exception as exc:  # noqa: BLE001
                    llm_data = {"explicacion": f"(LLM no disponible: {exc})"}
            bloques.append(_formatear_match(i, m, llm_data))
            bloques.append("")
            items_pdf.append((m, llm_data))
        resultados_pdf.append((est, items_pdf))

    contenido = "\n".join(bloques).rstrip() + "\n"
    salida_txt.write_text(contenido, encoding="utf-8")
    print(f"Reporte TXT generado: {salida_txt}")

    if salida_pdf is not None:
        generar_pdf(salida_pdf, estudiantes, becas, resultados_pdf, fecha=hoy)
        print(f"Reporte PDF generado: {salida_pdf}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Genera reporte_becas.txt y reporte_becas.pdf")
    parser.add_argument("--becas", default=str(AQUI / "becas.csv"))
    parser.add_argument("--estudiantes", default=str(AQUI / "estudiantes.csv"))
    parser.add_argument("--salida-txt", default=str(RAIZ_ENTREGA / "reporte_becas.txt"))
    parser.add_argument("--salida-pdf", default=str(RAIZ_ENTREGA / "reporte_becas.pdf"))
    parser.add_argument("--solo-txt", action="store_true", help="No generar PDF")
    parser.add_argument("--k", type=int, default=3)
    parser.add_argument("--sin-llm", action="store_true", help="No llamar al MaaS (solo filtros)")
    args = parser.parse_args(argv)
    generar_reporte(
        Path(args.becas),
        Path(args.estudiantes),
        Path(args.salida_txt),
        salida_pdf=None if args.solo_txt else Path(args.salida_pdf),
        k=args.k,
        usar_llm=not args.sin_llm,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
