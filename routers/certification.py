from fastapi import APIRouter, HTTPException
from database import get_connection

router = APIRouter()

REQUIRED_MISSIONS = 5
REQUIRED_AVG_SCORE = 70


@router.get("/{user_id}")
def check_certification(user_id: int):
    """Check if user qualifies for certification."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    if not user:
        conn.close()
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    cursor.execute("""
        SELECT mission_id, MAX(score) as best_score
        FROM results
        WHERE user_id = ?
        GROUP BY mission_id
    """, (user_id,))
    results = cursor.fetchall()
    conn.close()

    completed = [r for r in results if r["best_score"] >= 70]
    total_completed = len(completed)
    avg_score = (
        sum(r["best_score"] for r in results) / len(results)
        if results else 0
    )

    is_certified = total_completed >= REQUIRED_MISSIONS and avg_score >= REQUIRED_AVG_SCORE

    if is_certified:
        message = (
            f"🏆 ¡Felicitaciones {user['name']}! Has obtenido la certificación en "
            f"Habilidades Profesionales Bancarias con IA. "
            f"Completaste {total_completed} misiones con un promedio de {avg_score:.1f}/100."
        )
    elif total_completed < REQUIRED_MISSIONS:
        remaining = REQUIRED_MISSIONS - total_completed
        message = (
            f"Necesitas completar {remaining} misión(es) más con score ≥ 70 "
            f"para obtener la certificación."
        )
    else:
        needed = REQUIRED_AVG_SCORE - avg_score
        message = (
            f"Tienes las misiones completadas, pero tu promedio ({avg_score:.1f}) "
            f"necesita subir {needed:.1f} puntos más para la certificación."
        )

    return {
        "user_id": user_id,
        "user_name": user["name"],
        "is_certified": is_certified,
        "completed_missions": total_completed,
        "average_score": round(avg_score, 1),
        "required_missions": REQUIRED_MISSIONS,
        "required_score": REQUIRED_AVG_SCORE,
        "message": message,
    }
