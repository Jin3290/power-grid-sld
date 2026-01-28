from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from .models import Component, Measurement, Report
from typing import List, Dict, Any

def create_component(db: Session, component_data: dict):
    component = Component(**component_data)
    db.add(component)
    db.commit()
    db.refresh(component)
    return component

def get_components(db: Session):
    return db.query(Component).all()

def get_component(db: Session, component_id: int):
    return db.query(Component).filter(Component.id == component_id).first()

def update_component(db: Session, component_id: int, component_data: dict):
    component = db.query(Component).filter(Component.id == component_id).first()
    if component:
        for key, value in component_data.items():
            setattr(component, key, value)
        db.commit()
        db.refresh(component)
    return component

def delete_component(db: Session, component_id: int):
    component = db.query(Component).filter(Component.id == component_id).first()
    if component:
        db.delete(component)
        db.commit()
    return component

def create_measurement(db: Session, measurement_data: dict):
    # Converti timestamp da stringa a datetime se necessario
    if 'timestamp' in measurement_data and isinstance(measurement_data['timestamp'], str):
        measurement_data['timestamp'] = datetime.fromisoformat(measurement_data['timestamp'])
    
    measurement = Measurement(**measurement_data)
    db.add(measurement)
    db.commit()
    db.refresh(measurement)
    return measurement

def get_measurements_for_report(db: Session, start_date: datetime, end_date: datetime):
    return db.query(Measurement).filter(
        Measurement.timestamp >= start_date,
        Measurement.timestamp <= end_date
    ).all()

def get_components_summary(db: Session):
    return db.query(
        Component.component_type,
        func.count(Component.id).label('count')
    ).group_by(Component.component_type).all()
