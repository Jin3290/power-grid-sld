import json
import asyncio
from datetime import datetime
from sqlalchemy.orm import Session
from .models import Report, Component, Measurement
from .crud import get_measurements_for_report, get_components_summary
from sqlalchemy import func


async def generate_report_async(db: Session, start_date: datetime, end_date: datetime, report_id: int):
    """Generate report asynchronously"""
    try:
        # Simulate long processing
        await asyncio.sleep(2)

        # Get components summary
        components_summary = {}
        for comp_type, count in get_components_summary(db):
            components_summary[comp_type] = count

        # Get transformer capacity by voltage
        transformer_capacity = db.query(
            Component.voltage_kv,
            func.sum(Component.capacity_mva).label('total_capacity')
        ).filter(
            Component.component_type == 'transformer'
        ).group_by(Component.voltage_kv).all()

        # Get line length by voltage
        line_length = db.query(
            Component.voltage_kv,
            func.sum(Component.length_km).label('total_length')
        ).filter(
            Component.component_type == 'line'
        ).group_by(Component.voltage_kv).all()

        # Get average measurements
        measurements = get_measurements_for_report(db, start_date, end_date)
        avg_measurements = {}

        # Simple aggregation - in real scenario, you'd group by daily buckets
        for measurement in measurements:
            key = f"{measurement.measurement_type}_{measurement.component.component_type}"
            if key not in avg_measurements:
                avg_measurements[key] = {"sum": 0, "count": 0}
            avg_measurements[key]["sum"] += measurement.value
            avg_measurements[key]["count"] += 1

        for key in avg_measurements:
            if avg_measurements[key]["count"] > 0:
                avg_measurements[key] = avg_measurements[key]["sum"] / avg_measurements[key]["count"]

        report_data = {
            "components_by_type": components_summary,
            "transformer_capacity_by_voltage": {str(k): v for k, v in transformer_capacity},
            "line_length_by_voltage": {str(k): v for k, v in line_length},
            "average_measurements": avg_measurements,
            "period": f"{start_date} to {end_date}"
        }

        # Update report in database
        report = db.query(Report).filter(Report.id == report_id).first()
        if report:
            report.status = "completed"
            report.data = json.dumps(report_data)
            db.commit()

    except Exception as e:
        # Update report status to failed
        report = db.query(Report).filter(Report.id == report_id).first()
        if report:
            report.status = "failed"
            report.data = json.dumps({"error": str(e)})
            db.commit()
