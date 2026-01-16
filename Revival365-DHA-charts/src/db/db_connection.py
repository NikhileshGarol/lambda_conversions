from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime, Float, Enum, Date, TIMESTAMP, SmallInteger, Time
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config.config import config
import urllib
import os

# Database connection setup
def get_db_engine():
    databaseconfig = config.get_database_config()
    
    DB_USER = os.getenv("DB_USER", "")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_HOST = os.getenv("DB_HOST", "")
    DB_PORT = os.getenv("DB_PORT", "")
    DB_NAME = os.getenv("DB_NAME", "")
    engine = create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
    return engine
    
 
Base = declarative_base()

# Role model
class Role(Base):
    __tablename__ = 'role'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255))

# Updated User model to reflect the new schema
class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    mobile_number = Column(String(255), unique=True)
    first_name = Column(String(255))
    last_name = Column(String(255))
    email = Column(String(255))
    state = Column(String(255))
    zipcode = Column(String(255))
    role_id = Column(Integer, ForeignKey('role.id'))  # Foreign key to the Role table
    dob = Column(Date)
    sex = Column(String(255))  # Consider using an Enum for better control
    created = Column(TIMESTAMP)
    updated = Column(TIMESTAMP)
    password = Column(String(255))
    status = Column(SmallInteger)
    address = Column(String(255))
    city = Column(String(255))


# Updated GlucoseReadings model to reflect the new schema
class GlucoseReadings(Base):
    __tablename__ = 'glucose_readings'
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(TIMESTAMP)
    value = Column(Float(6, 2))
    patient_id = Column(Integer)  # Assuming patient_id references the User table
 
# GlucoseDailySummary model reflecting the provided schema
class GlucoseDailySummary(Base):
    __tablename__ = 'glucose_daily_summary'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    daily_average = Column(Float(20, 15), nullable=True)
    night_start = Column(Time, nullable=True)
    night_end = Column(Time, nullable=True)
    patient_id = Column(Integer)  # Assuming patient_id references the User table
    date = Column(Date, nullable=True)

class SpO2Readings(Base):
    __tablename__ = 'spo2_readings'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=True)
    value = Column(Float(6, 2), nullable=True)
    ble_summary_id = Column(Integer, ForeignKey('ble_summary.id'), nullable=False)  # Foreign key to the BleSummary table

# BodyTemperatureReadings model reflecting the provided schema
class BodyTemperatureReadings(Base):
    __tablename__ = 'body_temperature_readings'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=True)
    temperature = Column(Float(6, 2), nullable=True)
    ble_summary_id = Column(Integer, ForeignKey('ble_summary.id'), nullable=False)  # Foreign key to the BleSummary table

# BloodPressureReadings model reflecting the provided schema
class BloodPressureReadings(Base):
    __tablename__ = 'blood_pressure_readings'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=True)
    systolic = Column(Integer, nullable=True)
    diastolic = Column(Integer, nullable=True)
    ble_summary_id = Column(Integer, ForeignKey('ble_summary.id'), nullable=False)  # Foreign key to the BleSummary table


class BleSummary(Base):
    __tablename__ = 'ble_summary'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey('users.id'), nullable=True)  # Assuming patient_id references the User table
    date = Column(Date, nullable=True)
    spo2_daily_average = Column(Float(20, 15), nullable=True)
    hr_daily_average = Column(Float(20, 15), nullable=True)
    bp_daily_average = Column(Float(20, 15), nullable=True)
    ht_daily_average = Column(Float(20, 15), nullable=True)

# Updated HeartRateReadings model to include ble_summary_id
class HeartRateReadings(Base):
    __tablename__ = 'heart_rate_readings'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=True)
    value = Column(Float(6, 2), nullable=True)  # Updated to match the double(6,2) in the schema
    ble_summary_id = Column(Integer, ForeignKey('ble_summary.id'), nullable=False)  # Foreign key to the BleSummary table

