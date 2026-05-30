# Local Waste Services – Database-Driven Application

> **Module:** CPS7003B – Database Systems | **Institution:** St Mary's University  
> **Assessment:** 2 – Database Driven Application | **Date:** 15 May 2026

---

## Overview

A full-stack, four-tier database-driven application for **Local Waste Services**, a waste management provider serving households, schools, and small businesses. The system manages customer accounts, collection schedules, vehicle routes, crew assignments, incident reports, service requests, and recycling outcomes.

---

## Architecture

```
┌─────────────────────────────────────┐
│       Presentation Layer            │  ui/cli.py — menu-driven CLI
├─────────────────────────────────────┤
│         Business Layer              │  services/ — validation & logic
├─────────────────────────────────────┤
│       Data Access Layer             │  repositories/ — CRUD & queries
├─────────────────────────────────────┤
│           Data Layer                │  SQLite (SQLAlchemy) + MongoDB
└─────────────────────────────────────┘
```

---

## Features

- **Relational database** normalised to Third Normal Form (3NF) — 12 tables
- **SQLAlchemy 2.0 ORM** for parameterised, injection-safe queries
- **MongoDB hybrid store** for incident reports and audit events (optional)
- **Advanced queries** — joins, aggregations, GROUP BY, HAVING, conditional SUMs
- **Security** — SHA-256 password hashing with salt, input validation, ORM parameterisation
- **Performance** — 7 strategic indexes on high-frequency filter columns
- **Analytics** — 5 matplotlib chart types saved to `charts/`
- **Audit trail** — every create/update/delete is logged to `audit_logs` (and MongoDB)
- **29 automated pytest tests** — 100% pass rate

---

## Project Structure

```
local-waste-services/
│
├── database/
│   ├── models.py          # SQLAlchemy ORM models (~220 lines)
│   ├── connection.py      # Engine & session factory (~30 lines)
│   └── mongo_handler.py   # PyMongo wrapper (~75 lines)
│
├── repositories/
│   ├── customer_repo.py   # Customer CRUD (~80 lines)
│   ├── schedule_repo.py   # Schedule/route/crew CRUD + queries (~130 lines)
│   ├── incident_repo.py   # Incident/service request CRUD + queries (~110 lines)
│   └── recycling_repo.py  # Recycling CRUD + analytics queries (~70 lines)
│
├── services/
│   ├── customer_service.py  # Customer business logic (~65 lines)
│   ├── schedule_service.py  # Schedule business logic (~55 lines)
│   └── report_service.py    # Reporting aggregation (~50 lines)
│
├── ui/
│   └── cli.py             # CLI menu application (~290 lines)
│
├── utils/
│   ├── visualisation.py   # matplotlib chart generation (~80 lines)
│   └── seed_data.py       # Sample data population (~105 lines)
│
├── tests/
│   └── test_app.py        # 29 pytest tests (~280 lines)
│
├── charts/                # Generated PNG charts (auto-created)
├── main.py                # Entry point (~25 lines)
├── requirements.txt       # Pinned dependencies
└── README.md
```

---

## Database Schema

12 tables covering all operational entities:

| Table | Purpose |
|---|---|
| `customers` | Customer account records |
| `addresses` | Property addresses linked to customers |
| `bin_types` | Bin type catalogue (capacity, waste category) |
| `customer_bins` | Links customers to their assigned bin types (M:M) |
| `vehicles` | Collection vehicle fleet |
| `routes` | Collection routes by area and day |
| `crew_members` | Crew member records |
| `crew_assignments` | Crew/vehicle/route assignments per day (M:M) |
| `collection_schedules` | Individual collection events |
| `service_requests` | Customer-raised service tickets |
| `incident_reports` | Crew-reported incidents |
| `recycling_outcomes` | Recycling tonnage and contamination data |
| `audit_logs` | Immutable record of all data changes |

---

## Requirements

