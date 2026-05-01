import pytest
import sys
import os
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Use a real temp file so all connections share the same DB
_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp.close()
os.environ["DB_PATH"] = _tmp.name

from fastapi.testclient import TestClient
from database import init_db
from main import app

# ── Setup ──────────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    yield

client = TestClient(app)

# ── Unit: Evaluator ─────────────────────────────────────────────────────────────

def test_heuristic_short_response():
    from services.evaluator import _evaluate_heuristic
    result = _evaluate_heuristic("Test", "precisión", "ok")
    assert 0 <= result["score"] <= 100
    assert isinstance(result["feedback"], str)
    assert isinstance(result["strengths"], list)
    assert isinstance(result["improvements"], list)


def test_heuristic_good_response():
    from services.evaluator import _evaluate_heuristic
    response = (
        "Primero, identifico tres riesgos críticos en la cartera de crédito. "
        "Segundo, propongo implementar provisiones adicionales para reducir la morosidad. "
        "Tercero, recomiendo automatizar el proceso de scoring crediticio para mejorar "
        "la eficiencia. Finalmente, sugiero establecer métricas de seguimiento mensual "
        "con KPIs de rentabilidad y riesgo."
    )
    result = _evaluate_heuristic("Riesgo en Cartera", "precisión, claridad", response)
    assert result["score"] >= 50
    assert len(result["feedback"]) > 10


def test_heuristic_excellent_response():
    from services.evaluator import _evaluate_heuristic
    response = " ".join([
        "Primero implementar un sistema de scoring crediticio automatizado.",
        "Segundo reducir la morosidad mediante provisiones adicionales.",
        "Tercero optimizar el proceso de apertura de cuentas bancarias.",
        "Recomiendo establecer garantías adecuadas para cada crédito.",
        "Finalmente diseñar métricas de rentabilidad y KPIs de riesgo.",
        "La cartera requiere análisis de liquidez y margen de ganancia.",
        "El ROI esperado es positivo según los indicadores actuales.",
        "Además es necesario revisar los clientes con score bajo."
    ])
    result = _evaluate_heuristic("Misión avanzada", "precisión, claridad, estructura", response)
    assert result["score"] >= 70


# ── API: Missions ──────────────────────────────────────────────────────────────

def test_list_missions():
    resp = client.get("/api/missions/")
    assert resp.status_code == 200
    data = resp.json()
    assert "missions" in data
    assert data["total"] == 5


def test_get_mission_valid():
    resp = client.get("/api/missions/1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == 1
    assert "title" in data
    assert "description" in data
    assert "level" in data


def test_get_mission_not_found():
    resp = client.get("/api/missions/999")
    assert resp.status_code == 404


# ── API: Users ─────────────────────────────────────────────────────────────────

def test_create_user():
    resp = client.post("/api/users/", json={
        "username": "test_user_001",
        "name": "Analista Test",
        "email": "test@banco.com"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "test_user_001"
    assert "id" in data


def test_create_duplicate_user():
    client.post("/api/users/", json={"username": "dup_user_x", "name": "Dup"})
    resp = client.post("/api/users/", json={"username": "dup_user_x", "name": "Dup2"})
    assert resp.status_code == 400


def test_get_user():
    resp = client.get("/api/users/1")
    assert resp.status_code == 200
    assert resp.json()["id"] == 1


def test_get_user_not_found():
    resp = client.get("/api/users/99999")
    assert resp.status_code == 404


def test_user_progress_empty():
    create = client.post("/api/users/", json={"username": "fresh_user_xyz", "name": "Fresh"})
    uid = create.json()["id"]
    resp = client.get(f"/api/users/{uid}/progress")
    assert resp.status_code == 200
    data = resp.json()
    assert data["completed_missions"] == 0
    assert data["is_certified"] is False


# ── API: Submissions ───────────────────────────────────────────────────────────

def test_submit_too_short():
    resp = client.post("/api/submissions/", json={
        "user_id": 1,
        "mission_id": 1,
        "response": "Ok"
    })
    assert resp.status_code == 400


def test_submit_valid():
    resp = client.post("/api/submissions/", json={
        "user_id": 1,
        "mission_id": 1,
        "response": (
            "El resumen financiero muestra ingresos por comisiones de $45,200 con gastos "
            "operativos de $32,100, resultando en un margen positivo. La morosidad del 3.2% "
            "representa una alerta de riesgo que requiere atención inmediata. Recomiendo "
            "implementar un programa de fidelización para reducir cuentas cerradas y mejorar "
            "el NPS actual de 68 mediante capacitación del personal."
        )
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "score" in data
    assert 0 <= data["score"] <= 100
    assert "feedback" in data
    assert "attempt" in data


def test_submit_retry_increments_attempt():
    response_text = (
        "Propongo tres medidas para optimizar el proceso: primero, implementar verificación "
        "digital de documentos para reducir rechazos del 23%. Segundo, automatizar aprobaciones "
        "rutinarias para eliminar la dependencia del supervisor. Tercero, usar captura asistida "
        "para reducir errores del 8% actual."
    )
    r1 = client.post("/api/submissions/", json={
        "user_id": 1, "mission_id": 3, "response": response_text
    })
    r2 = client.post("/api/submissions/", json={
        "user_id": 1, "mission_id": 3, "response": response_text
    })
    assert r1.json()["attempt"] == 1
    assert r2.json()["attempt"] == 2


def test_submit_invalid_user():
    resp = client.post("/api/submissions/", json={
        "user_id": 99999,
        "mission_id": 1,
        "response": "Una respuesta válida con suficiente contenido para pasar el filtro de longitud mínima requerida."
    })
    assert resp.status_code == 404


def test_submission_history():
    resp = client.get("/api/submissions/history/1")
    assert resp.status_code == 200
    assert "history" in resp.json()


# ── API: Certification ─────────────────────────────────────────────────────────

def test_certification_not_qualified():
    resp = client.get("/api/certification/1")
    assert resp.status_code == 200
    data = resp.json()
    assert "is_certified" in data
    assert "message" in data


def test_certification_flow():
    """Full flow: create user, submit 5 missions, check certification."""
    create = client.post("/api/users/", json={
        "username": "cert_candidate_99",
        "name": "Candidato Certificación"
    })
    assert create.status_code == 200
    uid = create.json()["id"]

    long_response = (
        "Primero identifico los riesgos críticos en la cartera de crédito bancario. "
        "La morosidad elevada representa un riesgo alto que requiere provisiones adicionales. "
        "Segundo, propongo implementar un sistema de scoring crediticio automatizado. "
        "Tercero, recomiendo optimizar el proceso de apertura de cuentas para reducir el tiempo. "
        "Finalmente, sugiero establecer métricas de rentabilidad con KPIs mensuales de seguimiento. "
        "El ROI esperado es positivo según los indicadores de liquidez y margen actuales."
    )

    for mission_id in range(1, 6):
        resp = client.post("/api/submissions/", json={
            "user_id": uid,
            "mission_id": mission_id,
            "response": long_response
        })
        assert resp.status_code == 200

    cert_resp = client.get(f"/api/certification/{uid}")
    assert cert_resp.status_code == 200
    data = cert_resp.json()
    assert data["completed_missions"] >= 0
    assert "message" in data
