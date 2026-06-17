from datetime import date as date_type, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models import Patient, PrescriptionCode, Room, Schedule, Therapist
from ..schemas import (
    AutoAssignResult,
    PatientAutoAssign,
    RoomScheduleOut,
    RoomSlotOut,
    ScheduleItemOut,
    TherapistScheduleOut,
    TherapistSlotOut,
)
from ..scheduler.engine import make_label, room_station_list, schedule_patient
from ..constants import TIME_SLOTS

router = APIRouter()


def _rx_map(db: Session) -> dict:
    return {
        rx.code: {
            "name": rx.name,
            "duration": rx.duration,
            "room_name": rx.room_name,
            "zones": rx.station_zones,
            "overlay_targets": rx.overlay_targets,
            "time_window": rx.time_window,
        }
        for rx in db.query(PrescriptionCode).all()
    }


def _room_stations_map(db: Session) -> dict:
    return {r.name: r.stations for r in db.query(Room).all() if r.stations}


def _slot_sort_key(slot_time: str) -> int:
    try:
        return TIME_SLOTS.index(slot_time)
    except ValueError:
        return 99


@router.post("/auto-assign", response_model=AutoAssignResult)
def auto_assign(data: PatientAutoAssign, db: Session = Depends(get_db)):
    rx_map = _rx_map(db)
    room_capacity = {r.name: r.beds for r in db.query(Room).all()}
    room_stations = _room_stations_map(db)

    start_date = data.date
    end_date = data.end_date or start_date

    # 날짜 범위 생성
    dates: List[date_type] = []
    d = start_date
    while d <= end_date:
        dates.append(d)
        d += timedelta(days=1)

    patient = Patient(
        name=data.name,
        available_start=data.available_start,
        available_end=data.available_end,
        zone_restriction=data.zone_restriction,
    )
    db.add(patient)
    db.flush()

    first_day_saved: List[ScheduleItemOut] = []
    all_warnings: List[str] = []

    for target_date in dates:
        existing = db.query(Schedule).filter(Schedule.date == target_date).all()
        existing_list = [
            {"room_name": s.room_name, "slot_time": s.slot_time,
             "station": s.station, "prescription_code": s.prescription_code}
            for s in existing
        ]

        items, warnings = schedule_patient(
            patient_name=data.name,
            available_start=data.available_start,
            available_end=data.available_end,
            orders=data.orders,
            prescription_map=rx_map,
            room_capacity_map=room_capacity,
            existing_schedules=existing_list,
            target_date=target_date,
            room_stations_map=room_stations,
            zone_restriction=data.zone_restriction,
        )

        for item in items:
            s = Schedule(
                patient_id=patient.id,
                prescription_code=item["prescription_code"],
                overlay_code=item.get("overlay_code"),
                room_name=item["room_name"],
                slot_time=item["slot_time"],
                station=item["station"],
                date=target_date,
            )
            db.add(s)
            db.flush()
            if target_date == start_date:
                first_day_saved.append(ScheduleItemOut(
                    id=s.id,
                    slot_time=item["slot_time"],
                    date=target_date,
                    prescription_code=item["prescription_code"],
                    prescription_name=item["prescription_name"],
                    overlay_code=item.get("overlay_code"),
                    overlay_name=item.get("overlay_name"),
                    room_name=item["room_name"],
                    station=item["station"],
                    label=item["label"],
                ))

        if warnings:
            prefix = f"[{target_date}] " if len(dates) > 1 else ""
            all_warnings.extend(f"{prefix}{w}" for w in warnings)

    db.commit()
    return AutoAssignResult(
        patient_id=patient.id,
        patient_name=data.name,
        date=start_date,
        end_date=end_date if end_date != start_date else None,
        total_dates=len(dates),
        schedules=first_day_saved,
        warnings=all_warnings,
    )


