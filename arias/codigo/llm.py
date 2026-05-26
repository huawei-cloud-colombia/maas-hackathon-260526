"""Cliente Huawei MaaS — re-ranking y explicaciones en lenguaje natural."""
from __future__ import annotations

import json
import os
import time
from typing import Iterable

import requests

DEFAULT_MAAS_URL = "https://api-ap-southeast-1.modelarts-maas.com/openai/v1"
DEFAULT_MAAS_MODEL = "deepseek-v4-flash"


SYSTEM_PROMPT = """Eres un asesor de la Oficina de Relaciones Internacionales de una universidad.
Tu misión es ayudar a estudiantes a entender por qué una beca encaja con su perfil
y orientarlos sobre próximos pasos. Sé concreto, cálido y útil. No inventes datos
que no estén en la información que recibes. Responde siempre en español neutro."""

EXPLAIN_PROMPT_TEMPLATE = """Estudiante:
- Nombre: {nombre}
- Carrera: {carrera}
- GPA: {gpa}
- Idiomas: {idiomas}
- Países de interés: {pais_interes}
- Situación económica: {situacion}

Beca:
- Nombre: {beca_nombre}
- País: {pais}
- Monto USD: {monto}
- Carreras aceptadas: {carreras}
- GPA mínimo: {gpa_min}
- Idiomas requeridos: {idioma_req}
- Cierre: {cierre}
- Carta de motivación: {carta}

Coincidencias detectadas por filtros: {razones}
Advertencias / brechas: {advertencias}

Devuelve un JSON estricto (sin texto adicional) con:
{{
  "fit_score": <entero 0-100 evaluando qué tan buen ajuste es para el estudiante>,
  "explicacion": "<máximo 3 oraciones, segunda persona ('te recomendamos…'), específicas al perfil>",
  "siguientes_pasos": "<una recomendación concreta y accionable, máximo 1 oración>"
}}"""


class MaaSClient:
    def __init__(
        self,
        url: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
        timeout: int = 60,
    ):
        self.url = (url or os.environ.get("MAAS_URL") or DEFAULT_MAAS_URL).rstrip("/")
        self.api_key = api_key or os.environ.get("MAAS_API_KEY", "")
        self.model = model or os.environ.get("MAAS_MODEL") or DEFAULT_MAAS_MODEL
        self.timeout = timeout
        if not self.api_key:
            raise RuntimeError("Falta MAAS_API_KEY (variable de entorno o parámetro)")

    def chat(self, messages: list[dict], temperature: float = 0.3, max_tokens: int = 400) -> str:
        backoff = 2.0
        for intento in range(4):
            resp = requests.post(
                f"{self.url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
                timeout=self.timeout,
            )
            if resp.status_code == 429:
                time.sleep(backoff)
                backoff *= 2
                continue
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()
        resp.raise_for_status()
        return ""

    def explicar_match(self, estudiante: dict, match) -> dict:
        beca = match.beca
        prompt = EXPLAIN_PROMPT_TEMPLATE.format(
            nombre=estudiante.get("nombre", ""),
            carrera=estudiante.get("carrera", ""),
            gpa=estudiante.get("gpa", ""),
            idiomas=estudiante.get("idiomas", ""),
            pais_interes=estudiante.get("pais_interes", ""),
            situacion=estudiante.get("situacion_economica", ""),
            beca_nombre=beca.get("nombre_beca", ""),
            pais=beca.get("pais", ""),
            monto=beca.get("monto", ""),
            carreras=beca.get("carreras_aceptadas", ""),
            gpa_min=beca.get("gpa_minimo", ""),
            idioma_req=beca.get("idioma_requerido", ""),
            cierre=beca.get("fecha_cierre", ""),
            carta=beca.get("requiere_carta", ""),
            razones="; ".join(match.razones) or "ninguna",
            advertencias="; ".join(match.advertencias) or "ninguna",
        )
        raw = self.chat(
            [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )
        return _safe_parse_json(raw)


def _safe_parse_json(raw: str) -> dict:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.lower().startswith("json"):
            raw = raw[4:]
        raw = raw.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        start = raw.find("{")
        end = raw.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(raw[start : end + 1])
            except json.JSONDecodeError:
                pass
    return {"fit_score": 0, "explicacion": raw[:400], "siguientes_pasos": ""}
