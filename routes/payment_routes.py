from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from sqlalchemy.exc import IntegrityError
from collections import defaultdict
from sqlalchemy import extract
from database import get_db
import models, schemas

router = APIRouter(
    prefix="/payments",
    tags=["payments"],
)

@router.post("/", response_model=schemas.Payment, status_code=status.HTTP_201_CREATED)
def create_payment(payment: schemas.PaymentCreate, db: Session = Depends(get_db)):
    # Check if tenant exists
    tenant = db.query(models.Tenant).filter(models.Tenant.id == payment.tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Check if room exists
    room = db.query(models.Room).filter(models.Room.id == payment.room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    # Validate that tenant is assigned to this room
    if tenant.assigned_room_id != payment.room_id:
        raise HTTPException(status_code=400, detail="Tenant is not assigned to this room")
    
    db_payment = models.Payment(
        tenant_id=payment.tenant_id,
        room_id=payment.room_id,
        month=payment.month,
        year=payment.year,
        payment=payment.payment,
        payment_due=payment.payment_due,
        is_paid=payment.is_paid,
        property_id=payment.property_id,
        payment_date=payment.payment_date
    )
    
    try:
        db.add(db_payment)
        db.commit()
        db.refresh(db_payment)
        return db_payment
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400, 
            detail="Payment for this tenant, room, month, and year already exists"
        )

@router.get("/", response_model=List[schemas.Payment])
def read_payments(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    payments = db.query(models.Payment).offset(skip).limit(limit).all()
    return payments

@router.get("/{payment_id}", response_model=schemas.Payment)
def read_payment(payment_id: int, db: Session = Depends(get_db)):
    db_payment = db.query(models.Payment).filter(models.Payment.id == payment_id).first()
    if db_payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    return db_payment

@router.get("/property/{property_id}", response_model=List[schemas.Payment])
def read_payment(property_id: int, db: Session = Depends(get_db)):
    db_payment = db.query(models.Payment).filter(models.Payment.property_id == property_id).all()
    if db_payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    readings = db.query(models.Payment).filter(models.Payment.property_id == property_id).all()
    return readings

@router.get("/tenant/{tenant_id}", response_model=List[schemas.Payment])
def read_tenant_payments(tenant_id: int, db: Session = Depends(get_db)):
    # Check if tenant exists
    tenant = db.query(models.Tenant).filter(models.Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    payments = db.query(models.Payment).filter(models.Payment.tenant_id == tenant_id).all()
    return payments

@router.get("/room/{room_id}", response_model=List[schemas.Payment])
def read_room_payments(room_id: int, db: Session = Depends(get_db)):
    # Check if room exists
    room = db.query(models.Room).filter(models.Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    payments = db.query(models.Payment).filter(models.Payment.room_id == room_id).all()
    return payments

@router.put("/{payment_id}", response_model=schemas.Payment)
def update_payment(payment_id: int, payment: schemas.PaymentUpdate, db: Session = Depends(get_db)):
    db_payment = db.query(models.Payment).filter(models.Payment.id == payment_id).first()
    if db_payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    update_data = payment.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_payment, key, value)
    
    db.commit()
    db.refresh(db_payment)
    return db_payment

@router.delete("/{payment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_payment(payment_id: int, db: Session = Depends(get_db)):
    db_payment = db.query(models.Payment).filter(models.Payment.id == payment_id).first()
    if db_payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    db.delete(db_payment)
    db.commit()
    return None

@router.get("/{property_id}/{month}")
def property_monthly_details(property_id: int, month: int, db: Session = Depends(get_db)):
    # Fetch all rooms under the given property
    rooms = db.query(models.Room).filter(models.Room.property_id == property_id).all()
    if not rooms:
        raise HTTPException(status_code=404, detail="No rooms found for this property.")

    room_ids = [room.id for room in rooms]

    # Fetch meter readings for the specified month
    meter_readings = (
        db.query(models.Electricity)
        .filter(models.Electricity.room_id.in_(room_ids), extract('month', models.Electricity.reading_date) == month)
        .all()
    )

    # Fetch payments for the specified month
    payments = (
        db.query(models.Payment)
        .filter(models.Payment.room_id.in_(room_ids), models.Payment.month == month)
        .all()
    )

    # Organize data by room
    rooms_info = defaultdict(lambda: {"meter_readings": [], "payments": []})

    for reading in meter_readings:
        rooms_info[reading.room_id]["meter_readings"].append(schemas.Electricity.from_orm(reading))

    for payment in payments:
        rooms_info[payment.room_id]["payments"].append(schemas.Payment.from_orm(payment))

    # Structure response as a list
    room_details = []
    for room in rooms:
        room_data = {
            "room_number": room.room_number,
            "is_occupied": room.is_occupied,
            "meter_readings": rooms_info[room.id]["meter_readings"],
            "payments": rooms_info[room.id]["payments"],
        }
        room_details.append(room_data)

    return {
        "property_id": property_id,
        "month": month,
        "rooms": room_details  # ✅ List instead of dynamic key object
    }