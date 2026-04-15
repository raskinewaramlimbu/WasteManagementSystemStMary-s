"""SQLAlchemy ORM models for the Local Waste Services database.

Database is normalised to Third Normal Form (3NF):
  - 1NF: all columns hold atomic values; no repeating groups.
  - 2NF: every non-key column depends on the whole primary key.
  - 3NF: no transitive dependencies; each non-key column depends only on the PK.
"""
import hashlib
import os
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import (
    Boolean, Column, DateTime, Enum, Float, ForeignKey,
    Integer, String, Text, UniqueConstraint, Index,
)
from sqlalchemy.orm import relationship

from database.connection import Base


# ---------------------------------------------------------------------------
# Enum types
# ---------------------------------------------------------------------------

class AccountType(PyEnum):
    residential = "residential"
    commercial  = "commercial"
    school      = "school"

class PropertyType(PyEnum):
    house  = "house"
    flat   = "flat"
    office = "office"
    school = "school"

class WasteCategory(PyEnum):
    general   = "general"
    recycling = "recycling"
    garden    = "garden"
    food      = "food"

class VehicleType(PyEnum):
    refuse_truck    = "refuse_truck"
    recycling_truck = "recycling_truck"
    garden_waste    = "garden_waste"

class CrewRole(PyEnum):
    driver     = "driver"
    loader     = "loader"
    supervisor = "supervisor"

class Shift(PyEnum):
    morning   = "morning"
    afternoon = "afternoon"

class ScheduleStatus(PyEnum):
    pending   = "pending"
    completed = "completed"
    missed    = "missed"
    cancelled = "cancelled"

class RequestType(PyEnum):
    missed_collection = "missed_collection"
    bin_repair        = "bin_repair"
    new_bin           = "new_bin"
    complaint         = "complaint"
    query             = "query"

class RequestStatus(PyEnum):
    open        = "open"
    in_progress = "in_progress"
    resolved    = "resolved"
    closed      = "closed"

class Priority(PyEnum):
    low    = "low"
    medium = "medium"
    high   = "high"

class IncidentType(PyEnum):
    contamination = "contamination"
    damage        = "damage"
    access_issue  = "access_issue"
    hazardous     = "hazardous"
    missed        = "missed"

class Severity(PyEnum):
    low      = "low"
    medium   = "medium"
    high     = "high"
    critical = "critical"

class MaterialType(PyEnum):
    paper     = "paper"
    cardboard = "cardboard"
    plastic   = "plastic"
    glass     = "glass"
    metal     = "metal"
    organic   = "organic"

