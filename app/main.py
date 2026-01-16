# app/main.py
# ------------------------------------------------------------------
# Application entry point for the Revival365 FastAPI service
# ------------------------------------------------------------------

# Ensure environment variables from .env are loaded
# before importing modules that depend on configuration
from dotenv import load_dotenv
load_dotenv()

# Application routers
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, agp, appointments, appointments2, clinical_report_summary, glucose_alert, dha_charts, quiz
import logging
import os

# Database session factory
from .db import SessionLocal

# Keep timezone consistent with the Lambdas
os.environ["TZ"] = "Asia/Kolkata"
if hasattr(time := __import__("time"), "tzset"):
    time.tzset()

# ------------------------------------------------------------------
# Logging Configuration
# ------------------------------------------------------------------
# Configure global logging level for the application
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# FastAPI Application Initialization
# ------------------------------------------------------------------
app = FastAPI(
    title="Revival365 API",
    version="1.0.0",
    description="Revival365 FastAPI service"
)

# ------------------------------------------------------------------
# Application Startup Hook
# ------------------------------------------------------------------
@app.on_event("startup")
async def startup_event():
    """Check database connection on startup"""
    try:
        db = SessionLocal()

        # Execute a lightweight sanity check query
        # text() is used for SQLAlchemy 2.x compatibility
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        db.close()
        logger.info("✅ Database Connected Successfully")
    except Exception as e:
        logger.warning(f"⚠️ Database Connection Warning: {str(e)}")

# ------------------------------------------------------------------
# Middleware Configuration
# ------------------------------------------------------------------
# Enable Cross-Origin Resource Sharing (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------
# Router Registration
# ------------------------------------------------------------------
# Register API routers
app.include_router(agp.router)
app.include_router(appointments.router)
app.include_router(appointments2.router)
app.include_router(clinical_report_summary.router)
app.include_router(glucose_alert.router)
app.include_router(dha_charts.router)
app.include_router(quiz.router)





@app.get("/health")
def health_check():
    return {"status": "UP"}
