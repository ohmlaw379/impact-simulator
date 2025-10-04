from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime
from bson import ObjectId

class ImpactLocation(BaseModel):
    """Geographic impact location"""
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)
    name: str
    population: Optional[int] = 0
    country: Optional[str] = None

class ImpactParameters(BaseModel):
    """Enhanced impact simulation parameters"""
    asteroid_nasa_id: str
    impact_location: ImpactLocation
    
    # Impact conditions
    impact_velocity_kms: Optional[float] = None  # Auto-calculated from orbital data
    impact_angle_deg: float = Field(45, ge=15, le=90)
    
    # Advanced parameters
    target_density_kg_m3: float = 2700  # Average crustal density
    atmospheric_entry: bool = True
    fragmentation_altitude_km: Optional[float] = None

class ImpactMetric(BaseModel):
    """Individual impact metric with enhanced data"""
    value: str
    unit: str
    severity: str  # catastrophic, severe, moderate, minor
    description: str
    progress: float = 0
    scientific_basis: Optional[str] = None  # Reference to calculation method
    uncertainty_range: Optional[Dict[str, float]] = None  # min/max estimates

class ImpactResults(BaseModel):
    """Comprehensive impact simulation results"""
    immediate: Dict[str, ImpactMetric]
    environmental: Dict[str, ImpactMetric]
    human_impact: Dict[str, ImpactMetric]
    timeline: Dict[str, Dict[str, str]]
    
    # Enhanced scientific data
    asteroid_source: str  # "nasa_neo" or "custom"
    calculation_method: str  # "enhanced_physics" or "simplified"
    confidence_level: float = 0.95  # Statistical confidence
    
class Simulation(BaseModel):
    """Enhanced simulation with NASA data integration"""
    id: str = Field(alias="_id", default_factory=lambda: str(ObjectId()))
    
    # Core simulation data
    parameters: ImpactParameters
    results: Optional[ImpactResults] = None
    
    # Enhanced asteroid data
    asteroid_data: Optional[Dict[str, Any]] = None  # Full NASA asteroid record
    
    # Metadata
    name: str
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # User and sharing
    created_by: Optional[str] = None  # User ID when auth is implemented
    is_public: bool = True
    tags: List[str] = []
    
    # Scientific validation
    nasa_enhanced: bool = True  # Uses real NASA data
    peer_reviewed: bool = False  # Future feature
    
    class Config:
        populate_by_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }

class SimulationCreate(BaseModel):
    """Request model for creating new simulation"""
    parameters: ImpactParameters
    name: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = []

class SimulationUpdate(BaseModel):
    """Request model for updating simulation"""
    name: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    is_public: Optional[bool] = None