class AuditAction(PyEnum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


# ---------------------------------------------------------------------------
# Model definitions
# ---------------------------------------------------------------------------

class Customer(Base):
    __tablename__ = "customers"

    id             = Column(Integer, primary_key=True)
    account_number = Column(String(20), unique=True, nullable=False)
    name           = Column(String(100), nullable=False)
    email          = Column(String(150), unique=True, nullable=False)
    phone          = Column(String(20))
    account_type   = Column(Enum(AccountType), nullable=False, default=AccountType.residential)
    password_hash  = Column(String(64), nullable=False)
    is_active      = Column(Boolean, default=True)
    created_at     = Column(DateTime, default=datetime.utcnow)

    addresses         = relationship("Address", back_populates="customer", cascade="all, delete-orphan")
    customer_bins     = relationship("CustomerBin", back_populates="customer", cascade="all, delete-orphan")
    collection_schedules = relationship("CollectionSchedule", back_populates="customer")
    service_requests  = relationship("ServiceRequest", back_populates="customer", cascade="all, delete-orphan")

    def set_password(self, password: str):
        salt = os.urandom(16).hex()
        self.password_hash = hashlib.sha256((salt + password).encode()).hexdigest()

    def __repr__(self):
        return f"<Customer {self.account_number} – {self.name}>"


class Address(Base):
    __tablename__ = "addresses"

    id            = Column(Integer, primary_key=True)
    customer_id   = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    street_number = Column(String(10), nullable=False)
    street_name   = Column(String(150), nullable=False)
    city          = Column(String(100), nullable=False)
    postcode      = Column(String(10), nullable=False)
    property_type = Column(Enum(PropertyType), nullable=False, default=PropertyType.house)
    is_primary    = Column(Boolean, default=True)

    customer     = relationship("Customer", back_populates="addresses")
    customer_bins = relationship("CustomerBin", back_populates="address")

    __table_args__ = (
        Index("ix_address_postcode", "postcode"),
    )

    def __repr__(self):
        return f"<Address {self.street_number} {self.street_name}, {self.postcode}>"


class BinType(Base):
    __tablename__ = "bin_types"

    id               = Column(Integer, primary_key=True)
    name             = Column(String(50), unique=True, nullable=False)
    description      = Column(String(200))
    capacity_litres  = Column(Integer, nullable=False)
    waste_category   = Column(Enum(WasteCategory), nullable=False)
    colour           = Column(String(30))

    customer_bins = relationship("CustomerBin", back_populates="bin_type")
    collection_schedules = relationship("CollectionSchedule", back_populates="bin_type")

    def __repr__(self):
        return f"<BinType {self.name} ({self.capacity_litres}L)>"


class CustomerBin(Base):
    """Links a customer/address to a specific bin type (M:M resolution table)."""
    __tablename__ = "customer_bins"

    id          = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    bin_type_id = Column(Integer, ForeignKey("bin_types.id"), nullable=False)
    address_id  = Column(Integer, ForeignKey("addresses.id"), nullable=False)
    quantity    = Column(Integer, default=1)
    date_issued = Column(DateTime, default=datetime.utcnow)

    customer = relationship("Customer", back_populates="customer_bins")
    bin_type = relationship("BinType", back_populates="customer_bins")
    address  = relationship("Address", back_populates="customer_bins")


class Vehicle(Base):
    __tablename__ = "vehicles"

    id           = Column(Integer, primary_key=True)
    registration = Column(String(20), unique=True, nullable=False)
    make         = Column(String(50))
    model        = Column(String(50))
    capacity_kg  = Column(Float)
    vehicle_type = Column(Enum(VehicleType), nullable=False)
    is_active    = Column(Boolean, default=True)

    crew_assignments = relationship("CrewAssignment", back_populates="vehicle")

    def __repr__(self):
        return f"<Vehicle {self.registration}>"


class Route(Base):
    __tablename__ = "routes"

    id                     = Column(Integer, primary_key=True)
    route_code             = Column(String(20), unique=True, nullable=False)
    route_name             = Column(String(100), nullable=False)
    area                   = Column(String(100))
    estimated_duration_mins = Column(Integer)
    day_of_week            = Column(String(10))  # Monday, Tuesday, etc.

    crew_assignments     = relationship("CrewAssignment", back_populates="route")
    collection_schedules = relationship("CollectionSchedule", back_populates="route")
    incident_reports     = relationship("IncidentReport", back_populates="route")
    recycling_outcomes   = relationship("RecyclingOutcome", back_populates="route")

    __table_args__ = (
        Index("ix_route_area", "area"),
    )

    def __repr__(self):
        return f"<Route {self.route_code} – {self.route_name}>"


class CrewMember(Base):
    __tablename__ = "crew_members"

    id             = Column(Integer, primary_key=True)
    employee_id    = Column(String(20), unique=True, nullable=False)
    name           = Column(String(100), nullable=False)
    role           = Column(Enum(CrewRole), nullable=False)
    contact_number = Column(String(20))
    is_active      = Column(Boolean, default=True)

    crew_assignments = relationship("CrewAssignment", back_populates="crew_member")
    incident_reports = relationship("IncidentReport", back_populates="crew_member")
    service_requests = relationship("ServiceRequest", back_populates="assigned_to")

    def __repr__(self):
        return f"<CrewMember {self.employee_id} – {self.name}>"


class CrewAssignment(Base):
    """Assigns a crew member and vehicle to a route for a specific date/shift."""
    __tablename__ = "crew_assignments"

    id              = Column(Integer, primary_key=True)
    route_id        = Column(Integer, ForeignKey("routes.id"), nullable=False)
    crew_member_id  = Column(Integer, ForeignKey("crew_members.id"), nullable=False)
    vehicle_id      = Column(Integer, ForeignKey("vehicles.id"), nullable=False)
    assignment_date = Column(DateTime, nullable=False)
    shift           = Column(Enum(Shift), nullable=False, default=Shift.morning)

    route       = relationship("Route", back_populates="crew_assignments")
    crew_member = relationship("CrewMember", back_populates="crew_assignments")
    vehicle     = relationship("Vehicle", back_populates="crew_assignments")

    __table_args__ = (
        UniqueConstraint("crew_member_id", "assignment_date", "shift",
                         name="uq_crew_assignment"),
    )


class CollectionSchedule(Base):
    __tablename__ = "collection_schedules"

    id                    = Column(Integer, primary_key=True)
    route_id              = Column(Integer, ForeignKey("routes.id"), nullable=False)
    customer_id           = Column(Integer, ForeignKey("customers.id"), nullable=False)
    bin_type_id           = Column(Integer, ForeignKey("bin_types.id"), nullable=False)
    scheduled_date        = Column(DateTime, nullable=False)
    status                = Column(Enum(ScheduleStatus), default=ScheduleStatus.pending)
    actual_completion_date = Column(DateTime, nullable=True)
    notes                 = Column(Text)
    created_at            = Column(DateTime, default=datetime.utcnow)

    route    = relationship("Route", back_populates="collection_schedules")
    customer = relationship("Customer", back_populates="collection_schedules")
    bin_type = relationship("BinType", back_populates="collection_schedules")
    incident_reports = relationship("IncidentReport", back_populates="schedule")

    __table_args__ = (
        Index("ix_schedule_date", "scheduled_date"),
        Index("ix_schedule_status", "status"),
    )


class ServiceRequest(Base):
    __tablename__ = "service_requests"

    id           = Column(Integer, primary_key=True)
    customer_id  = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    request_type = Column(Enum(RequestType), nullable=False)
    description  = Column(Text)
    status       = Column(Enum(RequestStatus), default=RequestStatus.open)
    priority     = Column(Enum(Priority), default=Priority.medium)
    created_at   = Column(DateTime, default=datetime.utcnow)
    resolved_at  = Column(DateTime, nullable=True)
    assigned_to_id = Column(Integer, ForeignKey("crew_members.id"), nullable=True)

    customer    = relationship("Customer", back_populates="service_requests")
    assigned_to = relationship("CrewMember", back_populates="service_requests")


class IncidentReport(Base):
    __tablename__ = "incident_reports"

    id             = Column(Integer, primary_key=True)
    schedule_id    = Column(Integer, ForeignKey("collection_schedules.id"), nullable=True)
    crew_member_id = Column(Integer, ForeignKey("crew_members.id"), nullable=False)
    route_id       = Column(Integer, ForeignKey("routes.id"), nullable=False)
    incident_type  = Column(Enum(IncidentType), nullable=False)
    description    = Column(Text)
    severity       = Column(Enum(Severity), default=Severity.low)
    reported_at    = Column(DateTime, default=datetime.utcnow)
    is_resolved    = Column(Boolean, default=False)

    schedule    = relationship("CollectionSchedule", back_populates="incident_reports")
    crew_member = relationship("CrewMember", back_populates="incident_reports")
    route       = relationship("Route", back_populates="incident_reports")


class RecyclingOutcome(Base):
    __tablename__ = "recycling_outcomes"

    id                 = Column(Integer, primary_key=True)
    route_id           = Column(Integer, ForeignKey("routes.id"), nullable=False)
    collection_date    = Column(DateTime, nullable=False)
    material_type      = Column(Enum(MaterialType), nullable=False)
    weight_kg          = Column(Float, nullable=False)
    contamination_rate = Column(Float, default=0.0)  # 0.0 – 1.0
    recycling_facility = Column(String(150))
    processed_at       = Column(DateTime, nullable=True)

    route = relationship("Route", back_populates="recycling_outcomes")

    __table_args__ = (
        Index("ix_recycling_date", "collection_date"),
    )


class AuditLog(Base):
    """Immutable audit trail of all data modifications."""
    __tablename__ = "audit_logs"

    id         = Column(Integer, primary_key=True)
    table_name = Column(String(50), nullable=False)
    record_id  = Column(Integer)
    action     = Column(Enum(AuditAction), nullable=False)
    changed_by = Column(String(100))
    changed_at = Column(DateTime, default=datetime.utcnow)
    details    = Column(Text)  # JSON string with before/after values

    __table_args__ = (
        Index("ix_audit_table", "table_name"),
        Index("ix_audit_action", "action"),
    )