# Medications model reflecting the provided schema
class Medications(Base):
    __tablename__ = 'medications'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey('users.id'), nullable=True)  # Foreign key to the User table
    medication_name = Column(String(255), nullable=True)
    dosage = Column(String(255), nullable=True)
    frequency = Column(String(255), nullable=True)
    start_date = Column(TIMESTAMP, nullable=True)
    end_date = Column(TIMESTAMP, nullable=True)
    note = Column(String(255), nullable=True)


class GlucoseMonitorConfigSettingMaster(Base):
    __tablename__ = 'glucose_monitor_config_setting_master'

    id = Column(Integer, primary_key=True, autoincrement=True)
    fasting_end_time = Column(Time, nullable=True)
    breakfast_start = Column(Time, nullable=True)
    breakfast_end = Column(Time, nullable=True)
    lunch_start = Column(Time, nullable=True)
    lunch_end = Column(Time, nullable=True)
    dinner_start = Column(Time, nullable=True)
    dinner_end = Column(Time, nullable=True)
    dip_threshold_day = Column(Float(precision=6, asdecimal=True), nullable=True)
    dip_threshold_night = Column(Float(precision=6, asdecimal=True), nullable=True)
    spike_threshold_day = Column(Float(precision=6, asdecimal=True), nullable=True)
    spike_threshold_night = Column(Float(precision=6, asdecimal=True), nullable=True)
    time_after_spike_day = Column(Time, nullable=True)
    day_start = Column(Time, nullable=True)
    day_end = Column(Time, nullable=True)
    night_start = Column(Time, nullable=True)
    night_end = Column(Time, nullable=True)
    spike_threshold_breakfast = Column(Float(precision=6, asdecimal=True), nullable=True)
    spike_threshold_lunch = Column(Float(precision=6, asdecimal=True), nullable=True)
    spike_threshold_dinner = Column(Float(precision=6, asdecimal=True), nullable=True)
    spike_threshold_snack = Column(Float(precision=6, asdecimal=True), nullable=True)


# Define the PatientGlucoseMonitorConfigSetting model
class PatientGlucoseMonitorConfigSetting(Base):
    __tablename__ = 'patient_glucose_monitor_config_setting'

    id = Column(Integer, primary_key=True, autoincrement=True)
    fasting_end_time = Column(Time, nullable=True)
    breakfast_start = Column(Time, nullable=True)
    breakfast_end = Column(Time, nullable=True)
    lunch_start = Column(Time, nullable=True)
    lunch_end = Column(Time, nullable=True)
    dinner_start = Column(Time, nullable=True)
    dinner_end = Column(Time, nullable=True)
    dip_threshold_day = Column(Float(6, 2), nullable=True)
    dip_threshold_night = Column(Float(6, 2), nullable=True)
    spike_threshold_day = Column(Float(6, 2), nullable=True)
    spike_threshold_night = Column(Float(6, 2), nullable=True)
    time_after_spike_day = Column(Time, nullable=True)
    day_start = Column(Time, nullable=True)
    day_end = Column(Time, nullable=True)
    night_start = Column(Time, nullable=True)
    night_end = Column(Time, nullable=True)
    spike_threshold_breakfast = Column(Float(6, 2), nullable=True)
    spike_threshold_lunch = Column(Float(6, 2), nullable=True)
    spike_threshold_dinner = Column(Float(6, 2), nullable=True)
    spike_threshold_snack = Column(Float(6, 2), nullable=True)
    patient_id = Column(Integer, nullable=True)
    doctor_id = Column(Integer, nullable=True)
    from_date = Column(DateTime, nullable=True)
    to_date = Column(DateTime, nullable=True)

# Establishing the database session
engine = get_db_engine()
Session = sessionmaker(bind=engine)

# Main function
if __name__ == '__main__':
    # Attempt to connect to the database
    try:
        connection = engine.connect()
        print("Currently connected to the database.")
    except Exception as e:
        print(f"Failed to connect to the database: {e}")
    finally:
        connection.close()  # Ensure the connection is closed
