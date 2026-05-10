"""MongoDB handler for storing semi-structured incident data and audit logs.

MongoDB is used alongside SQLite in a hybrid approach:
  - SQLite (relational) → structured operational data (customers, schedules, routes)
  - MongoDB (document)  → flexible incident reports and system-wide audit events
"""
from datetime import datetime

try:
    from pymongo import MongoClient
    from pymongo.errors import ConnectionFailure
    _MONGO_AVAILABLE = True
except ImportError:
    _MONGO_AVAILABLE = False

MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "waste_services"


class MongoHandler:
    """Wraps PyMongo operations; degrades gracefully when MongoDB is offline."""

    def __init__(self):
        self._client = None
        self._db = None
        self._connected = False
        self._connect()

    def _connect(self):
        if not _MONGO_AVAILABLE:
            return
        try:
            self._client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
            self._client.admin.command("ping")
            self._db = self._client[DB_NAME]
            self._connected = True
        except Exception:
            self._connected = False

    @property
    def is_connected(self):
        return self._connected

    # ------------------------------------------------------------------
    # Incident reports
    # ------------------------------------------------------------------

    def log_incident(self, incident_data: dict) -> str | None:
        """Insert a rich incident document; returns inserted id string or None."""
        if not self._connected:
            return None
        doc = {**incident_data, "created_at": datetime.utcnow()}
        result = self._db.incidents.insert_one(doc)
        return str(result.inserted_id)

    def get_incidents_by_area(self, area: str) -> list[dict]:
        if not self._connected:
            return []
        return list(self._db.incidents.find({"area": area}, {"_id": 0}))

    def get_incidents_by_severity(self, severity: str) -> list[dict]:
        if not self._connected:
            return []
        return list(self._db.incidents.find({"severity": severity}, {"_id": 0}))

    def get_all_incidents(self) -> list[dict]:
        if not self._connected:
            return []
        return list(self._db.incidents.find({}, {"_id": 0}))

    # ------------------------------------------------------------------
    # Audit events
    # ------------------------------------------------------------------

    def log_audit_event(self, event_data: dict) -> str | None:
        if not self._connected:
            return None
        doc = {**event_data, "timestamp": datetime.utcnow()}
        result = self._db.audit_events.insert_one(doc)
        return str(result.inserted_id)

    def get_recent_audit_events(self, limit: int = 20) -> list[dict]:
        if not self._connected:
            return []
        return list(
            self._db.audit_events.find({}, {"_id": 0})
            .sort("timestamp", -1)
            .limit(limit)
        )

    def close(self):
        if self._client:
            self._client.close()


# Module-level singleton
mongo = MongoHandler()
