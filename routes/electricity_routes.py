from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database import get_db
import models, schemas

router = APIRouter(
    prefix="/electricity",
    tags=["electricity"],
)

@router.post("/", response_model=schemas.Electricity, status_code=status.HTTP_201_CREATED)
def create_electricity_reading(electricity: schemas.ElectricityCreate, db: Session = Depends(get_db)):
    # Check if room exists
    room = db.query(models.Room).filter(models.Room.id == electricity.room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    # Calculate consumption and total_amount
    consumption = electricity.current_reading - electricity.last_reading
    total_amount = consumption * electricity.rate
    
    db_electricity = models.Electricity(
        room_id=electricity.room_id,
        reading_date=electricity.reading_date,
        last_reading=electricity.last_reading,
        current_reading=electricity.current_reading,
        consumption=consumption,
        rate=electricity.rate,
        total_amount=total_amount
    )
    
    db.add(db_electricity)
    db.commit()
    db.refresh(db_electricity)
    return db_electricity

@router.get("/", response_model=List[schemas.Electricity])
def read_electricity_readings(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    readings = db.query(models.Electricity).offset(skip).limit(limit).all()
    return readings

@router.get("/{reading_id}", response_model=schemas.Electricity)
def read_electricity_reading(reading_id: int, db: Session = Depends(get_db)):
    db_reading = db.query(models.Electricity).filter(models.Electricity.id == reading_id).first()
    if db_reading is None:
        raise HTTPException(status_code=404, detail="Electricity reading not found")
    return db_reading

@router.get("/room/{room_id}", response_model=List[schemas.Electricity])
def read_room_electricity(room_id: int, db: Session = Depends(get_db)):
    # Check if room exists
    room = db.query(models.Room).filter(models.Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    readings = db.query(models.Electricity).filter(models.Electricity.room_id == room_id).all()
    return readings

@router.put("/{reading_id}", response_model=schemas.Electricity)
def update_electricity_reading(reading_id: int, electricity: schemas.ElectricityUpdate, db: Session = Depends(get_db)):
    db_reading = db.query(models.Electricity).filter(models.Electricity.id == reading_id).first()
    if db_reading is None:
        raise HTTPException(status_code=404, detail="Electricity reading not found")
    
    update_data = electricity.dict(exclude_unset=True)
    
    # Update fields
    for key, value in update_data.items():
        setattr(db_reading, key, value)
    
    # Recalculate consumption and total_amount if relevant fields were updated
    if any(k in update_data for k in ["last_reading", "current_reading", "rate"]):
        db_reading.consumption = db_reading.current_reading - db_reading.last_reading
        db_reading.total_amount = db_reading.consumption * db_reading.rate
    
    db.commit()
    db.refresh(db_reading)
    return db_reading

@router.delete("/{reading_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_electricity_reading(reading_id: int, db: Session = Depends(get_db)):
    db_reading = db.query(models.Electricity).filter(models.Electricity.id == reading_id).first()
    if db_reading is None:
        raise HTTPException(status_code=404, detail="Electricity reading not found")
    
    db.delete(db_reading)
    db.commit()
    return None