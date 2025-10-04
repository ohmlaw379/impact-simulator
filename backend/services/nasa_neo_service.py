import os
import aiohttp
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
from models.asteroid import Asteroid, CloseApproach, OrbitalElements, DiameterEstimate, AsteroidFilter
from dotenv import load_dotenv
from pathlib import Path

logger = logging.getLogger(__name__)

# Load environment variables
ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / '.env')

class NASANEOService:
    """Service for integrating with NASA NEO (Near Earth Object) API"""
    
    def __init__(self):
        self.api_key = os.environ.get('NASA_API_KEY')
        self.base_url = os.environ.get('NASA_NEO_BASE_URL', 'https://api.nasa.gov/neo/rest/v1/')
        self.session: Optional[aiohttp.ClientSession] = None
        
        if not self.api_key:
            logger.warning("NASA API key not found. Real NEO data will be unavailable.")
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make authenticated request to NASA NEO API"""
        if not self.session:
            raise RuntimeError("Service not properly initialized. Use async context manager.")
            
        if not self.api_key:
            raise RuntimeError("NASA API key not configured")
        
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        request_params = {"api_key": self.api_key}
        if params:
            request_params.update(params)
        
        try:
            async with self.session.get(url, params=request_params, timeout=30) as response:
                response.raise_for_status()
                data = await response.json()
                return data
                
        except aiohttp.ClientTimeout:
            logger.error(f"NASA API request timeout: {url}")
            raise RuntimeError("NASA API request timed out")
        except aiohttp.ClientError as e:
            logger.error(f"NASA API request failed: {url} - {str(e)}")
            raise RuntimeError(f"NASA API request failed: {str(e)}")
    
    async def get_neo_browse(self, limit: int = 20, page: int = 0) -> Dict[str, Any]:
        """Browse NEO database"""
        params = {
            "size": min(limit, 20),  # NASA API max is 20
            "page": page
        }
        return await self._make_request("neo/browse", params)
    
    async def get_neo_by_id(self, neo_id: str) -> Dict[str, Any]:
        """Get detailed NEO data by ID"""
        return await self._make_request(f"neo/{neo_id}")
    
    async def get_neo_feed(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """Get NEOs approaching Earth in date range"""
        params = {
            "start_date": start_date,
            "end_date": end_date
        }
        return await self._make_request("feed", params)
    
    async def search_asteroids(self, filters: AsteroidFilter) -> List[Dict[str, Any]]:
        """Search and filter asteroids from NASA NEO database"""
        all_asteroids = []
        page = 0
        collected = 0
        
        while collected < filters.limit:
            try:
                # Get page of results
                browse_data = await self.get_neo_browse(limit=20, page=page)
                neos = browse_data.get('near_earth_objects', [])
                
                if not neos:
                    break  # No more results
                
                # Apply filters
                for neo in neos:
                    if collected >= filters.limit:
                        break
                        
                    if self._matches_filter(neo, filters):
                        all_asteroids.append(neo)
                        collected += 1
                
                page += 1
                
                # Prevent infinite loops
                if page > 50:  # Reasonable limit
                    break
                    
            except Exception as e:
                logger.error(f"Error fetching NEO page {page}: {str(e)}")
                break
        
        return all_asteroids
    
    def _matches_filter(self, neo: Dict[str, Any], filters: AsteroidFilter) -> bool:
        """Check if NEO matches filter criteria"""
        # Diameter filter
        diameter_km = self._extract_average_diameter(neo)
        if diameter_km:
            if filters.diameter_min_km and diameter_km < filters.diameter_min_km:
                return False
            if filters.diameter_max_km and diameter_km > filters.diameter_max_km:
                return False
        
        # Potentially hazardous filter
        if filters.potentially_hazardous is not None:
            if neo.get('is_potentially_hazardous_asteroid') != filters.potentially_hazardous:
                return False
        
        # Close approaches filter
        if filters.has_close_approaches:
            approaches = neo.get('close_approach_data', [])
            if not approaches:
                return False
        
        return True
    
    def _extract_average_diameter(self, neo: Dict[str, Any]) -> Optional[float]:
        """Extract average diameter from NASA NEO data"""
        diameter_data = neo.get('estimated_diameter', {}).get('kilometers', {})
        min_diameter = diameter_data.get('estimated_diameter_min')
        max_diameter = diameter_data.get('estimated_diameter_max')
        
        if min_diameter is not None and max_diameter is not None:
            return (min_diameter + max_diameter) / 2
        return None
    
    def parse_neo_to_asteroid(self, neo_data: Dict[str, Any]) -> Asteroid:
        """Convert NASA NEO data to our Asteroid model"""
        
        # Extract diameter estimates
        diameter_km = neo_data.get('estimated_diameter', {}).get('kilometers', {})
        diameter = DiameterEstimate(
            min_km=diameter_km.get('estimated_diameter_min'),
            max_km=diameter_km.get('estimated_diameter_max'),
            average_km=self._extract_average_diameter(neo_data)
        )
        
        # Extract orbital elements if available
        orbital_data = neo_data.get('orbital_data', {})
        orbital_elements = None
        if orbital_data:
            orbital_elements = OrbitalElements(
                semi_major_axis_au=orbital_data.get('semi_major_axis'),
                eccentricity=orbital_data.get('eccentricity'),
                inclination_deg=orbital_data.get('inclination'),
                orbital_period_days=orbital_data.get('orbital_period'),
                perihelion_distance_au=orbital_data.get('perihelion_distance'),
                aphelion_distance_au=orbital_data.get('aphelion_distance')
            )
        
        # Extract close approach data
        close_approaches = []
        for approach in neo_data.get('close_approach_data', []):
            close_approaches.append(CloseApproach(
                date=approach.get('close_approach_date'),
                velocity_kms=float(approach.get('relative_velocity', {}).get('kilometers_per_second', 0)),
                distance_km=float(approach.get('miss_distance', {}).get('kilometers', 0)),
                orbiting_body=approach.get('orbiting_body', 'Earth')
            ))
        
        # Determine composition type based on absolute magnitude and name
        composition = self._estimate_composition(neo_data)
        
        return Asteroid(
            nasa_id=neo_data['id'],
            name=neo_data['name'],
            designation=neo_data.get('designation'),
            diameter=diameter,
            absolute_magnitude=neo_data.get('absolute_magnitude_h'),
            estimated_diameter_km=diameter.average_km,
            potentially_hazardous=neo_data.get('is_potentially_hazardous_asteroid', False),
            neo_type=self._classify_neo_type(orbital_elements),
            orbital_elements=orbital_elements,
            close_approaches=close_approaches,
            composition_type=composition,
            density_kg_m3=self._estimate_density(composition),
            nasa_data=neo_data,
            last_updated=datetime.utcnow()
        )
    
    def _estimate_composition(self, neo_data: Dict[str, Any]) -> str:
        """Estimate asteroid composition based on available data"""
        # Simple heuristic based on absolute magnitude and name patterns
        abs_mag = neo_data.get('absolute_magnitude_h')
        name = neo_data.get('name', '').lower()
        
        # Very bright objects tend to be metallic
        if abs_mag and abs_mag < 15:
            return "iron"
        
        # Most NEOs are rocky/stony
        return "rocky"
    
    def _estimate_density(self, composition: str) -> float:
        """Get estimated density based on composition"""
        density_map = {
            "rocky": 2600,  # kg/m³
            "iron": 7800,   # kg/m³
            "icy": 1000,    # kg/m³
            "stony": 3500   # kg/m³
        }
        return density_map.get(composition, 2600)
    
    def _classify_neo_type(self, orbital_elements: Optional[OrbitalElements]) -> Optional[str]:
        """Classify NEO type based on orbital elements"""
        if not orbital_elements or not orbital_elements.semi_major_axis_au:
            return None
            
        a = orbital_elements.semi_major_axis_au
        e = orbital_elements.eccentricity or 0
        
        # Simplified classification
        q = a * (1 - e)  # perihelion distance
        
        if a > 1.0 and q < 1.017:  # Apollo
            return "Apollo"
        elif a < 1.0:  # Aten
            return "Aten"
        elif a > 1.0 and q > 1.017 and q < 1.3:  # Amor
            return "Amor"
        else:
            return "Other"
    
    async def get_recent_close_approaches(self, days_ahead: int = 30) -> List[Dict[str, Any]]:
        """Get asteroids with close approaches in the next N days"""
        start_date = datetime.now().strftime('%Y-%m-%d')
        end_date = (datetime.now() + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
        
        feed_data = await self.get_neo_feed(start_date, end_date)
        
        approaching_asteroids = []
        for date, neos in feed_data.get('near_earth_objects', {}).items():
            for neo in neos:
                # Add approach date to neo data
                neo['approach_date'] = date
                approaching_asteroids.append(neo)
        
        # Sort by closest approach
        approaching_asteroids.sort(key=lambda x: (
            min([float(app.get('miss_distance', {}).get('kilometers', float('inf'))) 
                 for app in x.get('close_approach_data', [{}])])
        ))
        
        return approaching_asteroids

# Singleton instance
nasa_neo_service = NASANEOService()