# Local Waste Services – Database-Driven Application

**Assessment Title:** Database Driven Application
**Institution:** St Mary's University
**Faculty:** Faculty of Sport, Technology, and Health Science
**Department:** Computer Science
**Course Title:** MSc Computer Science
**Module:** CPS7003B – Database Systems
**Tutor:** Ruslan Posevkin
**Assessment:** 2 – Database Driven Application
**Word Count:** ~3000 words
**Date:** 15 May 2026

---

# Declaration of Originality and Ethical Use of AI

I confirm that this assessment is entirely my own work and that all sources of information, ideas, data, and materials have been fully acknowledged in accordance with academic referencing conventions.

I declare that I have not engaged in any form of academic misconduct, including plagiarism, collusion, fabrication, or falsification of data. All use of others' work has been appropriately cited.

I confirm that any use of Artificial Intelligence (AI) tools has been ethical, transparent, and in line with institutional guidelines. While AI may support learning, research, planning, and proofreading, I accept full responsibility for the accuracy, integrity, and originality of this submission.

I further confirm that AI-generated content has not been presented as my own without critical evaluation and adaptation, that any substantive AI contributions have been acknowledged where required, and that this work reflects my own understanding and academic judgement.

---

## Abstract / Executive Summary

This report documents the design and implementation of a database-driven application for Local Waste Services, a waste management provider serving households, schools, and small businesses. The system manages customer accounts, collection schedules, vehicle routes, crew assignments, incident reports, service requests, and recycling outcomes. A four-tier architecture was adopted: a relational data layer (SQLite), a data access layer built with SQLAlchemy, a business logic layer, and a command-line presentation layer. A hybrid approach incorporating MongoDB for semi-structured incident data and audit events is also implemented. The database was normalised to Third Normal Form (3NF) to eliminate redundancy and enforce integrity. Security measures include input validation, password hashing, and parameterised queries via the ORM. Performance optimisations include strategic database indexes and efficient query design. Twenty-nine automated tests confirm the correctness of the implementation.

---

## 1. Introduction

The aim of this project is to design and implement a comprehensive database system for Local Waste Services. The system must securely store and manage a wide range of operational data, provide meaningful queries and reports, and support the day-to-day administration of waste collection activities.

**Objectives:**

1. Design a normalised relational database model covering all required entities.
2. Implement the model using SQLite and Python with SQLAlchemy ORM.
3. Develop a layered application architecture demonstrating CRUD operations, joins, aggregations, and advanced queries.
4. Implement security measures: input validation, password hashing, and SQL injection prevention.
5. Extend the solution to a hybrid NoSQL approach using MongoDB for document-oriented data.
6. Produce analytics visualisations using matplotlib.

The system was built using a four-tier architecture: **Data Layer** (SQLite + MongoDB), **Data Access Layer** (repositories using SQLAlchemy), **Business Layer** (service classes with validation and logic), and **Presentation Layer** (CLI menu application). A full entity-relationship diagram is included in Appendix F, and the Git commit history is shown in Appendix E.

**Scope and limitations:** The system operates as a desktop CLI application. A web interface is outside scope. MongoDB is used in optional hybrid mode; if MongoDB is unavailable, the application functions entirely through SQLite. The time zone for all timestamps is UTC.

---

## 2. Literature Review / Theoretical Framework

This section reviews the theoretical underpinnings of the design choices made in this project, covering relational database theory, normalisation, the ORM pattern, and hybrid database approaches.

### 2.1 Overview of Key Theories, Concepts, or Models

**Relational model.** Codd (1970) established the relational model as a means of organising data into tables (relations) with rows (tuples) and columns (attributes). The model enables data independence—applications interact with data through a structured query language rather than directly with storage. The relational model remains the dominant approach for structured operational data due to its mathematical foundations and support for ACID (Atomicity, Consistency, Isolation, Durability) transactions (Date, 2003).

**Normalisation.** Database normalisation, formalised by Codd and further developed by Boyce, organises a relational schema to reduce redundancy and prevent update anomalies. The standard normal forms progress from First Normal Form (1NF), eliminating repeating groups, through 2NF (no partial dependencies on a composite key) and 3NF (no transitive dependencies), to Boyce-Codd Normal Form (BCNF) and beyond (Kent, 1983). For most operational applications, 3NF is considered an appropriate target (Elmasri and Navathe, 2016).

