from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Union
from fastapi import Body
from database import get_db
import models, schemas
from datetime import date, datetime
from collections import defaultdict
from sqlalchemy import extract

router = APIRouter(
    prefix="/electricity",
    tags=["electricity"],
)

# @router.post("/", response_model=schemas.Electricity, status_code=status.HTTP_201_CREATED)
# def create_electricity_reading(electricity: schemas.ElectricityCreate, db: Session = Depends(get_db)):
#     # Check if room exists
#     room = db.query(models.Room).filter(models.Room.id == electricity.room_id).first()
#     if not room:
#         raise HTTPException(status_code=404, detail="Room not found")
    
#     # Calculate consumption and total_amount
#     consumption = electricity.current_reading - electricity.last_reading
#     total_amount = consumption * electricity.rate
    
#     db_electricity = models.Electricity(
#         room_id=electricity.room_id,
#         reading_date=electricity.reading_date,
#         last_reading=electricity.last_reading,
#         current_reading=electricity.current_reading,
#         consumption=consumption,
#         rate=electricity.rate,
#         property_id=electricity.property_id,
#         total_amount=total_amount
#     )
    
#     db.add(db_electricity)
#     db.commit()
#     db.refresh(db_electricity)
#     return db_electricity

# @router.post("/", status_code=status.HTTP_201_CREATED)
# def create_electricity_readings(
#     data: Union[schemas.ElectricityCreate, List[schemas.ElectricityCreate]] = Body(...),
#     db: Session = Depends(get_db)
# ):
#     # Normalize single entry to list
#     if isinstance(data, dict):
#         data = [schemas.ElectricityCreate(**data)]

#     created_entries = []

#     for entry in data:
#         # 1. Lookup Room by room_number and property_id
#         room = db.query(models.Room).filter_by(
#             room_number=entry.room_number,
#             property_id=entry.property_id
#         ).first()

#         if not room:
#             raise HTTPException(
#                 status_code=404,
#                 detail=f"Room {entry.room_number} in property {entry.property_id} not found"
#             )

#         # 2. Calculate values
#         consumption = round(entry.current_reading - entry.last_reading, 2)
#         total_amount = consumption * entry.rate

#         # 3. Create Electricity entry
#         db_entry = models.Electricity(
#             room_id=room.id,  # ✅ add room_id
#             room_number=room.room_number,
#             last_reading=entry.last_reading,
#             current_reading=entry.current_reading,
#             consumption=consumption,
#             rate=entry.rate,
#             total_amount=total_amount,
#             property_id=entry.property_id
#             # ✅ no need to pass reading_date — default will handle it
#         )

#         db.add(db_entry)
#         created_entries.append(db_entry)

#     db.commit()
#     for e in created_entries:
#         db.refresh(e)

#     return created_entries if len(created_entries) > 1 else created_entries[0]

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_electricity_readings(
    data: Union[schemas.ElectricityCreate, List[schemas.ElectricityCreate]] = Body(...),
    db: Session = Depends(get_db)
):
    # Normalize single entry to list
    if isinstance(data, dict):
        data = [schemas.ElectricityCreate(**data)]

    created_entries = []

    for entry in data:
        # 1. Lookup Room by room_number and property_id
        room = db.query(models.Room).filter_by(
            room_number=entry.room_number,
            property_id=entry.property_id
        ).first()

        if not room:
            raise HTTPException(
                status_code=404,
                detail=f"Room {entry.room_number} in property {entry.property_id} not found"
            )

        # 2. Calculate values
        consumption = round(entry.current_reading - entry.last_reading, 2)
        total_amount = consumption * entry.rate

        # 3. Create Electricity entry
        db_entry = models.Electricity(
            room_id=room.id,  # ✅ add room_id
            room_number=room.room_number,
            last_reading=entry.last_reading,
            current_reading=entry.current_reading,
            consumption=consumption,
            rate=entry.rate,
            total_amount=total_amount,
            property_id=entry.property_id
            # ✅ no need to pass reading_date — default will handle it
        )

        db.add(db_entry)
        created_entries.append(db_entry)

        # 4. Create Payment entry
        tenant = room.tenant  # Room has a relationship with tenant
        if tenant:
            # Create a payment for the corresponding tenant
            payment = models.Payment(
                tenant_id=tenant.id,
                room_id=room.id,
                month=datetime.now().month,
                year=datetime.now().year,
                payment=total_amount,
                payment_due=None,  # Assuming no due for now
                is_paid=True,  # Assuming it's paid by default
                property_id=entry.property_id
            )

            db.add(payment)

    # Commit all changes to the database
    db.commit()

    # Refresh entries to get the latest values
    for e in created_entries:
        db.refresh(e)

    return created_entries if len(created_entries) > 1 else created_entries[0]

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

@router.get("/property/{property_id}", response_model=List[schemas.Electricity])
def read_room_electricity(property_id: int, db: Session = Depends(get_db)):
    # Check if room exists
    room = db.query(models.Room).filter(models.Room.property_id == property_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    readings = db.query(models.Electricity).filter(models.Electricity.property_id == property_id).all()
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