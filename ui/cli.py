"""Presentation Layer: menu-driven command-line interface."""
import os
import sys

# Add project root to path when running directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_session, init_db
from database.mongo_handler import mongo
from repositories import customer_repo, schedule_repo, incident_repo, recycling_repo
from services import customer_service, schedule_service, report_service
from utils import visualisation


def clear():
    os.system("cls" if os.name == "nt" else "clear")


def pause():
    input("\nPress Enter to continue...")


def print_header(title: str):
    print("\n" + "=" * 60)
    print(f"  LOCAL WASTE SERVICES – {title}")
    print("=" * 60)


def print_table(headers: list[str], rows: list[list]):
    widths = [max(len(str(h)), max((len(str(r[i])) for r in rows), default=0))
              for i, h in enumerate(headers)]
    sep = "+-" + "-+-".join("-" * w for w in widths) + "-+"
    fmt = "| " + " | ".join(f"{{:<{w}}}" for w in widths) + " |"
    print(sep)
    print(fmt.format(*headers))
    print(sep)
    for row in rows:
        print(fmt.format(*[str(v) for v in row]))
    print(sep)


# ---------------------------------------------------------------------------
# Sub-menus
# ---------------------------------------------------------------------------

def menu_customers(session):
    while True:
        print_header("CUSTOMER MANAGEMENT")
        print("  1. List all customers")
        print("  2. Search customer")
        print("  3. View customer details")
        print("  4. Register new customer")
        print("  5. Update contact details")
        print("  6. Deactivate account")
        print("  0. Back")
        choice = input("\nSelect: ").strip()

        if choice == "1":
            customers = customer_repo.get_all_customers(session)
            if not customers:
                print("No customers found.")
            else:
                print_table(
                    ["ID", "Account", "Name", "Type", "Email"],
                    [[c.id, c.account_number, c.name, c.account_type.value, c.email]
                     for c in customers]
                )
            pause()

        elif choice == "2":
            q = input("Search (name or email): ").strip()
            results = customer_repo.search_customers(session, q)
            if results:
                print_table(
                    ["ID", "Account", "Name", "Email"],
                    [[c.id, c.account_number, c.name, c.email] for c in results]
                )
            else:
                print("No matches found.")
            pause()

        elif choice == "3":
            try:
                cid = int(input("Customer ID: "))
                summary = customer_service.get_customer_summary(session, cid)
                if not summary:
                    print("Customer not found.")
                else:
                    print(f"\n  Account : {summary['account_number']}")
                    print(f"  Name    : {summary['name']}")
                    print(f"  Email   : {summary['email']}")
                    print(f"  Phone   : {summary['phone']}")
                    print(f"  Type    : {summary['type']}")
                    print(f"  Active  : {summary['active']}")
                    print(f"  Address : {', '.join(summary['addresses'])}")
            except ValueError:
                print("Invalid ID.")
            pause()

        elif choice == "4":
            print("\n  -- Register New Customer --")
            try:
                acc  = input("Account number: ").strip()
                name = input("Full name: ").strip()
                email = input("Email: ").strip()
                phone = input("Phone: ").strip()
                atype = input("Type (residential/commercial/school) [residential]: ").strip() or "residential"
                snum  = input("Street number: ").strip()
                sname = input("Street name: ").strip()
                city  = input("City: ").strip()
                pc    = input("Postcode: ").strip()
                ptype = input("Property type (house/flat/office/school) [house]: ").strip() or "house"
                customer, err = customer_service.register_customer(
                    session, acc, name, email, phone, atype,
                    snum, sname, city, pc, ptype
                )
                if err:
                    print(f"  Error: {err}")
                else:
                    print(f"  Customer registered with ID {customer.id}.")
            except Exception as e:
                print(f"  Error: {e}")
            pause()

        elif choice == "5":
            try:
                cid   = int(input("Customer ID: "))
                email = input("New email (leave blank to skip): ").strip() or None
                phone = input("New phone (leave blank to skip): ").strip() or None
                c, err = customer_service.update_contact_details(session, cid, email, phone)
                print(f"  Error: {err}" if err else "  Updated successfully.")
            except ValueError:
                print("Invalid ID.")
            pause()

        elif choice == "6":
            try:
                cid = int(input("Customer ID to deactivate: "))
                ok = customer_service.close_account(session, cid)
                print("  Account deactivated." if ok else "  Customer not found.")
            except ValueError:
                print("Invalid ID.")
            pause()

        elif choice == "0":
            break


