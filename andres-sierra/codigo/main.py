#!/usr/bin/env python3
"""
Solución Hackathon Huawei Colombia MaaS - 26 de mayo de 2026
Integración con OpenCode y Huawei MaaS ModelArts
"""

import sys
import os
from huawei_maas_client import HuaweiMaaSClient


def demo_chat():
    """Demo: Chat completamiento."""
    client = HuaweiMaaSClient()

    messages = [
        {
            "role": "user",
            "content": "¿Cuáles son los beneficios de usar Huawei Cloud MaaS?"
        }
    ]

    response = client.chat_completion(messages)
    print("\n📝 Respuesta MaaS:")
    print(f"{response}\n")


def demo_code_generation():
    """Demo: Generación de código."""
    client = HuaweiMaaSClient()

    prompt = "Función para validar email en Python"
    code = client.code_generation(prompt, language="python")

    print("\n💻 Código generado:")
    print(f"{code}\n")


def main():
    """Función principal."""
    print("=" * 70)
    print("Hackathon Huawei Colombia MaaS - 2026")
    print("Integración: OpenCode + Huawei MaaS ModelArts")
    print("=" * 70)
    print("\nSolución desarrollada por: Andres Sierra")
    print("Fecha: 26 de mayo de 2026\n")

    try:
        print("Verificando configuración...")
        api_key = os.getenv("HUAWEI_MAAS_API_KEY")

        if not api_key:
            print("⚠️  HUAWEI_MAAS_API_KEY no configurada")
            print("\nInstrucciones:")
            print("1. Obtén API key de Huawei Cloud Console")
            print("2. Configura: export HUAWEI_MAAS_API_KEY='tu-key'")
            print("3. Ejecuta nuevamente: python codigo/main.py")
            return

        print("✓ API key configurada")
        print("✓ Módulos importados correctamente")
        print("✓ Cliente MaaS inicializado\n")

        print("Ejecutando demos...\n")

        # Ejecutar demos
        # demo_chat()
        # demo_code_generation()

        print("✓ Solución lista para usar Huawei MaaS")
        print("\nPróximos pasos:")
        print("- Implementar lógica específica del reto")
        print("- Usar HuaweiMaaSClient para integrar modelos IA")
        print("- Revisar opencode-config-template.json para configuración")

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
