from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from typing import List, Optional
import logging
from services.nasa_neo_service import nasa_neo_service
from models.asteroid import Asteroid, AsteroidFilter, AsteroidSearchResult

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/neo", tags=["NASA NEO Integration"])

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

@router.get("/asteroids", response_model=AsteroidSearchResult)
async def get_asteroids(
    limit: int = Query(20, ge=1, le=100, description="Number of asteroids to return"),
    diameter_min_km: Optional[float] = Query(None, ge=0.001, description="Minimum diameter in kilometers"),
    diameter_max_km: Optional[float] = Query(None, ge=0.001, description="Maximum diameter in kilometers"),
    potentially_hazardous: Optional[bool] = Query(None, description="Filter by potentially hazardous asteroids"),
    refresh_cache: bool = Query(False, description="Force refresh from NASA API")
):
    """Get real asteroids from NASA NEO database with filtering"""
    
    try:
        filters = AsteroidFilter(
            limit=limit,
            diameter_min_km=diameter_min_km,
            diameter_max_km=diameter_max_km,
            potentially_hazardous=potentially_hazardous
        )
        
        # Check cache first (unless refresh requested)
        if not refresh_cache:
            cached_asteroids = await db.asteroids.find(
                {"is_active": True},
                limit=limit
            ).to_list(limit)
            
            if cached_asteroids:
                # Fix ObjectId serialization for cached data
                for asteroid_data in cached_asteroids:
                    if '_id' in asteroid_data:
                        asteroid_data['_id'] = str(asteroid_data['_id'])
                asteroids = [Asteroid(**asteroid) for asteroid in cached_asteroids]
                return AsteroidSearchResult(
                    asteroids=asteroids,
                    total=len(asteroids),
                    limit=limit,
                    offset=0,
                    has_more=len(asteroids) == limit
                )
        
        # Fetch from NASA API
        async with nasa_neo_service as service:
            neo_data_list = await service.search_asteroids(filters)
            
            asteroids = []
            for neo_data in neo_data_list:
                try:
                    asteroid = service.parse_neo_to_asteroid(neo_data)
                    
                    # Cache in database
                    asteroid_dict = asteroid.dict()
                    asteroid_dict.pop('_id', None)  # Remove the generated ID for upsert
                    await db.asteroids.update_one(
                        {"nasa_id": asteroid.nasa_id},
                        {"$set": asteroid_dict},
                        upsert=True
                    )
                    
                    asteroids.append(asteroid)
                    
                except Exception as e:
                    logger.warning(f"Failed to parse NEO data: {str(e)}")
                    continue
            
            return AsteroidSearchResult(
                asteroids=asteroids,
                total=len(asteroids),
                limit=limit,
                offset=0,
                has_more=len(asteroids) == limit
            )
    
    except Exception as e:
        logger.error(f"Failed to fetch asteroids: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch asteroid data: {str(e)}")

@router.get("/asteroid/{nasa_id}", response_model=Asteroid)
async def get_asteroid_by_id(nasa_id: str):
    """Get detailed asteroid data by NASA NEO ID"""
    
    try:
        # Check cache first
        cached_asteroid = await db.asteroids.find_one({"nasa_id": nasa_id})
        if cached_asteroid:
            # Convert ObjectId to string for Pydantic model
            if '_id' in cached_asteroid:
                cached_asteroid['_id'] = str(cached_asteroid['_id'])
            return Asteroid(**cached_asteroid)
        
        # Fetch from NASA API
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
        logger.error(f"Failed to fetch asteroid {nasa_id}: {str(e)}")
        raise HTTPException(status_code=404, detail=f"Asteroid not found: {str(e)}")