- Python 3.11+
- SQLite 3 (built-in)
- MongoDB Community *(optional — app runs in SQLite-only mode if unavailable)*

Install Python dependencies:

```bash
pip install -r requirements.txt
```

**requirements.txt includes:**

```
sqlalchemy==2.0.49
pymongo==4.17.0
matplotlib==3.10.9
pytest==9.0.3
```

---

## Getting Started

### 1. Clone the repository

```bash
git clone <repository-url>
cd local-waste-services
```
# 2. (Optional) Create a virtual environment
python -m venv venv
source venv/bin/activate      # Linux/macOS
venv\Scripts\activate         # Windows

### 3. Install dependencies and run

```bash
pip install -r requirements.txt
python main.py --seed (optional to populate database)
python main.py
```

On first run, the database is initialised automatically and tables are created via `Base.metadata.create_all()`.

### 4. Seed sample data

From the CLI menu, select the **Seed Data** option, or run directly:

```bash
python -c "from utils.seed_data import seed; seed()"
```

This populates the database with:
- 12 customers (residential, commercial, school)
- 5 routes across London
- 5 vehicles & 8 crew members
- 96 collection schedules
- 25 incident reports
- 240 recycling outcome records

### 5. Run tests

```bash
pytest tests/test_app.py -v
```

All 29 tests should pass. Tests use an isolated in-memory SQLite database.

### 6. Generate charts

From the CLI menu, select **Analytics / Visualisations**. Charts are saved to `charts/`:

| File | Description |
|---|---|
| `completion_rates.png` | Collection completion % by route |
| `recycling_materials.png` | Recycled weight by material type (pie) |
| `contamination_by_material.png` | Average contamination rate per material |
| `incident_types.png` | Frequency of each incident type |
| `missed_collections.png` | Missed collection counts per route |

---

## MongoDB (Optional Hybrid Mode)

If MongoDB is running locally on the default port (`mongodb://localhost:27017`), the application will:

- Mirror incident reports to the `incidents` collection
- Mirror audit events to the `audit_events` collection

If MongoDB is **unavailable**, the application degrades gracefully to SQLite-only mode — no configuration change is needed.

---

## Security

| Measure | Implementation |
|---|---|
| SQL injection prevention | SQLAlchemy ORM parameterised queries |
| Password hashing | SHA-256 via `hashlib` with salt |
| Input validation | Regex email checks, whitelist account types |
| Audit logging | All writes recorded in `audit_logs` |
| Foreign key enforcement | `PRAGMA foreign_keys = ON` at connection time |

> **Note:** In a production system, bcrypt or Argon2 with a per-user random salt would replace the current SHA-256 scheme (OWASP, 2021).

---

## Advanced Queries

| Query | Technique |
|---|---|
| Missed collections by route | JOIN + GROUP BY + ORDER BY |
| Recycling performance by material | GROUP BY + aggregate (SUM, AVG) |
| Contamination hotspots | JOIN + GROUP BY + HAVING |
| Collection completion rate | Conditional SUM + percentage calculation |

---

## Performance Optimisations

Seven indexes are applied to frequently filtered columns:

- `addresses.postcode`
- `collection_schedules.scheduled_date`
- `collection_schedules.status`
- `recycling_outcomes.collection_date`
- `routes.area`
- `audit_logs.table_name`
- `audit_logs.action`

---

## References

- Codd, E. F. (1970). *A relational model of data for large shared data banks.* CACM, 13(6).
- Elmasri, R. and Navathe, S. B. (2016). *Fundamentals of Database Systems.* 7th edn. Pearson.
- Sadalage, P. J. and Fowler, M. (2012). *NoSQL Distilled.* Addison-Wesley.
- OWASP (2021). *Password Storage Cheat Sheet.* https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html

---

## Licence

This project was submitted as coursework for CPS7003B – Database Systems at St Mary's University. Not licensed for redistribution.
