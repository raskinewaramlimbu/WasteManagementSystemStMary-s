"""Data Access Layer: Customer and Address CRUD operations."""
import hashlib
import os
from sqlalchemy.orm import Session
from database.models import Customer, Address, AccountType, PropertyType


def _hash_password(password: str) -> str:
    salt = "ws_static_salt"  # deterministic for demo; production uses os.urandom
    return hashlib.sha256((salt + password).encode()).hexdigest()


# ---------------------------------------------------------------------------
# Customer CRUD
# ---------------------------------------------------------------------------

def create_customer(session: Session, account_number: str, name: str, email: str,
                    phone: str, account_type: str = "residential",
                    password: str = "Password1!") -> Customer:
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
    session.refresh(customer)
    return customer


def get_customer_by_id(session: Session, customer_id: int) -> Customer | None:
    return session.get(Customer, customer_id)


def get_customer_by_email(session: Session, email: str) -> Customer | None:
    return session.query(Customer).filter(Customer.email == email).first()


def get_customer_by_account(session: Session, account_number: str) -> Customer | None:
    return session.query(Customer).filter(
        Customer.account_number == account_number
    ).first()


def get_all_customers(session: Session) -> list[Customer]:
    return session.query(Customer).filter(Customer.is_active == True).all()


def update_customer(session: Session, customer_id: int, **kwargs) -> Customer | None:
    customer = session.get(Customer, customer_id)
    if not customer:
        return None
    for key, value in kwargs.items():
        if hasattr(customer, key):
            setattr(customer, key, value)
    session.commit()
    session.refresh(customer)
    return customer


def deactivate_customer(session: Session, customer_id: int) -> bool:
    customer = session.get(Customer, customer_id)
    if not customer:
        return False
    customer.is_active = False
    session.commit()
    return True


def search_customers(session: Session, query: str) -> list[Customer]:
    like = f"%{query}%"
    return session.query(Customer).filter(
        (Customer.name.ilike(like)) | (Customer.email.ilike(like))
    ).all()


# ---------------------------------------------------------------------------
# Address CRUD
# ---------------------------------------------------------------------------

def add_address(session: Session, customer_id: int, street_number: str,
                street_name: str, city: str, postcode: str,
                property_type: str = "house", is_primary: bool = True) -> Address:
    if is_primary:
        session.query(Address).filter(
            Address.customer_id == customer_id, Address.is_primary == True
        ).update({"is_primary": False})
    address = Address(
        customer_id=customer_id,
        street_number=street_number,
        street_name=street_name,
        city=city,
        postcode=postcode,
        property_type=PropertyType[property_type],
        is_primary=is_primary,
    )
    session.add(address)
    session.commit()
    session.refresh(address)
    return address


def get_addresses_for_customer(session: Session, customer_id: int) -> list[Address]:
    return session.query(Address).filter(Address.customer_id == customer_id).all()
