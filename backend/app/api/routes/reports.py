"""Reports — Milestone 7.

POST /reports/generate -> creates report record (no PDF yet, JSON)
GET  /reports
GET  /reports/{id}
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse, Response
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


def _render_html(report: Report) -> str:
    # Minimal styled HTML for download/print — no external deps, free tier safe
    import json
    import html as h

    def j(v):
        try:
            return h.escape(json.dumps(v, indent=2)[:2000])
        except Exception:
            return h.escape(str(v)[:2000])

    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>{h.escape(report.title)}</title>
<style>
body{{font-family:system-ui,sans-serif;max-width:800px;margin:32px auto;padding:24px;color:#111}}
h1{{border-bottom:2px solid #111;padding-bottom:8px}} h2{{color:#333;border-bottom:1px solid #eee;padding-bottom:4px}}
pre{{background:#f6f7f8;padding:12px;border-radius:8px;overflow:auto;font-size:12px}} .meta{{color:#666;font-size:12px}}
</style></head><body>
<h1>📊 {h.escape(report.title)}</h1>
<p class="meta">Report ID: {report.id} | Project: {report.project_id} | Created: {report.created_at.isoformat() if report.created_at else ""}</p>
<h2>Dataset Information</h2><pre>{j(report.dataset_info)}</pre>
<h2>Methods Used</h2><pre>{j(report.methods)}</pre>
<h2>Results (Verified)</h2><pre>{j(report.results)}</pre>
<h2>Charts</h2><pre>{j(report.charts)}</pre>
<h2>Interpretation</h2><p>{h.escape(report.interpretation or "See results")}</p>
<h2>Limitations</h2><p>{h.escape(report.limitations or "Check assumptions; not a substitute for expert review.")}</p>
<hr><p class="meta">Generated by StatLab Zim — all numbers from Python verification; AI only drafted prose. <a href="/docs">API Docs</a></p>
</body></html>"""


@router.get("/{report_id}/html", response_class=HTMLResponse, summary="Report as HTML (download/print)")
def get_report_html(report_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    r = db.query(Report).filter(Report.id == report_id, Report.owner_id == current_user.id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Report not found")
    return HTMLResponse(content=_render_html(r))


@router.get("/{report_id}/download", summary="Report download (HTML file)")
def download_report(report_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    r = db.query(Report).filter(Report.id == report_id, Report.owner_id == current_user.id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Report not found")
    html = _render_html(r)
    headers = {"Content-Disposition": f'attachment; filename="report-{report_id}.html"'}
    return Response(content=html, media_type="text/html", headers=headers)
