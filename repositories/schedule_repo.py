"""Data Access Layer: Collection schedule, route, crew, and vehicle CRUD."""
from datetime import datetime
from sqlalchemy import func
from sqlalchemy.orm import Session

from database.models import (
    CollectionSchedule, Route, CrewMember, Vehicle, CrewAssignment,
    BinType, CustomerBin, ScheduleStatus, CrewRole, VehicleType,
    Shift, WasteCategory,
)


# ---------------------------------------------------------------------------
# Bin types
# ---------------------------------------------------------------------------

def create_bin_type(session: Session, name: str, description: str,
                    capacity_litres: int, waste_category: str,
                    colour: str) -> BinType:
    bt = BinType(
        name=name,
        description=description,
        capacity_litres=capacity_litres,
        waste_category=WasteCategory[waste_category],
        colour=colour,
    )
    session.add(bt)
    session.commit()
    session.refresh(bt)
    return bt


def get_all_bin_types(session: Session) -> list[BinType]:
    return session.query(BinType).all()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

def create_route(session: Session, route_code: str, route_name: str,
                 area: str, estimated_duration_mins: int,
                 day_of_week: str) -> Route:
    route = Route(
        route_code=route_code,
        route_name=route_name,
        area=area,
        estimated_duration_mins=estimated_duration_mins,
        day_of_week=day_of_week,
    )
    session.add(route)
    session.commit()
    session.refresh(route)
    return route


def get_all_routes(session: Session) -> list[Route]:
    return session.query(Route).all()


def get_route_by_code(session: Session, route_code: str) -> Route | None:
    return session.query(Route).filter(Route.route_code == route_code).first()


# ---------------------------------------------------------------------------
# Vehicles
# ---------------------------------------------------------------------------

def create_vehicle(session: Session, registration: str, make: str, model: str,
                   capacity_kg: float, vehicle_type: str) -> Vehicle:
    v = Vehicle(
        registration=registration,
        make=make,
        model=model,
        capacity_kg=capacity_kg,
        vehicle_type=VehicleType[vehicle_type],
    )
    session.add(v)
    session.commit()
    session.refresh(v)
    return v


def get_all_vehicles(session: Session) -> list[Vehicle]:
    return session.query(Vehicle).filter(Vehicle.is_active == True).all()


# ---------------------------------------------------------------------------
# Crew members
# ---------------------------------------------------------------------------

def create_crew_member(session: Session, employee_id: str, name: str,
                       role: str, contact_number: str) -> CrewMember:
    cm = CrewMember(
        employee_id=employee_id,
        name=name,
        role=CrewRole[role],
        contact_number=contact_number,
    )
    session.add(cm)
    session.commit()
    session.refresh(cm)
    return cm


def get_all_crew(session: Session) -> list[CrewMember]:
    return session.query(CrewMember).filter(CrewMember.is_active == True).all()


def assign_crew_to_route(session: Session, route_id: int, crew_member_id: int,
                         vehicle_id: int, assignment_date: datetime,
                         shift: str = "morning") -> CrewAssignment:
    ca = CrewAssignment(
        route_id=route_id,
        crew_member_id=crew_member_id,
        vehicle_id=vehicle_id,
        assignment_date=assignment_date,
        shift=Shift[shift],
    )
    session.add(ca)
    session.commit()
    session.refresh(ca)
    return ca


# ---------------------------------------------------------------------------
# Collection schedules
# ---------------------------------------------------------------------------

def create_schedule(session: Session, route_id: int, customer_id: int,
                    bin_type_id: int, scheduled_date: datetime,
                    notes: str = "") -> CollectionSchedule:
    s = CollectionSchedule(
        route_id=route_id,
        customer_id=customer_id,
        bin_type_id=bin_type_id,
        scheduled_date=scheduled_date,
        notes=notes,
    )
    session.add(s)
    session.commit()
    session.refresh(s)
    return s


def get_schedules_by_customer(session: Session, customer_id: int) -> list[CollectionSchedule]:
    return (
        session.query(CollectionSchedule)
        .filter(CollectionSchedule.customer_id == customer_id)
        .order_by(CollectionSchedule.scheduled_date.desc())
        .all()
    )


def get_upcoming_schedules(session: Session, days_ahead: int = 7) -> list[CollectionSchedule]:
    from datetime import timedelta
    cutoff = datetime.utcnow() + timedelta(days=days_ahead)
    return (
        session.query(CollectionSchedule)
        .filter(
            CollectionSchedule.scheduled_date <= cutoff,
            CollectionSchedule.status == ScheduleStatus.pending,
        )
        .order_by(CollectionSchedule.scheduled_date)
        .all()
    )


def update_schedule_status(session: Session, schedule_id: int,
                            status: str,
                            completion_date: datetime | None = None) -> CollectionSchedule | None:
    s = session.get(CollectionSchedule, schedule_id)
    if not s:
        return None
    s.status = ScheduleStatus[status]
    if completion_date:
        s.actual_completion_date = completion_date
    session.commit()
    session.refresh(s)
    return s


def get_missed_collections_summary(session: Session):
    """Advanced query: missed count grouped by route and ordered descending."""
    from database.models import Route
    return (
        session.query(
            Route.route_name,
            Route.area,
            func.count(CollectionSchedule.id).label("missed_count"),
        )
        .join(CollectionSchedule, CollectionSchedule.route_id == Route.id)
        .filter(CollectionSchedule.status == ScheduleStatus.missed)
        .group_by(Route.id)
        .order_by(func.count(CollectionSchedule.id).desc())
        .all()
    )


def get_collection_completion_rate(session: Session):
    """Advanced query: completion rate per route."""
    from sqlalchemy import case
    return (
        session.query(
            Route.route_name,
            func.count(CollectionSchedule.id).label("total"),
            func.sum(
                case((CollectionSchedule.status == ScheduleStatus.completed, 1), else_=0)
            ).label("completed"),
        )
        .join(CollectionSchedule, CollectionSchedule.route_id == Route.id)
        .group_by(Route.id)
        .order_by(Route.route_name)
        .all()
    )
