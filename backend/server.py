from fastapi import FastAPI, APIRouter
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List
import uuid
from datetime import datetime

# Import new routers
from routers import nasa_neo, enhanced_simulation

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(
    title="Asteroid Impact Simulator API",
    description="Enhanced asteroid impact simulation using real NASA NEO data",
    version="2.0.0"
)

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Define Models (keeping existing ones)
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

# Original routes (keeping for compatibility)
@api_router.get("/")
async def root():
    return {
        "message": "Asteroid Impact Simulator API v2.0",
        "features": [
            "NASA NEO real data integration",
            "Enhanced physics calculations",
            "Orbital mechanics modeling",
            "Scientific impact assessment"
        ],
        "nasa_api_configured": bool(os.environ.get('NASA_API_KEY')),
        "version": "2.0.0"
    }

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

# Health check endpoint
@api_router.get("/health")
async def health_check():
    try:
        # Test database connection
        await db.command("ping")
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    # Test NASA API configuration
    nasa_configured = bool(os.environ.get('NASA_API_KEY'))
    
    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "database": db_status,
        "nasa_api_configured": nasa_configured,
        "timestamp": datetime.utcnow().isoformat()
    }

# Include the enhanced routers
app.include_router(nasa_neo.router)
app.include_router(enhanced_simulation.router)
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Asteroid Impact Simulator API v2.0 starting up...")
    
    # Test NASA API configuration
    nasa_key = os.environ.get('NASA_API_KEY')
    if nasa_key:
        logger.info(f"✅ NASA API configured (key: {nasa_key[:10]}...)")
    else:
        logger.warning("⚠️  NASA API key not configured - real NEO data unavailable")
    
    # Test database connection
    try:
        await db.command("ping")
        logger.info("✅ MongoDB connection successful")
        
        # Create indexes for better performance
        await db.asteroids.create_index("nasa_id", unique=True)
        await db.asteroids.create_index("potentially_hazardous")
        await db.asteroids.create_index("estimated_diameter_km")
        await db.simulations.create_index("created_at")
        await db.simulations.create_index("nasa_enhanced")
        
        logger.info("✅ Database indexes created")
        
    except Exception as e:
        logger.error(f"❌ Database connection failed: {str(e)}")
    
    logger.info("🌌 Asteroid Impact Simulator API ready!")

@app.on_event("shutdown")
async def shutdown_db_client():
    logger.info("🛑 Shutting down Asteroid Impact Simulator API...")
    client.close()
    logger.info("✅ Database connection closed")