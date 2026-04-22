"""Data Access Layer: Incident reports and service requests CRUD."""
from datetime import datetime
from sqlalchemy import func
from sqlalchemy.orm import Session

from database.models import (
    IncidentReport, ServiceRequest, AuditLog,
    IncidentType, Severity, RequestType, RequestStatus, Priority, AuditAction,
)


# ---------------------------------------------------------------------------
# Incident reports
# ---------------------------------------------------------------------------

def create_incident(session: Session, crew_member_id: int, route_id: int,
                    incident_type: str, description: str,
                    severity: str = "low",
                    schedule_id: int | None = None) -> IncidentReport:
    ir = IncidentReport(
        schedule_id=schedule_id,
        crew_member_id=crew_member_id,
        route_id=route_id,
        incident_type=IncidentType[incident_type],
        description=description,
        severity=Severity[severity],
    )
    session.add(ir)
    session.commit()
    session.refresh(ir)
    return ir


def get_all_incidents(session: Session) -> list[IncidentReport]:
    return (
        session.query(IncidentReport)
        .order_by(IncidentReport.reported_at.desc())
        .all()
    )


def get_incidents_by_type(session: Session, incident_type: str) -> list[IncidentReport]:
    return (
        session.query(IncidentReport)
        .filter(IncidentReport.incident_type == IncidentType[incident_type])
        .all()
    )


def resolve_incident(session: Session, incident_id: int) -> IncidentReport | None:
    ir = session.get(IncidentReport, incident_id)
    if not ir:
        return None
    ir.is_resolved = True
    session.commit()
    session.refresh(ir)
    return ir


def get_incident_counts_by_type(session: Session):
    """Advanced query: count incidents grouped by type and severity."""
    return (
        session.query(
            IncidentReport.incident_type,
            IncidentReport.severity,
            func.count(IncidentReport.id).label("count"),
        )
        .group_by(IncidentReport.incident_type, IncidentReport.severity)
        .order_by(func.count(IncidentReport.id).desc())
        .all()
    )


# ---------------------------------------------------------------------------
# Service requests
# ---------------------------------------------------------------------------

def create_service_request(session: Session, customer_id: int,
                            request_type: str, description: str,
                            priority: str = "medium") -> ServiceRequest:
    sr = ServiceRequest(
        customer_id=customer_id,
        request_type=RequestType[request_type],
        description=description,
        priority=Priority[priority],
    )
    session.add(sr)
    session.commit()
    session.refresh(sr)
    return sr


def get_open_service_requests(session: Session) -> list[ServiceRequest]:
    return (
        session.query(ServiceRequest)
        .filter(ServiceRequest.status == RequestStatus.open)
        .order_by(ServiceRequest.created_at.asc())
        .all()
    )


def resolve_service_request(session: Session, request_id: int) -> ServiceRequest | None:
    sr = session.get(ServiceRequest, request_id)
    if not sr:
        return None
    sr.status = RequestStatus.resolved
    sr.resolved_at = datetime.utcnow()
    session.commit()
    session.refresh(sr)
    return sr


def get_requests_by_type_summary(session: Session):
    """Advanced query: service request counts grouped by type."""
    return (
        session.query(
            ServiceRequest.request_type,
            func.count(ServiceRequest.id).label("count"),
        )
        .group_by(ServiceRequest.request_type)
        .order_by(func.count(ServiceRequest.id).desc())
        .all()
    )


# ---------------------------------------------------------------------------
# Audit log
# ---------------------------------------------------------------------------

def write_audit_log(session: Session, table_name: str, record_id: int,
                    action: str, changed_by: str, details: str = "") -> AuditLog:
    log = AuditLog(
        table_name=table_name,
        record_id=record_id,
        action=AuditAction[action],
        changed_by=changed_by,
        details=details,
    )
    session.add(log)
    session.commit()
    return log


def get_audit_logs(session: Session, table_name: str | None = None,
                   limit: int = 50) -> list[AuditLog]:
    q = session.query(AuditLog)
    if table_name:
        q = q.filter(AuditLog.table_name == table_name)
    return q.order_by(AuditLog.changed_at.desc()).limit(limit).all()