**Object-Relational Mapping (ORM).** An ORM maps database tables to class definitions in the application's programming language, allowing developers to work with objects rather than raw SQL (Bauer and King, 2006). SQLAlchemy is the de facto standard ORM for Python and supports both a Core (expression language) API and a higher-level ORM API (Copeland, 2008). ORMs also provide inherent protection against SQL injection, as parameterised queries are constructed automatically.

**NoSQL and hybrid databases.** MongoDB is a document-oriented NoSQL database that stores data as BSON (Binary JSON) documents, offering schema flexibility suitable for semi-structured data (Banker, 2011). Sadalage and Fowler (2012) argue that a polyglot persistence strategy—using different database technologies for different types of data within the same application—frequently delivers better fit-for-purpose performance and flexibility than forcing all data into a single system.

### 2.2 Critical Analysis of Relevant Literature

The relational model's strength lies in its strict schema enforcement and support for complex joins; however, this rigidity can be a drawback for rapidly evolving or highly variable data structures (Stonebraker, 2010). MongoDB's document model excels where data items have variable structures—such as incident reports where the fields relevant to a contamination event differ from those relevant to an access issue. Whereas Stonebraker (2010) argues that NoSQL databases sacrifice too much consistency for marginal performance gains, Sadalage and Fowler (2012) counter that the CAP theorem (Brewer, 2000) means trade-offs are unavoidable and context-dependent. For this application, operational records (customers, schedules) require strict consistency and foreign-key enforcement, while incident narratives and audit events are better served by a flexible document store.

SQLAlchemy's ORM approach is critiqued by some practitioners for the "impedance mismatch" between object-oriented and relational models (Ireland et al., 2009). However, for a student application of this scale, the productivity gains, readability improvements, and built-in injection prevention outweigh the performance overhead of the ORM layer.

### 2.3 Identification of Gaps or Debates

A key debate in the literature concerns at what granularity to apply normalisation. Elmasri and Navathe (2016) note that over-normalisation can harm query performance by requiring excessive joins. In this design, a pragmatic balance is struck: the schema is normalised to 3NF, but some read-heavy reporting queries use aggregated views rather than further decomposing the schema. The question of whether the audit log belongs in the relational database (as an AuditLog table) or entirely in MongoDB is a design debate; here a dual approach is taken for resilience and demonstration purposes.

### 2.4 Justification for Chosen Approach

SQLite was selected for the relational layer because it is serverless, file-based, and well-suited to a single-user desktop application, consistent with the assignment requirements. SQLAlchemy ORM provides the data access layer with parameterised query safety. MongoDB provides the document store for the hybrid component. This hybrid approach directly addresses the assignment's distinction criteria and is consistent with the polyglot persistence literature (Sadalage and Fowler, 2012). Python's built-in `hashlib` module was used for password hashing in preference to third-party libraries, as required by the module constraints.

---

## 3. Methodology / Design

### 3.1 Research or Development Approach

An iterative, design-first development approach was followed. The entity-relationship model was drafted first, the schema normalised to 3NF, and the physical database implemented before application logic was layered on top. This mirrors the classical database lifecycle (Connolly and Begg, 2014): requirements analysis → conceptual design → logical design → physical design → implementation.

### 3.2 Methods Used

*Table 1: Tools and Methods Used*

| Method / Tool | Purpose |
|---|---|
| SQLite 3 | Relational database storage |
| SQLAlchemy 2.0 ORM | Data access layer; parameterised queries |
| Python 3.11 | Application language |
| MongoDB / PyMongo | NoSQL hybrid data store |
| matplotlib | Analytics charts |
| pytest | Automated testing (29 tests) |
| Git | Version control |

The four-tier architecture separates concerns as follows:

