from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, SessionLocal, engine
from .models import PrescriptionCode, Room
from .constants import PRESCRIPTION_MASTER, ROOM_MASTER
from .routers import patients, prescriptions, rooms, schedules, therapists


def _seed():
    db = SessionLocal()
    try:
        if db.query(Room).count() == 0:
            for name, data in ROOM_MASTER.items():
                db.add(Room(name=name, beds=data["beds"]))
            db.commit()

        if db.query(PrescriptionCode).count() == 0:
            for code, data in PRESCRIPTION_MASTER.items():
                db.add(PrescriptionCode(
                    code=code, name=data["name"],
                    duration=data["duration"], room_name=data["room"],
                ))
            db.commit()
    finally:
        db.close()


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
