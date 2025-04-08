from pydantic import BaseModel, EmailStr, Field
from datetime import datetime, date
from typing import List, Optional, Union

# Landlord Schemas
class LandlordBase(BaseModel):
    username: str
    email: EmailStr
    mobile_number: str
    is_subscription: bool = False
    is_active: bool = True

class LandlordCreate(LandlordBase):
    pass

class LandlordUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    mobile_number: Optional[str] = None
    is_subscription: Optional[bool] = None
    is_active: Optional[bool] = None

class Landlord(LandlordBase):
    user_id: int
    created_at: datetime
    modified_at: datetime

    class Config:
        orm_mode = True

# Property Schemas
class PropertyBase(BaseModel):
    address: str
    property_name: str
    is_active: bool = True

class PropertyCreate(PropertyBase):
    landlord_id: int

class PropertyUpdate(BaseModel):
    address: Optional[str] = None
    property_name: Optional[str] = None
    is_active: Optional[bool] = None

class Property(PropertyBase):
    id: int
    landlord_id: int
    created_at: datetime

    class Config:
        orm_mode = True

# Room Schemas
class RoomBase(BaseModel):
    room_number: str
    is_occupied: bool = False

class RoomCreate(RoomBase):
    property_id: int

class RoomUpdate(BaseModel):
    room_number: Optional[str] = None
    is_occupied: Optional[bool] = None

# class Room(RoomBase):
#     id: int
#     property_id: int
#     tenants: list[Tenant] = []  # Add tenants to the room schema for display
    
#     class Config:
#         orm_mode = True

# Tenant Schemas
class TenantBase(BaseModel):
    name: str
    email: EmailStr
    mobile_number: str
    total_person: int = 1
    aadhar_photo: Optional[str] = None
    other_images: Optional[str] = None
    move_in_date: date
    property_id: int
    is_active: bool = True

class TenantCreate(TenantBase):
    assigned_room_id: int

class TenantUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    mobile_number: Optional[str] = None
    total_person: Optional[int] = None
    aadhar_photo: Optional[str] = None
    other_images: Optional[str] = None
    move_in_date: Optional[date] = None
    is_active: Optional[bool] = None

class Tenant(TenantBase):
    id: int
    assigned_room_id: int

    class Config:
        orm_mode = True

#Room schmeas
class Room(RoomBase):
    id: int
    property_id: int
    tenants: list[Tenant] = []  # Add tenants to the room schema for display
    
    class Config:
        orm_mode = True

# Payment Schemas
class PaymentBase(BaseModel):
    month: int
    year: int
    payment: float
    payment_due: Optional[float] = None
    is_paid: bool = True
    payment_date: Optional[date] = None

class PaymentCreate(PaymentBase):
    tenant_id: int
    room_id: int

class PaymentUpdate(BaseModel):
    payment: Optional[float] = None
    payment_due: Optional[float] = None
    is_paid: Optional[bool] = None
    payment_date: Optional[date] = None

class Payment(PaymentBase):
    id: int
    tenant_id: int
    room_id: int

    class Config:
        orm_mode = True

# Electricity Schemas
class ElectricityBase(BaseModel):
    # reading_date: date
    last_reading: float
    current_reading: float
    rate: float = 10.1

class ElectricityCreate(ElectricityBase):
    # room_id: int
    room_number: str
    property_id: int

class ElectricityUpdate(BaseModel):
    reading_date: Optional[date] = None
    last_reading: Optional[float] = None
    current_reading: Optional[float] = None
    rate: Optional[float] = None

class BulkElectricityCreate(BaseModel):
    entries: Union[ElectricityCreate, List[ElectricityCreate]]

class Electricity(ElectricityBase):
    id: int
    room_id: int
    consumption: Optional[float]
    total_amount: Optional[float]

    class Config:
        orm_mode = True