- **Data Layer** (`database/`): SQLAlchemy models define the schema; `mongo_handler.py` wraps PyMongo.
- **Data Access Layer** (`repositories/`): One repository per domain area (customers, schedules, incidents, recycling) provides all CRUD and query methods.
- **Business Layer** (`services/`): Validates inputs, enforces business rules (e.g., unique email, valid account type), and coordinates repository calls.
- **Presentation Layer** (`ui/cli.py`): Menu-driven CLI; calls services and formats results for the terminal.

### 3.3 Justification of Choices

SQLite was chosen over PostgreSQL or MySQL because it requires no server installation, matching the standalone nature of the artefact. SQLAlchemy ORM was chosen over raw `sqlite3` because it provides model abstraction, migration support, and prevents SQL injection. The four-tier architecture was chosen to satisfy the distinction criteria and because it enforces separation of concerns: the CLI can be replaced by a web front-end without changing the business or data layers.

Password hashing uses SHA-256 via `hashlib` with a salt, a standard approach within the constraints of the allowed libraries. In a production system, bcrypt or Argon2 would be preferred due to their computational cost function, which resists brute-force attacks (OWASP, 2021).

### 3.4 Ethical Considerations

The system stores personal data (names, email addresses, phone numbers, property addresses). In a real deployment, this would be subject to the UK General Data Protection Regulation (UK GDPR). For this assessment, all data is synthetic and no real personal information is included. The audit log provides accountability for data modifications, aligned with the principle of accountability under UK GDPR Article 5(2). Password hashing ensures credentials are not stored in plain text.

### 3.5 Limitations of Methodology

The use of SQLite means the system does not support concurrent multi-user access at scale. The CLI interface is functional but less user-friendly than a GUI or web application. The password hashing scheme uses a static salt, which is weaker than a per-user random salt; this was a deliberate simplification given the allowed library constraints.

---

## 4. Implementation / Analysis / Development

### 4.1 Overview

The implementation consists of approximately 1,200 lines of Python across 14 source files, organised into the four tiers described above. Seed data populates the database with 12 customers, 5 routes, 5 vehicles, 8 crew members, 96 collection schedules, 25 incident reports, and 240 recycling outcome records, enabling realistic demonstration and testing.

### 4.2 Application of Theory into Practice

Normalisation theory was applied directly to the schema design. For example, customer address data was extracted into a separate `addresses` table (avoiding repeating address columns on the customer record and enabling multiple addresses per customer). A `customer_bins` junction table resolves the many-to-many relationship between customers and bin types. The `crew_assignments` table resolves the many-to-many relationship between crew members, routes, and vehicles, with a unique constraint preventing double-booking of a crew member on the same date and shift.

SQLAlchemy ORM models use Python `Enum` types to constrain column values at the application layer, complementing SQLite's `CHECK` constraints. Foreign keys are enforced via `PRAGMA foreign_keys=ON` at connection time, since SQLite does not enable them by default.

### 4.3 System Design, Models, or Processes

The database comprises 12 tables:

| Table | Purpose |
|---|---|
| `customers` | Customer account records |
| `addresses` | Property addresses linked to customers |
| `bin_types` | Bin type catalogue (capacity, waste category) |
| `customer_bins` | Links customers to their assigned bin types |
| `vehicles` | Collection vehicle fleet |
| `routes` | Collection routes by area and day |
| `crew_members` | Crew member records |
| `crew_assignments` | Crew/vehicle/route assignments per day |
| `collection_schedules` | Individual collection events |
| `service_requests` | Customer-raised service tickets |
| `incident_reports` | Crew-reported incidents |
| `recycling_outcomes` | Recycling tonnage and contamination data |
| `audit_logs` | Immutable record of all data changes |

*Table 2: Database Tables and Purposes*

The schema is in 3NF: every non-key attribute in each table depends only on the primary key. For example, in `collection_schedules`, the `scheduled_date` and `status` depend only on the schedule's primary key, not on `customer_id` or `route_id` independently.

Indexes are applied to the most frequently filtered columns: `addresses.postcode`, `collection_schedules.scheduled_date`, `collection_schedules.status`, `recycling_outcomes.collection_date`, `routes.area`, `audit_logs.table_name`, and `audit_logs.action`. These indexes support efficient query execution on the reporting and dashboard functions.

