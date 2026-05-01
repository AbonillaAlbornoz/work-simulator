from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database import init_db
from routers import missions, submissions, users, certification

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(
    title="Banking Simulator API",
    description="Simulador Profesional con IA para el sector bancario",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(missions.router, prefix="/api/missions", tags=["Missions"])
app.include_router(submissions.router, prefix="/api/submissions", tags=["Submissions"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(certification.router, prefix="/api/certification", tags=["Certification"])

@app.get("/")
def root():
    return {"message": "Banking Simulator API v1.0", "status": "running"}
