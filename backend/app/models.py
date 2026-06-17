from sqlalchemy import Column, Integer, String, Date, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .database import Base


class Room(Base):
    __tablename__ = "rooms"
    name = Column(String, primary_key=True)
    beds = Column(Integer, nullable=False)
    # 명명된 스테이션 목록. 예: [{"name": "M1", "zone": "M"}, ...]
    # null/빈 리스트면 기존처럼 단순 번호 베드(1..beds)를 사용한다.
    stations = Column(JSON, nullable=True)

    prescriptions = relationship("PrescriptionCode", back_populates="room")
    schedules = relationship("Schedule", back_populates="room")


class PrescriptionCode(Base):
    __tablename__ = "prescription_codes"
    code = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    duration = Column(Integer, nullable=False)
    room_name = Column(String, ForeignKey("rooms.name"), nullable=False)
    # 배정 가능한 스테이션 zone 목록. null/빈 리스트면 제한 없음(해당 치료실의 모든 스테이션 가능).
    station_zones = Column(JSON, nullable=True)
    # 이 코드가 "중첩 사용" 코드인 경우, 함께 사용될 수 있는 대상 코드 목록 (예: MM151AM -> ["MM301AM","MM302AM"]).
    overlay_targets = Column(JSON, nullable=True)
    # "AM"/"PM"이면 해당 코드는 오전/오후 슬롯에만 배정 가능. null이면 시간대 제한 없음.
    time_window = Column(String, nullable=True)

    room = relationship("Room", back_populates="prescriptions")
    schedules = relationship("Schedule", back_populates="prescription")


class Therapist(Base):
    __tablename__ = "therapists"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    room_name = Column(String, ForeignKey("rooms.name"), nullable=False)

    schedules = relationship("Schedule", back_populates="therapist")


class Patient(Base):
    __tablename__ = "patients"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    available_start = Column(String, nullable=False)
    available_end = Column(String, nullable=False)
    # 뇌재활치료실 M/B/T 존 제한. null이면 처방 코드의 zones 그대로 사용.
    zone_restriction = Column(String, nullable=True)

    schedules = relationship("Schedule", back_populates="patient", cascade="all, delete-orphan")


class Schedule(Base):
    __tablename__ = "schedules"
    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    prescription_code = Column(String, ForeignKey("prescription_codes.code"), nullable=False)
    # 중첩 사용된 코드 (예: MM301AM 슬롯에 MM151AM이 함께 배정된 경우 "MM151AM")
    overlay_code = Column(String, nullable=True)
    room_name = Column(String, ForeignKey("rooms.name"), nullable=False)
    slot_time = Column(String, nullable=False)
    # 스테이션 식별자. 명명된 스테이션 방("M1","황병훈" 등) 또는 일반 베드("1","2" 등)
    station = Column(String, nullable=False)
    therapist_id = Column(Integer, ForeignKey("therapists.id"), nullable=True)
    date = Column(Date, nullable=False)

    patient = relationship("Patient", back_populates="schedules")
    room = relationship("Room", back_populates="schedules")
    prescription = relationship("PrescriptionCode", back_populates="schedules")
    therapist = relationship("Therapist", back_populates="schedules")
