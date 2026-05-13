"""Pytest test suite for the Local Waste Services application.

Tests cover: model creation, CRUD operations, business logic validation,
advanced queries, and the service layer.
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.connection import Base
from database import models  # registers all models
from database.models import (
    Customer, Address, BinType, Route, Vehicle, CrewMember,
    CollectionSchedule, IncidentReport, RecyclingOutcome,
    AccountType, WasteCategory, ScheduleStatus,
)
from repositories import customer_repo, schedule_repo, recycling_repo
from repositories.incident_repo import (
    create_incident, create_service_request, get_open_service_requests,
    resolve_service_request, get_incident_counts_by_type,
)
from services import customer_service, schedule_service, report_service


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def session():
    """In-memory SQLite session, rolled back after each test."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    s = Session()
    yield s
    s.close()
    Base.metadata.drop_all(engine)


@pytest.fixture
def sample_customer(session):
    c, _ = customer_service.register_customer(
        session, "TEST001", "Test User", "test@example.com",
        "07700900000", "residential",
        "1", "Test Street", "London", "SW1A 1AA", "house",
    )
    return c


@pytest.fixture
def sample_route(session):
    return schedule_repo.create_route(
        session, "TR001", "Test Route", "North", 120, "Monday"
    )


@pytest.fixture
def sample_bin_type(session):
    return schedule_repo.create_bin_type(
        session, "Test Bin", "A test bin", 240, "general", "black"
    )


@pytest.fixture
def sample_vehicle(session):
    return schedule_repo.create_vehicle(
        session, "TX01 AAA", "Ford", "Transit", 3500, "refuse_truck"
    )


@pytest.fixture
def sample_crew(session):
    return schedule_repo.create_crew_member(
        session, "EMP999", "Test Crew", "driver", "07700999999"
    )


# ---------------------------------------------------------------------------
# Customer tests
# ---------------------------------------------------------------------------

class TestCustomerCRUD:

    def test_create_customer(self, session):
        c, err = customer_service.register_customer(
            session, "ACC001", "Alice", "alice@test.com", "07700000001",
            "residential", "10", "Oak St", "London", "EC1A 1AA",
        )
        assert err == ""
        assert c is not None
        assert c.name == "Alice"
        assert c.account_number == "ACC001"

    def test_duplicate_email_rejected(self, session, sample_customer):
        _, err = customer_service.register_customer(
            session, "ACC002", "Bob", "test@example.com", "07700000002",
            "residential", "2", "Elm St", "London", "EC1A 2AA",
        )
        assert "already exists" in err

    def test_duplicate_account_number_rejected(self, session, sample_customer):
        _, err = customer_service.register_customer(
            session, "TEST001", "Carol", "carol@test.com", "07700000003",
            "residential", "3", "Pine St", "London", "EC1A 3AA",
        )
        assert "Account number" in err

    def test_invalid_email_rejected(self, session):
        _, err = customer_service.register_customer(
            session, "ACC003", "Dave", "not-an-email", "07700000004",
            "residential", "4", "Ash St", "London", "EC1A 4AA",
        )
        assert "Invalid e-mail" in err

    def test_invalid_account_type_rejected(self, session):
        _, err = customer_service.register_customer(
            session, "ACC004", "Eve", "eve@test.com", "07700000005",
            "corporate",  # invalid
            "5", "Birch St", "London", "EC1A 5AA",
        )
        assert "Invalid account type" in err

    def test_get_customer_by_id(self, session, sample_customer):
        c = customer_repo.get_customer_by_id(session, sample_customer.id)
        assert c is not None
        assert c.name == "Test User"

    def test_search_customers(self, session, sample_customer):
        results = customer_repo.search_customers(session, "Test")
        assert len(results) >= 1

    def test_update_contact_details(self, session, sample_customer):
        c, err = customer_service.update_contact_details(
            session, sample_customer.id, email="new@example.com"
        )
        assert err == ""
        assert c.email == "new@example.com"

    def test_deactivate_customer(self, session, sample_customer):
        ok = customer_service.close_account(session, sample_customer.id)
        assert ok is True
        c = customer_repo.get_customer_by_id(session, sample_customer.id)
        assert c.is_active is False

    def test_address_created_with_customer(self, session, sample_customer):
        addrs = customer_repo.get_addresses_for_customer(session, sample_customer.id)
        assert len(addrs) == 1
        assert addrs[0].street_name == "Test Street"


