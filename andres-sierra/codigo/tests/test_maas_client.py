import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from unittest.mock import patch, MagicMock
from services.maas_client import MaaSClient, resolve_afinidades
import json


class TestMaaSClientInit:
    def test_no_api_key(self):
        client = MaaSClient(api_key="")
        assert client.available is False

    def test_with_api_key(self):
        with patch("services.maas_client.OpenAI") as mock_openai:
            mock_openai.return_value = MagicMock()
            client = MaaSClient(api_key="test-key")
            assert client.available is True


class TestCheckAfinidad:
    def test_unavailable_returns_none(self):
        client = MaaSClient(api_key="")
        result = client.check_afinidad_carrera("Derecho", ["Ingeniería de Sistemas"])
        assert result is None

    def test_valid_json_response(self):
        with patch("services.maas_client.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = json.dumps({
                "es_afin": True,
                "nivel_afinidad": "alto",
                "razon_breve": "Ambas son ingenierías",
                "confianza": 0.85
            })
            mock_client.chat.completions.create.return_value = mock_response
            client = MaaSClient(api_key="test-key")
            result = client.check_afinidad_carrera("Ingeniería Industrial", ["Ingeniería de Sistemas"])
            assert result is not None
            assert result["es_afin"] is True
            assert result["confianza"] == 0.85

    def test_invalid_json_returns_none(self):
        with patch("services.maas_client.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "not valid json"
            mock_client.chat.completions.create.return_value = mock_response
            client = MaaSClient(api_key="test-key")
            result = client.check_afinidad_carrera("Derecho", ["Ingeniería"])
            assert result is None

    def test_missing_keys_returns_none(self):
        with patch("services.maas_client.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = json.dumps({"es_afin": True})
            mock_client.chat.completions.create.return_value = mock_response
            client = MaaSClient(api_key="test-key")
            result = client.check_afinidad_carrera("Derecho", ["Ingeniería"])
            assert result is None

    def test_api_error_returns_none(self):
        with patch("services.maas_client.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            mock_client.chat.completions.create.side_effect = Exception("Connection timeout")
            client = MaaSClient(api_key="test-key")
            result = client.check_afinidad_carrera("Derecho", ["Ingeniería"])
            assert result is None


class TestGenerarExplicacion:
    def test_unavailable_returns_none(self):
        client = MaaSClient(api_key="")
        result = client.generar_explicacion("Test", "Derecho", "Beca X", "España", ["Carrera exacta"], 80)
        assert result is None

    def test_valid_response(self):
        with patch("services.maas_client.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Esta beca es ideal porque coincide con tu carrera."
            mock_client.chat.completions.create.return_value = mock_response
            client = MaaSClient(api_key="test-key")
            result = client.generar_explicacion("María", "Derecho", "Beca X", "España", ["Carrera exacta"], 80)
            assert result is not None


class TestResolveAfinidades:
    def test_no_client_returns_empty(self):
        client = MaaSClient(api_key="")
        result = resolve_afinidades([], MagicMock(), client)
        assert result == {}

    def test_max_calls_limit(self):
        with patch("services.maas_client.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = json.dumps({
                "es_afin": True, "nivel_afinidad": "alto",
                "razon_breve": "test", "confianza": 0.8
            })
            mock_client.chat.completions.create.return_value = mock_response
            client = MaaSClient(api_key="test-key")
            import pandas as pd
            becas_df = pd.DataFrame({
                "id_beca": ["B001"],
                "carreras_lista": [["Ingeniería de Sistemas"]],
            })
            elig = [
                {"eligible": True, "carrera_exacta": False, "estudiante_carrera": "Derecho", "id_beca": "B001", "nombre_beca": "Test"},
            ] * 5
            result = resolve_afinidades(elig, becas_df, client, max_calls=2)
            assert len(result) <= 2
