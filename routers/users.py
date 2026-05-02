from fastapi import APIRouter, HTTPException
from models.schemas import UserCreate
from database import get_connection

router = APIRouter()
REQUIRED_MISSIONS = 5
REQUIRED_AVG_SCORE = 70


@router.post("/")
def create_user(user: UserCreate):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        profession = getattr(user, 'profession', 'banking') or 'banking'
        cursor.execute(
            "INSERT INTO users (username, name, email, profession) VALUES (?, ?, ?, ?)",
            (user.username, user.name, user.email, profession)
        )
        user_id = cursor.lastrowid
        conn.commit()
    except Exception:
        conn.close()
        raise HTTPException(status_code=400, detail="El nombre de usuario ya existe")
    conn.close()
    return {"id": user_id, "username": user.username, "name": user.name,
            "email": user.email, "profession": profession}


@router.get("/{user_id}")
def get_user(user_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id=?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return dict(user)


@router.patch("/{user_id}/profession")
def update_profession(user_id: int, payload: dict):
    """Switch the active profession for a user."""
    profession = payload.get("profession", "banking")
    if profession not in ("banking", "legal"):
        raise HTTPException(status_code=400, detail="Profesión no válida")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET profession=? WHERE id=?", (profession, user_id))
    conn.commit()
    conn.close()
    return {"user_id": user_id, "profession": profession}


@router.get("/{user_id}/progress")
def get_user_progress(user_id: int, profession: str = "banking"):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE id=?", (user_id,))
    user = cursor.fetchone()
    if not user:
        conn.close()
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    cursor.execute("""
        SELECT r.mission_id, m.title, m.level,
               MAX(r.score) as best_score,
               COUNT(r.id) as attempts,
               MAX(r.submitted_at) as last_attempt
        FROM results r
        JOIN missions m ON r.mission_id = m.id
        WHERE r.user_id=? AND m.profession=?
        GROUP BY r.mission_id
    """, (user_id, profession))
    mission_results = [dict(row) for row in cursor.fetchall()]

    cursor.execute("SELECT COUNT(*) as total FROM missions WHERE profession=?", (profession,))
    total_missions = cursor.fetchone()["total"]
    conn.close()

    completed = len([r for r in mission_results if r["best_score"] >= 70])
    avg_score = (
        sum(r["best_score"] for r in mission_results) / len(mission_results)
        if mission_results else 0
    )
    is_certified = completed >= REQUIRED_MISSIONS and avg_score >= REQUIRED_AVG_SCORE

    return {
        "user_id": user_id,
        "user_name": user["name"],
        "profession": profession,
        "completed_missions": completed,
        "total_missions": total_missions,
        "average_score": round(avg_score, 1),
        "mission_results": mission_results,
        "is_certified": is_certified,
        "required_missions": REQUIRED_MISSIONS,
        "required_score": REQUIRED_AVG_SCORE,
    }
