from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models import Therapist, Room
from ..schemas import TherapistCreate, TherapistOut

router = APIRouter()


@router.get("/", response_model=List[TherapistOut])
def list_therapists(db: Session = Depends(get_db)):
    return db.query(Therapist).all()


@router.post("/", response_model=TherapistOut)
def create_therapist(data: TherapistCreate, db: Session = Depends(get_db)):
    if not db.query(Room).filter(Room.name == data.room_name).first():
        raise HTTPException(status_code=400, detail=f"치료실 '{data.room_name}'이 존재하지 않습니다")
    t = Therapist(**data.model_dump())
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


@router.put("/{therapist_id}", response_model=TherapistOut)
def update_therapist(therapist_id: int, data: TherapistCreate, db: Session = Depends(get_db)):
    t = db.query(Therapist).filter(Therapist.id == therapist_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="치료사를 찾을 수 없습니다")
    for k, v in data.model_dump().items():
        setattr(t, k, v)
    db.commit()
    db.refresh(t)
    return t


@router.delete("/{therapist_id}")
def delete_therapist(therapist_id: int, db: Session = Depends(get_db)):
    t = db.query(Therapist).filter(Therapist.id == therapist_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="치료사를 찾을 수 없습니다")
    db.delete(t)
    db.commit()
    return {"ok": True}
