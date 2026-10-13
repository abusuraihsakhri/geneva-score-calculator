"""
FastAPI REST API Server for Geneva Score Calculator.
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, StrictBool
from fastapi.responses import FileResponse
from pathlib import Path
from geneva import calculate_score
from .base import AuditLogger, PHIGuard
from .models import SystemTaskPayload, ConsensusDossier
from .supervisor import SystemSupervisor

supervisor = SystemSupervisor(model_provider="mock")

app = FastAPI(
    title="Geneva Score Calculator API",
    description="Enterprise Distributed Component Platform (Clinical & Biomedical AI)",
    version="3.1.0",
)


class ChatRequest(BaseModel):
    query: str


@app.get("/health")
def health():
    return {"status": "HEALTHY", "service": "geneva-score-calculator", "domain": "Clinical & Biomedical AI", "standard": "CAP / CLSI / ISO Standards", "version": "3.0.0-ENTERPRISE"}


@app.get("/metrics")
def metrics():
    return {
        "dossiers_processed_total": len(supervisor.dossier_registry),
        "audit_blocks_total": len(AuditLogger.get_trail()),
        "system_status": "NOMINAL_OPTIMAL"
    }


@app.post("/api/audit")
def api_audit(payload: SystemTaskPayload):
    dossier = supervisor.process_task(payload)
    return dossier.to_dict()


@app.post("/api/chat")
def api_chat(req: ChatRequest):
    try:
        ans = supervisor.query_supervisory_chat(req.query)
        return {"response": ans}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/audit/logs")
def api_audit_logs():
    return {"audit_trail": AuditLogger.get_trail(), "verified": AuditLogger.verify_integrity()}


# Independent clinical scoring endpoint; legacy audit endpoints above are unrelated.
# The clinical calculator never forwards the submitted criteria to the audit agents.
class GenevaScoreRequest(BaseModel):
    age: float = Field(ge=0, le=120, allow_inf_nan=False)
    heart_rate: float = Field(gt=0, le=300, allow_inf_nan=False)
    previous_dvt_pe: StrictBool
    surgery_or_fracture_1mo: StrictBool
    active_malignancy: StrictBool
    unilateral_leg_pain: StrictBool
    hemoptysis: StrictBool
    deep_vein_tenderness_and_unilateral_edema: StrictBool


@app.post("/api/geneva")
def api_geneva_score(payload: GenevaScoreRequest):
    return calculate_score(payload.model_dump())


WEB_ROOT = Path(__file__).resolve().parent.parent / "web"


@app.get("/", include_in_schema=False)
def calculator_home():
    return FileResponse(WEB_ROOT / "index.html")


@app.get("/calculator.js", include_in_schema=False)
def browser_scoring_script():
    return FileResponse(WEB_ROOT / "calculator.js", media_type="text/javascript")


@app.get("/ui.js", include_in_schema=False)
def browser_ui_script():
    return FileResponse(WEB_ROOT / "ui.js", media_type="text/javascript")
