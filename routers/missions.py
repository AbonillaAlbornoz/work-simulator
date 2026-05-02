import json
from fastapi import APIRouter, HTTPException
from database import get_connection

router = APIRouter()
PASS_SCORE = 70


def _mission_with_status(mission: dict, user_id: int, cursor) -> dict:
    """Enrich a mission dict with unlocked/completed status for a given user."""
    m = dict(mission)
    order = m.get("order", m["id"])

    # Best score for this mission
    cursor.execute(
        "SELECT MAX(score) as best FROM results WHERE user_id=? AND mission_id=?",
        (user_id, m["id"])
    )
    row = cursor.fetchone()
    best_score = row["best"] if row and row["best"] is not None else None
    m["best_score"] = best_score
    m["completed"] = best_score is not None and best_score >= PASS_SCORE

    # Unlocked if it's the first mission OR the previous one is completed
    if order <= 1:
        m["unlocked"] = True
    else:
        cursor.execute("""
            SELECT MAX(r.score) as best
            FROM results r
            JOIN missions prev ON prev.id = r.mission_id
            WHERE r.user_id = ? AND prev."order" = ?
        """, (user_id, order - 1))
        prev = cursor.fetchone()
        m["unlocked"] = prev and prev["best"] is not None and prev["best"] >= PASS_SCORE

    return m


@router.get("/")
def list_missions(user_id: int = 1):
    """List missions with unlock/completion status for a user."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM missions ORDER BY "order"')
    missions = [_mission_with_status(dict(row), user_id, cursor)
                for row in cursor.fetchall()]
    conn.close()
    return {"missions": missions, "total": len(missions)}


@router.get("/{mission_id}")
def get_mission(mission_id: int, user_id: int = 1):
    """Get a mission with unlock status. Returns 403 if locked."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM missions WHERE id=?", (mission_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Misión no encontrada")

    mission = _mission_with_status(dict(row), user_id, cursor)

    if not mission["unlocked"]:
        conn.close()
        raise HTTPException(
            status_code=403,
            detail="Misión bloqueada. Completa la misión anterior con score ≥ 70 para desbloquearla."
        )

    # Attach attempt history for retry loop
    cursor.execute("""
        SELECT id, score, attempt, submitted_at
        FROM results
        WHERE user_id=? AND mission_id=?
        ORDER BY attempt ASC
    """, (user_id, mission_id))
    mission["attempts_history"] = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return mission