def menu_schedules(session):
    while True:
        print_header("COLLECTION SCHEDULES")
        print("  1. View all routes")
        print("  2. View upcoming collections")
        print("  3. View schedules for a customer")
        print("  4. Book a collection")
        print("  5. Mark collection complete")
        print("  6. Mark collection missed")
        print("  7. View missed collections summary")
        print("  0. Back")
        choice = input("\nSelect: ").strip()

        if choice == "1":
            routes = schedule_repo.get_all_routes(session)
            print_table(
                ["ID", "Code", "Name", "Area", "Day", "Duration (min)"],
                [[r.id, r.route_code, r.route_name, r.area, r.day_of_week,
                  r.estimated_duration_mins] for r in routes]
            )
            pause()

        elif choice == "2":
            schedules = schedule_repo.get_upcoming_schedules(session, days_ahead=30)
            if not schedules:
                print("No upcoming pending collections.")
            else:
                print_table(
                    ["ID", "Customer", "Route", "Bin Type", "Scheduled Date"],
                    [[s.id, s.customer.name, s.route.route_name,
                      s.bin_type.name, s.scheduled_date.strftime("%Y-%m-%d")]
                     for s in schedules]
                )
            pause()

        elif choice == "3":
            try:
                cid = int(input("Customer ID: "))
                scheds = schedule_repo.get_schedules_by_customer(session, cid)
                if scheds:
                    print_table(
                        ["ID", "Route", "Bin", "Date", "Status"],
                        [[s.id, s.route.route_name, s.bin_type.name,
                          s.scheduled_date.strftime("%Y-%m-%d"), s.status.value]
                         for s in scheds]
                    )
                else:
                    print("No schedules for this customer.")
            except ValueError:
                print("Invalid ID.")
            pause()

        elif choice == "4":
            try:
                routes  = schedule_repo.get_all_routes(session)
                bins    = schedule_repo.get_all_bin_types(session)
                print_table(["ID", "Route Code", "Name"], [[r.id, r.route_code, r.route_name] for r in routes])
                route_id = int(input("Route ID: "))
                cust_id  = int(input("Customer ID: "))
                print_table(["ID", "Name", "Category"], [[b.id, b.name, b.waste_category.value] for b in bins])
                bin_id   = int(input("Bin Type ID: "))
                date_str = input("Scheduled date (YYYY-MM-DD): ")
                from datetime import datetime
                sdate = datetime.strptime(date_str, "%Y-%m-%d")
                s = schedule_service.book_collection(session, route_id, cust_id, bin_id, sdate)
                print(f"  Collection booked with ID {s.id}.")
            except (ValueError, Exception) as e:
                print(f"  Error: {e}")
                session.rollback()
            pause()

        elif choice == "5":
            try:
                sid = int(input("Schedule ID: "))
                s = schedule_service.mark_collection_complete(session, sid)
                print("  Marked complete." if s else "  Schedule not found.")
            except ValueError:
                print("Invalid ID.")
            pause()

        elif choice == "6":
            try:
                sid    = int(input("Schedule ID: "))
                reason = input("Reason: ")
                s = schedule_service.mark_collection_missed(session, sid, reason)
                print("  Marked as missed." if s else "  Schedule not found.")
            except ValueError:
                print("Invalid ID.")
            pause()

        elif choice == "7":
            data = report_service.get_missed_collections(session)
            if data:
                print_table(
                    ["Route", "Area", "Missed"],
                    [[d["route"], d["area"], d["missed"]] for d in data]
                )
            else:
                print("No missed collections recorded.")
            pause()

        elif choice == "0":
            break


