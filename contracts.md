# Asteroid Impact Simulator - Backend Integration Contracts

## NASA NEO API Integration

### API Details
- **NASA NEO API Key**: `0jwz5yFePHG2hYoJ9cX2Sqhb2fbiixORVeuc54y7`
- **Base URL**: `https://api.nasa.gov/neo/rest/v1/`
- **Purpose**: Real Near-Earth Object data integration for enhanced realism

### Backend API Endpoints to Create

#### 1. `/api/neo/asteroids` (GET)
**Purpose**: Fetch real asteroids from NASA NEO database
**Parameters**: 
- `limit`: Number of asteroids (default: 20)
- `diameter_min`: Minimum diameter in meters
- `diameter_max`: Maximum diameter in meters
- `potentially_hazardous`: Boolean filter

**Response**:
```json
{
  "asteroids": [
    {
      "id": "2000433",
      "name": "433 Eros",
      "diameter_km": 16.84,
      "orbital_period": 643.219,
      "eccentricity": 0.2229,
      "inclination": 10.83,
      "potentially_hazardous": false,
      "close_approaches": [...],
      "absolute_magnitude": 11.16
    }
  ]
}
```

#### 2. `/api/neo/asteroid/{id}` (GET) 
**Purpose**: Get detailed asteroid data for specific NEO
**Response**: Full orbital parameters and physical characteristics

#### 3. `/api/simulation/run` (POST)
**Purpose**: Enhanced simulation using real NASA asteroid data
**Request**:
```json
{
  "asteroid_id": "2000433", // NASA NEO ID
  "impact_location": {"lat": 40.7128, "lng": -74.0060},
  "impact_velocity": 20.5, // km/s
  "impact_angle": 45
}
```

#### 4. `/api/neo/close-approaches` (GET)
**Purpose**: Get asteroids with upcoming close approaches
**Parameters**: 
- `start_date`: YYYY-MM-DD
- `end_date`: YYYY-MM-DD

### Enhanced Physics Calculations

#### Real Orbital Mechanics Integration
1. **Velocity Calculation**: Use orbital elements to calculate realistic impact velocities
2. **Mass Estimation**: NASA diameter + density models for accurate mass
3. **Impact Energy**: E = ½mv² with real asteroid parameters
4. **Crater Scaling**: Use real asteroid composition and target material

#### Enhanced Impact Modeling
```python
# Real asteroid parameters from NASA
orbital_velocity = calculate_orbital_velocity(semi_major_axis, eccentricity)
escape_velocity = 11.2  # km/s Earth escape velocity
impact_velocity = sqrt(orbital_velocity² + escape_velocity²)

# Enhanced crater calculation with real composition
crater_diameter = scaling_law(kinetic_energy, target_density, asteroid_density)
```

### Frontend Integration Changes

#### Replace Mock Data With Real NASA Data
1. **Scenario Selection**: Real asteroids (Eros, Bennu, Apophis, etc.)
2. **Asteroid Browser**: Search/filter real NASA NEO database
3. **Real-time Updates**: Show asteroids approaching Earth
4. **Orbital Visualization**: Display real orbital paths

#### New Frontend Components
1. **AsteroidBrowser**: Browse NASA NEO database
2. **OrbitVisualization**: 3D orbital mechanics display
3. **RealTimeTracker**: Live asteroid approach data
4. **EnhancedResults**: Scientific accuracy indicators

### Database Schema Changes

#### Asteroid Table
```sql
CREATE TABLE asteroids (
    id VARCHAR PRIMARY KEY,  -- NASA NEO ID
    name VARCHAR NOT NULL,
    diameter_km FLOAT,
    orbital_period_days FLOAT,
    eccentricity FLOAT,
    inclination_deg FLOAT,
    absolute_magnitude FLOAT,
    potentially_hazardous BOOLEAN,
    last_updated TIMESTAMP,
    nasa_data JSONB  -- Store complete NASA response
);
```

#### Enhanced Simulations Table
```sql
CREATE TABLE simulations (
    id UUID PRIMARY KEY,
    asteroid_id VARCHAR REFERENCES asteroids(id),
    impact_location JSONB,
    calculated_velocity FLOAT,
    impact_angle FLOAT,
    results JSONB,
    nasa_enhanced BOOLEAN DEFAULT true,
    created_at TIMESTAMP
);
```

### Real Data Enhancement Features

#### 1. Scientific Accuracy Mode
- Use real orbital mechanics for velocity calculations
- Real asteroid composition data for impact modeling
- NASA-validated size and mass estimates

#### 2. Real Asteroid Scenarios
- **433 Eros**: Large S-type asteroid
- **101955 Bennu**: OSIRIS-REx target asteroid  
- **99942 Apophis**: 2029 close approach asteroid
- **1566 Icarus**: High-velocity Apollo asteroid

#### 3. Live Asteroid Tracking
- Show real asteroids currently approaching Earth
- Display NASA close-approach data
- Alert system for potentially hazardous asteroids

### API Rate Limiting & Caching
- Cache NASA responses for 24 hours
- Implement request throttling (1000/hour NASA limit)
- Background sync for asteroid database updates

### Error Handling
- Graceful fallback to enhanced mock data if NASA API unavailable
- Retry logic for failed NASA API calls
- Data validation for orbital parameters

### Testing Strategy
1. **Real Data Validation**: Compare calculations with NASA JPL
2. **API Integration Tests**: Mock NASA responses
3. **Performance Tests**: Handle large asteroid datasets
4. **Scientific Accuracy**: Validate physics calculations

## Implementation Priority
1. NASA NEO API integration backend
2. Enhanced physics calculations
3. Real asteroid database
4. Frontend real data integration
5. Advanced visualization features

This integration will transform the simulator from a demonstration tool into a scientifically accurate asteroid impact modeling system using real NASA data.