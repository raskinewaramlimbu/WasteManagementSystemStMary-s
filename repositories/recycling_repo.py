"""Data Access Layer: Recycling outcomes CRUD and analytics queries."""
from datetime import datetime
from sqlalchemy import func
from sqlalchemy.orm import Session

from database.models import RecyclingOutcome, Route, MaterialType


def create_recycling_outcome(session: Session, route_id: int,
                              collection_date: datetime, material_type: str,
                              weight_kg: float, contamination_rate: float,
                              recycling_facility: str,
                              processed_at: datetime | None = None) -> RecyclingOutcome:
    ro = RecyclingOutcome(
        route_id=route_id,
        collection_date=collection_date,
        material_type=MaterialType[material_type],
        weight_kg=weight_kg,
        contamination_rate=max(0.0, min(1.0, contamination_rate)),
        recycling_facility=recycling_facility,
        processed_at=processed_at,
    )
    session.add(ro)
    session.commit()
    session.refresh(ro)
    return ro


def get_all_recycling_outcomes(session: Session) -> list[RecyclingOutcome]:
    return (
        session.query(RecyclingOutcome)
        .order_by(RecyclingOutcome.collection_date.desc())
        .all()
    )


def get_recycling_by_material(session: Session):
    """Advanced query: total weight and average contamination grouped by material."""
    return (
        session.query(
            RecyclingOutcome.material_type,
            func.sum(RecyclingOutcome.weight_kg).label("total_weight_kg"),
            func.avg(RecyclingOutcome.contamination_rate).label("avg_contamination"),
            func.count(RecyclingOutcome.id).label("collections"),
        )
        .group_by(RecyclingOutcome.material_type)
        .order_by(func.sum(RecyclingOutcome.weight_kg).desc())
        .all()
    )


def get_recycling_by_route(session: Session):
    """Advanced query: recycling totals per route with join."""
    return (
        session.query(
            Route.route_name,
            Route.area,
            func.sum(RecyclingOutcome.weight_kg).label("total_kg"),
            func.avg(RecyclingOutcome.contamination_rate).label("avg_contamination"),
        )
        .join(RecyclingOutcome, RecyclingOutcome.route_id == Route.id)
        .group_by(Route.id)
        .order_by(func.sum(RecyclingOutcome.weight_kg).desc())
        .all()
    )


def get_contamination_hotspots(session: Session, threshold: float = 0.2):
    """Advanced query: routes where average contamination exceeds threshold."""
    return (
        session.query(
            Route.route_name,
            Route.area,
            func.avg(RecyclingOutcome.contamination_rate).label("avg_contamination"),
        )
        .join(RecyclingOutcome, RecyclingOutcome.route_id == Route.id)
        .group_by(Route.id)
        .having(func.avg(RecyclingOutcome.contamination_rate) > threshold)
        .order_by(func.avg(RecyclingOutcome.contamination_rate).desc())
        .all()
    )
