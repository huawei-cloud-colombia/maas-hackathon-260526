#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cliente para la API de MaaS (Model as a Service) de Huawei Cloud.
Integra el modelo Deepseek v3.2 para potenciar el sistema de recomendación de becas.
"""

import json
import os
import requests


# =============================================================================
# CONFIGURACIÓN DE MaaS - Huawei Cloud
# =============================================================================
MaaS_CONFIG = {
    # URL base de la API MaaS (OpenAI-compatible endpoint)
    "base_url": os.environ.get(
        "MAAS_BASE_URL",
        "https://api-ap-southeast-1.modelarts-maas.com/openai/v1"
    ),
    # API Key de MaaS
    "api_key": os.environ.get(
        "MAAS_API_KEY",
        "fprCflUTJedqwsePaRkhft86j3SVVSQBSWVDAQ4l8mctFzgdvDhBzRnUgfHcqxblYO6zUn5XCvZok09TVd76-g"
    ),
    # Modelo Deepseek v3.2 (recomendado por MaaS)
    "model": os.environ.get("MAAS_MODEL", "deepseek-v3.2"),
    # Temperatura para generación (0.0 = determinista, 1.0 = creativo)
    "temperature": float(os.environ.get("MAAS_TEMPERATURE", "0.3")),
    # Máximo de tokens en la respuesta
    "max_tokens": int(os.environ.get("MAAS_MAX_TOKENS", "2048")),
}


# =============================================================================
# EXCEPCIONES
# =============================================================================

class MaaSError(Exception):
    """Error genérico de MaaS."""
    pass


class MaaSAuthError(MaaSError):
    """Error de autenticación con MaaS."""
    pass


class MaaSConnectionError(MaaSError):
    """Error de conexión con MaaS."""
    pass


# =============================================================================
# CLIENTE MaaS
# =============================================================================

class MaaSClient:
    """
    Cliente para interactuar con la API de MaaS de Huawei Cloud.
    Utiliza el formato OpenAI-compatible para chat completions.
    """

    def __init__(self, config=None):
        self.config = config or MaaS_CONFIG
        self._validate_config()

    def _validate_config(self):
        """Valida la configuración del cliente."""
        if not self.config.get("api_key"):
            print("  [MaaS] WARNING: API Key no configurada. "
                  "Configure MAAS_API_KEY como variable de entorno.")
            print("  [MaaS] El sistema funcionara en modo fallback (sin IA).")

    @property
    def is_configured(self):
        """Retorna True si el cliente esta configurado con API key."""
        return bool(self.config.get("api_key"))

    def chat_completion(self, messages, temperature=None, max_tokens=None):
        """
        Envia una solicitud de chat completion a la API MaaS.

        Args:
            messages: Lista de mensajes en formato OpenAI
                     [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]
            temperature: Temperatura de generacion (opcional)
            max_tokens: Maximo de tokens en respuesta (opcional)

        Returns:
            str: Contenido de la respuesta del modelo
        """
        if not self.is_configured:
            raise MaaSAuthError("API Key de MaaS no configurada.")

        url = f"{self.config['base_url']}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config['api_key']}",
        }
        payload = {
            "model": self.config["model"],
            "messages": messages,
            "temperature": temperature or self.config["temperature"],
            "max_tokens": max_tokens or self.config["max_tokens"],
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
        except requests.exceptions.ConnectionError as e:
            raise MaaSConnectionError(f"No se pudo conectar a MaaS: {e}")
        except requests.exceptions.Timeout:
            raise MaaSConnectionError("Timeout al conectar con MaaS (60s).")

        if response.status_code == 401:
            raise MaaSAuthError("API Key invalida o expirada.")
        elif response.status_code == 404:
            raise MaaSError(f"Modelo '{self.config['model']}' no encontrado en MaaS.")
        elif response.status_code != 200:
            raise MaaSError(f"Error MaaS ({response.status_code}): {response.text}")

        try:
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            raise MaaSError(f"Error parseando respuesta de MaaS: {e}")


# =============================================================================
# FUNCIONES DE INTEGRACION CON EL SISTEMA DE BECAS
# =============================================================================

def generar_explicacion_recomendacion(client, estudiante, beca, puntuacion, desglose):
    """
    Usa Deepseek v3.2 para generar una explicacion personalizada de por que
    la beca es recomendada para el estudiante.
    """
    prompt = f"""Eres un asesor academico experto en becas internacionales. Genera una explicacion breve y personalizada (maximo 3 lineas) de por que esta beca es recomendada para el estudiante, destacando los puntos fuertes de la coincidencia.

