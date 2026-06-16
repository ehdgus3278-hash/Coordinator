from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models import Room
from ..schemas import RoomCreate, RoomOut

router = APIRouter()


@router.get("/", response_model=List[RoomOut])
def list_rooms(db: Session = Depends(get_db)):
    return db.query(Room).all()


@router.post("/", response_model=RoomOut)
def create_room(data: RoomCreate, db: Session = Depends(get_db)):
    if db.query(Room).filter(Room.name == data.name).first():
        raise HTTPException(status_code=400, detail="이미 존재하는 치료실입니다")
    room = Room(**data.model_dump())
    db.add(room)
    db.commit()
    db.refresh(room)
    return room


@router.put("/{name}", response_model=RoomOut)
def update_room(name: str, data: RoomCreate, db: Session = Depends(get_db)):
    room = db.query(Room).filter(Room.name == name).first()
    if not room:
        raise HTTPException(status_code=404, detail="치료실을 찾을 수 없습니다")
    room.beds = data.beds
    room.stations = [s.model_dump() for s in data.stations] if data.stations else None
    db.commit()
    db.refresh(room)
    return room
