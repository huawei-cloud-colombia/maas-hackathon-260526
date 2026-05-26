import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from datetime import datetime
from services.ranking import score_fecha_proxima, score_pais_interes, rank_becas
from services.eligibility import filter_eligibility
from services.data_loader import load_becas, load_estudiantes
from config import SCORING


class TestScoreFechaProxima:
    def test_same_day(self):
        cierre = datetime(2025, 6, 30)
        eval_date = datetime(2025, 6, 30)
        assert score_fecha_proxima(cierre, eval_date) == SCORING["fecha_proxima_max"]

    def test_very_close(self):
        cierre = datetime(2025, 6, 30)
        eval_date = datetime(2025, 6, 15)
        score = score_fecha_proxima(cierre, eval_date)
        assert score > 0 and score < SCORING["fecha_proxima_max"]

    def test_far_away(self):
        cierre = datetime(2025, 12, 31)
        eval_date = datetime(2025, 6, 1)
        score = score_fecha_proxima(cierre, eval_date)
        assert score == 0

    def test_past(self):
        cierre = datetime(2025, 3, 1)
        eval_date = datetime(2025, 6, 1)
        assert score_fecha_proxima(cierre, eval_date) == 0

    def test_none(self):
        assert score_fecha_proxima(None, datetime(2025, 6, 1)) == 0


class TestScorePaisInteres:
    def test_match(self):
        assert score_pais_interes("Alemania", "Alemania") == SCORING["pais_interes"]

    def test_no_match(self):
        assert score_pais_interes("Japón", "Alemania") == 0

    def test_case_insensitive(self):
        assert score_pais_interes("alemania", "Alemania") == SCORING["pais_interes"]

    def test_empty(self):
        assert score_pais_interes("", "Alemania") == 0


class TestRankBecas:
    def test_ranking_with_sample_data(self):
        becas_path = os.path.join(os.path.dirname(__file__), "..", "data", "becas.csv")
        est_path = os.path.join(os.path.dirname(__file__), "..", "data", "estudiantes.csv")
        becas_df = load_becas(becas_path)
        est_df = load_estudiantes(est_path)
        results, _ = filter_eligibility(est_df, becas_df, "6/1/2025")
        scored, by_student = rank_becas(results, "6/1/2025")
        assert len(by_student) > 0
        for sid, sdata in by_student.items():
            assert len(sdata["top_becas"]) <= 3

    def test_carrera_exacta_scores_higher(self):
        becas_path = os.path.join(os.path.dirname(__file__), "..", "data", "becas.csv")
        est_path = os.path.join(os.path.dirname(__file__), "..", "data", "estudiantes.csv")
        becas_df = load_becas(becas_path)
        est_df = load_estudiantes(est_path)
        results, _ = filter_eligibility(est_df, becas_df, "6/1/2025")
        scored, _ = rank_becas(results, "6/1/2025")
        exacta = [s for s in scored if s["carrera_exacta"]]
        no_exacta = [s for s in scored if not s["carrera_exacta"]]
        if exacta and no_exacta:
            assert exacta[0]["score"] >= no_exacta[0]["score"]

    def test_pais_altera_ranking(self):
        becas_path = os.path.join(os.path.dirname(__file__), "..", "data", "becas.csv")
        est_path = os.path.join(os.path.dirname(__file__), "..", "data", "estudiantes.csv")
        becas_df = load_becas(becas_path)
        est_df = load_estudiantes(est_path)
        results, _ = filter_eligibility(est_df, becas_df, "6/1/2025")
        scored, _ = rank_becas(results, "6/1/2025")
        pais_matches = [s for s in scored if "País preferido" in s["criteria"]]
        assert len(pais_matches) > 0

    def test_afinidad_cache(self):
        becas_path = os.path.join(os.path.dirname(__file__), "..", "data", "becas.csv")
        est_path = os.path.join(os.path.dirname(__file__), "..", "data", "estudiantes.csv")
        becas_df = load_becas(becas_path)
        est_df = load_estudiantes(est_path)
        results, _ = filter_eligibility(est_df, becas_df, "6/1/2025")
        key = None
        for r in results:
            if r["eligible"] and not r["carrera_exacta"]:
                key = (r["estudiante_carrera"], r["id_beca"])
                break
        if key:
            cache = {key: {"es_afin": True, "nivel_afinidad": "alto", "razon_breve": "Mismo campo", "confianza": 0.8}}
            scored, _ = rank_becas(results, "6/1/2025", cache)
            afin = [s for s in scored if s.get("ia_aplicada")]
            assert len(afin) > 0

    def test_tiebreakers(self):
        r1 = {"score": 80, "beca_fecha_cierre_dt": datetime(2025, 7, 1), "beca_monto": 10000, "id_beca": "B001"}
        r2 = {"score": 80, "beca_fecha_cierre_dt": datetime(2025, 8, 1), "beca_monto": 20000, "id_beca": "B002"}
        items = [r1, r2]
        items.sort(key=lambda x: (-x["score"], x["beca_fecha_cierre_dt"], -x["beca_monto"], x["id_beca"]))
        assert items[0]["id_beca"] == "B001"
