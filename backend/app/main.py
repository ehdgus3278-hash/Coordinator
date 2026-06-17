from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, SessionLocal, engine
from .models import PrescriptionCode, Room, Schedule, Therapist
from .constants import (
    AM_SLOTS, BRAIN_ROOM, BRAIN_THERAPISTS, PRESCRIPTION_MASTER, ROOM_MASTER, ROOM_STATIONS,
)
from .routers import patients, prescriptions, rooms, schedules, therapists

# 기본 코드(MM301 등)는 다시 유효한 코드로 복원되었으므로 마이그레이션 대상이 없다.
LEGACY_PRESCRIPTION_CODES: list = []


def _seed():
    db = SessionLocal()
    try:
        if db.query(Room).count() == 0:
            for name, data in ROOM_MASTER.items():
                db.add(Room(name=name, beds=data["beds"], stations=ROOM_STATIONS.get(name)))
            db.commit()

        existing_codes = {c for (c,) in db.query(PrescriptionCode.code).all()}
        for code, data in PRESCRIPTION_MASTER.items():
            if code not in existing_codes:
                db.add(PrescriptionCode(
                    code=code, name=data["name"],
                    duration=data["duration"], room_name=data["room"],
                    station_zones=data.get("zones"),
                    overlay_targets=data.get("overlay_targets"),
                    time_window=data.get("time_window"),
                ))
        db.commit()

        _migrate_legacy_codes(db)

        if db.query(Therapist).count() == 0:
            for name in BRAIN_THERAPISTS:
                db.add(Therapist(name=name, room_name=BRAIN_ROOM))
            db.commit()
    finally:
        db.close()


def _migrate_legacy_codes(db):
    for legacy in LEGACY_PRESCRIPTION_CODES:
        old = db.query(PrescriptionCode).filter(PrescriptionCode.code == legacy).first()
        if not old:
            continue
        # 일반 ORM 속성 대입 대신 bulk update를 쓰는 이유: PrescriptionCode.schedules
        # 관계가 delete cascade가 아니라서, old를 삭제할 때 아직 이 관계에 걸려 있는
        # Schedule의 FK를 SQLAlchemy가 먼저 NULL로 만들어버려 NOT NULL 제약을 위반한다.
        # bulk update + commit으로 참조를 먼저 끊어두면 delete 시점에는 참조가 없다.
        db.query(Schedule).filter(
            Schedule.prescription_code == legacy, Schedule.slot_time.in_(AM_SLOTS)
        ).update({"prescription_code": legacy + "AM"}, synchronize_session=False)
        db.query(Schedule).filter(
            Schedule.prescription_code == legacy, ~Schedule.slot_time.in_(AM_SLOTS)
        ).update({"prescription_code": legacy + "PM"}, synchronize_session=False)
        db.query(Schedule).filter(
            Schedule.overlay_code == legacy, Schedule.slot_time.in_(AM_SLOTS)
        ).update({"overlay_code": legacy + "AM"}, synchronize_session=False)
        db.query(Schedule).filter(
            Schedule.overlay_code == legacy, ~Schedule.slot_time.in_(AM_SLOTS)
        ).update({"overlay_code": legacy + "PM"}, synchronize_session=False)
        db.commit()
        db.delete(old)
        db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    _seed()
    yield


app = FastAPI(title="재활치료 스케줄링 코디네이터", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(patients.router,      prefix="/api/patients",      tags=["patients"])
app.include_router(prescriptions.router, prefix="/api/prescriptions", tags=["prescriptions"])
app.include_router(rooms.router,         prefix="/api/rooms",         tags=["rooms"])
app.include_router(schedules.router,     prefix="/api/schedules",     tags=["schedules"])
app.include_router(therapists.router,    prefix="/api/therapists",    tags=["therapists"])


@app.get("/api/health")
def health():
    return {"status": "ok"}