def menu_incidents(session):
    while True:
        print_header("INCIDENTS & SERVICE REQUESTS")
        print("  1. List all incidents")
        print("  2. Report new incident")
        print("  3. Resolve incident")
        print("  4. Open service requests")
        print("  5. Raise service request")
        print("  6. Resolve service request")
        print("  7. Audit log")
        print("  0. Back")
        choice = input("\nSelect: ").strip()

        if choice == "1":
            incidents = incident_repo.get_all_incidents(session)
            if incidents:
                print_table(
                    ["ID", "Type", "Severity", "Route", "Resolved", "Reported"],
                    [[i.id, i.incident_type.value, i.severity.value,
                      i.route.route_name, "Yes" if i.is_resolved else "No",
                      i.reported_at.strftime("%Y-%m-%d")] for i in incidents]
                )
            else:
                print("No incidents found.")
            pause()

        elif choice == "2":
            try:
                crew_list = schedule_repo.get_all_crew(session)
                routes    = schedule_repo.get_all_routes(session)
                print_table(["ID", "Name", "Role"], [[c.id, c.name, c.role.value] for c in crew_list])
                crew_id   = int(input("Crew Member ID: "))
                print_table(["ID", "Code", "Name"], [[r.id, r.route_code, r.route_name] for r in routes])
                route_id  = int(input("Route ID: "))
                itype     = input("Type (contamination/damage/access_issue/hazardous/missed): ").strip()
                desc      = input("Description: ").strip()
                sev       = input("Severity (low/medium/high) [low]: ").strip() or "low"
                inc = schedule_service.report_incident(session, crew_id, route_id, itype, desc, sev)
                print(f"  Incident logged with ID {inc.id}.")
                if mongo.is_connected:
                    mongo.log_incident({
                        "incident_id": inc.id,
                        "type": itype,
                        "severity": sev,
                        "area": next((r.area for r in routes if r.id == route_id), ""),
                        "description": desc,
                    })
                    print("  Also stored in MongoDB.")
            except (ValueError, Exception) as e:
                print(f"  Error: {e}")
                session.rollback()
            pause()

        elif choice == "3":
            try:
                iid = int(input("Incident ID: "))
                inc = incident_repo.resolve_incident(session, iid)
                print("  Incident resolved." if inc else "  Not found.")
            except ValueError:
                print("Invalid ID.")
            pause()

        elif choice == "4":
            requests = incident_repo.get_open_service_requests(session)
            if requests:
                print_table(
                    ["ID", "Customer", "Type", "Priority", "Created"],
                    [[r.id, r.customer.name, r.request_type.value,
                      r.priority.value, r.created_at.strftime("%Y-%m-%d")]
                     for r in requests]
                )
            else:
                print("No open service requests.")
            pause()

        elif choice == "5":
            try:
                cid    = int(input("Customer ID: "))
                rtype  = input("Type (missed_collection/bin_repair/new_bin/complaint/query): ").strip()
                desc   = input("Description: ").strip()
                prio   = input("Priority (low/medium/high) [medium]: ").strip() or "medium"
                sr = schedule_service.raise_service_request(session, cid, rtype, desc, prio)
                print(f"  Service request raised with ID {sr.id}.")
            except (ValueError, Exception) as e:
                print(f"  Error: {e}")
                session.rollback()
            pause()

        elif choice == "6":
            try:
                rid = int(input("Request ID: "))
                sr = schedule_service.resolve_request(session, rid)
                print("  Request resolved." if sr else "  Not found.")
            except ValueError:
                print("Invalid ID.")
            pause()

        elif choice == "7":
            logs = incident_repo.get_audit_logs(session, limit=20)
            if logs:
                print_table(
                    ["ID", "Table", "Record", "Action", "By", "At"],
                    [[l.id, l.table_name, l.record_id, l.action.value,
                      l.changed_by, l.changed_at.strftime("%Y-%m-%d %H:%M")]
                     for l in logs]
                )
            else:
                print("No audit entries.")
            pause()

        elif choice == "0":
            break


