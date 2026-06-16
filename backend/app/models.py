from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base


class Room(Base):
    __tablename__ = "rooms"
    name = Column(String, primary_key=True)
    beds = Column(Integer, nullable=False)

    prescriptions = relationship("PrescriptionCode", back_populates="room")
    schedules = relationship("Schedule", back_populates="room")


class PrescriptionCode(Base):
    __tablename__ = "prescription_codes"
    code = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    duration = Column(Integer, nullable=False)
    room_name = Column(String, ForeignKey("rooms.name"), nullable=False)

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

    schedules = relationship("Schedule", back_populates="patient", cascade="all, delete-orphan")


class Schedule(Base):
    __tablename__ = "schedules"
    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    prescription_code = Column(String, ForeignKey("prescription_codes.code"), nullable=False)
    room_name = Column(String, ForeignKey("rooms.name"), nullable=False)
    slot_time = Column(String, nullable=False)
    bed_number = Column(Integer, nullable=False)
    therapist_id = Column(Integer, ForeignKey("therapists.id"), nullable=True)
    date = Column(Date, nullable=False)

    patient = relationship("Patient", back_populates="schedules")
    room = relationship("Room", back_populates="schedules")
    prescription = relationship("PrescriptionCode", back_populates="schedules")
    therapist = relationship("Therapist", back_populates="schedules")
