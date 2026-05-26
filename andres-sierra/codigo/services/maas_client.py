import json
import os
import logging
from openai import OpenAI
from config import MAAS_BASE_URL, MAAS_API_KEY, MAAS_MODEL, MAAS_TIMEOUT

logger = logging.getLogger(__name__)


class MaaSClient:
    def __init__(self, base_url=None, api_key=None, model=None, timeout=None):
        self.base_url = base_url if base_url is not None else MAAS_BASE_URL
        self.api_key = api_key if api_key is not None else MAAS_API_KEY
        self.model = model if model is not None else MAAS_MODEL
        self.timeout = timeout if timeout is not None else MAAS_TIMEOUT
        self.available = bool(self.api_key)
        self._client = None
        if self.available:
            try:
                self._client = OpenAI(
                    base_url=self.base_url,
                    api_key=self.api_key,
                    timeout=self.timeout,
                )
            except Exception as e:
                logger.warning(f"Error inicializando cliente MaaS: {e}")
                self.available = False

    def check_afinidad_carrera(self, carrera_estudiante, carreras_beca, beca_nombre=""):
        if not self.available:
            return None
        prompt = (
            f"Determina si la carrera '{carrera_estudiante}' es afín a alguna de estas carreras aceptadas: "
            f"{', '.join(carreras_beca)}. "
            f"Responde SOLO en JSON con estas claves: "
            f'"es_afin" (booleano), "nivel_afinidad" (bajo/medio/alto), '
            f'"razon_breve" (máximo 15 palabras), "confianza" (0.0 a 1.0). '
            f"No incluyas texto fuera del JSON."
        )
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content.strip()
            result = json.loads(content)
            required_keys = {"es_afin", "nivel_afinidad", "razon_breve", "confianza"}
            if not required_keys.issubset(result.keys()):
                logger.warning(f"JSON de MaaS incompleto: {list(result.keys())}")
                return None
            if not isinstance(result["es_afin"], bool):
                result["es_afin"] = str(result["es_afin"]).lower() in ("true", "yes", "1")
            result["confianza"] = float(result.get("confianza", 0))
            return result
        except json.JSONDecodeError as e:
            logger.warning(f"JSON inválido de MaaS: {e}")
            return None
        except Exception as e:
            logger.warning(f"Error MaaS afinidad: {e}")
            return None

    def generar_explicacion(self, estudiante_nombre, estudiante_carrera, beca_nombre, beca_pais, criteria, score):
        if not self.available:
            return None
        prompt = (
            f"Genera una explicación breve (máximo 2 oraciones) de por qué la beca '{beca_nombre}' "
            f"en {beca_pais} es recomendada para {estudiante_nombre} ({estudiante_carrera}). "
            f"Criterios cumplidos: {', '.join(criteria)}. Puntaje: {score}/100. "
            f"Responde en español, tono profesional, sin datos personales."
        )
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.warning(f"Error MaaS explicación: {e}")
            return None


def resolve_afinidades(eligibility_results, becas_df, client=None, max_calls=10):
    afinidades_cache = {}
    if client is None:
        client = MaaSClient()
    calls = 0
    for r in eligibility_results:
        if not r["eligible"] or r["carrera_exacta"]:
            continue
        key = (r["estudiante_carrera"], r["id_beca"])
        if key in afinidades_cache:
            continue
        if calls >= max_calls:
            break
        beca_row = becas_df[becas_df["id_beca"] == r["id_beca"]]
        if beca_row.empty:
            continue
        carreras_beca = beca_row.iloc[0]["carreras_lista"]
        result = client.check_afinidad_carrera(r["estudiante_carrera"], carreras_beca, r["nombre_beca"])
        calls += 1
        if result and result.get("es_afin"):
            afinidades_cache[key] = result
        else:
            afinidades_cache[key] = {"es_afin": False, "nivel_afinidad": "bajo", "razon_breve": "No afín", "confianza": 0}
    return afinidades_cache
