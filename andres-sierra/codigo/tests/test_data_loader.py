import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from services.data_loader import (
    load_becas, load_estudiantes, validate_columns,
    parse_date, parse_idioma, parse_carreras
)
from config import BECAS_REQUIRED_COLS, ESTUDIANTES_REQUIRED_COLS
import pandas as pd


class TestParseDate:
    def test_mdy_format(self):
        d = parse_date("6/30/2025")
        assert d is not None
        assert d.month == 6 and d.day == 30 and d.year == 2025

    def test_ymd_format(self):
        d = parse_date("2025-06-30")
        assert d is not None
        assert d.year == 2025 and d.month == 6

    def test_empty(self):
        assert parse_date("") is None
        assert parse_date(float("nan")) is None

    def test_invalid(self):
        assert parse_date("not-a-date") is None


class TestParseIdioma:
    def test_single(self):
        r = parse_idioma("Inglés-B2")
        assert len(r) == 1
        assert r[0]["idioma"] == "Inglés"
        assert r[0]["nivel"] == "B2"

    def test_multiple(self):
        r = parse_idioma("Inglés-C1;Español-C2")
        assert len(r) == 2
        assert r[0]["nivel"] == "C1"
        assert r[1]["nivel"] == "C2"

    def test_empty(self):
        assert parse_idioma("") == []
        assert parse_idioma(float("nan")) == []


class TestParseCarreras:
    def test_multiple(self):
        r = parse_carreras("Ingeniería de Sistemas;Matemáticas")
        assert len(r) == 2
        assert "Ingeniería de Sistemas" in r

    def test_empty(self):
        assert parse_carreras("") == []


class TestValidateColumns:
    def test_missing_columns(self):
        df = pd.DataFrame({"a": [1], "b": [2]})
        with pytest.raises(ValueError, match="columnas faltantes"):
            validate_columns(df, ["a", "c"], "test.csv")

    def test_all_present(self):
        df = pd.DataFrame({"a": [1], "b": [2]})
        validate_columns(df, ["a", "b"], "test.csv")


class TestLoadBecas:
    def test_load_sample(self):
        path = os.path.join(os.path.dirname(__file__), "..", "data", "becas.csv")
        df = load_becas(path)
        assert len(df) > 0
        assert "carreras_lista" in df.columns
        assert "idioma_req_lang" in df.columns
        assert "fecha_cierre_dt" in df.columns

    def test_missing_column(self):
        csv = "id_beca,nombre_beca\nB001,Test\n"
        with pytest.raises(ValueError):
            load_becas(csv)


class TestLoadEstudiantes:
    def test_load_sample(self):
        path = os.path.join(os.path.dirname(__file__), "..", "data", "estudiantes.csv")
        df = load_estudiantes(path)
        assert len(df) > 0
        assert "idiomas_lista" in df.columns
        assert "situacion_ec_norm" in df.columns

    def test_missing_column(self):
        csv = "id_estudiante,nombre\nE001,Test\n"
        with pytest.raises(ValueError):
            load_estudiantes(csv)