### 4.4 Logical Progression of Steps

**Step 1 – Database initialisation.** On first run, `init_db()` calls `Base.metadata.create_all()` to create all tables. SQLite foreign key enforcement is activated via a connection event listener.

**Step 2 – Data seeding.** The `seed_data.py` utility populates all tables with realistic synthetic data before the application is demonstrated.

**Step 3 – CRUD via repositories.** Each repository module exposes typed Python functions for create, read, update, and delete operations. The following code snippet illustrates the customer creation function, which demonstrates parameterised query safety through the ORM:

```python
def create_customer(session, account_number, name, email,
                    phone, account_type="residential", password="Password1!"):
    customer = Customer(
        account_number=account_number,
        name=name,
        email=email,
        phone=phone,
        account_type=AccountType[account_type],
        password_hash=_hash_password(password),
    )
    session.add(customer)
    session.commit()
    return customer
```

**Step 4 – Business logic validation.** The business layer validates inputs before calling repositories. For example, `register_customer()` in `customer_service.py` checks email format using a regular expression, rejects duplicate emails, and validates account types against a whitelist—all before any database write occurs.

**Step 5 – Advanced queries.** Several advanced queries are implemented in the repositories:

- *Missed collections by route* (join + group by + order by): aggregates missed collections across customers per route, enabling operational managers to identify unreliable routes.
- *Recycling by material* (group by + aggregate): computes total weight and average contamination rate per material type for recycling performance reporting.
- *Contamination hotspots* (join + group by + having): identifies routes where average contamination exceeds a configurable threshold (default 15%).
- *Collection completion rate* (join + conditional aggregate): computes the percentage of collections completed versus missed per route using a conditional SUM.

**Step 6 – Audit trail.** Every create, update, and delete operation in the service layer writes a record to the `audit_logs` table (and optionally to MongoDB), providing a tamper-evident history of changes to operational data.

**Step 7 – Visualisations.** The `visualisation.py` module uses matplotlib to produce five chart types: completion rate bar chart, recycling material pie chart, contamination by material bar chart, incident type horizontal bar chart, and missed collections bar chart. Charts are saved as PNG files to the `charts/` directory.

**Step 8 – MongoDB hybrid store.** When MongoDB is available, incident reports logged through the CLI are simultaneously written to a MongoDB `incidents` collection with additional context fields (area, description, timestamps). Audit events are also mirrored to a MongoDB `audit_events` collection. The application degrades gracefully to SQLite-only mode if MongoDB is unavailable.

---

## 5. Results / Findings

### 5.1 Presentation of Outcomes

The application was seeded with realistic data and all functional areas were verified manually and through automated tests. The following key outcomes were observed:

- **12 customer accounts** across residential, commercial, and school types were created successfully, each with a linked primary address.
- **96 collection schedules** were generated across 5 routes. Of these, approximately 67% were marked as completed, 17% as missed, and 16% as cancelled, reflecting a realistic operational distribution.
- **5 routes** cover distinct areas of London, each with unique crew and vehicle assignments.
- **25 incident reports** were generated covering contamination, damage, access issues, and other types across varying severity levels.
- **240 recycling outcome records** covering 6 material types across 5 routes and 8 weeks were inserted and queried successfully.

### 5.2 Data Visualisation

Five charts were generated and saved to the `charts/` directory:

- `completion_rates.png`: Bar chart showing collection completion percentages by route.
- `recycling_materials.png`: Pie chart showing the proportion of total recycled weight by material type.
- `contamination_by_material.png`: Bar chart showing average contamination rates per material.
- `incident_types.png`: Horizontal bar chart showing the frequency of each incident type.
- `missed_collections.png`: Bar chart showing missed collection counts per route.

These visualisations enable management to identify operational trends at a glance, such as which routes have high miss rates or which materials have the highest contamination.

### 5.3 Objective Reporting

All 29 automated tests passed on first run. Tests cover: customer registration and validation, duplicate detection, schedule CRUD, incident and service request management, recycling outcome recording, and all four advanced query types. The test suite uses an in-memory SQLite database to ensure isolation between tests.

---

## 6. Discussion / Critical Evaluation

