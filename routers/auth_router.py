"""
Auth router:
  POST /api/auth/register       — email + password signup
  POST /api/auth/login          — email + password login
  POST /api/auth/google         — Google ID token → JWT
  GET  /api/auth/me             — return current user from JWT
"""
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel, EmailStr
from typing import Optional
import sqlite3

from database import get_connection
from auth import (
    hash_password, verify_password,
    create_access_token, decode_access_token,
    verify_google_token,
)

router = APIRouter()


# ── Schemas ────────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    profession: str = "banking"


class LoginRequest(BaseModel):
    email: str
    password: str


class GoogleLoginRequest(BaseModel):
    id_token: str
    profession: str = "banking"


# ── Helpers ────────────────────────────────────────────────────────────────────

def _get_user_by_email(email: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def _get_user_by_id(user_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def _create_user(name: str, email: str, hashed_pw: Optional[str],
                 google_id: Optional[str], profession: str) -> dict:
    conn = get_connection()
    cursor = conn.cursor()
    # generate a unique username from email
    base = email.split("@")[0].replace(".", "_").replace("+", "_")[:30]
    username = base
    suffix = 1
    while True:
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        if not cursor.fetchone():
            break
        username = f"{base}_{suffix}"; suffix += 1

    cursor.execute("""
        INSERT INTO users (username, name, email, password_hash, google_id, profession)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (username, name, email, hashed_pw, google_id, profession))
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return _get_user_by_id(user_id)


def _token_response(user: dict) -> dict:
    token = create_access_token({"sub": str(user["id"]), "email": user["email"]})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "profession": user.get("profession", "banking"),
        },
    }


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.post("/register")
def register(req: RegisterRequest):
    if _get_user_by_email(req.email):
        raise HTTPException(status_code=400, detail="Ya existe una cuenta con este email")
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="La contraseña debe tener al menos 6 caracteres")
    hashed = hash_password(req.password)
    user = _create_user(req.name, req.email, hashed, None, req.profession)
    return _token_response(user)


@router.post("/login")
def login(req: LoginRequest):
    user = _get_user_by_email(req.email)
    if not user:
        raise HTTPException(status_code=401, detail="Email o contraseña incorrectos")
    if not user.get("password_hash"):
        raise HTTPException(status_code=400, detail="Esta cuenta usa login con Google")
    if not verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Email o contraseña incorrectos")
    return _token_response(user)


@router.post("/google")
async def google_login(req: GoogleLoginRequest):
    payload = await verify_google_token(req.id_token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token de Google inválido")

    google_id = payload.get("sub")
    email = payload.get("email", "")
    name = payload.get("name", email.split("@")[0])

    # Find by google_id first, then by email
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE google_id = ?", (google_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        user = dict(row)
    else:
        existing = _get_user_by_email(email)
        if existing:
            # Link Google ID to existing email account
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET google_id = ? WHERE id = ?",
                           (google_id, existing["id"]))
            conn.commit()
            conn.close()
            user = _get_user_by_id(existing["id"])
        else:
            user = _create_user(name, email, None, google_id, req.profession)

    return _token_response(user)


@router.get("/me")
def get_me(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token requerido")
    token = authorization.split(" ", 1)[1]
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
    user = _get_user_by_id(int(payload["sub"]))
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "profession": user.get("profession", "banking"),
        "created_at": user.get("created_at"),
    }
