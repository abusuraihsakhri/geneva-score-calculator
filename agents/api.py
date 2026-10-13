"""
FastAPI REST API Server for Geneva Score Calculator.
"""
from fastapi import FastAPI, HTTPException, Header, Depends
import os
import hmac
from pydantic import BaseModel, Field, StrictBool, ConfigDict
from fastapi.responses import FileResponse
from pathlib import Path
from geneva import calculate_score
from .base import AuditLogger, PHIGuard
from .models import SystemTaskPayload, ConsensusDossier
from .supervisor import SystemSupervisor

supervisor = SystemSupervisor(model_provider="mock")

app = FastAPI(
    title="Geneva Score Calculator API",
    description="Revised Geneva PE pretest probability score; separate nonclinical legacy prototype endpoints.",
    version="3.1.0",
)


class ChatRequest(BaseModel):
    query: str


@app.get("/health")
def health():
    return {"status": "HEALTHY", "service": "geneva-score-calculator", "version": "3.1.0"}


@app.get("/metrics")
def metrics():
    return {
        "dossiers_processed_total": len(supervisor.dossier_registry),
        "audit_blocks_total": len(AuditLogger.get_trail()),
        "system_status": "NOMINAL_OPTIMAL"
    }



def require_legacy_token(x_legacy_token: str | None = Header(default=None)):
    """Disable the nonclinical legacy API unless an operator configures a token."""
    expected = os.environ.get("GENEVA_LEGACY_API_TOKEN")
    if not expected or not x_legacy_token or not hmac.compare_digest(expected, x_legacy_token):
        raise HTTPException(status_code=403, detail="Legacy API access is disabled or unauthorized")


@app.post("/api/audit")
def api_audit(payload: SystemTaskPayload, _auth: None = Depends(require_legacy_token)):
    dossier = supervisor.process_task(payload)
    return dossier.to_dict()


@app.post("/api/chat")
def api_chat(req: ChatRequest, _auth: None = Depends(require_legacy_token)):
    try:
        ans = supervisor.query_supervisory_chat(req.query)
        return {"response": ans}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/audit/logs")
def api_audit_logs(_auth: None = Depends(require_legacy_token)):
    return {"audit_trail": AuditLogger.get_trail(), "verified": AuditLogger.verify_integrity()}


# Independent clinical scoring endpoint; legacy audit endpoints above are unrelated.
# The clinical calculator never forwards the submitted criteria to the audit agents.
class GenevaScoreRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
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
