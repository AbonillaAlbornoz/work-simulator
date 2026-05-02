import json
from fastapi import APIRouter, HTTPException
from models.schemas import SubmissionRequest
from services.evaluator import evaluate_with_ai
from database import get_connection

router = APIRouter()
PASS_SCORE = 70


@router.post("/")
async def submit_response(submission: SubmissionRequest):
    """Submit a mission response. Validates unlock status before evaluating."""
    if not submission.response or len(submission.response.strip()) < 10:
        raise HTTPException(status_code=400, detail="La respuesta es demasiado corta")

    conn = get_connection()
    cursor = conn.cursor()

    # Validate user
    cursor.execute("SELECT id, name FROM users WHERE id=?", (submission.user_id,))
    user = cursor.fetchone()
    if not user:
        conn.close()
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Validate mission exists
    cursor.execute("SELECT * FROM missions WHERE id=?", (submission.mission_id,))
    mission = cursor.fetchone()
    if not mission:
        conn.close()
        raise HTTPException(status_code=404, detail="Misión no encontrada")

    mission = dict(mission)
    order = mission.get("order", mission["id"])

    # Check unlock: mission 1 is always open; others need previous passed
    if order > 1:
        cursor.execute("""
            SELECT MAX(r.score) as best
            FROM results r
            JOIN missions prev ON prev.id = r.mission_id
            WHERE r.user_id=? AND prev."order"=?
        """, (submission.user_id, order - 1))
        prev = cursor.fetchone()
        if not prev or prev["best"] is None or prev["best"] < PASS_SCORE:
            conn.close()
            raise HTTPException(
                status_code=403,
                detail="Misión bloqueada. Completa la misión anterior con score ≥ 70."
            )

    # Count previous attempts for this user+mission
    cursor.execute(
        "SELECT COUNT(*) as cnt FROM results WHERE user_id=? AND mission_id=?",
        (submission.user_id, submission.mission_id)
    )
    attempt = cursor.fetchone()["cnt"] + 1

    # Fetch previous best for comparison
    cursor.execute(
        "SELECT MAX(score) as best FROM results WHERE user_id=? AND mission_id=?",
        (submission.user_id, submission.mission_id)
    )
    prev_best_row = cursor.fetchone()
    prev_best = prev_best_row["best"] if prev_best_row and prev_best_row["best"] is not None else None

    conn.close()

    # Evaluate
    evaluation = await evaluate_with_ai(
        mission_title=mission["title"],
        mission_description=mission["description"],
        mission_criteria=mission["criteria"],
        mission_structure=mission.get("expected_structure", ""),
        user_response=submission.response,
    )

    # Persist
    conn = get_connection()
    cursor = conn.cursor()
    action_plan_json = json.dumps(evaluation.get("action_plan", []), ensure_ascii=False)
    cursor.execute("""
        INSERT INTO results (user_id, mission_id, response, score, feedback, action_plan, attempt)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        submission.user_id, submission.mission_id, submission.response,
        evaluation["score"], evaluation["feedback"], action_plan_json, attempt
    ))
    result_id = cursor.lastrowid
    conn.commit()
    conn.close()

    score = evaluation["score"]
    score_delta = (score - prev_best) if prev_best is not None else None

    return {
        "id": result_id,
        "user_id": submission.user_id,
        "mission_id": submission.mission_id,
        "mission_title": mission["title"],
        "score": score,
        "feedback": evaluation["feedback"],
        "strengths": evaluation.get("strengths", []),
        "improvements": evaluation.get("improvements", []),
        "action_plan": evaluation.get("action_plan", []),
        "attempt": attempt,
        "passed": score >= PASS_SCORE,
        "prev_best": prev_best,
        "score_delta": score_delta,
    }


@router.get("/history/{user_id}")
def get_submission_history(user_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE id=?", (user_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    cursor.execute("""
        SELECT r.id, r.mission_id, r.score, r.attempt, r.submitted_at,
               m.title as mission_title, m.level as mission_level
        FROM results r
        JOIN missions m ON r.mission_id = m.id
        WHERE r.user_id=?
        ORDER BY r.submitted_at DESC
    """, (user_id,))
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return {"user_id": user_id, "history": results, "total": len(results)}
