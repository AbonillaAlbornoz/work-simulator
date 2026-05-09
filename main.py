from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database import init_db
from routers import missions, submissions, users, certification
from routers.auth_router import router as auth_router
from routers.certificate_router import router as certificate_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="WorkSim AI API",
    description="Plataforma de entrenamiento profesional con IA",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router,        prefix="/api/auth",        tags=["Auth"])
app.include_router(certificate_router, prefix="/api/certificate",  tags=["Certificate"])
app.include_router(missions.router,    prefix="/api/missions",    tags=["Missions"])
app.include_router(submissions.router, prefix="/api/submissions", tags=["Submissions"])
app.include_router(users.router,       prefix="/api/users",       tags=["Users"])
app.include_router(certification.router, prefix="/api/certification", tags=["Certification-legacy"])


@app.get("/")
def root():
    return {"message": "WorkSim AI API v2.0", "status": "running"}
