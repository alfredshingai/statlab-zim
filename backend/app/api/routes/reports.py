"""Reports — Milestone 7.

POST /reports/generate -> creates report record (no PDF yet, JSON)
GET  /reports
GET  /reports/{id}
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.routes.auth import get_current_user
from app.db.models import Report, Project, User
from app.db.session import get_db

router = APIRouter(prefix="/reports", tags=["reports"])


class GenerateReportRequest(BaseModel):
    project_id: str
    title: str
    dataset_info: dict | None = None
    methods: list[str] | None = None
    results: dict | None = None
    charts: list[dict] | None = None
    interpretation: str | None = None
    limitations: str | None = None


class ReportResponse(BaseModel):
    id: str
    title: str
    project_id: str
    dataset_info: dict | None
    methods: list[str] | None
    results: dict | None
    charts: list[dict] | None
    interpretation: str | None
    limitations: str | None
    created_at: str


@router.post("/generate", response_model=ReportResponse, status_code=201)
def generate_report(
    payload: GenerateReportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    proj = db.query(Project).filter(Project.id == payload.project_id, Project.owner_id == current_user.id).first()
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    rep = Report(
        title=payload.title,
        dataset_info=payload.dataset_info,
        methods=payload.methods,
        results=payload.results,
        charts=payload.charts,
        interpretation=payload.interpretation,
        limitations=payload.limitations,
        project_id=payload.project_id,
        owner_id=current_user.id,
    )
    db.add(rep)
    db.commit()
    db.refresh(rep)
    return ReportResponse(
        id=rep.id,
        title=rep.title,
        project_id=rep.project_id,
        dataset_info=rep.dataset_info,
        methods=rep.methods,
        results=rep.results,
        charts=rep.charts,
        interpretation=rep.interpretation,
        limitations=rep.limitations,
        created_at=rep.created_at.isoformat(),
    )


@router.get("", response_model=list[ReportResponse])
def list_reports(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rows = db.query(Report).filter(Report.owner_id == current_user.id).order_by(Report.created_at.desc()).all()
    return [
        ReportResponse(
            id=r.id,
            title=r.title,
            project_id=r.project_id,
            dataset_info=r.dataset_info,
            methods=r.methods,
            results=r.results,
            charts=r.charts,
            interpretation=r.interpretation,
            limitations=r.limitations,
            created_at=r.created_at.isoformat(),
        )
        for r in rows
    ]


@router.get("/{report_id}", response_model=ReportResponse)
def get_report(report_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    r = db.query(Report).filter(Report.id == report_id, Report.owner_id == current_user.id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Report not found")
    return ReportResponse(
        id=r.id,
        title=r.title,
        project_id=r.project_id,
        dataset_info=r.dataset_info,
        methods=r.methods,
        results=r.results,
        charts=r.charts,
        interpretation=r.interpretation,
        limitations=r.limitations,
        created_at=r.created_at.isoformat(),
    )
