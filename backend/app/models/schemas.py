from typing import Any, Optional
from pydantic import BaseModel, Field


# ---------- Auth ----------
class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    role: str


# ---------- Chat / Analysis ----------
class AskRequest(BaseModel):
    question: str = Field(..., min_length=3)
    region: Optional[str] = None


class Citation(BaseModel):
    source_type: str          # postgres | slack | csv | jira | salesforce | google_sheets | vector_store
    source_name: str
    reference: str            # e.g. table name, channel, filename, doc id
    snippet: str
    record_count: Optional[int] = None


class TraceStep(BaseModel):
    step_id: int
    node: str                 # LangGraph node name
    action: str
    tool: Optional[str] = None
    input: Optional[Any] = None
    output_summary: Optional[str] = None
    status: str                # success | error
    duration_ms: float
    timestamp: str


class RootCause(BaseModel):
    rank: str                  # primary | secondary
    description: str
    metric: str
    change_pct: float
    evidence_count: int


class Recommendation(BaseModel):
    title: str
    detail: str
    estimated_impact: str
    priority: str              # high | medium | low


class AnalysisResponse(BaseModel):
    request_id: str
    question: str
    executive_summary: str
    root_causes: list[RootCause]
    recommendations: list[Recommendation]
    citations: list[Citation]
    trace: list[TraceStep]
    kpi_snapshot: dict[str, Any]


# ---------- KPI ----------
class KPI(BaseModel):
    name: str
    value: float
    unit: str
    change_pct: float
    trend: str                 # up | down | flat
    is_anomaly: bool = False