@router.get("/close-approaches")
async def get_close_approaches(
    days_ahead: int = Query(30, ge=1, le=365, description="Number of days to look ahead"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of asteroids to return")
):
    """Get asteroids with upcoming close approaches to Earth"""
    
    try:
        async with nasa_neo_service as service:
            approaching_asteroids = await service.get_recent_close_approaches(days_ahead)
            
            # Limit results
            limited_asteroids = approaching_asteroids[:limit]
            
            # Parse and enhance with our models
            enhanced_approaches = []
            for neo_data in limited_asteroids:
                try:
                    asteroid = service.parse_neo_to_asteroid(neo_data)
                    
                    # Add approach date from the feed data
                    approach_info = {
                        "asteroid": asteroid.dict(),
                        "approach_date": neo_data.get('approach_date'),
                        "closest_approach_km": min([
                            float(app.get('miss_distance', {}).get('kilometers', float('inf')))
                            for app in neo_data.get('close_approach_data', [{}])
                        ]),
                        "relative_velocity_kms": [
                            float(app.get('relative_velocity', {}).get('kilometers_per_second', 0))
                            for app in neo_data.get('close_approach_data', [])
                        ][0] if neo_data.get('close_approach_data') else 0
                    }
                    
                    enhanced_approaches.append(approach_info)
                    
                except Exception as e:
                    logger.warning(f"Failed to parse approaching asteroid: {str(e)}")
                    continue
            
            return {
                "approaching_asteroids": enhanced_approaches,
                "total_found": len(approaching_asteroids),
                "returned": len(enhanced_approaches),
                "days_ahead": days_ahead
            }
    
    except Exception as e:
        logger.error(f"Failed to fetch close approaches: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch close approach data: {str(e)}")

@router.post("/sync")
async def sync_nasa_data(background_tasks: BackgroundTasks):
    """Background task to sync NASA NEO database"""
    
    async def sync_task():
        try:
            logger.info("Starting NASA NEO database sync...")
            
            async with nasa_neo_service as service:
                # Fetch multiple pages of asteroids
                total_synced = 0
                
                for page in range(10):  # Sync 10 pages (200 asteroids)
                    try:
                        browse_data = await service.get_neo_browse(limit=20, page=page)
                        neos = browse_data.get('near_earth_objects', [])
                        
                        if not neos:
                            break
                        
                        for neo_data in neos:
                            try:
                                asteroid = service.parse_neo_to_asteroid(neo_data)
                                
                                # Upsert to database
                                asteroid_dict = asteroid.dict()
                                asteroid_dict.pop('_id', None)  # Remove the generated ID for upsert
                                await db.asteroids.update_one(
                                    {"nasa_id": asteroid.nasa_id},
                                    {"$set": asteroid_dict},
                                    upsert=True
                                )
                                
                                total_synced += 1
                                
                            except Exception as e:
                                logger.warning(f"Failed to sync asteroid: {str(e)}")
                                continue
                    
                    except Exception as e:
                        logger.error(f"Failed to sync page {page}: {str(e)}")
                        break
                
                logger.info(f"NASA NEO sync completed. Synced {total_synced} asteroids.")
                
        except Exception as e:
            logger.error(f"NASA NEO sync failed: {str(e)}")
    
    background_tasks.add_task(sync_task)
    
    return {
        "message": "NASA NEO database sync started in background",
        "status": "in_progress"
    }

@router.get("/stats")
async def get_neo_stats():
    """Get statistics about cached NEO data"""
    
    try:
        total_asteroids = await db.asteroids.count_documents({"is_active": True})
        hazardous_count = await db.asteroids.count_documents({
            "is_active": True,
            "potentially_hazardous": True
        })
        
        # Size distribution
        size_stats = await db.asteroids.aggregate([
            {"$match": {"is_active": True}},
            {"$group": {
                "_id": None,
                "avg_diameter": {"$avg": "$estimated_diameter_km"},
                "max_diameter": {"$max": "$estimated_diameter_km"},
                "min_diameter": {"$min": "$estimated_diameter_km"}
            }}
        ]).to_list(1)
        
        # Composition distribution
        composition_stats = await db.asteroids.aggregate([
            {"$match": {"is_active": True}},
            {"$group": {
                "_id": "$composition_type",
                "count": {"$sum": 1}
            }}
        ]).to_list(10)
        
        return {
            "total_asteroids": total_asteroids,
            "potentially_hazardous": hazardous_count,
            "size_statistics": size_stats[0] if size_stats else {},
            "composition_distribution": composition_stats,
            "last_updated": (await db.asteroids.find_one(
                {"is_active": True},
                sort=[("last_updated", -1)]
            ) or {}).get("last_updated")
        }
    
    except Exception as e:
        logger.error(f"Failed to get NEO stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")

@router.get("/featured")
async def get_featured_asteroids():
    """Get a curated list of famous/interesting asteroids"""
    
    # List of famous asteroid NASA IDs
    famous_asteroids = [
        "2000433",   # Eros
        "3554375",   # Bennu (101955 Bennu)
        "99942",     # Apophis  
        "1566",      # Icarus
        "4179",      # Toutatis
        "25143",     # Itokawa
    ]
    
    featured = []
    
    for nasa_id in famous_asteroids:
        try:
            # Try to get from cache first
            cached = await db.asteroids.find_one({"nasa_id": nasa_id})
            
            if cached:
                asteroid = Asteroid(**cached)
            else:
                # Fetch from NASA API if not cached
                try:
                    async with nasa_neo_service as service:
                        neo_data = await service.get_neo_by_id(nasa_id)
                        asteroid = service.parse_neo_to_asteroid(neo_data)
                        
                        # Cache it
                        asteroid_dict = asteroid.dict()
                        asteroid_dict.pop('_id', None)  # Remove the generated ID for upsert
                        await db.asteroids.update_one(
                            {"nasa_id": asteroid.nasa_id},
                            {"$set": asteroid_dict},
                            upsert=True
                        )
                except:
                    continue  # Skip if can't fetch
            
            featured.append({
                "asteroid": asteroid.dict(),
                "description": _get_asteroid_description(nasa_id),
                "significance": _get_asteroid_significance(nasa_id)
            })
        
        except Exception as e:
            logger.warning(f"Failed to fetch featured asteroid {nasa_id}: {str(e)}")
            continue
    
    return {
        "featured_asteroids": featured,
        "count": len(featured)
    }

def _get_asteroid_description(nasa_id: str) -> str:
    """Get description for famous asteroids"""
    descriptions = {
        "2000433": "433 Eros - First asteroid landed on by spacecraft (NEAR Shoemaker)",
        "3554375": "101955 Bennu - Target of OSIRIS-REx sample return mission",
        "99942": "99942 Apophis - Will make close approach to Earth in 2029",
        "1566": "1566 Icarus - High-velocity Apollo asteroid, first radar-detected",
        "4179": "4179 Toutatis - Tumbling asteroid studied by radar",
        "25143": "25143 Itokawa - Target of Japan's Hayabusa mission"
    }
    return descriptions.get(nasa_id, "Notable near-Earth asteroid")

def _get_asteroid_significance(nasa_id: str) -> str:
    """Get significance of famous asteroids"""
    significance = {
        "2000433": "Space exploration milestone",
        "3554375": "Active sample return target",
        "99942": "2029 close approach - no impact risk",
        "1566": "High-velocity impact scenario",
        "4179": "Complex rotation dynamics",
        "25143": "Sample return success"
    }
    return significance.get(nasa_id, "Scientific interest")