DATOS DEL ESTUDIANTE:
- Nombre: {estudiante['nombre']}
- Carrera: {estudiante['carrera']}
- GPA: {estudiante['gpa']}
- Idiomas: {estudiante['idiomas']}
- Paises de interes: {estudiante['pais_interes']}
- Situacion economica: {estudiante.get('situacion_economica', 'N/A')}

DATOS DE LA BECA:
- Nombre: {beca['nombre_beca']}
- Pais: {beca['pais']}
- Monto: ${beca['monto']}
- Carreras aceptadas: {beca['carreras_aceptadas']}
- GPA minimo: {beca['gpa_minimo']}
- Idioma requerido: {beca['idioma_requerido']}
- Fecha de cierre: {beca['fecha_cierre']}

PUNTUACION DE AFINIDAD: {puntuacion}/100
DESGLOSE: {json.dumps(desglose, ensure_ascii=False)}

Genera la explicacion en espanol, de forma directa y motivante para el estudiante."""

    messages = [
        {"role": "system", "content": "Eres un asesor academico experto en becas internacionales. Proporcionas recomendaciones claras, breves y motivantes."},
        {"role": "user", "content": prompt},
    ]

    try:
        return client.chat_completion(messages, temperature=0.4, max_tokens=300)
    except MaaSError as e:
        return f"[Explicacion IA no disponible: {e}]"


def generar_resumen_estudiante(client, estudiante, recomendaciones):
    """
    Usa Deepseek v3.2 para generar un resumen personalizado del perfil del estudiante
    y sus oportunidades de becas.
    """
    becas_info = []
    for i, rec in enumerate(recomendaciones, 1):
        becas_info.append(
            f"{i}. {rec['beca']['nombre_beca']} ({rec['beca']['pais']}) - "
            f"${rec['beca']['monto']} - {rec['puntuacion']} pts - "
            f"Cierra: {rec['beca']['fecha_cierre']}"
        )
    becas_str = "\n".join(becas_info)

    prompt = f"""Genera un resumen breve (maximo 4 lineas) para el estudiante sobre sus mejores oportunidades de becas. Se motivante pero realista.

ESTUDIANTE: {estudiante['nombre']} - {estudiante['carrera']} (GPA: {estudiante['gpa']})
IDIOMAS: {estudiante['idiomas']}
PAISES DE INTERES: {estudiante['pais_interes']}

TOP BECAS RECOMENDADAS:
{becas_str}

Genera el resumen en espanol, directo y util para el estudiante."""

    messages = [
        {"role": "system", "content": "Eres un asesor academico que ayuda a estudiantes a entender sus oportunidades de becas internacionales."},
        {"role": "user", "content": prompt},
    ]

    try:
        return client.chat_completion(messages, temperature=0.5, max_tokens=400)
    except MaaSError as e:
        return f"[Resumen IA no disponible: {e}]"


def enriquecer_reporte_con_ia(client, recomendaciones):
    """
    Enriquece todas las recomendaciones con explicaciones generadas por Deepseek v3.2.

    Args:
        client: Instancia de MaaSClient
        recomendaciones: Lista de recomendaciones por estudiante

    Returns:
        Lista enriquecida con campos 'explicacion_ia' y 'resumen_ia'
    """
    if not client.is_configured:
        print("  [MaaS] Modo fallback: API Key no configurada. Omitiendo IA.")
        return recomendaciones

    print("\n[Deepseek v3.2 MaaS] Enriqueciendo recomendaciones con IA...")

    for i, rec in enumerate(recomendaciones):
        est = rec["estudiante"]
        print(f"  [Deepseek] Procesando {est['nombre']}...")

        # Generar resumen del estudiante
        try:
            resumen = generar_resumen_estudiante(client, est, rec["becas_recomendadas"])
            rec["resumen_ia"] = resumen
        except MaaSError as e:
            rec["resumen_ia"] = f"[Resumen IA no disponible: {e}]"

        # Generar explicacion para cada beca recomendada
        for bec_rec in rec["becas_recomendadas"]:
            try:
                explicacion = generar_explicacion_recomendacion(
                    client, est, bec_rec["beca"], bec_rec["puntuacion"], bec_rec["desglose"]
                )
                bec_rec["explicacion_ia"] = explicacion
            except MaaSError as e:
                bec_rec["explicacion_ia"] = f"[Explicacion IA no disponible: {e}]"

        print(f"  [Deepseek] OK {est['nombre']} - {len(rec['becas_recomendadas'])} explicaciones generadas")

    print("[Deepseek v3.2 MaaS] Enriquecimiento completado.")
    return recomendaciones