def menu_recycling(session):
    while True:
        print_header("RECYCLING OUTCOMES")
        print("  1. View all recycling outcomes")
        print("  2. Summary by material")
        print("  3. Summary by route")
        print("  4. Contamination hotspots")
        print("  0. Back")
        choice = input("\nSelect: ").strip()

        if choice == "1":
            outcomes = recycling_repo.get_all_recycling_outcomes(session)
            if outcomes:
                print_table(
                    ["ID", "Route", "Material", "Weight (kg)", "Contam. %", "Date"],
                    [[o.id, o.route.route_name, o.material_type.value,
                      round(o.weight_kg, 1), f"{o.contamination_rate*100:.1f}%",
                      o.collection_date.strftime("%Y-%m-%d")]
                     for o in outcomes[:30]]
                )
                if len(outcomes) > 30:
                    print(f"  ... and {len(outcomes)-30} more records.")
            else:
                print("No recycling data found.")
            pause()

        elif choice == "2":
            summary = report_service.get_recycling_summary(session)
            print(f"\n  Total recycled: {summary['total_weight_kg']} kg\n")
            print_table(
                ["Material", "Weight (kg)", "Avg Contam. %", "Collections"],
                [[d["material"], d["weight_kg"], d["avg_contamination_pct"],
                  d["collections"]] for d in summary["by_material"]]
            )
            pause()

        elif choice == "3":
            rows = recycling_repo.get_recycling_by_route(session)
            if rows:
                print_table(
                    ["Route", "Area", "Total (kg)", "Avg Contam. %"],
                    [[r.route_name, r.area, round(r.total_kg or 0, 1),
                      f"{(r.avg_contamination or 0)*100:.1f}%"] for r in rows]
                )
            else:
                print("No data.")
            pause()

        elif choice == "4":
            hotspots = report_service.get_contamination_hotspots(session)
            if hotspots:
                print_table(
                    ["Route", "Area", "Avg Contamination %"],
                    [[h["route"], h["area"], h["avg_contamination_pct"]]
                     for h in hotspots]
                )
            else:
                print("No contamination hotspots above threshold.")
            pause()

        elif choice == "0":
            break


def menu_reports(session):
    while True:
        print_header("ANALYTICS & CHARTS")
        print("  1. Generate completion rate chart")
        print("  2. Generate recycling breakdown chart")
        print("  3. Generate contamination by material chart")
        print("  4. Generate incident type chart")
        print("  5. Generate missed collections chart")
        print("  6. Generate ALL charts")
        print("  0. Back")
        choice = input("\nSelect: ").strip()

        if choice in ("1", "6"):
            data = report_service.get_completion_stats(session)["completion_by_route"]
            path = visualisation.plot_completion_rates(data)
            if path:
                print(f"  Saved: {path}")

        if choice in ("2", "6"):
            summary = report_service.get_recycling_summary(session)
            path = visualisation.plot_recycling_by_material(summary["by_material"])
            if path:
                print(f"  Saved: {path}")

        if choice in ("3", "6"):
            summary = report_service.get_recycling_summary(session)
            path = visualisation.plot_contamination_by_material(summary["by_material"])
            if path:
                print(f"  Saved: {path}")

        if choice in ("4", "6"):
            data = report_service.get_incident_summary(session)
            path = visualisation.plot_incident_types(data)
            if path:
                print(f"  Saved: {path}")

        if choice in ("5", "6"):
            data = report_service.get_missed_collections(session)
            path = visualisation.plot_missed_collections(data)
            if path:
                print(f"  Saved: {path}")

        if choice not in ("1", "2", "3", "4", "5", "6", "0"):
            print("Invalid choice.")

        if choice == "0":
            break
        else:
            pause()


