from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from typing import List, Optional
import logging
from datetime import datetime
from bson import ObjectId

from models.simulation import Simulation, SimulationCreate, SimulationUpdate, ImpactParameters
from models.asteroid import Asteroid
from services.nasa_neo_service import nasa_neo_service
from services.physics_engine import physics_engine

logger = logging.getLogger(__name__)

def get_database():
    """Get database connection"""
    from motor.motor_asyncio import AsyncIOMotorClient
    import os
    from dotenv import load_dotenv
    from pathlib import Path
    
    # Load environment variables
    ROOT_DIR = Path(__file__).parent.parent
    load_dotenv(ROOT_DIR / '.env')
    
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    return client[os.environ['DB_NAME']]

# Initialize database connection
db = get_database()

router = APIRouter(prefix="/api/simulation", tags=["Enhanced Simulation"])

@router.post("/run", response_model=Simulation)
async def run_enhanced_simulation(simulation_request: SimulationCreate):
    """Run enhanced asteroid impact simulation using real NASA data"""
    
    try:
        params = simulation_request.parameters
        
        # Get asteroid data (from cache or NASA API)
        asteroid = await _get_asteroid_data(params.asteroid_nasa_id)
        
        if not asteroid:
            raise HTTPException(
                status_code=404, 
                detail=f"Asteroid with NASA ID {params.asteroid_nasa_id} not found"
            )
        
        logger.info(f"Running enhanced simulation for {asteroid.name} ({asteroid.nasa_id})")
        
        # Run enhanced physics calculations
        results = physics_engine.calculate_impact_scenario(asteroid, params)
        
        # Create simulation record
        simulation = Simulation(
            parameters=params,
            results=results,
            asteroid_data=asteroid.dict(),
            name=simulation_request.name or f"Impact: {asteroid.name} → {params.impact_location.name}",
            description=simulation_request.description or f"Enhanced simulation using NASA data for {asteroid.name}",
            tags=simulation_request.tags or ["nasa-enhanced", asteroid.composition_type],
            nasa_enhanced=True
        )
        
        # Save to database
        result = await db.simulations.insert_one(simulation.dict())
        simulation.id = str(result.inserted_id)
        
        logger.info(f"Enhanced simulation completed and saved with ID: {simulation.id}")
        
        return simulation
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Enhanced simulation failed: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Simulation failed: {str(e)}"
        )

@router.get("/simulations", response_model=List[Simulation])
async def get_simulations(
    limit: int = 20,
    nasa_enhanced_only: bool = False,
    asteroid_type: Optional[str] = None
):
    """Get list of saved simulations"""
    
    try:
        # Build query
        query = {}
        if nasa_enhanced_only:
            query["nasa_enhanced"] = True
        if asteroid_type:
            query["tags"] = asteroid_type
        
        # Fetch simulations
        simulations_data = await db.simulations.find(
            query,
            sort=[("created_at", -1)],
            limit=limit
        ).to_list(limit)
        
        simulations = [Simulation(**sim) for sim in simulations_data]
        
        return simulations
    
    except Exception as e:
        logger.error(f"Failed to fetch simulations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch simulations: {str(e)}")