# ---------------------------------------------------------------------------
# Collection schedule tests
# ---------------------------------------------------------------------------

class TestSchedules:

    def test_create_schedule(self, session, sample_customer, sample_route, sample_bin_type):
        s = schedule_service.book_collection(
            session, sample_route.id, sample_customer.id, sample_bin_type.id,
            datetime.utcnow() + timedelta(days=3)
        )
        assert s is not None
        assert s.status == ScheduleStatus.pending

    def test_mark_complete(self, session, sample_customer, sample_route, sample_bin_type):
        s = schedule_service.book_collection(
            session, sample_route.id, sample_customer.id, sample_bin_type.id,
            datetime.utcnow()
        )
        updated = schedule_service.mark_collection_complete(session, s.id)
        assert updated.status == ScheduleStatus.completed
        assert updated.actual_completion_date is not None

    def test_mark_missed(self, session, sample_customer, sample_route, sample_bin_type):
        s = schedule_service.book_collection(
            session, sample_route.id, sample_customer.id, sample_bin_type.id,
            datetime.utcnow()
        )
        updated = schedule_service.mark_collection_missed(session, s.id, "No access")
        assert updated.status == ScheduleStatus.missed

    def test_get_upcoming_schedules(self, session, sample_customer, sample_route, sample_bin_type):
        schedule_service.book_collection(
            session, sample_route.id, sample_customer.id, sample_bin_type.id,
            datetime.utcnow() + timedelta(days=1)
        )
        upcoming = schedule_repo.get_upcoming_schedules(session, days_ahead=7)
        assert len(upcoming) >= 1

    def test_get_schedules_by_customer(self, session, sample_customer, sample_route, sample_bin_type):
        schedule_service.book_collection(
            session, sample_route.id, sample_customer.id, sample_bin_type.id,
            datetime.utcnow()
        )
        schedules = schedule_repo.get_schedules_by_customer(session, sample_customer.id)
        assert len(schedules) >= 1

    def test_schedule_invalid_id_returns_none(self, session):
        result = schedule_repo.update_schedule_status(session, 99999, "completed")
        assert result is None


# ---------------------------------------------------------------------------
# Incident and service request tests
# ---------------------------------------------------------------------------

class TestIncidents:

    def test_create_incident(self, session, sample_crew, sample_route):
        inc = create_incident(
            session, sample_crew.id, sample_route.id,
            "contamination", "Plastic found in food bin", "medium"
        )
        assert inc is not None
        assert inc.is_resolved is False

    def test_resolve_incident(self, session, sample_crew, sample_route):
        inc = create_incident(
            session, sample_crew.id, sample_route.id,
            "damage", "Bin lid broken", "low"
        )
        resolved = schedule_service.report_incident.__module__  # just check exists
        from repositories.incident_repo import resolve_incident
        result = resolve_incident(session, inc.id)
        assert result.is_resolved is True

    def test_create_service_request(self, session, sample_customer):
        sr = schedule_service.raise_service_request(
            session, sample_customer.id, "missed_collection",
            "My bin was not collected last Monday.", "high"
        )
        assert sr is not None

    def test_open_service_requests(self, session, sample_customer):
        schedule_service.raise_service_request(
            session, sample_customer.id, "query", "General query", "low"
        )
        open_reqs = get_open_service_requests(session)
        assert len(open_reqs) >= 1

    def test_resolve_service_request(self, session, sample_customer):
        sr = schedule_service.raise_service_request(
            session, sample_customer.id, "bin_repair", "Wheel broken", "medium"
        )
        resolved = schedule_service.resolve_request(session, sr.id)
        assert resolved is not None
        assert resolved.resolved_at is not None


