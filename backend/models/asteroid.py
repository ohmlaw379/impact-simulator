from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId

class CloseApproach(BaseModel):
    """NASA NEO Close Approach Data"""
    date: str
    velocity_kms: float
    distance_km: float
    orbiting_body: str
    
class OrbitalElements(BaseModel):
    """Orbital mechanics parameters"""
    semi_major_axis_au: Optional[float] = None
    eccentricity: Optional[float] = None
    inclination_deg: Optional[float] = None
    orbital_period_days: Optional[float] = None
    perihelion_distance_au: Optional[float] = None
    aphelion_distance_au: Optional[float] = None

class DiameterEstimate(BaseModel):
    """Size estimates from NASA"""
    min_km: Optional[float] = None
    max_km: Optional[float] = None
    average_km: Optional[float] = None

class Asteroid(BaseModel):
    """Enhanced Asteroid model with NASA NEO data"""
    id: str = Field(alias="_id", default_factory=lambda: str(ObjectId()))
    nasa_id: str  # NASA NEO reference ID
    name: str
    designation: Optional[str] = None
    
    # Physical characteristics
    diameter: DiameterEstimate
    absolute_magnitude: Optional[float] = None
    estimated_diameter_km: Optional[float] = None
    
    # Classification
    potentially_hazardous: bool = False
    neo_type: Optional[str] = None  # Apollo, Aten, Amor, etc.
    
    # Orbital data
    orbital_elements: Optional[OrbitalElements] = None
    close_approaches: List[CloseApproach] = []
    
    # Enhanced simulation data
    composition_type: str = "rocky"  # rocky, iron, icy
    density_kg_m3: Optional[float] = None
    
    # Metadata
    nasa_data: Optional[Dict[str, Any]] = None
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True
    
    class Config:
        populate_by_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }

class AsteroidFilter(BaseModel):
    """Filter parameters for asteroid search"""
    diameter_min_km: Optional[float] = None
    diameter_max_km: Optional[float] = None
    potentially_hazardous: Optional[bool] = None
    neo_type: Optional[str] = None
    has_close_approaches: Optional[bool] = None
    limit: int = 20
    offset: int = 0

class AsteroidSearchResult(BaseModel):
    """Search results with pagination"""
    asteroids: List[Asteroid]
    total: int
    limit: int
    offset: int
    has_more: bool