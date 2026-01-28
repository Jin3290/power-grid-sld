from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()


class ComponentType(enum.Enum):
    TRANSFORMER = "transformer"
    LINE = "line"
    SWITCH = "switch"


class MeasurementType(enum.Enum):
    VOLTAGE = "Voltage"
    CURRENT = "Current"
    POWER = "Power"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String)  # "manager" or "user"


class Component(Base):
    __tablename__ = "components"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    substation = Column(String)
    component_type = Column(String)

    # Transformer specific
    capacity_mva = Column(Float, nullable=True)

    # Common for Transformer and Line
    voltage_kv = Column(Float, nullable=True)

    # Line specific
    length_km = Column(Float, nullable=True)

    # Switch specific
    status = Column(String, nullable=True)

    measurements = relationship("Measurement", back_populates="component")


class Measurement(Base):
    __tablename__ = "measurements"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    value = Column(Float)
    measurement_type = Column(String)
    component_id = Column(Integer, ForeignKey("components.id"))

    component = relationship("Component", back_populates="measurements")


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    status = Column(String, default="pending")  # pending, completed, failed
    data = Column(String)  # JSON string
