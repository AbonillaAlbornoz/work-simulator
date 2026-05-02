import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database import init_db
from routers import missions, submissions, users, certification


# Lifespan para inicializar la DB
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Inicializando base de datos...")
    init_db()
    print("Base de datos lista")
    yield
    print("Apagando aplicación...")


# Crear app
app = FastAPI(
    title="Banking Simulator API",
    description="Simulador Profesional con IA para el sector bancario",
    version="1.0.0",
    lifespan=lifespan
)


# CORS (para frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Routers
app.include_router(missions.router, prefix="/api/missions", tags=["Missions"])
app.include_router(submissions.router, prefix="/api/submissions", tags=["Submissions"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(certification.router, prefix="/api/certification", tags=["Certification"])


# Health check (clave para Render)
@app.get("/")
def root():
    return {
        "message": "Banking Simulator API v1.0",
        "status": "running"
    }


# 🚀 Entry point (CLAVE para cloud)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))  # Render usa PORT
    uvicorn.run(app, host="0.0.0.0", port=port)