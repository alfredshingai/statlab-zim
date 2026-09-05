"""Project endpoints — Milestone 3 + 5.

- POST /projects (protected, user-specific)
- GET  /projects
- GET  /projects/{id}
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.routes.auth import get_current_user
from app.db.models import Project, User
from app.db.session import get_db

router = APIRouter(prefix="/projects", tags=["projects"])


class CreateProjectRequest(BaseModel):
    name: str
    description: str | None = None


class ProjectResponse(BaseModel):
    id: str
    name: str
    description: str | None
    owner_id: str
    created_at: str
    updated_at: str


@router.post("", response_model=ProjectResponse, status_code=201)
def create_project(
    payload: CreateProjectRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    proj = Project(name=payload.name, description=payload.description, owner_id=current_user.id)
    db.add(proj)
    db.commit()
    db.refresh(proj)
    return ProjectResponse(
        id=proj.id,
        name=proj.name,
        description=proj.description,
        owner_id=proj.owner_id,
        created_at=proj.created_at.isoformat(),
        updated_at=proj.updated_at.isoformat(),
    )


@router.get("", response_model=list[ProjectResponse])
def list_projects(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rows = db.query(Project).filter(Project.owner_id == current_user.id).order_by(Project.created_at.desc()).all()
    return [
        ProjectResponse(
            id=r.id,
            name=r.name,
            description=r.description,
            owner_id=r.owner_id,
            created_at=r.created_at.isoformat(),
            updated_at=r.updated_at.isoformat(),
        )
        for r in rows
    ]


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    proj = db.query(Project).filter(Project.id == project_id, Project.owner_id == current_user.id).first()
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectResponse(
        id=proj.id,
        name=proj.name,
        description=proj.description,
        owner_id=proj.owner_id,
        created_at=proj.created_at.isoformat(),
        updated_at=proj.updated_at.isoformat(),
    )
