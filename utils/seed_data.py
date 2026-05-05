"""Populates the database with realistic sample data for demonstration."""
import random
from datetime import datetime, timedelta

from database.connection import get_session, init_db
from repositories import customer_repo, schedule_repo, recycling_repo
from repositories.incident_repo import create_incident, create_service_request


CUSTOMER_DATA = [
    ("ACC001", "Alice Johnson",      "alice.j@email.com",     "07700900001", "residential", "12", "Maple Street",    "London", "SW1A 1AA", "house"),
    ("ACC002", "Bob Williams",       "bob.w@email.com",       "07700900002", "residential", "34", "Oak Avenue",      "London", "SW1A 2BB", "flat"),
    ("ACC003", "Carol Davies",       "carol.d@email.com",     "07700900003", "residential", "56", "Elm Road",        "London", "SW1A 3CC", "house"),
    ("ACC004", "David Brown",        "david.b@email.com",     "07700900004", "commercial",  "78", "High Street",     "London", "EC1A 1AA", "office"),
    ("ACC005", "Eve Martin",         "eve.m@email.com",       "07700900005", "residential", "90", "Pine Lane",       "London", "SW2A 4DD", "house"),
    ("ACC006", "Frank Wilson",       "frank.w@email.com",     "07700900006", "commercial",  "11", "Business Park",   "London", "EC2A 2BB", "office"),
    ("ACC007", "Grace Taylor",       "grace.t@email.com",     "07700900007", "residential", "22", "Cedar Close",     "London", "SW3A 5EE", "flat"),
    ("ACC008", "Henry Moore",        "henry.m@email.com",     "07700900008", "residential", "33", "Birch Way",       "London", "SW4A 6FF", "house"),
    ("ACC009", "Ivy Anderson",       "ivy.a@email.com",       "07700900009", "school",      "44", "School Lane",     "London", "NW1A 7GG", "school"),
    ("ACC010", "Jack Thomas",        "jack.t@email.com",      "07700900010", "residential", "55", "Willow Drive",    "London", "NW2A 8HH", "house"),
    ("ACC011", "Karen Jackson",      "karen.j@email.com",     "07700900011", "residential", "66", "Ash Court",       "London", "NW3A 9II", "flat"),
    ("ACC012", "Liam White",         "liam.w@email.com",      "07700900012", "commercial",  "77", "Commerce Road",   "London", "EC3A 1JJ", "office"),
]

BIN_TYPE_DATA = [
    ("General Waste Bin",   "Black bin for non-recyclable waste",       240, "general",   "black"),
    ("Recycling Bin",       "Blue bin for mixed recyclable materials",  240, "recycling", "blue"),
    ("Garden Waste Bin",    "Green bin for garden and plant waste",     240, "garden",    "green"),
    ("Food Waste Caddy",    "Small caddy for kitchen food scraps",       7,  "food",      "brown"),
    ("Large Recycling Bin", "Large blue bin for commercial recycling",  360, "recycling", "blue"),
]

ROUTE_DATA = [
    ("R001", "North London Residential", "North London",  180, "Monday"),
    ("R002", "South London Residential", "South London",  200, "Tuesday"),
    ("R003", "East London Commercial",   "East London",   150, "Wednesday"),
    ("R004", "West London Mixed",        "West London",   220, "Thursday"),
    ("R005", "Central London Schools",   "Central London",120, "Friday"),
]

VEHICLE_DATA = [
    ("LR21 ABC", "Dennis", "Eagle",  8000, "refuse_truck"),
    ("LR21 DEF", "Dennis", "Eagle",  8000, "refuse_truck"),
    ("LR21 GHI", "Volvo",  "FE280",  6000, "recycling_truck"),
    ("LR21 JKL", "Volvo",  "FE280",  6000, "recycling_truck"),
    ("LR21 MNO", "MAN",    "TGS",    5000, "garden_waste"),
]

CREW_DATA = [
    ("EMP001", "Tom Harris",   "driver",     "07711001001"),
    ("EMP002", "Sara Lee",     "loader",     "07711001002"),
    ("EMP003", "Mike Evans",   "loader",     "07711001003"),
    ("EMP004", "Lisa Scott",   "supervisor", "07711001004"),
    ("EMP005", "James King",   "driver",     "07711001005"),
    ("EMP006", "Anna Wright",  "loader",     "07711001006"),
    ("EMP007", "Chris Hall",   "driver",     "07711001007"),
    ("EMP008", "Diana Turner", "loader",     "07711001008"),
]

FACILITIES = [
    "Greenway Recycling Centre",
    "EcoSort Facility",
    "ClearPath Processing",
    "ReNew Materials Hub",
]

