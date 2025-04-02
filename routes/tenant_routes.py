from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database import get_db
import models, schemas

router = APIRouter(
    prefix="/tenants",
    tags=["tenants"],
)

@router.post("/", response_model=schemas.Tenant, status_code=status.HTTP_201_CREATED)
def create_tenant(tenant: schemas.TenantCreate, db: Session = Depends(get_db)):
    # Check if room exists
    room = db.query(models.Room).filter(models.Room.id == tenant.assigned_room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    # Check if room is already occupied
    if room.is_occupied:
        raise HTTPException(status_code=400, detail="Room is already occupied")
    
    db_tenant = models.Tenant(
        name=tenant.name,
        email=tenant.email,
        mobile_number=tenant.mobile_number,
        total_person=tenant.total_person,
        aadhar_photo=tenant.aadhar_photo,
        other_images=tenant.other_images,
        assigned_room_id=tenant.assigned_room_id,
        move_in_date=tenant.move_in_date,
        is_active=tenant.is_active
    )
    
    # Update room occupancy status
    room.is_occupied = True
    
    db.add(db_tenant)
    db.commit()
    db.refresh(db_tenant)
    return db_tenant

@router.get("/", response_model=List[schemas.Tenant])
def read_tenants(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    tenants = db.query(models.Tenant).offset(skip).limit(limit).all()
    return tenants

@router.get("/{tenant_id}", response_model=schemas.Tenant)
def read_tenant(tenant_id: int, db: Session = Depends(get_db)):
    db_tenant = db.query(models.Tenant).filter(models.Tenant.id == tenant_id).first()
    if db_tenant is None:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return db_tenant

@router.get("/room/{room_id}", response_model=schemas.Tenant)
def read_room_tenant(room_id: int, db: Session = Depends(get_db)):
    db_tenant = db.query(models.Tenant).filter(models.Tenant.assigned_room_id == room_id).first()
    if db_tenant is None:
        raise HTTPException(status_code=404, detail="No tenant found for this room")
    return db_tenant

@router.put("/{tenant_id}", response_model=schemas.Tenant)
def update_tenant(tenant_id: int, tenant: schemas.TenantUpdate, db: Session = Depends(get_db)):
    db_tenant = db.query(models.Tenant).filter(models.Tenant.id == tenant_id).first()
    if db_tenant is None:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    update_data = tenant.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_tenant, key, value)
    
    # Handle room occupancy based on tenant active status
    if 'is_active' in update_data:
        room = db.query(models.Room).filter(models.Room.id == db_tenant.assigned_room_id).first()
        room.is_occupied = update_data['is_active']
    
    db.commit()
    db.refresh(db_tenant)
    return db_tenant

@router.delete("/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tenant(tenant_id: int, db: Session = Depends(get_db)):
    db_tenant = db.query(models.Tenant).filter(models.Tenant.id == tenant_id).first()
    if db_tenant is None:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Update room to unoccupied
    room = db.query(models.Room).filter(models.Room.id == db_tenant.assigned_room_id).first()
    if room:
        room.is_occupied = False
    
    db.delete(db_tenant)
    db.commit()
    return None