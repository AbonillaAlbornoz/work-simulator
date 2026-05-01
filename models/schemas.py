from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class Mission(BaseModel):
    id: int
    title: str
    description: str
    level: str
    criteria: str
    max_score: int = 100


class User(BaseModel):
    id: int
    username: str
    name: str
    email: Optional[str] = None
    created_at: Optional[str] = None


class UserCreate(BaseModel):
    username: str
    name: str
    email: Optional[str] = None


class SubmissionRequest(BaseModel):
    user_id: int
    mission_id: int
    response: str


class EvaluationResult(BaseModel):
    score: int
    feedback: str
    strengths: list[str] = []
    improvements: list[str] = []


class SubmissionResponse(BaseModel):
    id: int
    user_id: int
    mission_id: int
    score: int
    feedback: str
    attempt: int
    submitted_at: str


class UserProgress(BaseModel):
    user_id: int
    completed_missions: int
    total_missions: int
    average_score: float
    results: list[dict]
    is_certified: bool


class CertificationStatus(BaseModel):
    user_id: int
    is_certified: bool
    completed_missions: int
    average_score: float
    required_missions: int
    required_score: int
    message: str
