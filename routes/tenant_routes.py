from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import shutil
import uuid
from database import get_db
import models, schemas
from pydantic import EmailStr
from datetime import date

UPLOAD_DIR = "static/tenants"

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
    
    # Save uploaded files
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    def save_file(upload_file: UploadFile):
        extension = os.path.splitext(upload_file.filename)[1]
        unique_name = f"{uuid.uuid4()}{extension}"
        file_path = os.path.join(UPLOAD_DIR, unique_name)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
        return file_path

    # Handle optional file saving (only if it's a file and not None)
    aadhar_path = save_file(tenant.aadhar_photo) if isinstance(tenant.aadhar_photo, UploadFile) else None
    other_images_path = save_file(tenant.other_images) if isinstance(tenant.other_images, UploadFile) else None

    db_tenant = models.Tenant(
        name=tenant.name,
        email=tenant.email,
        mobile_number=tenant.mobile_number,
        total_person=tenant.total_person,
        aadhar_photo=aadhar_path,
        # aadhar_photo=tenant.aadhar_photo,
        other_images=other_images_path,
        # other_images=tenant.other_images,
        assigned_room_id=tenant.assigned_room_id,
        move_in_date=tenant.move_in_date,
        property_id=tenant.property_id,
        is_active=tenant.is_active
    )
    
    # Update room occupancy status
    room.is_occupied = True
    
    db.add(db_tenant)
    db.commit()
    db.refresh(db_tenant)
    return db_tenant