@router.get("/patient/{patient_id}", response_model=AutoAssignResult)
def get_patient_schedule(
    patient_id: int,
    date: date_type = Query(...),
    db: Session = Depends(get_db),
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="환자를 찾을 수 없습니다")

    schedules = (
        db.query(Schedule)
        .filter(Schedule.patient_id == patient_id, Schedule.date == date)
        .all()
    )
    rx = _rx_map(db)

    items = sorted([
        ScheduleItemOut(
            id=s.id,
            slot_time=s.slot_time,
            prescription_code=s.prescription_code,
            prescription_name=rx.get(s.prescription_code, {}).get("name", s.prescription_code),
            overlay_code=s.overlay_code,
            overlay_name=rx.get(s.overlay_code, {}).get("name") if s.overlay_code else None,
            room_name=s.room_name,
            station=s.station,
            label=make_label(patient.name, s.prescription_code, s.overlay_code),
            therapist_name=s.therapist.name if s.therapist else None,
        )
        for s in schedules
    ], key=lambda x: _slot_sort_key(x.slot_time))

    return AutoAssignResult(patient_id=patient.id, patient_name=patient.name,
                            date=date, schedules=items)


@router.get("/room", response_model=RoomScheduleOut)
def get_room_schedule(
    room_name: str = Query(...),
    date: date_type = Query(...),
    db: Session = Depends(get_db),
):
    room = db.query(Room).filter(Room.name == room_name).first()
    if not room:
        raise HTTPException(status_code=404, detail="치료실을 찾을 수 없습니다")

    schedules = (
        db.query(Schedule)
        .filter(Schedule.room_name == room_name, Schedule.date == date)
        .all()
    )
    rx = _rx_map(db)
    stations_map = {room_name: room.stations} if room.stations else {}
    station_names = [s["name"] for s in room_station_list(room_name, stations_map, {room_name: room.beds})]
    station_order = {name: i for i, name in enumerate(station_names)}

    slots = sorted([
        RoomSlotOut(
            slot_time=s.slot_time,
            patient_id=s.patient_id,
            patient_name=s.patient.name,
            prescription_code=s.prescription_code,
            prescription_name=rx.get(s.prescription_code, {}).get("name", s.prescription_code),
            overlay_code=s.overlay_code,
            station=s.station,
            label=make_label(s.patient.name, s.prescription_code, s.overlay_code),
        )
        for s in schedules
    ], key=lambda x: (_slot_sort_key(x.slot_time), station_order.get(x.station, 99)))

    return RoomScheduleOut(room_name=room_name, beds=room.beds, stations=station_names, date=date, slots=slots)


@router.get("/therapist/{therapist_id}", response_model=TherapistScheduleOut)
def get_therapist_schedule(
    therapist_id: int,
    date: date_type = Query(...),
    db: Session = Depends(get_db),
):
    therapist = db.query(Therapist).filter(Therapist.id == therapist_id).first()
    if not therapist:
        raise HTTPException(status_code=404, detail="치료사를 찾을 수 없습니다")

    room = db.query(Room).filter(Room.name == therapist.room_name).first()
    station_names = {s["name"] for s in (room.stations or [])} if room else set()

    query = db.query(Schedule).filter(Schedule.room_name == therapist.room_name, Schedule.date == date)
    if therapist.name in station_names:
        query = query.filter(Schedule.station == therapist.name)
    schedules = query.all()

    rx = _rx_map(db)

    slots = sorted([
        TherapistSlotOut(
            slot_time=s.slot_time,
            patient_id=s.patient_id,
            patient_name=s.patient.name,
            prescription_code=s.prescription_code,
            prescription_name=rx.get(s.prescription_code, {}).get("name", s.prescription_code),
            label=make_label(s.patient.name, s.prescription_code, s.overlay_code),
        )
        for s in schedules
    ], key=lambda x: _slot_sort_key(x.slot_time))

    return TherapistScheduleOut(
        therapist_id=therapist.id,
        therapist_name=therapist.name,
        room_name=therapist.room_name,
        date=date,
        slots=slots,
    )


@router.delete("/{schedule_id}")
def delete_schedule(schedule_id: int, db: Session = Depends(get_db)):
    s = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="스케줄을 찾을 수 없습니다")
    db.delete(s)
    db.commit()
    return {"ok": True}
