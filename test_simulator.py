import pytest
import sys
import os
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp.close()
os.environ["DB_PATH"] = _tmp.name

from fastapi.testclient import TestClient
from database import init_db
from main import app

client = TestClient(app)

GOOD_RESPONSE = (
    "1. Resumen de resultados: Los ingresos por comisiones alcanzaron $45,200 con gastos operativos "
    "de $32,100, generando un margen positivo. Se abrieron 87 cuentas nuevas aunque se cerraron 23. "
    "El NPS de 68 refleja satisfacción moderada del cliente. "
    "2. Alerta de riesgo: La morosidad del 3.2% supera el umbral estándar del 2.5%, lo que representa "
    "un riesgo alto de deterioro de cartera si no se actúa con provisiones adicionales inmediatas. "
    "3. Recomendación: Implementar un programa de recuperación temprana de cartera en 30 días, "
    "establecer KPIs semanales de morosidad y revisar los criterios de otorgamiento de crédito."
)


@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    yield


# ── Evaluator unit tests ────────────────────────────────────────

def test_heuristic_short_response():
    from services.evaluator import _evaluate_heuristic
    result = _evaluate_heuristic("Test", "precisión", "estructura esperada", "corto")
    assert 0 <= result["score"] <= 100
    assert isinstance(result["feedback"], str)
    assert isinstance(result["strengths"], list)
    assert isinstance(result["improvements"], list)
    assert isinstance(result["action_plan"], list)
    assert len(result["action_plan"]) >= 1


def test_heuristic_returns_action_plan():
    from services.evaluator import _evaluate_heuristic
    result = _evaluate_heuristic("Misión", "criterios", "1. Punto A\n2. Punto B", "respuesta corta")
    assert "action_plan" in result
    assert len(result["action_plan"]) > 0


def test_heuristic_good_response_scores_higher():
    from services.evaluator import _evaluate_heuristic
    bad = _evaluate_heuristic("T", "c", "1. A\n2. B", "ok")
    good = _evaluate_heuristic("T", "c", "1. A\n2. B", GOOD_RESPONSE)
    assert good["score"] > bad["score"]


# ── Missions list & status ──────────────────────────────────────

def test_list_missions_returns_five():
    r = client.get("/api/missions/?user_id=1")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 5


def test_mission_1_unlocked_by_default():
    r = client.get("/api/missions/?user_id=1")
    missions = r.json()["missions"]
    m1 = next(m for m in missions if m["id"] == 1)
    assert m1["unlocked"] is True


def test_mission_2_locked_initially():
    r = client.get("/api/missions/?user_id=1")
    missions = r.json()["missions"]
    m2 = next(m for m in missions if m["id"] == 2)
    assert m2["unlocked"] is False


def test_get_mission_1_ok():
    r = client.get("/api/missions/1?user_id=1")
    assert r.status_code == 200
    data = r.json()
    assert "narrative" in data
    assert "objective" in data
    assert "expected_structure" in data
    assert "attempts_history" in data


def test_get_locked_mission_returns_403():
    r = client.get("/api/missions/2?user_id=1")
    assert r.status_code == 403


def test_get_missing_mission_returns_404():
    r = client.get("/api/missions/999?user_id=1")
    assert r.status_code == 404


# ── Submit & progression ────────────────────────────────────────

def test_submit_too_short_returns_400():
    r = client.post("/api/submissions/", json={
        "user_id": 1, "mission_id": 1, "response": "ok"
    })
    assert r.status_code == 400


def test_submit_locked_mission_returns_403():
    r = client.post("/api/submissions/", json={
        "user_id": 1, "mission_id": 2, "response": GOOD_RESPONSE
    })
    assert r.status_code == 403


def test_submit_mission_1_returns_full_evaluation():
    r = client.post("/api/submissions/", json={
        "user_id": 1, "mission_id": 1, "response": GOOD_RESPONSE
    })
    assert r.status_code == 200
    data = r.json()
    assert "score" in data
    assert "feedback" in data
    assert "strengths" in data
    assert "improvements" in data
    assert "action_plan" in data
    assert isinstance(data["action_plan"], list)
    assert 0 <= data["score"] <= 100
    assert data["attempt"] == 1


def test_submit_returns_score_delta_on_retry():
    client.post("/api/submissions/", json={
        "user_id": 1, "mission_id": 1, "response": GOOD_RESPONSE
    })
    r2 = client.post("/api/submissions/", json={
        "user_id": 1, "mission_id": 1, "response": GOOD_RESPONSE
    })
    data = r2.json()
    assert data["attempt"] >= 2
    assert data["prev_best"] is not None
    assert "score_delta" in data


def test_unlock_progression():
    """Completing mission 1 with score >= 70 unlocks mission 2."""
    # Submit mission 1 until it passes (heuristic should pass for GOOD_RESPONSE)
    client.post("/api/submissions/", json={
        "user_id": 1, "mission_id": 1, "response": GOOD_RESPONSE
    })
    # Check if mission 2 is now unlocked
    r = client.get("/api/missions/?user_id=1")
    missions = r.json()["missions"]
    m1 = next(m for m in missions if m["id"] == 1)
    m2 = next(m for m in missions if m["id"] == 2)

    if m1["completed"]:
        assert m2["unlocked"] is True
    # If score wasn't high enough, mission 2 stays locked — that's valid too
    else:
        assert m2["unlocked"] is False


def test_mission_has_narrative_and_structure():
    r = client.get("/api/missions/1?user_id=1")
    data = r.json()
    assert len(data["narrative"]) > 20
    assert len(data["objective"]) > 20
    assert len(data["expected_structure"]) > 10


# ── Users & progress ────────────────────────────────────────────

def test_create_user():
    r = client.post("/api/users/", json={"username": "u_test1", "name": "Test"})
    assert r.status_code == 200
    assert "id" in r.json()


def test_duplicate_user_returns_400():
    client.post("/api/users/", json={"username": "dup_99", "name": "A"})
    r = client.post("/api/users/", json={"username": "dup_99", "name": "B"})
    assert r.status_code == 400


def test_progress_endpoint():
    r = client.get("/api/users/1/progress")
    assert r.status_code == 200
    data = r.json()
    assert "completed_missions" in data
    assert "is_certified" in data


# ── Certification ────────────────────────────────────────────────

def test_certification_not_qualified_initially():
    r = client.get("/api/certification/1")
    assert r.status_code == 200
    assert r.json()["is_certified"] is False


def test_history_endpoint():
    r = client.get("/api/submissions/history/1")
    assert r.status_code == 200
    assert "history" in r.json()
