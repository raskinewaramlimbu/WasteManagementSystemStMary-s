"""Business Layer: analytics, reporting, and visualisation coordination."""
import math
from sqlalchemy.orm import Session

from repositories import schedule_repo, recycling_repo, incident_repo


def get_completion_stats(session: Session) -> dict:
    rows = schedule_repo.get_collection_completion_rate(session)
    results = []
    for row in rows:
        total = row.total or 0
        completed = row.completed or 0
        rate = (completed / total * 100) if total > 0 else 0.0
        results.append({
            "route": row.route_name,
            "total": total,
            "completed": completed,
            "rate_pct": round(rate, 1),
        })
    return {"completion_by_route": results}


def get_recycling_summary(session: Session) -> dict:
    material_rows = recycling_repo.get_recycling_by_material(session)
    materials = []
    total_weight = 0.0
    for row in material_rows:
        w = row.total_weight_kg or 0.0
        total_weight += w
        materials.append({
            "material": row.material_type.value,
            "weight_kg": round(w, 2),
            "avg_contamination_pct": round((row.avg_contamination or 0.0) * 100, 1),
            "collections": row.collections,
        })
    return {"total_weight_kg": round(total_weight, 2), "by_material": materials}


def get_incident_summary(session: Session) -> dict:
    rows = incident_repo.get_incident_counts_by_type(session)
    return [
        {
            "type": row.incident_type.value,
            "severity": row.severity.value,
            "count": row.count,
        }
        for row in rows
    ]


def get_missed_collections(session: Session) -> list[dict]:
    rows = schedule_repo.get_missed_collections_summary(session)
    return [
        {"route": row.route_name, "area": row.area, "missed": row.missed_count}
        for row in rows
    ]


def get_contamination_hotspots(session: Session) -> list[dict]:
    rows = recycling_repo.get_contamination_hotspots(session, threshold=0.15)
    return [
        {
            "route": row.route_name,
            "area": row.area,
            "avg_contamination_pct": round((row.avg_contamination or 0.0) * 100, 1),
        }
        for row in rows
    ]
