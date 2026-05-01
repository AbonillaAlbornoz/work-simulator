from fastapi import APIRouter, HTTPException
from database import get_connection

router = APIRouter()


@router.get("/")
def list_missions():
    """List all available missions."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM missions ORDER BY id")
    missions = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return {"missions": missions, "total": len(missions)}


@router.get("/{mission_id}")
def get_mission(mission_id: int):
    """Get a specific mission by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM missions WHERE id = ?", (mission_id,))
    mission = cursor.fetchone()
    conn.close()
    if not mission:
        raise HTTPException(status_code=404, detail="Misión no encontrada")
    return dict(mission)