MATERIALS = ["paper", "cardboard", "plastic", "glass", "metal", "organic"]
INCIDENT_TYPES = ["contamination", "damage", "access_issue", "hazardous", "missed"]
SEVERITIES = ["low", "medium", "high"]
REQUEST_TYPES = ["missed_collection", "bin_repair", "new_bin", "complaint", "query"]
PRIORITIES = ["low", "medium", "high"]


def seed():
    init_db()
    session = get_session()
    random.seed(42)

    # Skip if already seeded
    if customer_repo.get_all_customers(session):
        print("Database already contains data – skipping seed.")
        session.close()
        return

    print("Seeding database...")

    # --- Bin types ---
    bins = {}
    for name, desc, cap, cat, col in BIN_TYPE_DATA:
        bt = schedule_repo.create_bin_type(session, name, desc, cap, cat, col)
        bins[cat] = bt  # keeps last per category; sufficient for seed

    bin_list = list(bins.values())

    # --- Customers ---
    customers = []
    for acc, name, email, phone, atype, snum, sname, city, pc, ptype in CUSTOMER_DATA:
        c, err = __import__("services.customer_service", fromlist=["register_customer"]).register_customer(
            session, acc, name, email, phone, atype, snum, sname, city, pc, ptype
        )
        if c:
            customers.append(c)

    # --- Routes ---
    routes = []
    for rcode, rname, area, dur, day in ROUTE_DATA:
        r = schedule_repo.create_route(session, rcode, rname, area, dur, day)
        routes.append(r)

    # --- Vehicles ---
    vehicles = []
    for reg, make, model, cap, vtype in VEHICLE_DATA:
        v = schedule_repo.create_vehicle(session, reg, make, model, cap, vtype)
        vehicles.append(v)

    # --- Crew ---
    crew = []
    for emp_id, name, role, phone in CREW_DATA:
        cm = schedule_repo.create_crew_member(session, emp_id, name, role, phone)
        crew.append(cm)

    # --- Crew assignments (last 30 days) ---
    for i, route in enumerate(routes):
        for day_offset in range(30):
            date = datetime.utcnow() - timedelta(days=day_offset)
            crew_member = crew[i % len(crew)]
            vehicle = vehicles[i % len(vehicles)]
            try:
                schedule_repo.assign_crew_to_route(
                    session, route.id, crew_member.id, vehicle.id, date
                )
            except Exception:
                session.rollback()

    # --- Collection schedules (last 60 days) ---
    statuses = ["completed", "completed", "completed", "completed", "missed", "cancelled"]
    schedules = []
    for customer in customers:
        route = random.choice(routes)
        bt = random.choice(bin_list)
        for week in range(8):
            sdate = datetime.utcnow() - timedelta(weeks=week)
            status = random.choice(statuses)
            s = schedule_repo.create_schedule(
                session, route.id, customer.id, bt.id, sdate,
                "Regular collection"
            )
            schedule_repo.update_schedule_status(
                session, s.id, status,
                sdate + timedelta(hours=2) if status == "completed" else None
            )
            schedules.append(s)

    # --- Incident reports ---
    for _ in range(25):
        schedule_repo_module = __import__("repositories.schedule_repo", fromlist=["get_all_routes"])
        inc_type = random.choice(INCIDENT_TYPES)
        sev = random.choice(SEVERITIES)
        crew_m = random.choice(crew)
        route = random.choice(routes)
        create_incident(
            session, crew_m.id, route.id, inc_type,
            f"Reported {inc_type} on route {route.route_code}", sev
        )

    # --- Service requests ---
    for customer in random.sample(customers, min(8, len(customers))):
        rtype = random.choice(REQUEST_TYPES)
        priority = random.choice(PRIORITIES)
        create_service_request(
            session, customer.id, rtype,
            f"Customer request: {rtype}", priority
        )

    # --- Recycling outcomes ---
    for route in routes:
        for week in range(8):
            for mat in MATERIALS:
                weight = round(random.uniform(50, 500), 2)
                contamination = round(random.uniform(0.02, 0.35), 3)
                rdate = datetime.utcnow() - timedelta(weeks=week)
                recycling_repo.create_recycling_outcome(
                    session, route.id, rdate, mat, weight,
                    contamination, random.choice(FACILITIES),
                    rdate + timedelta(days=3),
                )

    print(f"  Customers   : {len(customers)}")
    print(f"  Routes      : {len(routes)}")
    print(f"  Vehicles    : {len(vehicles)}")
    print(f"  Crew        : {len(crew)}")
    print(f"  Schedules   : {len(schedules)}")
    print("Seeding complete.")
    session.close()


if __name__ == "__main__":
    seed()
