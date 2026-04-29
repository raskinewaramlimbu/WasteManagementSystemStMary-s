"""Business Layer: collection scheduling, crew assignment, and service requests."""
from datetime import datetime
from sqlalchemy.orm import Session

from repositories import schedule_repo, incident_repo
from repositories.incident_repo import write_audit_log


def book_collection(session: Session, route_id: int, customer_id: int,
                    bin_type_id: int, scheduled_date: datetime,
                    notes: str = ""):
    """Create a scheduled collection and log the event."""
    schedule = schedule_repo.create_schedule(
        session, route_id, customer_id, bin_type_id, scheduled_date, notes
    )
    write_audit_log(session, "collection_schedules", schedule.id, "CREATE",
                    "system", f"Scheduled for {scheduled_date.date()}")
    return schedule


def mark_collection_complete(session: Session, schedule_id: int):
    schedule = schedule_repo.update_schedule_status(
        session, schedule_id, "completed", datetime.utcnow()
    )
    if schedule:
        write_audit_log(session, "collection_schedules", schedule_id, "UPDATE",
                        "crew", "Marked completed")
    return schedule


def mark_collection_missed(session: Session, schedule_id: int, reason: str = ""):
    schedule = schedule_repo.update_schedule_status(session, schedule_id, "missed")
    if schedule:
        write_audit_log(session, "collection_schedules", schedule_id, "UPDATE",
                        "crew", f"Missed: {reason}")
    return schedule


def report_incident(session: Session, crew_member_id: int, route_id: int,
                    incident_type: str, description: str, severity: str,
                    schedule_id: int | None = None):
    incident = incident_repo.create_incident(
        session, crew_member_id, route_id, incident_type,
        description, severity, schedule_id
    )
    write_audit_log(session, "incident_reports", incident.id, "CREATE",
                    "crew", f"{incident_type} – {severity}")
    return incident


def raise_service_request(session: Session, customer_id: int,
                           request_type: str, description: str,
                           priority: str = "medium"):
    sr = incident_repo.create_service_request(
        session, customer_id, request_type, description, priority
    )
    write_audit_log(session, "service_requests", sr.id, "CREATE",
                    "customer", request_type)
    return sr


def resolve_request(session: Session, request_id: int):
    sr = incident_repo.resolve_service_request(session, request_id)
    if sr:
        write_audit_log(session, "service_requests", request_id, "UPDATE",
                        "staff", "Resolved")
    return sr