@router.post("/test", response_model=schemas.Tenant, status_code=status.HTTP_201_CREATED)
def create_tenant(
    name: str = Form(...),
    email: EmailStr = Form(...),
    mobile_number: str = Form(...),
    total_person: int = Form(...),
    move_in_date: date = Form(...),
    property_id: int = Form(...),
    is_active: bool = Form(...),
    assigned_room_id: int = Form(...),
    aadhar_photo: UploadFile = File(...),
    other_images: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # Room check
    room = db.query(models.Room).filter(models.Room.id == assigned_room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    if room.is_occupied:
        raise HTTPException(status_code=400, detail="Room is already occupied")

    # Save files
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    def save_file(upload_file: UploadFile):
        ext = os.path.splitext(upload_file.filename)[1]
        unique_name = f"{uuid.uuid4()}{ext}"
        path = os.path.join(UPLOAD_DIR, unique_name)
        with open(path, "wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
        return path

    aadhar_path = save_file(aadhar_photo)
    other_path = save_file(other_images)

    # Save to DB
    db_tenant = models.Tenant(
        name=name,
        email=email,
        mobile_number=mobile_number,
        total_person=total_person,
        aadhar_photo=aadhar_path,
        other_images=other_path,
        assigned_room_id=assigned_room_id,
        move_in_date=move_in_date,
        property_id=property_id,
        is_active=is_active,
    )

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

@router.get("/property/{property_id}", status_code=status.HTTP_200_OK)
def read_property_tenants(
    property_id: int,
    is_active: Optional[bool] = Query(True, description="Filter tenants by active status. Default is True."),
    db: Session = Depends(get_db)
):
    # Fetch the property
    db_property = db.query(models.Property).filter(models.Property.id == property_id).first()

    if not db_property:
        raise HTTPException(status_code=404, detail="Property not found")

    property_data = {
        "property_name": db_property.property_name,
        "address": db_property.address,
        "rooms": []
    }

    # Prepare list to track rooms with tenants
    rooms_with_tenants = []

    for room in db_property.rooms:
        # Fetch tenants based on filters
        tenants_query = db.query(models.Tenant).filter(
            models.Tenant.assigned_room_id == room.id,
            models.Tenant.property_id == property_id
        )

        if is_active is not None:
            tenants_query = tenants_query.filter(models.Tenant.is_active == is_active)

        tenants = tenants_query.all()

        # Only include room if it has at least one tenant
        if tenants:
            tenant = tenants[0]
            room_data = {
                "room_number": room.room_number,
                "is_occupied": room.is_occupied,
                "tenants": {
                    "tenant_name": tenant.name,
                    "tenant_email": tenant.email,
                    "tenant_mobile": tenant.mobile_number,
                    "move_in_date": tenant.move_in_date,
                    "total_person": tenant.total_person,
                    "aadhar_photo": tenant.aadhar_photo,
                    "other_images": tenant.other_images,
                }
            }
            rooms_with_tenants.append(room_data)

    # If no rooms had tenants, return rooms as null
    if not rooms_with_tenants:
        property_data["rooms"] = None
    else:
        property_data["rooms"] = rooms_with_tenants

    return property_data

# @router.get("/property/{property_id}", status_code=status.HTTP_200_OK)
# def read_property_tenants(
#     property_id: int,
#     is_active: Optional[bool] = Query(True, description="Filter tenants by active status. Default is True."),
#     db: Session = Depends(get_db)
# ):
#     # Fetch the property along with its associated rooms and tenants
#     db_property = db.query(models.Property).filter(models.Property.id == property_id).first()
    
#     if not db_property:
#         raise HTTPException(status_code=404, detail="Property not found")

#     # Prepare the response structure
#     property_data = {
#         "property_name": db_property.property_name,
#         "address": db_property.address,
#         "rooms": []
#     }

#     # Loop through all the rooms in the property
#     for room in db_property.rooms:
#         room_data = {
#             "room_number": room.room_number,
#             "is_occupied": room.is_occupied,
#             "tenants": None  # Default to None
#         }

#         # Fetch tenants based on active status filter
#         tenants_query = db.query(models.Tenant).filter(
#             models.Tenant.assigned_room_id == room.id,
#             models.Tenant.property_id == property_id
#         )

#         # Apply active status filter if provided
#         if is_active is not None:
#             tenants_query = tenants_query.filter(models.Tenant.is_active == is_active)

#         tenants = tenants_query.all()

#         # Add first tenant’s detail if any exist
#         if tenants:
#             tenant = tenants[0]
#             room_data["tenants"] = {
#                 "tenant_name": tenant.name,
#                 "tenant_email": tenant.email,
#                 "tenant_mobile": tenant.mobile_number,
#                 "move_in_date": tenant.move_in_date,
#                 "total_person": tenant.total_person,
#                 "aadhar_photo": tenant.aadhar_photo,
#                 "other_images": tenant.other_images,
#             }

#         # Add the room data to property data
#         property_data["rooms"].append(room_data)

#     return property_data


# @router.get("/property/{property_id}", status_code=status.HTTP_200_OK)
# def read_property_tenants(
#     property_id: int,
#     is_active: Optional[bool] = Query(True, description="Filter tenants by active status. Default is True."),
#     db: Session = Depends(get_db)
# ):
#     # Fetch the property along with its associated rooms and tenants
#     db_property = db.query(models.Property).filter(models.Property.id == property_id).first()
    
#     if not db_property:
#         raise HTTPException(status_code=404, detail="Property not found")

#     property_data = {
#         "property_name": db_property.property_name,
#         "address": db_property.address,
#         "rooms": []
#     }

#     for room in db_property.rooms:
#         # Filter tenants for the room
#         tenants_query = db.query(models.Tenant).filter(
#             models.Tenant.assigned_room_id == room.id,
#             models.Tenant.property_id == property_id
#         )

#         if is_active is not None:
#             tenants_query = tenants_query.filter(models.Tenant.is_active == is_active)

#         tenants = tenants_query.all()

#         # ⚠️ Skip the room if no matching tenants and active filter is on
#         if is_active is not None and not tenants:
#             continue

#         room_data = {
#             "room_number": room.room_number,
#             "is_occupied": room.is_occupied,
#             "tenants": None
#         }

#         if tenants:
#             tenant = tenants[0]
#             room_data["tenants"] = {
#                 "tenant_name": tenant.name,
#                 "tenant_email": tenant.email,
#                 "tenant_mobile": tenant.mobile_number,
#                 "move_in_date": tenant.move_in_date,
#                 "total_person": tenant.total_person,
#                 "aadhar_photo": tenant.aadhar_photo,
#                 "other_images": tenant.other_images,
#             }

#         property_data["rooms"].append(room_data)

#     return property_data