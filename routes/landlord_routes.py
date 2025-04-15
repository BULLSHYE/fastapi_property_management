from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from typing import List
from utlis import hash_password, verify_password
from database import get_db
import models, schemas

router = APIRouter(
    prefix="/landlords",
    tags=["landlords"],
)

@router.post("/", response_model=schemas.Landlord, status_code=status.HTTP_201_CREATED)
def create_landlord(landlord: schemas.LandlordCreate, db: Session = Depends(get_db)):
    hashed_pw = hash_password(landlord.password)
    db_landlord = models.Landlord(
        username=landlord.username,
        email=landlord.email,
        mobile_number=landlord.mobile_number,
        is_subscription=landlord.is_subscription,
        password=hashed_pw,
        is_active=landlord.is_active
    )
    db.add(db_landlord)
    db.commit()
    db.refresh(db_landlord)
    return db_landlord

@router.post("/login")
def login_landlord(credentials: schemas.LandlordLogin, db: Session = Depends(get_db)):
    db_landlord = db.query(models.Landlord).filter(
        (models.Landlord.username == credentials.username_or_email) |
        (models.Landlord.email == credentials.username_or_email)
    ).first()

    if not db_landlord or not verify_password(credentials.password, db_landlord.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {
        "message": "Login successful",
        "landlord_id": db_landlord.user_id,
        "username": db_landlord.username,
        "email": db_landlord.email
    }

@router.get("/", response_model=List[schemas.Landlord])
def read_landlords(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    landlords = db.query(models.Landlord).offset(skip).limit(limit).all()
    return landlords

@router.get("/{landlord_id}", response_model=schemas.Landlord)
def read_landlord(landlord_id: int, db: Session = Depends(get_db)):
    db_landlord = db.query(models.Landlord).filter(models.Landlord.user_id == landlord_id).first()
    if db_landlord is None:
        raise HTTPException(status_code=404, detail="Landlord not found")
    return db_landlord

@router.put("/{landlord_id}", response_model=schemas.Landlord)
def update_landlord(landlord_id: int, landlord: schemas.LandlordUpdate, db: Session = Depends(get_db)):
    db_landlord = db.query(models.Landlord).filter(models.Landlord.user_id == landlord_id).first()
    if db_landlord is None:
        raise HTTPException(status_code=404, detail="Landlord not found")
    
    update_data = landlord.dict(exclude_unset=True)
    if "password" in update_data:
        update_data["password"] = hash_password(update_data["password"])
        
    for key, value in update_data.items():
        setattr(db_landlord, key, value)
    
    db.commit()
    db.refresh(db_landlord)
    return db_landlord

@router.delete("/{landlord_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_landlord(landlord_id: int, db: Session = Depends(get_db)):
    db_landlord = db.query(models.Landlord).filter(models.Landlord.user_id == landlord_id).first()
    if db_landlord is None:
        raise HTTPException(status_code=404, detail="Landlord not found")
    
    db.delete(db_landlord)
    db.commit()
    return None