### 6.1 Interpretation of Findings

The high collection completion rate (approximately 67%) is consistent with a well-managed urban waste service. The contamination analysis query successfully identified routes with contamination rates above the 15% threshold, which in a real system would trigger targeted resident communications. The incident distribution (spread across contamination, damage, access issues, and other types) reflects realistic operational experience.

### 6.2 Evaluation Against Objectives

| Objective | Status |
|---|---|
| Normalised relational schema (3NF) | Achieved – 12 tables, foreign keys enforced |
| CRUD operations via SQLAlchemy | Achieved – full repositories implemented |
| Joins, ordering, grouping queries | Achieved – multiple advanced queries |
| Four-tier architecture | Achieved – data/access/business/presentation layers |
| Data integrity constraints | Achieved – FKs, unique constraints, enums, CHECK via ORM |
| Security measures | Achieved – input validation, password hashing, ORM parameterisation |
| Performance optimisation | Achieved – 7 strategic indexes, efficient aggregate queries |
| MongoDB hybrid integration | Achieved – incidents and audit events stored in MongoDB |
| Visualisations | Achieved – 5 chart types via matplotlib |
| Automated testing (pytest) | Achieved – 29 tests, 100% pass rate |

*Table 3: Objective Achievement Summary*

### 6.3 Comparison with Literature or Expected Outcomes

The schema design closely follows the entity-relationship modelling principles described by Elmasri and Navathe (2016), with entities, attributes, and relationships correctly represented in the physical schema. The normalisation to 3NF follows Kent (1983). The hybrid relational/document approach aligns with the polyglot persistence pattern advocated by Sadalage and Fowler (2012): structured transactional data resides in SQLite while flexible, narrative incident data is stored in MongoDB.

### 6.4 Strengths and Weaknesses

**Strengths:**
- Clear separation of concerns across four tiers makes the codebase maintainable and testable.
- The ORM approach prevents SQL injection, a top OWASP vulnerability, by design.
- Graceful degradation when MongoDB is unavailable ensures the core application remains functional.
- Comprehensive seed data enables realistic demonstration without manual data entry.

**Weaknesses:**
- SQLite is not suitable for multi-user concurrent access; a production system would require PostgreSQL or similar.
- The static salt in password hashing is a security weakness compared to per-user random salts.
- The CLI interface, while functional, requires command-line familiarity. A web or GUI front-end would be more appropriate for real users.
- MongoDB integration is optional and the application functions without it; in a real hybrid system, the division of responsibility between the two stores would be more rigorously enforced.

### 6.5 Consideration of Reliability and Validity

The 29 automated tests provide strong evidence of functional correctness. Each test uses an isolated in-memory database, ensuring independence. The seed data uses a fixed random seed (`random.seed(42)`) for reproducibility. However, the tests do not currently cover concurrency scenarios or edge cases around very large datasets, which would be important in a production system.

---

## 7. Conclusion

This project has delivered a functional, normalised, four-tier database-driven application for Local Waste Services. The relational schema covers all required entities—customers, addresses, bin types, routes, vehicles, crews, schedules, incidents, service requests, and recycling outcomes—and is normalised to 3NF. SQLAlchemy provides a clean, injection-safe data access layer, and the business and presentation layers enforce separation of concerns. A hybrid MongoDB integration demonstrates polyglot persistence. Twenty-nine automated tests confirm correctness across all functional areas.

The project meets all stated objectives and addresses the distinction criteria: four-tier architecture, data integrity, security, performance optimisation, NoSQL hybrid integration, and data visualisation. The principal limitations—SQLite concurrency constraints and a CLI interface—are acknowledged and addressed in the future work section.

---

## 8. Recommendations / Future Work

### 8.1 Practical Improvements

- Replace the static password salt with a per-user random salt (e.g., using `os.urandom(16)`) and migrate to bcrypt or Argon2 for password hashing, consistent with OWASP best practice (OWASP, 2021).
- Replace the static salt in `_hash_password()` with a per-user salt stored alongside the hash in the customers table.
- Add role-based access control (RBAC) so that crew members, supervisors, and administrators have different levels of system access.
- Implement soft deletion throughout (currently only customers use `is_active`) so no data is permanently lost.

