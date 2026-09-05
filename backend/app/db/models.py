"""SQLAlchemy models — Milestone 3.

Stores: Users, Datasets, Analysis Projects, Analysis Results, Report Metadata.
Learning: tables, relationships, primary/foreign keys, indexes, timestamps.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    JSON,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


def _uuid():
    return str(uuid.uuid4())


def _now():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=_uuid)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=_now, onupdate=_now)

    datasets = relationship("Dataset", back_populates="owner", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="owner", cascade="all, delete-orphan")

    __table_args__ = (Index("ix_users_email", "email"),)


class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(String(36), primary_key=True, default=_uuid)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=True)  # object storage later
    file_size = Column(Integer, nullable=True)
    rows = Column(Integer, nullable=False)
    columns = Column(Integer, nullable=False)
    column_names = Column(JSON, nullable=False)  # list[str]
    dtypes = Column(JSON, nullable=True)
    # Optional: store preview as JSON for quick fetch
    preview = Column(JSON, nullable=True)

    owner_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    owner = relationship("User", back_populates="datasets")

    project_id = Column(String(36), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True)
    project = relationship("Project", back_populates="datasets")

    created_at = Column(DateTime(timezone=True), default=_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=_now, onupdate=_now)

    analyses = relationship("AnalysisResult", back_populates="dataset", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_datasets_owner", "owner_id"),
        Index("ix_datasets_project", "project_id"),
        Index("ix_datasets_created", "created_at"),
    )


class Project(Base):
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True, default=_uuid)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    owner_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    owner = relationship("User", back_populates="projects")

    datasets = relationship("Dataset", back_populates="project")
    analyses = relationship("AnalysisResult", back_populates="project", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="project", cascade="all, delete-orphan")

    created_at = Column(DateTime(timezone=True), default=_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=_now, onupdate=_now)

    __table_args__ = (
        Index("ix_projects_owner", "owner_id"),
        Index("ix_projects_name", "name"),
    )


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(String(36), primary_key=True, default=_uuid)
    analysis_type = Column(String(50), nullable=False)  # descriptive, pearson, etc.
    parameters = Column(JSON, nullable=True)  # input columns, alpha, etc.
    result = Column(JSON, nullable=False)  # structured JSON from stats_tests
    # For reproducibility: store dataset snapshot hash or version
    dataset_id = Column(String(36), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    dataset = relationship("Dataset", back_populates="analyses")

    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=True)
    project = relationship("Project", back_populates="analyses")

    owner_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)

    created_at = Column(DateTime(timezone=True), default=_now, nullable=False)

    __table_args__ = (
        Index("ix_analysis_dataset", "dataset_id"),
        Index("ix_analysis_type", "analysis_type"),
    )


class Report(Base):
    __tablename__ = "reports"

    id = Column(String(36), primary_key=True, default=_uuid)
    title = Column(String(255), nullable=False)
    dataset_info = Column(JSON, nullable=True)
    methods = Column(JSON, nullable=True)  # list of methods used
    results = Column(JSON, nullable=True)
    charts = Column(JSON, nullable=True)  # references to charts
    interpretation = Column(Text, nullable=True)
    limitations = Column(Text, nullable=True)

    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    project = relationship("Project", back_populates="reports")

    owner_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)

    created_at = Column(DateTime(timezone=True), default=_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=_now, onupdate=_now)

    __table_args__ = (Index("ix_reports_project", "project_id"),)
