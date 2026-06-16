from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models import PrescriptionCode, Room
from ..schemas import PrescriptionCodeCreate, PrescriptionCodeOut

router = APIRouter()


@router.get("/", response_model=List[PrescriptionCodeOut])
def list_prescriptions(db: Session = Depends(get_db)):
    return db.query(PrescriptionCode).all()


@router.post("/", response_model=PrescriptionCodeOut)
def create_prescription(data: PrescriptionCodeCreate, db: Session = Depends(get_db)):
    if not db.query(Room).filter(Room.name == data.room_name).first():
        raise HTTPException(status_code=400, detail=f"치료실 '{data.room_name}'이 존재하지 않습니다")
    if db.query(PrescriptionCode).filter(PrescriptionCode.code == data.code).first():
        raise HTTPException(status_code=400, detail="이미 존재하는 처방코드입니다")
    rx = PrescriptionCode(**data.model_dump())
    db.add(rx)
    db.commit()
    db.refresh(rx)
    return rx


@router.put("/{code}", response_model=PrescriptionCodeOut)
def update_prescription(code: str, data: PrescriptionCodeCreate, db: Session = Depends(get_db)):
    rx = db.query(PrescriptionCode).filter(PrescriptionCode.code == code).first()
    if not rx:
        raise HTTPException(status_code=404, detail="처방코드를 찾을 수 없습니다")
    for k, v in data.model_dump().items():
        setattr(rx, k, v)
    db.commit()
    db.refresh(rx)
    return rx


@router.delete("/{code}")
def delete_prescription(code: str, db: Session = Depends(get_db)):
    rx = db.query(PrescriptionCode).filter(PrescriptionCode.code == code).first()
    if not rx:
        raise HTTPException(status_code=404, detail="처방코드를 찾을 수 없습니다")
    db.delete(rx)
    db.commit()
    return {"ok": True}
