from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, Float, ForeignKey, UniqueConstraint, Table, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import pytz

Base = declarative_base()

class Landlord(Base):
    __tablename__ = 'landlord'
    
    user_id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    mobile_number = Column(String(15), nullable=False)
    created_at = Column(DateTime, default=datetime.now(pytz.UTC))
    modified_at = Column(DateTime, default=datetime.now(pytz.UTC), onupdate=datetime.now(pytz.UTC))
    is_subscription = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    properties = relationship("Property", back_populates="landlord", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Landlord {self.username}>"

class Property(Base):
    __tablename__ = 'property'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    landlord_id = Column(Integer, ForeignKey('landlord.user_id', ondelete='CASCADE'), nullable=False)
    address = Column(String(255), nullable=False)
    property_name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.now(pytz.UTC))
    is_active = Column(Boolean, default=True)
    
    # Relationships
    landlord = relationship("Landlord", back_populates="properties")
    rooms = relationship("Room", back_populates="property", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Property {self.property_name}>"

class Room(Base):
    __tablename__ = 'room'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    property_id = Column(Integer, ForeignKey('property.id', ondelete='CASCADE'), nullable=False)
    room_number = Column(String(10), nullable=False)
    is_occupied = Column(Boolean, default=False)
    
    # Relationships
    property = relationship("Property", back_populates="rooms")
    tenant = relationship("Tenant", back_populates="assigned_room", uselist=False, cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="room", cascade="all, delete-orphan")
    electricity_readings = relationship("Electricity", back_populates="room", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Room {self.room_number}>"

class Tenant(Base):
    __tablename__ = 'tenant'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    mobile_number = Column(String(15), nullable=False)
    total_person = Column(Integer, default=1)
    aadhar_photo = Column(String, nullable=False)
    other_images = Column(String, nullable=False)
    assigned_room_id = Column(Integer, ForeignKey('room.id', ondelete='CASCADE'), nullable=False, unique=True)
    move_in_date = Column(Date, nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    assigned_room = relationship("Room", back_populates="tenant")
    payments = relationship("Payment", back_populates="tenant", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Tenant {self.name}>"

class Payment(Base):
    __tablename__ = 'payment'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(Integer, ForeignKey('tenant.id', ondelete='CASCADE'), nullable=False)
    room_id = Column(Integer, ForeignKey('room.id', ondelete='CASCADE'), nullable=False)
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    payment = Column(Float, nullable=False)
    payment_due = Column(Float, nullable=True)
    is_paid = Column(Boolean, default=True)
    payment_date = Column(Date, default=datetime.now(pytz.UTC).date())
    
    # Relationships
    tenant = relationship("Tenant", back_populates="payments")
    room = relationship("Room", back_populates="payments")
    
    __table_args__ = (
        UniqueConstraint('tenant_id', 'room_id', 'month', 'year', name='unique_payment_per_month'),
    )
    
    def __repr__(self):
        return f"<Payment for tenant_id={self.tenant_id}, {self.month}/{self.year}>"

class Electricity(Base):
    __tablename__ = 'electricity'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    room_id = Column(Integer, ForeignKey('room.id', ondelete='CASCADE'), nullable=False)
    reading_date = Column(Date, default=datetime.now(pytz.UTC).date())
    last_reading = Column(Float, nullable=False)
    current_reading = Column(Float, nullable=False)
    consumption = Column(Float, nullable=True)
    rate = Column(Float, default=10.1)
    total_amount = Column(Float, nullable=True)
    
    # Relationships
    room = relationship("Room", back_populates="electricity_readings")
    
    def __repr__(self):
        return f"<Electricity reading for room_id={self.room_id} on {self.reading_date}>"