def menu_crew(session):
    while True:
        print_header("CREW & VEHICLES")
        print("  1. List crew members")
        print("  2. List vehicles")
        print("  3. View crew assignments")
        print("  0. Back")
        choice = input("\nSelect: ").strip()

        if choice == "1":
            crew = schedule_repo.get_all_crew(session)
            print_table(
                ["ID", "Employee ID", "Name", "Role", "Contact"],
                [[c.id, c.employee_id, c.name, c.role.value, c.contact_number]
                 for c in crew]
            )
            pause()

        elif choice == "2":
            vehicles = schedule_repo.get_all_vehicles(session)
            print_table(
                ["ID", "Reg", "Make", "Model", "Capacity (kg)", "Type"],
                [[v.id, v.registration, v.make, v.model, v.capacity_kg, v.vehicle_type.value]
                 for v in vehicles]
            )
            pause()

        elif choice == "3":
            from database.models import CrewAssignment
            db_session = session
            assignments = db_session.query(CrewAssignment).order_by(
                CrewAssignment.assignment_date.desc()
            ).limit(20).all()
            if assignments:
                print_table(
                    ["ID", "Route", "Crew", "Vehicle", "Date", "Shift"],
                    [[a.id, a.route.route_name, a.crew_member.name,
                      a.vehicle.registration,
                      a.assignment_date.strftime("%Y-%m-%d"), a.shift.value]
                     for a in assignments]
                )
            else:
                print("No assignments found.")
            pause()

        elif choice == "0":
            break


def menu_mongodb(session):
    """MongoDB integration demo."""
    print_header("MONGODB – HYBRID DATA STORE")
    if not mongo.is_connected:
        print("\n  MongoDB is not running or not reachable.")
        print("  Start MongoDB with: mongod --dbpath /data/db")
        print("  The application continues to work fully via SQLite.")
        pause()
        return

    while True:
        print_header("MONGODB INTEGRATION")
        print("  1. View incidents stored in MongoDB")
        print("  2. View recent audit events in MongoDB")
        print("  3. MongoDB connection status")
        print("  0. Back")
        choice = input("\nSelect: ").strip()

        if choice == "1":
            docs = mongo.get_all_incidents()
            if docs:
                for d in docs:
                    print(f"  [{d.get('severity','?')}] {d.get('type','?')} – {d.get('description','')[:60]}")
            else:
                print("  No incidents stored in MongoDB yet.")
            pause()

        elif choice == "2":
            events = mongo.get_recent_audit_events()
            if events:
                for e in events:
                    print(f"  {e.get('timestamp','')} | {e}")
            else:
                print("  No audit events stored in MongoDB yet.")
            pause()

        elif choice == "3":
            print(f"\n  Connected: {mongo.is_connected}")
            pause()

        elif choice == "0":
            break


# ---------------------------------------------------------------------------
# Main menu
# ---------------------------------------------------------------------------

def main():
    init_db()
    session = get_session()

    print_header("MAIN MENU")
    print("\n  Database initialised.")
    if mongo.is_connected:
        print("  MongoDB connected.")
    else:
        print("  MongoDB offline – running in SQLite-only mode.")

    while True:
        print_header("MAIN MENU")
        print("  1. Customer Management")
        print("  2. Collection Schedules")
        print("  3. Incidents & Service Requests")
        print("  4. Recycling Outcomes")
        print("  5. Analytics & Charts")
        print("  6. Crew & Vehicles")
        print("  7. MongoDB Integration")
        print("  0. Exit")
        choice = input("\nSelect: ").strip()

        if   choice == "1": menu_customers(session)
        elif choice == "2": menu_schedules(session)
        elif choice == "3": menu_incidents(session)
        elif choice == "4": menu_recycling(session)
        elif choice == "5": menu_reports(session)
        elif choice == "6": menu_crew(session)
        elif choice == "7": menu_mongodb(session)
        elif choice == "0":
            print("\n  Goodbye.\n")
            session.close()
            mongo.close()
            break
        else:
            print("  Invalid choice.")


if __name__ == "__main__":
    main()
