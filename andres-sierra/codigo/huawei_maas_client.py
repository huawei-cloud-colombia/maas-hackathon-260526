"""
Cliente para integración con Huawei MaaS ModelArts OpenCode.

Proporciona funcionalidad para llamar modelos de IA a través de Huawei Cloud MaaS.
"""

import os
from openai import OpenAI


class HuaweiMaaSClient:
    """Cliente para Huawei MaaS API."""

    def __init__(self, api_key=None):
        """
        Inicializa cliente MaaS.

        Args:
            api_key: Clave API de Huawei Cloud. Si no se proporciona, usa HUAWEI_MAAS_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("HUAWEI_MAAS_API_KEY")
        if not self.api_key:
            raise ValueError("HUAWEI_MAAS_API_KEY no configurada")

        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api-ap-southeast-1.modelarts-maas.com/openai/v1"
        )
        self.model = "glm-5"

    def chat_completion(self, messages, temperature=0.7, max_tokens=1024):
        """
        Obtiene completamiento de chat del modelo GLM-5.

        Args:
            messages: Lista de mensajes (formato OpenAI standard)
            temperature: Control de creatividad (0-1)
            max_tokens: Máximo de tokens en respuesta

        Returns:
            str: Contenido de respuesta del modelo
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content

    def code_generation(self, prompt, language="python"):
        """
        Genera código usando el modelo.

        Args:
            prompt: Descripción de código a generar
            language: Lenguaje de programación

        Returns:
            str: Código generado
        """
        messages = [
            {
                "role": "system",
                "content": f"Eres experto en programación {language}. Genera código limpio, seguro y bien comentado."
            },
            {
                "role": "user",
                "content": f"Genera código {language}:\n{prompt}"
            }
        ]
        return self.chat_completion(messages, temperature=0.3)

    def analyze_code(self, code):
        """
        Analiza código para detectar errores y mejoras.

        Args:
            code: Código a analizar

        Returns:
            str: Análisis y recomendaciones
        """
        messages = [
            {
                "role": "system",
                "content": "Eres experto en revisión de código. Identifica errores, vulnerabilidades y mejoras."
            },
            {
                "role": "user",
                "content": f"Analiza este código:\n\n```\n{code}\n```"
            }
        ]
        return self.chat_completion(messages, temperature=0.3)
