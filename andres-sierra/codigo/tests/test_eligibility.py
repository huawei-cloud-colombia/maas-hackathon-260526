import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from datetime import datetime
from services.eligibility import (
    cefr_sufficient, idioma_sufficient, gpa_eligible,
    beca_abierta, situacion_ec_eligible, carrera_exacta, filter_eligibility
)
from services.data_loader import load_becas, load_estudiantes


class TestCEFRSufficient:
    def test_equal(self):
        assert cefr_sufficient("B2", "B2") is True

    def test_superior(self):
        assert cefr_sufficient("C1", "B2") is True

    def test_inferior(self):
        assert cefr_sufficient("A2", "B1") is False

    def test_full_order(self):
        levels = ["A1", "A2", "B1", "B2", "C1", "C2"]
        for i, low in enumerate(levels):
            for j, high in enumerate(levels):
                assert cefr_sufficient(low, high) == (i >= j)


class TestIdiomaSufficient:
    def test_sufficient(self):
        idiomas = [{"idioma": "Inglés", "nivel": "C1"}, {"idioma": "Español", "nivel": "C2"}]
        assert idioma_sufficient(idiomas, "Inglés", "B2") is True

    def test_insufficient(self):
        idiomas = [{"idioma": "Inglés", "nivel": "A2"}]
        assert idioma_sufficient(idiomas, "Inglés", "B1") is False

    def test_language_not_present(self):
        idiomas = [{"idioma": "Español", "nivel": "C2"}]
        assert idioma_sufficient(idiomas, "Inglés", "B2") is False

    def test_no_requirement(self):
        assert idioma_sufficient([], None, None) is True


class TestGPAEligible:
    def test_equal(self):
        assert gpa_eligible(3.5, 3.5) is True

    def test_higher(self):
        assert gpa_eligible(3.8, 3.5) is True

    def test_lower(self):
        assert gpa_eligible(3.0, 3.5) is False

    def test_none(self):
        assert gpa_eligible(None, 3.0) is False


class TestBecaAbierta:
    def test_open(self):
        cierre = datetime(2025, 8, 15)
        eval_date = datetime(2025, 6, 1)
        assert beca_abierta(cierre, eval_date) is True

    def test_closed(self):
        cierre = datetime(2025, 3, 31)
        eval_date = datetime(2025, 6, 1)
        assert beca_abierta(cierre, eval_date) is False

    def test_no_eval_date(self):
        cierre = datetime(2025, 3, 31)
        assert beca_abierta(cierre, None) is True

    def test_no_cierre(self):
        assert beca_abierta(None, datetime(2025, 6, 1)) is True


class TestSituacionEC:
    def test_no_restriction(self):
        eligible, pend = situacion_ec_eligible("baja", "")
        assert eligible is True and pend is False

    def test_exact_match(self):
        eligible, pend = situacion_ec_eligible("baja", "baja")
        assert eligible is True

    def test_lower_qualifies(self):
        eligible, _ = situacion_ec_eligible("baja", "media")
        assert eligible is True

    def test_higher_does_not_qualify(self):
        eligible, _ = situacion_ec_eligible("alta", "baja")
        assert eligible is False


class TestCarreraExacta:
    def test_match(self):
        assert carrera_exacta("Ingeniería de Sistemas", ["Ingeniería de Sistemas", "Matemáticas"]) is True

    def test_no_match(self):
        assert carrera_exacta("Derecho", ["Ingeniería de Sistemas", "Matemáticas"]) is False


class TestFilterEligibility:
    def test_full_pipeline(self):
        becas_path = os.path.join(os.path.dirname(__file__), "..", "data", "becas.csv")
        est_path = os.path.join(os.path.dirname(__file__), "..", "data", "estudiantes.csv")
        becas_df = load_becas(becas_path)
        est_df = load_estudiantes(est_path)
        results, warnings = filter_eligibility(est_df, becas_df, "6/1/2025")
        assert len(results) > 0
        eligible = [r for r in results if r["eligible"]]
        assert len(eligible) > 0

    def test_beca_vencida(self):
        becas_path = os.path.join(os.path.dirname(__file__), "..", "data", "becas.csv")
        est_path = os.path.join(os.path.dirname(__file__), "..", "data", "estudiantes.csv")
        becas_df = load_becas(becas_path)
        est_df = load_estudiantes(est_path)
        results, _ = filter_eligibility(est_df, becas_df, "12/31/2026")
        closed_becas = [r for r in results if not r["eligible"] and "cerrada" in " ".join(r["reasons"]).lower()]
        assert len(closed_becas) > 0

        results2, _ = filter_eligibility(est_df, becas_df, "1/1/2024")
        closed_early = [r for r in results2 if not r["eligible"] and "cerrada" in " ".join(r["reasons"]).lower()]
        assert len(closed_early) == 0
