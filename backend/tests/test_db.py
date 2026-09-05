"""Milestone 3 — Database tests."""

import pytest
from sqlalchemy import inspect

from app.db.base import Base
from app.db.models import User, Dataset, Project, AnalysisResult, Report
from app.db.session import engine, SessionLocal


@pytest.fixture(scope="module")
def db_engine():
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    return engine


def test_tables_exist(db_engine):
    inspector = inspect(db_engine)
    tables = inspector.get_table_names()
    for expected in ["users", "datasets", "projects", "analysis_results", "reports"]:
        assert expected in tables


def test_indexes_exist(db_engine):
    inspector = inspect(db_engine)
    assert "ix_users_email" in [i["name"] for i in inspector.get_indexes("users")]
    assert "ix_datasets_owner" in [i["name"] for i in inspector.get_indexes("datasets")]


def test_relationships_and_transactions():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Clear any previous test user with same email
        db.query(User).filter(User.email == "test@statlab.zim").delete()
        db.commit()
        # Create user -> project -> dataset -> analysis -> report
        with db.begin():
            user = User(email="test@statlab.zim", hashed_password="hashed", full_name="Test User")
            db.add(user)
            db.flush()
            project = Project(name="Test Project", owner_id=user.id, description="Demo")
            db.add(project)
            db.flush()
            dataset = Dataset(
                filename="sample.csv",
                original_filename="sample.csv",
                rows=10,
                columns=3,
                column_names=["a", "b", "c"],
                dtypes={"a": "int64"},
                owner_id=user.id,
                project_id=project.id,
            )
            db.add(dataset)
            db.flush()
            analysis = AnalysisResult(
                analysis_type="pearson",
                parameters={"x_col": "a", "y_col": "b"},
                result={"statistic": 0.5, "p_value": 0.01},
                dataset_id=dataset.id,
                project_id=project.id,
                owner_id=user.id,
            )
            db.add(analysis)
            db.flush()
            report = Report(
                title="Report 1",
                dataset_info={"rows": 10},
                methods=["pearson"],
                results={"r": 0.5},
                project_id=project.id,
                owner_id=user.id,
            )
            db.add(report)

        # Verify relationships
        assert db.query(User).filter(User.email == "test@statlab.zim").first() is not None
        proj = db.query(Project).filter(Project.name == "Test Project").first()
        assert proj is not None
        assert proj.owner.email == "test@statlab.zim"
        ds = db.query(Dataset).filter(Dataset.filename == "sample.csv").first()
        assert ds is not None
        assert ds.owner_id == proj.owner_id
        ar = db.query(AnalysisResult).filter(AnalysisResult.analysis_type == "pearson").first()
        assert ar is not None
        assert ar.dataset_id == ds.id

        # Timestamps
        assert proj.created_at is not None
        assert ds.created_at is not None

        # Test foreign key transaction rollback
        try:
            with db.begin():
                # Insert and rollback via exception
                bad = Project(name="Bad", owner_id="nonexistent")
                db.add(bad)
                db.flush()
                raise ValueError("rollback test")
        except Exception:
            pass
        # Ensure Bad not persisted
        assert db.query(Project).filter(Project.name == "Bad").first() is None

        # Primary key test
        assert user.id is not None
        assert dataset.id is not None

    finally:
        # Cleanup
        db.query(Report).filter(Report.title == "Report 1").delete()
        db.query(AnalysisResult).filter(AnalysisResult.analysis_type == "pearson").delete()
        db.query(Dataset).filter(Dataset.filename == "sample.csv").delete()
        db.query(Project).filter(Project.name == "Test Project").delete()
        db.query(User).filter(User.email == "test@statlab.zim").delete()
        db.commit()
        db.close()


def test_primary_keys_unique():
    db = SessionLocal()
    try:
        u1 = User(email="unique1@test.com", hashed_password="h")
        u2 = User(email="unique2@test.com", hashed_password="h")
        db.add_all([u1, u2])
        db.commit()
        assert u1.id != u2.id
        db.query(User).filter(User.email.in_(["unique1@test.com", "unique2@test.com"])).delete(synchronize_session=False)
        db.commit()
    finally:
        db.close()
