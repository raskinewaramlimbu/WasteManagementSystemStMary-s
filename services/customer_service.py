"""Business Layer: customer account management and validation."""
import re
from sqlalchemy.orm import Session

from database.models import Customer
from repositories import customer_repo
from repositories.incident_repo import write_audit_log


def _validate_email(email: str) -> bool:
    return bool(re.fullmatch(r"[^@]+@[^@]+\.[^@]+", email))


def _validate_phone(phone: str) -> bool:
    return bool(re.fullmatch(r"[\d\s\-\+\(\)]{7,20}", phone))


def register_customer(session: Session, account_number: str, name: str,
                      email: str, phone: str, account_type: str,
                      street_number: str, street_name: str, city: str,
                      postcode: str, property_type: str = "house",
                      password: str = "Password1!") -> tuple[Customer | None, str]:
    """Create a customer and their primary address; returns (customer, error_msg)."""
    if not name.strip():
        return None, "Name cannot be blank."
    if not _validate_email(email):
        return None, "Invalid e-mail address."
    if phone and not _validate_phone(phone):
        return None, "Invalid phone number."
    if customer_repo.get_customer_by_email(session, email):
        return None, "An account with that e-mail already exists."
    if customer_repo.get_customer_by_account(session, account_number):
        return None, "Account number already in use."
    if account_type not in ("residential", "commercial", "school"):
        return None, "Invalid account type."

    customer = customer_repo.create_customer(
        session, account_number, name, email, phone, account_type, password
    )
    customer_repo.add_address(
        session, customer.id, street_number, street_name, city,
        postcode, property_type, is_primary=True,
    )
    write_audit_log(session, "customers", customer.id, "CREATE", "system",
                    f"New customer: {name}")
    return customer, ""


def update_contact_details(session: Session, customer_id: int,
                            email: str | None = None,
                            phone: str | None = None) -> tuple[Customer | None, str]:
    if email and not _validate_email(email):
        return None, "Invalid e-mail address."
    if phone and not _validate_phone(phone):
        return None, "Invalid phone number."
    updates = {}
    if email:
        updates["email"] = email
    if phone:
        updates["phone"] = phone
    if not updates:
        return None, "No fields to update."
    customer = customer_repo.update_customer(session, customer_id, **updates)
    if customer:
        write_audit_log(session, "customers", customer_id, "UPDATE", "system",
                        f"Updated fields: {list(updates.keys())}")
    return customer, ""


def close_account(session: Session, customer_id: int) -> bool:
    result = customer_repo.deactivate_customer(session, customer_id)
    if result:
        write_audit_log(session, "customers", customer_id, "DELETE", "system",
                        "Account deactivated")
    return result


def get_customer_summary(session: Session, customer_id: int) -> dict:
    """Return a dict suitable for display on the presentation layer."""
    customer = customer_repo.get_customer_by_id(session, customer_id)
    if not customer:
        return {}
    addresses = customer_repo.get_addresses_for_customer(session, customer_id)
    return {
        "id": customer.id,
        "account_number": customer.account_number,
        "name": customer.name,
        "email": customer.email,
        "phone": customer.phone,
        "type": customer.account_type.value,
        "active": customer.is_active,
        "addresses": [
            f"{a.street_number} {a.street_name}, {a.city} {a.postcode}"
            for a in addresses
        ],
    }
