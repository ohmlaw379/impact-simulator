// Mock data for Asteroid Impact Simulator

export const predefinedScenarios = [
  {
    id: 'continental-crisis',
    name: 'Continental Crisis',
    description: 'A 1000.0m rocky asteroid impacts New York City at 20.0 km/s, creating a 16.3km crater and devastating effects across 1833km radius.',
    severity: 'SEVERE EVENT',
    asteroidParams: {
      diameter: 1000,
      speed: 20.0,
      angle: 45,
      composition: 'rocky',
      density: 2600,
      location: { lat: 40.7128, lng: -74.0060, name: 'New York City' }
    }
  },
  {
    id: 'regional-disaster',
    name: 'Regional Disaster',
    description: 'A 500m iron asteroid strikes Los Angeles at 15 km/s, causing severe regional damage.',
    severity: 'HIGH EVENT',
    asteroidParams: {
      diameter: 500,
      speed: 15.0,
      angle: 30,
      composition: 'iron',
      density: 7800,
      location: { lat: 34.0522, lng: -118.2437, name: 'Los Angeles' }
    }
  },
  {
    id: 'city-destroyer',
    name: 'City Destroyer',
    description: 'A 200m stony asteroid impacts London at 12 km/s, devastating the metropolitan area.',
    severity: 'MODERATE EVENT',
    asteroidParams: {
      diameter: 200,
      speed: 12.0,
      angle: 60,
      composition: 'stony',
      density: 3500,
      location: { lat: 51.5074, lng: -0.1278, name: 'London' }
    }
  }
];

export const historicalComparisons = [
  {
    name: 'Tunguska Event (1908)',
    energy: 15, // megatons
    crater: 0, // no crater
    description: 'Flattened 2,000 km² of forest in Siberia'
  },
  {
    name: 'Chicxulub Impact',
    energy: 100000000, // 100 million megatons
    crater: 150000, // 150km
    description: 'Caused the extinction of dinosaurs 66 million years ago'
  },
  {
    name: 'Hiroshima Bomb',
    energy: 0.015, // megatons
    crater: 0,
    description: 'Nuclear weapon dropped in 1945'
  }
];

export const educationalContent = {
  asteroidTypes: {
    rocky: {
      name: 'Rocky (Stony)',
      density: '2.0-4.0 g/cm³',
      composition: 'Silicate minerals, similar to terrestrial rocks',
      percentage: '92.8% of all asteroids'
    },
    iron: {
      name: 'Iron (Metallic)', 
      density: '7.0-8.0 g/cm³',
      composition: 'Iron-nickel alloy',
      percentage: '5.7% of all asteroids'
    },
    stony: {
      name: 'Stony-Iron',
      density: '4.0-6.0 g/cm³', 
      composition: 'Mixed silicate and metal',
      percentage: '1.5% of all asteroids'
    }
  },
  impactPhysics: {
    energy: 'Kinetic energy = ½ × mass × velocity²',
    crater: 'Crater diameter ≈ (energy/target_strength)^0.25',
    shockwave: 'Travels at supersonic speeds, causing structural damage',
    fireball: 'Superheated plasma expands rapidly from impact site'
  }
};

