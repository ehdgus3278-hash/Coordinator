from pydantic import BaseModel
from typing import List, Optional
from datetime import date


class StationOut(BaseModel):
    name: str
    zone: str


class RoomBase(BaseModel):
    name: str
    beds: int
    stations: Optional[List[StationOut]] = None

class RoomCreate(RoomBase):
    pass

class RoomOut(RoomBase):
    model_config = {"from_attributes": True}


class PrescriptionCodeBase(BaseModel):
    code: str
    name: str
    duration: int
    room_name: str
    station_zones: Optional[List[str]] = None
    overlay_targets: Optional[List[str]] = None

class PrescriptionCodeCreate(PrescriptionCodeBase):
    pass

class PrescriptionCodeOut(PrescriptionCodeBase):
    model_config = {"from_attributes": True}


class TherapistBase(BaseModel):
    name: str
    room_name: str

class TherapistCreate(TherapistBase):
    pass

class TherapistOut(TherapistBase):
    id: int
    model_config = {"from_attributes": True}


class PatientOut(BaseModel):
    id: int
    name: str
    available_start: str
    available_end: str
    model_config = {"from_attributes": True}


class PatientAutoAssign(BaseModel):
    name: str
    available_start: str
    available_end: str
    orders: List[str]
    date: date


class ScheduleItemOut(BaseModel):
    id: int
    slot_time: str
    prescription_code: str
    prescription_name: str
    overlay_code: Optional[str] = None
    overlay_name: Optional[str] = None
    room_name: str
    station: str
    label: str
    therapist_name: Optional[str] = None
    model_config = {"from_attributes": True}


class AutoAssignResult(BaseModel):
    patient_id: int
    patient_name: str
    date: date
    schedules: List[ScheduleItemOut]
    warnings: List[str] = []


class RoomSlotOut(BaseModel):
    slot_time: str
    patient_id: int
    patient_name: str
    prescription_code: str
    prescription_name: str
    overlay_code: Optional[str] = None
    station: str
    label: str

class RoomScheduleOut(BaseModel):
    room_name: str
    beds: int
    stations: List[str]
    date: date
    slots: List[RoomSlotOut]


class TherapistSlotOut(BaseModel):
    slot_time: str
    patient_id: int
    patient_name: str
    prescription_code: str
    prescription_name: str
    label: str

class TherapistScheduleOut(BaseModel):
    therapist_id: int
    therapist_name: str
    room_name: str
    date: date
    slots: List[TherapistSlotOut]