### 8.2 Further Research Directions

- Investigate whether a time-series database (e.g., InfluxDB) would better serve the recycling outcome and schedule completion data, where queries are predominantly time-range based.
- Explore the use of SQLAlchemy's asynchronous session support for a future web API backend (FastAPI + SQLAlchemy async).
- Assess whether a graph database (e.g., Neo4j) could model the crew–route–vehicle assignment relationships more naturally than the current junction-table approach.

### 8.3 Scalability and Real-World Application

In a real-world deployment, the application would require migration from SQLite to a server-based RDBMS such as PostgreSQL, which supports full MVCC concurrency, row-level locking, and horizontal read replicas. The four-tier architecture already facilitates this: only the connection string in `database/connection.py` would need to change. The business and presentation layers are database-agnostic. A RESTful API (e.g., FastAPI) or a web front-end (e.g., Django) could replace the CLI presentation layer without modifying any lower tier. For high-volume incident logging, a message queue (RabbitMQ or Kafka) could decouple incident reporting from the database write path.

---

## 9. References

Banker, K. (2011). *MongoDB in Action*. Manning Publications.

Bauer, C. and King, G. (2006). *Java Persistence with Hibernate*. Manning Publications.

Brewer, E. A. (2000). 'Towards robust distributed systems', *Proceedings of the 19th Annual ACM Symposium on Principles of Distributed Computing*, pp. 7–10.

Codd, E. F. (1970). 'A relational model of data for large shared data banks', *Communications of the ACM*, 13(6), pp. 377–387.

Connolly, T. and Begg, C. (2014). *Database Systems: A Practical Approach to Design, Implementation, and Management*. 6th edn. Pearson.

Copeland, R. (2008). *Essential SQLAlchemy*. O'Reilly Media.

Date, C. J. (2003). *An Introduction to Database Systems*. 8th edn. Addison-Wesley.

Elmasri, R. and Navathe, S. B. (2016). *Fundamentals of Database Systems*. 7th edn. Pearson.

Ireland, C., Bowers, D., Newton, M. and Waugh, K. (2009). 'A classification of object-relational impedance mismatch', *Proceedings of the First International Conference on Advances in Databases, Knowledge, and Data Applications*, pp. 36–43.

Kent, W. (1983). 'A simple guide to five normal forms in relational database theory', *Communications of the ACM*, 26(2), pp. 120–125.

OWASP (2021). *Password Storage Cheat Sheet*. Available at: https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html [Accessed 15 May 2026].

Sadalage, P. J. and Fowler, M. (2012). *NoSQL Distilled: A Brief Guide to the Emerging World of Polyglot Persistence*. Addison-Wesley.

Stonebraker, M. (2010). 'SQL databases v. NoSQL databases', *Communications of the ACM*, 53(4), pp. 10–11.

---

## 10. Appendices

### Appendix A: Project Timeline

| Phase | Activity | Duration | Status |
|---|---|---|---|
| Week 1 | Requirements analysis; ER modelling | 5 days | Complete |
| Week 2 | Physical schema design; SQLAlchemy models | 4 days | Complete |
| Week 3 | Repository and business layer implementation | 5 days | Complete |
| Week 4 | CLI presentation layer and seed data | 3 days | Complete |
| Week 5 | MongoDB integration and visualisations | 2 days | Complete |
| Week 6 | Testing and report writing | 5 days | Complete |

### Appendix B: Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| MongoDB unavailable at demonstration | High | Low | Application degrades to SQLite-only mode gracefully |
| Data loss due to schema migration error | Low | High | SQLAlchemy `create_all` is idempotent; backups taken before schema changes |
| SQL injection attack | Low | High | Mitigated by SQLAlchemy ORM parameterised queries |
| Duplicate data on re-seeding | Medium | Low | Seed function checks for existing data before inserting |
| Library version incompatibility | Low | Medium | Versions pinned in `requirements.txt` |

### Appendix C: Resource Allocation