// Function to calculate impact effects (simplified physics)
export const calculateImpact = (params) => {
  const { diameter, speed, density, composition, location } = params;
  
  // Basic calculations (simplified)
  const radius = diameter / 2;
  const volume = (4/3) * Math.PI * Math.pow(radius, 3);
  const mass = volume * density; // kg
  const velocity = speed * 1000; // m/s
  const kineticEnergy = 0.5 * mass * Math.pow(velocity, 2); // joules
  const energyMegatons = kineticEnergy / (4.184 * Math.pow(10, 15)); // convert to megatons TNT
  
  // Crater diameter (simplified Holsapple & Schmidt scaling)
  const craterDiameter = Math.pow(energyMegatons / 1000, 0.25) * diameter * 0.1;
  
  // Temperature at impact (simplified)
  const temperature = Math.min(50000, velocity * 0.5 + Math.pow(diameter, 0.5) * 1000);
  
  // Shockwave radius (empirical formula)
  const shockwaveRadius = Math.pow(energyMegatons, 0.33) * 10;
  
  // Seismic magnitude
  const seismicMagnitude = Math.min(10, Math.log10(energyMegatons) + 2);
  
  // Debris field radius
  const debrisRadius = shockwaveRadius * 3;
  
  // Fireball radius
  const fireballRadius = Math.pow(energyMegatons, 0.4) * 0.5;
  
  return {
    immediate: {
      craterDiameter: {
        value: craterDiameter.toFixed(1),
        unit: 'km',
        severity: craterDiameter > 10 ? 'catastrophic' : craterDiameter > 5 ? 'severe' : craterDiameter > 1 ? 'moderate' : 'minor',
        description: `The impact crater formed by the asteroid collision, with rim heights reaching ${(craterDiameter * 0.1).toFixed(0)}m above ground level.`,
        progress: Math.min(100, (craterDiameter / 20) * 100)
      },
      energy: {
        value: Math.round(energyMegatons).toLocaleString(),
        unit: 'megatons TNT',
        severity: energyMegatons > 50000 ? 'catastrophic' : energyMegatons > 10000 ? 'severe' : energyMegatons > 1000 ? 'moderate' : 'minor',
        description: `Total kinetic energy released upon impact, equivalent to ${Math.round(energyMegatons)} megatons of TNT explosives.`,
        progress: Math.min(100, (energyMegatons / 100000) * 100)
      },
      temperature: {
        value: Math.round(temperature).toLocaleString(),
        unit: '°C', 
        severity: temperature > 8000 ? 'catastrophic' : temperature > 3000 ? 'severe' : temperature > 1000 ? 'moderate' : 'minor',
        description: `Peak temperature at impact site, hot enough to vaporize rock and create a plasma fireball.`,
        progress: Math.min(100, (temperature / 50000) * 100)
      },
      fireballRadius: {
        value: fireballRadius.toFixed(1),
        unit: 'km',
        severity: fireballRadius > 50 ? 'catastrophic' : fireballRadius > 20 ? 'severe' : fireballRadius > 5 ? 'moderate' : 'minor',
        description: `Radius of the superheated fireball, causing thermal radiation burns and igniting fires.`,
        progress: Math.min(100, (fireballRadius / 100) * 100)
      }
    },
    environmental: {
      shockwaveRadius: {
        value: shockwaveRadius.toFixed(1),
        unit: 'km',
        severity: shockwaveRadius > 1000 ? 'catastrophic' : shockwaveRadius > 500 ? 'severe' : shockwaveRadius > 100 ? 'moderate' : 'minor',
        description: `Radius of destructive shockwave causing building collapse and seismic damage.`,
        progress: Math.min(100, (shockwaveRadius / 2000) * 100)
      },
      debrisFieldRadius: {
        value: debrisRadius.toFixed(1),
        unit: 'km',
        severity: debrisRadius > 3000 ? 'catastrophic' : debrisRadius > 1500 ? 'severe' : debrisRadius > 500 ? 'moderate' : 'minor',
        description: `Area covered by ejected debris and impact fragments raining from the sky.`,
        progress: Math.min(100, (debrisRadius / 6000) * 100)
      },
      seismicMagnitude: {
        value: seismicMagnitude.toFixed(1),
        unit: 'magnitude',
        severity: seismicMagnitude > 7 ? 'catastrophic' : seismicMagnitude > 6 ? 'severe' : seismicMagnitude > 4 ? 'moderate' : 'minor',
        description: `Earthquake magnitude generated by the impact, felt across continental distances.`,
        progress: Math.min(100, (seismicMagnitude / 10) * 100)
      },
      atmosphericDust: {
        value: (energyMegatons * 0.001).toFixed(2),
        unit: 'billion tons',
        severity: energyMegatons > 10000 ? 'catastrophic' : energyMegatons > 1000 ? 'severe' : 'moderate',
        description: `Dust and debris ejected into the atmosphere, potentially blocking sunlight.`,
        progress: Math.min(100, (energyMegatons / 100000) * 100)
      }
    },
    humanImpact: {
      casualtiesImmediate: {
        value: Math.round(Math.pow(shockwaveRadius, 2) * 100).toLocaleString(),
        unit: 'estimated casualties',
        severity: shockwaveRadius > 500 ? 'catastrophic' : shockwaveRadius > 200 ? 'severe' : shockwaveRadius > 50 ? 'moderate' : 'minor',
        description: `Estimated immediate casualties from thermal radiation, shockwave, and debris.`,
        progress: Math.min(100, (shockwaveRadius / 1000) * 100)
      },
      infrastructureDamage: {
        value: Math.round(shockwaveRadius * 2).toLocaleString(),
        unit: 'km radius affected',
        severity: shockwaveRadius > 300 ? 'catastrophic' : shockwaveRadius > 150 ? 'severe' : 'moderate',
        description: `Radius of severe infrastructure damage including buildings, roads, and utilities.`,
        progress: Math.min(100, (shockwaveRadius / 1000) * 100)
      },
      economicLoss: {
        value: Math.round(energyMegatons * 10).toLocaleString(),
        unit: 'billion USD',
        severity: energyMegatons > 10000 ? 'catastrophic' : energyMegatons > 1000 ? 'severe' : 'moderate',
        description: `Estimated economic losses from infrastructure damage and business disruption.`,
        progress: Math.min(100, (energyMegatons / 100000) * 100)
      },
      refugeePopulation: {
        value: Math.round(Math.pow(debrisRadius, 2) * 50).toLocaleString(),
        unit: 'displaced persons',
        severity: debrisRadius > 1000 ? 'catastrophic' : debrisRadius > 500 ? 'severe' : 'moderate',
        description: `Population requiring evacuation and temporary relocation due to impact effects.`,
        progress: Math.min(100, (debrisRadius / 3000) * 100)
      }
    },
    timeline: {
      t0: { time: '0 seconds', event: 'Initial impact and crater formation' },
      t1: { time: '10 seconds', event: 'Fireball expansion and thermal radiation peak' },
      t2: { time: '2 minutes', event: 'Shockwave reaches maximum extent' },
      t3: { time: '10 minutes', event: 'Debris begins falling back to Earth' },
      t4: { time: '1 hour', event: 'Seismic waves circle the globe' },
      t5: { time: '24 hours', event: 'Atmospheric dust affects regional weather' },
      t6: { time: '1 week', event: 'Global atmospheric effects become apparent' },
      t7: { time: '1 month', event: 'Ecological and climate impacts emerge' },
      t8: { time: '1 year', event: 'Long-term environmental recovery begins' }
    }
  };
};

export const compositionData = {
  rocky: { density: 2600, strength: 'medium', description: 'Most common type, similar to Earth rocks' },
  iron: { density: 7800, strength: 'high', description: 'Dense metallic composition, creates deeper craters' },
  stony: { density: 3500, strength: 'medium-high', description: 'Mixed composition of rock and metal' },
  icy: { density: 1000, strength: 'low', description: 'Comet-like composition, mostly water ice' }
};

export const locationSuggestions = [
  { name: 'New York City', lat: 40.7128, lng: -74.0060, population: 8400000 },
  { name: 'Los Angeles', lat: 34.0522, lng: -118.2437, population: 4000000 },
  { name: 'London', lat: 51.5074, lng: -0.1278, population: 9000000 },
  { name: 'Tokyo', lat: 35.6762, lng: 139.6503, population: 14000000 },
  { name: 'Mumbai', lat: 19.0760, lng: 72.8777, population: 20400000 },
  { name: 'São Paulo', lat: -23.5505, lng: -46.6333, population: 12300000 },
  { name: 'Ocean Impact', lat: 0, lng: -30, population: 0 }
];