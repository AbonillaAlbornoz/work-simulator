from fastapi import APIRouter, HTTPException
from models.schemas import SubmissionRequest
from services.evaluator import evaluate_with_ai
from database import get_connection

router = APIRouter()

REQUIRED_MISSIONS = 5
REQUIRED_AVG_SCORE = 70


@router.post("/")
async def submit_response(submission: SubmissionRequest):
    """Submit a mission response and receive AI evaluation."""
    if not submission.response or len(submission.response.strip()) < 10:
        raise HTTPException(status_code=400, detail="La respuesta es demasiado corta")

    conn = get_connection()
    cursor = conn.cursor()

    # Validate user
    cursor.execute("SELECT id, name FROM users WHERE id = ?", (submission.user_id,))
    user = cursor.fetchone()
    if not user:
        conn.close()
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Validate mission
    cursor.execute("SELECT * FROM missions WHERE id = ?", (submission.mission_id,))
    mission = cursor.fetchone()
    if not mission:
        conn.close()
        raise HTTPException(status_code=404, detail="Misión no encontrada")

    # Get attempt number
    cursor.execute(
        "SELECT COUNT(*) as cnt FROM results WHERE user_id = ? AND mission_id = ?",
        (submission.user_id, submission.mission_id)
    )
    attempt = cursor.fetchone()["cnt"] + 1

    conn.close()

    # Evaluate with AI
    evaluation = await evaluate_with_ai(
        mission_title=mission["title"],
        mission_description=mission["description"],
        mission_criteria=mission["criteria"],
        user_response=submission.response,
    )

    # Save result
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO results (user_id, mission_id, response, score, feedback, attempt)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        submission.user_id,
        submission.mission_id,
        submission.response,
        evaluation["score"],
        evaluation["feedback"],
        attempt
    ))
    result_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return {
        "id": result_id,
        "user_id": submission.user_id,
        "mission_id": submission.mission_id,
        "mission_title": mission["title"],
        "score": evaluation["score"],
        "feedback": evaluation["feedback"],
        "strengths": evaluation.get("strengths", []),
        "improvements": evaluation.get("improvements", []),
        "attempt": attempt,
        "passed": evaluation["score"] >= 70,
    }


@router.get("/history/{user_id}")
def get_submission_history(user_id: int):
    """Get all submissions for a user."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    cursor.execute("""
        SELECT r.*, m.title as mission_title, m.level as mission_level
        FROM results r
        JOIN missions m ON r.mission_id = m.id
        WHERE r.user_id = ?
        ORDER BY r.submitted_at DESC
    """, (user_id,))
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return {"user_id": user_id, "history": results, "total": len(results)}
