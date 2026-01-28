from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List
import asyncio
import json

from .database import get_db, create_tables
from .models import User, Component, Measurement, Report
from .auth import (
    get_current_user, require_manager, create_access_token,
    verify_password, get_password_hash
)
from .crud import *
from .reports import generate_report_async

app = FastAPI(title="Power Grid SLD API", version="1.0.0")


# Create tables on startup
@app.on_event("startup")
def startup_event():
    create_tables()

    # Create default users
    db = next(get_db())

    # Create manager user
    manager = db.query(User).filter(User.username == "manager").first()
    if not manager:
        manager = User(
            username="manager",
            hashed_password=get_password_hash("manager123"),
            role="manager"
        )
        db.add(manager)

    # Create regular user
    user = db.query(User).filter(User.username == "user").first()
    if not user:
        user = User(
            username="user",
            hashed_password=get_password_hash("user123"),
            role="user"
        )
        db.add(user)

    db.commit()


# Authentication endpoints
@app.post("/login")
def login(username: str, password: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer", "role": user.role}


# Component endpoints
@app.get("/components")
def list_components(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return get_components(db)


@app.post("/components")
def create_component_endpoint(
        component_data: dict,
        current_user: User = Depends(require_manager),
        db: Session = Depends(get_db)
):
    return create_component(db, component_data)


@app.put("/components/{component_id}")
def update_component_endpoint(
        component_id: int,
        component_data: dict,
        current_user: User = Depends(require_manager),
        db: Session = Depends(get_db)
):
    component = update_component(db, component_id, component_data)
    if not component:
        raise HTTPException(status_code=404, detail="Component not found")
    return component


@app.delete("/components/{component_id}")
def delete_component_endpoint(
        component_id: int,
        current_user: User = Depends(require_manager),
        db: Session = Depends(get_db)
):
    component = delete_component(db, component_id)
    if not component:
        raise HTTPException(status_code=404, detail="Component not found")
    return {"message": "Component deleted"}


# Measurement endpoints
@app.post("/measurements")
def create_measurement_endpoint(
        measurement_data: dict,
        current_user: User = Depends(require_manager),
        db: Session = Depends(get_db)
):
    return create_measurement(db, measurement_data)


# Report endpoints
@app.post("/reports")
def create_report(
        start_date: str,
        end_date: str,
        background_tasks: BackgroundTasks,
        current_user: User = Depends(require_manager),
        db: Session = Depends(get_db)
):
    start_dt = datetime.fromisoformat(start_date)
    end_dt = datetime.fromisoformat(end_date)

    report = Report(start_date=start_dt, end_date=end_dt)
    db.add(report)
    db.commit()
    db.refresh(report)

    # Schedule background task
    background_tasks.add_task(generate_report_async, db, start_dt, end_dt, report.id)

    return {"report_id": report.id, "status": "pending"}


@app.get("/reports")
def list_reports(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    reports = db.query(Report).all()
    return [
        {
            "id": r.id,
            "created_at": r.created_at,
            "start_date": r.start_date,
            "end_date": r.end_date,
            "status": r.status
        }
        for r in reports
    ]


@app.get("/reports/{report_id}")
def get_report(
        report_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    result = {
        "id": report.id,
        "created_at": report.created_at,
        "start_date": report.start_date,
        "end_date": report.end_date,
        "status": report.status
    }

    if report.status == "completed" and report.data:
        result["data"] = json.loads(report.data)

    return result


# Health check
@app.get("/health")
def health_check():
    return {"status": "healthy"}