@router.get("/simulation/{simulation_id}", response_model=Simulation)
async def get_simulation(simulation_id: str):
    """Get specific simulation by ID"""
    
    try:
        if not ObjectId.is_valid(simulation_id):
            raise HTTPException(status_code=400, detail="Invalid simulation ID format")
        
        simulation_data = await db.simulations.find_one({"_id": ObjectId(simulation_id)})
        
        if not simulation_data:
            raise HTTPException(status_code=404, detail="Simulation not found")
        
        return Simulation(**simulation_data)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch simulation {simulation_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch simulation: {str(e)}")

@router.put("/simulation/{simulation_id}", response_model=Simulation)
async def update_simulation(simulation_id: str, update_request: SimulationUpdate):
    """Update simulation metadata"""
    
    try:
        if not ObjectId.is_valid(simulation_id):
            raise HTTPException(status_code=400, detail="Invalid simulation ID format")
        
        # Build update query
        update_data = {"updated_at": datetime.utcnow()}
        
        if update_request.name is not None:
            update_data["name"] = update_request.name
        if update_request.description is not None:
            update_data["description"] = update_request.description
        if update_request.tags is not None:
            update_data["tags"] = update_request.tags
        if update_request.is_public is not None:
            update_data["is_public"] = update_request.is_public
        
        # Update simulation
        result = await db.simulations.update_one(
            {"_id": ObjectId(simulation_id)},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Simulation not found")
        
        # Return updated simulation
        simulation_data = await db.simulations.find_one({"_id": ObjectId(simulation_id)})
        return Simulation(**simulation_data)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update simulation {simulation_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update simulation: {str(e)}")

@router.delete("/simulation/{simulation_id}")
async def delete_simulation(simulation_id: str):
    """Delete simulation"""
    
    try:
        if not ObjectId.is_valid(simulation_id):
            raise HTTPException(status_code=400, detail="Invalid simulation ID format")
        
        result = await db.simulations.delete_one({"_id": ObjectId(simulation_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Simulation not found")
        
        return {"message": "Simulation deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete simulation {simulation_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete simulation: {str(e)}")

@router.post("/compare")
async def compare_simulations(simulation_ids: List[str]):
    """Compare multiple simulations side by side"""
    
    try:
        if len(simulation_ids) < 2 or len(simulation_ids) > 5:
            raise HTTPException(
                status_code=400, 
                detail="Must compare between 2 and 5 simulations"
            )
        
        # Validate and fetch simulations
        simulations = []
        for sim_id in simulation_ids:
            if not ObjectId.is_valid(sim_id):
                raise HTTPException(status_code=400, detail=f"Invalid simulation ID: {sim_id}")
            
            sim_data = await db.simulations.find_one({"_id": ObjectId(sim_id)})
            if not sim_data:
                raise HTTPException(status_code=404, detail=f"Simulation not found: {sim_id}")
            
            simulations.append(Simulation(**sim_data))
        
        # Build comparison matrix
        comparison = {
            "simulations": [sim.dict() for sim in simulations],
            "comparison_matrix": _build_comparison_matrix(simulations),
            "summary": _generate_comparison_summary(simulations)
        }
        
        return comparison
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to compare simulations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")

@router.get("/statistics")
async def get_simulation_statistics():
    """Get aggregate statistics across all simulations"""
    
    try:
        # Basic counts
        total_sims = await db.simulations.count_documents({})
        nasa_enhanced = await db.simulations.count_documents({"nasa_enhanced": True})
        
        # Most simulated asteroids
        popular_asteroids = await db.simulations.aggregate([
            {"$match": {"nasa_enhanced": True}},
            {"$group": {
                "_id": "$asteroid_data.nasa_id",
                "name": {"$first": "$asteroid_data.name"},
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]).to_list(10)
        
        # Impact location distribution
        impact_locations = await db.simulations.aggregate([
            {"$group": {
                "_id": "$parameters.impact_location.name",
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]).to_list(10)
        
        # Average impact metrics (for NASA enhanced simulations)
        avg_metrics = await db.simulations.aggregate([
            {"$match": {"nasa_enhanced": True, "results": {"$exists": True}}},
            {"$group": {
                "_id": None,
                "avg_energy_mt": {"$avg": {"$toDouble": "$results.immediate.energy.value"}},
                "avg_crater_km": {"$avg": {"$toDouble": "$results.immediate.craterDiameter.value"}}
            }}
        ]).to_list(1)
        
        return {
            "total_simulations": total_sims,
            "nasa_enhanced_count": nasa_enhanced,
            "enhancement_rate": (nasa_enhanced / total_sims * 100) if total_sims > 0 else 0,
            "popular_asteroids": popular_asteroids,
            "popular_locations": impact_locations,
            "average_metrics": avg_metrics[0] if avg_metrics else {},
            "last_simulation": (await db.simulations.find_one(
                {},
                sort=[("created_at", -1)]
            ) or {}).get("created_at")
        }
    
    except Exception as e:
        logger.error(f"Failed to get simulation statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")

# Helper functions

async def _get_asteroid_data(nasa_id: str) -> Optional[Asteroid]:
    """Get asteroid data from cache or NASA API"""
    
    # Try cache first
    cached_asteroid = await db.asteroids.find_one({"nasa_id": nasa_id})
    if cached_asteroid:
        # Convert ObjectId to string for Pydantic model
        if '_id' in cached_asteroid:
            cached_asteroid['_id'] = str(cached_asteroid['_id'])
        return Asteroid(**cached_asteroid)
    
    # Fetch from NASA API
    try:
        async with nasa_neo_service as service:
            neo_data = await service.get_neo_by_id(nasa_id)
            asteroid = service.parse_neo_to_asteroid(neo_data)
            
            # Cache the result
            asteroid_dict = asteroid.dict()
            asteroid_dict.pop('_id', None)  # Remove the generated ID for upsert
            await db.asteroids.update_one(
                {"nasa_id": asteroid.nasa_id},
                {"$set": asteroid_dict},
                upsert=True
            )
            
            return asteroid
    
    except Exception as e:
        logger.error(f"Failed to fetch asteroid data for {nasa_id}: {str(e)}")
        return None

def _build_comparison_matrix(simulations: List[Simulation]) -> dict:
    """Build comparison matrix for simulations"""
    
    matrix = {
        "crater_diameters": [],
        "energies": [],
        "casualties": [],
        "shockwave_radii": []
    }
    
    for sim in simulations:
        if sim.results:
            matrix["crater_diameters"].append({
                "simulation_id": sim.id,
                "name": sim.name,
                "value": sim.results.immediate.get("craterDiameter", {}).value or "0"
            })
            
            matrix["energies"].append({
                "simulation_id": sim.id,
                "name": sim.name,
                "value": sim.results.immediate.get("energy", {}).value or "0"
            })
            
            matrix["casualties"].append({
                "simulation_id": sim.id,
                "name": sim.name,
                "value": sim.results.human_impact.get("casualtiesImmediate", {}).value or "0"
            })
            
            matrix["shockwave_radii"].append({
                "simulation_id": sim.id,
                "name": sim.name,
                "value": sim.results.environmental.get("shockwaveRadius", {}).value or "0"
            })
    
    return matrix

def _generate_comparison_summary(simulations: List[Simulation]) -> dict:
    """Generate summary of comparison"""
    
    return {
        "total_compared": len(simulations),
        "nasa_enhanced": sum(1 for sim in simulations if sim.nasa_enhanced),
        "locations": list(set(sim.parameters.impact_location.name for sim in simulations)),
        "asteroid_types": list(set(
            sim.asteroid_data.get("composition_type") 
            for sim in simulations 
            if sim.asteroid_data
        ))
    }