from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import extract
from sqlalchemy.orm import Session
from typing import List
from collections import defaultdict
from database import get_db
import models, schemas

router = APIRouter(
    prefix="/properties",
    tags=["properties"],
)

@router.post("/", response_model=schemas.Property, status_code=status.HTTP_201_CREATED)
def create_property(property_data: schemas.PropertyCreate, db: Session = Depends(get_db)):
    # Check if landlord exists
    landlord = db.query(models.Landlord).filter(models.Landlord.user_id == property_data.landlord_id).first()
    if not landlord:
        raise HTTPException(status_code=404, detail="Landlord not found")
    
    db_property = models.Property(
        landlord_id=property_data.landlord_id,
        address=property_data.address,
        property_name=property_data.property_name,
        landmark=property_data.landmark,
        city=property_data.city,
        state=property_data.state,
        is_active=property_data.is_active
    )
    db.add(db_property)
    db.commit()
    db.refresh(db_property)
    return db_property

@router.get("/", response_model=List[schemas.Property])
def read_properties(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    properties = db.query(models.Property).offset(skip).limit(limit).all()
    return properties

@router.get("/{property_id}", response_model=schemas.Property)
def read_property(property_id: int, db: Session = Depends(get_db)):
    db_property = db.query(models.Property).filter(models.Property.id == property_id).first()
    if db_property is None:
        raise HTTPException(status_code=404, detail="Property not found")
    return db_property

@router.get("/landlord/{landlord_id}", response_model=List[schemas.Property])
def read_landlord_properties(landlord_id: int, db: Session = Depends(get_db)):
    # Check if landlord exists
    landlord = db.query(models.Landlord).filter(models.Landlord.user_id == landlord_id).first()
    if not landlord:
        raise HTTPException(status_code=404, detail="Landlord not found")
    
    properties = db.query(models.Property).filter(models.Property.landlord_id == landlord_id).all()
    return properties

@router.put("/{property_id}", response_model=schemas.Property)
def update_property(property_id: int, property_data: schemas.PropertyUpdate, db: Session = Depends(get_db)):
    db_property = db.query(models.Property).filter(models.Property.id == property_id).first()
    if db_property is None:
        raise HTTPException(status_code=404, detail="Property not found")
    
    update_data = property_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_property, key, value)
    
    db.commit()
    db.refresh(db_property)
    return db_property

@router.delete("/{property_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_property(property_id: int, db: Session = Depends(get_db)):
    db_property = db.query(models.Property).filter(models.Property.id == property_id).first()
    if db_property is None:
        raise HTTPException(status_code=404, detail="Property not found")
    
    db.delete(db_property)
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