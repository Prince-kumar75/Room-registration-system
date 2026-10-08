from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import date, datetime

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


class RoomBase(BaseModel):
    room_number: str
    room_type: str
    price_per_night: float
    capacity: int
    description: Optional[str] = None
    amenities: Optional[str] = None
    image_url: Optional[str] = None
    is_available: bool = True

class RoomResponse(RoomBase):
    id: int

    class Config:
        from_attributes = True


class BookingCreate(BaseModel):
    room_id: int
    check_in_date: date
    check_out_date: date

class BookingResponse(BaseModel):
    id: int
    user_id: int
    room_id: int
    check_in_date: date
    check_out_date: date
    total_price: float
    status: str
    created_at: datetime
    room: RoomResponse

    class Config:
        from_attributes = True
