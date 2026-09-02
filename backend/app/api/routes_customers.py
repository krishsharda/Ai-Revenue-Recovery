from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.customer import Customer
from ..schemas.recovery import CustomerOut

router = APIRouter(tags=["customers"])


@router.get("/customers", response_model=list[CustomerOut])
def list_customers(
    db: Session = Depends(get_db),
    limit: int = Query(100, ge=1, le=500),
) -> list[Customer]:
    return db.execute(
        select(Customer).order_by(Customer.id).limit(limit)
    ).scalars().all()


@router.get("/customers/{customer_id}", response_model=CustomerOut)
def get_customer(customer_id: int, db: Session = Depends(get_db)) -> Customer:
    cust = db.get(Customer, customer_id)
    if cust is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return cust