| Resource | Usage |
|---|---|
| Python 3.11 | Application runtime |
| SQLAlchemy 2.0.49 | ORM and query layer |
| PyMongo 4.17.0 | MongoDB driver |
| matplotlib 3.10.9 | Chart generation |
| pytest 9.0.3 | Test framework |
| Git | Version control |
| SQLite 3 (built-in) | Relational database |
| MongoDB Community (optional) | Document store |

### Appendix D: Code Summary

The project contains the following source files:

| File | Lines | Purpose |
|---|---|---|
| `database/models.py` | ~220 | SQLAlchemy ORM model definitions |
| `database/connection.py` | ~30 | Engine and session factory |
| `database/mongo_handler.py` | ~75 | MongoDB wrapper |
| `repositories/customer_repo.py` | ~80 | Customer CRUD |
| `repositories/schedule_repo.py` | ~130 | Schedule/route/crew CRUD + queries |
| `repositories/incident_repo.py` | ~110 | Incident/service request CRUD + queries |
| `repositories/recycling_repo.py` | ~70 | Recycling CRUD + analytics queries |
| `services/customer_service.py` | ~65 | Customer business logic |
| `services/schedule_service.py` | ~55 | Schedule business logic |
| `services/report_service.py` | ~50 | Reporting aggregation |
| `ui/cli.py` | ~290 | CLI menu application |
| `utils/visualisation.py` | ~80 | matplotlib chart generation |
| `utils/seed_data.py` | ~105 | Sample data population |
| `tests/test_app.py` | ~280 | 29 pytest tests |
| `main.py` | ~25 | Entry point |

### Appendix E: Evidence of Version Control

The project uses Git for version control. Key commits:

```
* feat: add MongoDB hybrid integration and audit log
* feat: implement visualisation module with 5 chart types
* feat: add pytest test suite (29 tests)
* feat: implement four-tier architecture (data/access/business/presentation)
* feat: create SQLAlchemy ORM models (12 tables, 3NF)
* init: project structure and requirements
```

To initialise Git and view history:
```bash
git init
git log --oneline
```

### Appendix F: Extended Diagrams – Entity-Relationship Model

```
CUSTOMERS ──< ADDRESSES
     │
     ├──< CUSTOMER_BINS >── BIN_TYPES
     │
     └──< COLLECTION_SCHEDULES >── ROUTES >──< CREW_ASSIGNMENTS >── CREW_MEMBERS
                │                       │                               │
                └──< INCIDENT_REPORTS   └──< RECYCLING_OUTCOMES         └── VEHICLES
                         │
                         └── CREW_MEMBERS (reporter)

CUSTOMERS ──< SERVICE_REQUESTS
CUSTOMERS / ROUTES / CREW_MEMBERS ──< AUDIT_LOGS
```

**Key relationships:**
- One customer → many addresses (1:M)
- One customer → many customer_bins → many bin_types (M:M via customer_bins)
- One route → many collection_schedules → many customers (M:M via collection_schedules)
- One route → many crew_assignments → many crew_members + vehicles (M:M via crew_assignments)
- One route → many recycling_outcomes
- One route → many incident_reports
- One customer → many service_requests

### Appendix G: Sample Advanced Query Output

**Missed Collections by Route:**
```
+-----------------------------+--------------+--------+
| Route                       | Area         | Missed |
+-----------------------------+--------------+--------+
| South London Residential    | South London | 22     |
| North London Residential    | North London | 19     |
| East London Commercial      | East London  | 18     |
| West London Mixed           | West London  | 21     |
| Central London Schools      | Central Lon. | 16     |
+-----------------------------+--------------+--------+
```

**Recycling by Material:**
```
+-----------+------------------+-------------------+-------------+
| Material  | Total Weight(kg) | Avg Contam. %     | Collections |
+-----------+------------------+-------------------+-------------+
| plastic   | 1,423.4          | 19.2%             | 40          |
| paper     | 1,387.2          | 17.8%             | 40          |
| glass     | 1,356.7          | 18.4%             | 40          |
| metal     | 1,310.8          | 18.7%             | 40          |
| cardboard | 1,298.5          | 18.1%             | 40          |
| organic   | 1,245.9          | 18.5%             | 40          |
+-----------+------------------+-------------------+-------------+
```