# ---------------------------------------------------------------------------
# Recycling outcome tests
# ---------------------------------------------------------------------------

class TestRecycling:

    def test_create_recycling_outcome(self, session, sample_route):
        ro = recycling_repo.create_recycling_outcome(
            session, sample_route.id, datetime.utcnow(),
            "plastic", 150.5, 0.12, "EcoSort Facility"
        )
        assert ro is not None
        assert ro.contamination_rate == 0.12

    def test_contamination_clamped(self, session, sample_route):
        ro = recycling_repo.create_recycling_outcome(
            session, sample_route.id, datetime.utcnow(),
            "glass", 200.0, 1.5, "GreenWay"  # over 1.0 should be clamped
        )
        assert ro.contamination_rate <= 1.0

    def test_recycling_by_material(self, session, sample_route):
        recycling_repo.create_recycling_outcome(
            session, sample_route.id, datetime.utcnow(),
            "paper", 300.0, 0.05, "ReNew Hub"
        )
        recycling_repo.create_recycling_outcome(
            session, sample_route.id, datetime.utcnow(),
            "paper", 200.0, 0.08, "ReNew Hub"
        )
        results = recycling_repo.get_recycling_by_material(session)
        paper = next((r for r in results if r.material_type.value == "paper"), None)
        assert paper is not None
        assert round(paper.total_weight_kg, 1) == 500.0

    def test_contamination_hotspots(self, session, sample_route):
        recycling_repo.create_recycling_outcome(
            session, sample_route.id, datetime.utcnow(),
            "plastic", 100.0, 0.40, "Facility A"  # high contamination
        )
        hotspots = recycling_repo.get_contamination_hotspots(session, threshold=0.15)
        assert len(hotspots) >= 1


# ---------------------------------------------------------------------------
# Advanced query tests
# ---------------------------------------------------------------------------

class TestAdvancedQueries:

    def test_missed_collections_summary(self, session, sample_customer, sample_route, sample_bin_type):
        s1 = schedule_service.book_collection(
            session, sample_route.id, sample_customer.id, sample_bin_type.id,
            datetime.utcnow()
        )
        s2 = schedule_service.book_collection(
            session, sample_route.id, sample_customer.id, sample_bin_type.id,
            datetime.utcnow()
        )
        schedule_service.mark_collection_missed(session, s1.id)
        schedule_service.mark_collection_missed(session, s2.id)
        results = report_service.get_missed_collections(session)
        assert any(r["route"] == "Test Route" for r in results)

    def test_completion_stats(self, session, sample_customer, sample_route, sample_bin_type):
        s = schedule_service.book_collection(
            session, sample_route.id, sample_customer.id, sample_bin_type.id,
            datetime.utcnow()
        )
        schedule_service.mark_collection_complete(session, s.id)
        stats = report_service.get_completion_stats(session)
        route_stat = next(
            (r for r in stats["completion_by_route"] if r["route"] == "Test Route"), None
        )
        assert route_stat is not None
        assert route_stat["rate_pct"] > 0

    def test_recycling_summary(self, session, sample_route):
        recycling_repo.create_recycling_outcome(
            session, sample_route.id, datetime.utcnow(),
            "metal", 500.0, 0.05, "Facility X"
        )
        summary = report_service.get_recycling_summary(session)
        assert summary["total_weight_kg"] >= 500.0

    def test_incident_summary(self, session, sample_crew, sample_route):
        create_incident(session, sample_crew.id, sample_route.id,
                        "contamination", "Test", "high")
        create_incident(session, sample_crew.id, sample_route.id,
                        "contamination", "Test 2", "low")
        summary = report_service.get_incident_summary(session)
        assert len(summary) >= 1
