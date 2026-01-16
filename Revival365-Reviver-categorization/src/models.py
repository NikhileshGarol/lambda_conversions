# models.py
from sqlalchemy import create_engine, Column, Integer, Float, DateTime, Date
from sqlalchemy.orm import sessionmaker, declarative_base

# -------------------------------
# DB Setup (PyMySQL driver)
# -------------------------------
# DB_URL = "mysql+pymysql://admin:MvqHf1QnpP1F1UqT57Pr@revival365ai-db.chisukc6ague.ap-south-1.rds.amazonaws.com/revival"
DB_URL = "mysql+pymysql://dbadmin:Stixis)(*7@10.0.0.15:3306/revival_dev"

# create_engine outside handler to reuse connections across invocations
engine = create_engine(
    DB_URL,
    pool_recycle=3600,  # avoids MySQL 'MySQL server has gone away'
    pool_pre_ping=True  # checks connection before using
)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# -------------------------------
# ORM Models
# -------------------------------


class PatientsDoctorsMapping(Base):
    __tablename__ = "patients_doctors_mapping"
    user_id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, primary_key=True)


class MyPlan(Base):
    __tablename__ = "my_plan"
    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer)
    to_date = Column(Date)


class GlucoseReading(Base):
    __tablename__ = "glucose_readings"
    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer)
    value = Column(Float)
    actual_time = Column(DateTime)


class HeartRateReading(Base):
    __tablename__ = "heart_rate_readings"
    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer)
    value = Column(Integer)
    actual_time = Column(DateTime)


class BloodPressureReading(Base):
    __tablename__ = "blood_pressure_readings"
    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer)
    systolic = Column(Integer)
    diastolic = Column(Integer)
    actual_time = Column(DateTime)
