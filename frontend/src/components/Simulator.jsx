import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Slider } from './ui/slider';
import { Separator } from './ui/separator';
import { useToast } from '../hooks/use-toast';
import { 
  Zap, 
  Mountain, 
  Thermometer, 
  Radio, 
  Users, 
  TrendingDown, 
  Globe, 
  Clock,
  Flame,
  Building,
  DollarSign,
  UserX,
  MapPin,
  Play,
  Save,
  Share2,
  RotateCcw,
} from 'lucide-react';
import { predefinedScenarios, calculateImpact, compositionData, locationSuggestions, historicalComparisons, educationalContent } from '../data/mock';

const Simulator = () => {
  const { toast } = useToast();
  const [activeTab, setActiveTab] = useState('immediate');
  const [simulationResults, setSimulationResults] = useState(null);
  const [selectedScenario, setSelectedScenario] = useState('');
  const [customMode, setCustomMode] = useState(false);
  // Removed showComparison and showEducation state variables
  const [savedSimulations, setSavedSimulations] = useState([]);
  
  const [asteroidParams, setAsteroidParams] = useState({
    diameter: 1000,
    speed: 20,
    angle: 45,
    composition: 'rocky',
    location: { lat: 40.7128, lng: -74.0060, name: 'New York City' }
  });

  useEffect(() => {
    // Load default scenario on mount
    loadScenario('continental-crisis');
    
    // Load saved simulations from localStorage
    const saved = localStorage.getItem('asteroidSimulations');
    if (saved) {
      setSavedSimulations(JSON.parse(saved));
    }
  }, []);

  const loadScenario = (scenarioId) => {
    const scenario = predefinedScenarios.find(s => s.id === scenarioId);
    if (scenario) {
      setAsteroidParams({
        ...scenario.asteroidParams,
        density: compositionData[scenario.asteroidParams.composition].density
      });
      setSelectedScenario(scenarioId);
      setCustomMode(false);
    }
  };

  const runSimulation = () => {
    const params = {
      ...asteroidParams,
      density: compositionData[asteroidParams.composition].density
    };
    
    const results = calculateImpact(params);
    setSimulationResults(results);
    
    toast({
      title: "Simulation Complete",
      description: `Impact calculated for ${asteroidParams.location.name}`,
    });
  };

  const saveSimulation = () => {
    if (!simulationResults) return;
    
    const simulation = {
      id: Date.now(),
      name: customMode ? 'Custom Simulation' : predefinedScenarios.find(s => s.id === selectedScenario)?.name || 'Simulation',
      params: asteroidParams,
      results: simulationResults,
      timestamp: new Date().toLocaleString()
    };
    
    const updated = [...savedSimulations, simulation];
    setSavedSimulations(updated);
    localStorage.setItem('asteroidSimulations', JSON.stringify(updated));
    
    toast({
      title: "Simulation Saved",
      description: "Your simulation has been saved locally",
    });
  };

  const shareSimulation = () => {
    if (!simulationResults) return;
    
    const shareData = {
      title: 'Asteroid Impact Simulation Results',
      text: `Simulated ${asteroidParams.diameter}m asteroid impact on ${asteroidParams.location.name}`,
      url: window.location.href
    };
    
    if (navigator.share) {
      navigator.share(shareData);
    } else {
      navigator.clipboard.writeText(JSON.stringify(asteroidParams));
      toast({
        title: "Parameters Copied",
        description: "Simulation parameters copied to clipboard",
      });
    }
  };

  const resetSimulation = () => {
    setAsteroidParams({
      diameter: 100,
      speed: 15,
      angle: 45,
      composition: 'rocky',
      location: { lat: 40.7128, lng: -74.0060, name: 'New York City' }
    });
    setSimulationResults(null);
    setSelectedScenario('');
    setCustomMode(true);
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'catastrophic': return 'bg-red-500';
      case 'severe': return 'bg-orange-500';
      case 'moderate': return 'bg-yellow-500';
      case 'minor': return 'bg-green-500';
      default: return 'bg-gray-500';
    }
  };

  const getSeverityTextColor = (severity) => {
    switch (severity) {
      case 'catastrophic': return 'text-red-400';
      case 'severe': return 'text-orange-400';
      case 'moderate': return 'text-yellow-400';
      case 'minor': return 'text-green-400';
      default: return 'text-gray-400';
    }
  };

  const getIcon = (type) => {
    const iconProps = { size: 20, className: 'text-orange-400' };
    switch (type) {
      case 'crater': return <Mountain {...iconProps} />;
      case 'energy': return <Zap {...iconProps} />;
      case 'temperature': return <Thermometer {...iconProps} />;
      case 'fireball': return <Flame {...iconProps} />;
      case 'shockwave': return <Radio {...iconProps} />;
      case 'debris': return <TrendingDown {...iconProps} />;
      case 'seismic': return <Globe {...iconProps} />;
      case 'dust': return <Globe {...iconProps} />;
      case 'casualties': return <UserX {...iconProps} />;
      case 'infrastructure': return <Building {...iconProps} />;
      case 'economic': return <DollarSign {...iconProps} />;
      case 'refugees': return <Users {...iconProps} />;
      default: return <Globe {...iconProps} />;
    }
  };

  const renderMetricCard = (key, metric, type) => (
    <Card key={key} className="bg-black/60 border-orange-500/30 hover:bg-black/80 transition-all duration-300 backdrop-blur-md hover:shadow-lg hover:shadow-orange-500/20">
      <CardContent className="p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            {getIcon(type)}
            <h3 className="font-semibold text-white capitalize">
              {key.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase())}
            </h3>
          </div>
          <Badge className={`${getSeverityColor(metric.severity)} text-white border-0`}>
            {metric.severity}
          </Badge>
        </div>
        
        <div className="space-y-3">
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold text-white">
              {metric.value}
            </span>
            <span className="text-sm text-gray-400">{metric.unit}</span>
          </div>
          
          <Progress 
            value={metric.progress} 
            className="h-2 bg-gray-700"
          />
          
          <p className="text-sm text-gray-300 leading-relaxed">
            {metric.description}
          </p>
          
          <div className="flex gap-1 mt-2">
            {[1, 2, 3, 4, 5].map(dot => (
              <div 
                key={dot}
                className={`w-2 h-2 rounded-full ${
                  dot <= Math.ceil(metric.progress / 20) 
                    ? getSeverityColor(metric.severity).replace('bg-', 'bg-') 
                    : 'bg-gray-600'
                }`}
              />
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );

  return (
    <div className="min-h-screen bg-black relative overflow-hidden">
      {/* Animated Stars Background */}
      <div className="absolute inset-0">
        <div className="absolute inset-0 bg-gradient-to-b from-gray-900/50 via-blue-950/30 to-black"></div>
        {/* Star field */}
        {[...Array(100)].map((_, i) => (
          <div
            key={i}
            className="absolute animate-pulse"
            style={{
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
              width: Math.random() > 0.7 ? '2px' : '1px',
              height: Math.random() > 0.7 ? '2px' : '1px',
              backgroundColor: Math.random() > 0.5 ? '#ffffff' : '#fbbf24',
              animationDelay: `${Math.random() * 3}s`,
              animationDuration: `${2 + Math.random() * 3}s`
            }}
          />
        ))}
        {/* Larger glowing stars */}
        {[...Array(20)].map((_, i) => (
          <div
            key={`glow-${i}`}
            className="absolute rounded-full animate-pulse"
            style={{
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
              width: '3px',
              height: '3px',
              backgroundColor: '#f97316',
              boxShadow: '0 0 6px #f97316, 0 0 12px #f97316',
              animationDelay: `${Math.random() * 4}s`,
              animationDuration: `${3 + Math.random() * 2}s`
            }}
          />
        ))}
      </div>

      {/* Hero Section */}
      <div className="relative z-10 overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-orange-600/20 via-red-600/20 to-yellow-600/20 backdrop-blur-sm" />
        <div className="relative max-w-7xl mx-auto px-4 py-16 text-center">
          <div className="flex items-center justify-center gap-2 mb-4">
            <Zap className="text-orange-500 text-4xl" size={40} />
            <h1 className="text-5xl font-bold text-white">
              Asteroid Impact Simulator
            </h1>
          </div>
          <p className="text-xl text-gray-300 mb-8 max-w-3xl mx-auto">
            Experience the devastating power of cosmic collisions and witness the aftermath of an asteroid impact on Earth
          </p>
          
          {/* Buttons removed as requested */}
        </div>
      </div>

      <div className="relative z-10 max-w-7xl mx-auto px-4 pb-16">

        {/* Educational and Historical content sections removed */}

        {/* Controls Section */}
        <Card className="mb-8 bg-gray-900/80 border-orange-500/30 backdrop-blur-md">
          <CardHeader>
            <CardTitle className="text-white">Simulation Controls</CardTitle>
            <div className="flex gap-2">
              <Button 
                onClick={runSimulation}
                className="bg-orange-600 hover:bg-orange-700 text-white"
              >
                <Play className="mr-2" size={16} />
                Run Simulation
              </Button>
              <Button onClick={resetSimulation} variant="outline" className="border-orange-500/50 text-orange-300 hover:bg-orange-500/10 backdrop-blur-sm">
                <RotateCcw className="mr-2" size={16} />
                Reset
              </Button>
              {simulationResults && (
                <>
                  <Button onClick={saveSimulation} variant="outline" className="border-orange-500/50 text-orange-300 hover:bg-orange-500/10 backdrop-blur-sm">
                    <Save className="mr-2" size={16} />
                    Save
                  </Button>
                  <Button onClick={shareSimulation} variant="outline" className="border-orange-500/50 text-orange-300 hover:bg-orange-500/10 backdrop-blur-sm">
                    <Share2 className="mr-2" size={16} />
                    Share
                  </Button>
                </>
              )}
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Scenario Selection */}
            <div className="grid md:grid-cols-2 gap-6">
              <div>
                <Label className="text-white mb-2 block">Predefined Scenarios</Label>
                <Select value={selectedScenario} onValueChange={loadScenario}>
                  <SelectTrigger className="bg-black/50 border-orange-500/30 text-white backdrop-blur-md">
                    <SelectValue placeholder="Select a scenario" />
                  </SelectTrigger>
                  <SelectContent className="bg-black/90 border-orange-500/30 backdrop-blur-md">
                    {predefinedScenarios.map(scenario => (
                      <SelectItem key={scenario.id} value={scenario.id} className="text-white">
                        {scenario.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Button 
                  onClick={() => setCustomMode(true)}
                  variant="link" 
                  className="text-orange-400 p-0 mt-2"
                >
                  Or customize parameters →
                </Button>
              </div>
              
              <div>
                <Label className="text-white mb-2 block">Impact Location</Label>
                <Select 
                  value={asteroidParams.location.name} 
                  onValueChange={(name) => {
                    const location = locationSuggestions.find(l => l.name === name);
                    if (location) {
                      setAsteroidParams(prev => ({ ...prev, location }));
                    }
                  }}
                >
                  <SelectTrigger className="bg-black/50 border-orange-500/30 text-white backdrop-blur-md">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-black/90 border-orange-500/30 backdrop-blur-md">
                    {locationSuggestions.map(location => (
                      <SelectItem key={location.name} value={location.name} className="text-white">
                        <div className="flex items-center gap-2">
                          <MapPin size={14} />
                          {location.name}
                          {location.population > 0 && (
                            <span className="text-xs text-gray-400">({(location.population / 1000000).toFixed(1)}M pop.)</span>
                          )}
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Custom Parameters */}
            {customMode && (
              <div className="space-y-4 p-4 bg-black/40 rounded-lg border border-orange-500/30 backdrop-blur-md">
                <h4 className="font-semibold text-white">Custom Asteroid Parameters</h4>
                
                <div className="grid md:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <div>
                      <Label className="text-white">Diameter: {asteroidParams.diameter}m</Label>
                      <Slider
                        value={[asteroidParams.diameter]}
                        onValueChange={([value]) => 
                          setAsteroidParams(prev => ({ ...prev, diameter: value }))
                        }
                        min={10}
                        max={2000}
                        step={10}
                        className="mt-2"
                      />
                    </div>
                    
                    <div>
                      <Label className="text-white">Speed: {asteroidParams.speed} km/s</Label>
                      <Slider
                        value={[asteroidParams.speed]}
                        onValueChange={([value]) => 
                          setAsteroidParams(prev => ({ ...prev, speed: value }))
                        }
                        min={5}
                        max={50}
                        step={0.5}
                        className="mt-2"
                      />
                    </div>
                  </div>
                  
                  <div className="space-y-4">
                    <div>
                      <Label className="text-white">Impact Angle: {asteroidParams.angle}°</Label>
                      <Slider
                        value={[asteroidParams.angle]}
                        onValueChange={([value]) => 
                          setAsteroidParams(prev => ({ ...prev, angle: value }))
                        }
                        min={15}
                        max={90}
                        step={5}
                        className="mt-2"
                      />
                    </div>
                    
                    <div>
                      <Label className="text-white">Composition</Label>
                      <Select 
                        value={asteroidParams.composition} 
                        onValueChange={(composition) => 
                          setAsteroidParams(prev => ({ ...prev, composition }))
                        }
                      >
                        <SelectTrigger className="bg-black/50 border-orange-500/30 text-white mt-2 backdrop-blur-md">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent className="bg-black/90 border-orange-500/30 backdrop-blur-md">
                          {Object.entries(compositionData).map(([key, data]) => (
                            <SelectItem key={key} value={key} className="text-white">
                              {key.charAt(0).toUpperCase() + key.slice(1)} - {data.description}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Results Section */}
        {simulationResults && (
          <div className="space-y-6">
            {/* Event Summary */}
            <Card className="bg-gradient-to-r from-red-900/40 to-orange-900/40 border-orange-500/50 backdrop-blur-md shadow-2xl shadow-red-500/20">
              <CardContent className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <Badge className="bg-red-600 text-white px-4 py-1 text-sm font-semibold">
                    SEVERE EVENT
                  </Badge>
                </div>
                <h2 className="text-3xl font-bold text-white mb-4">Continental Crisis</h2>
                <p className="text-gray-300 text-lg">
                  A {asteroidParams.diameter}m {asteroidParams.composition} asteroid impacts {asteroidParams.location.name} at {asteroidParams.speed} km/s, 
                  creating devastating effects across a massive radius.
                </p>
              </CardContent>
            </Card>

            {/* Tabbed Results */}
            <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
              <TabsList className="bg-black/60 border-orange-500/30 p-1 backdrop-blur-md">
                <TabsTrigger 
                  value="immediate" 
                  className="data-[state=active]:bg-orange-600 data-[state=active]:text-white text-gray-300"
                >
                  <Zap className="mr-2" size={16} />
                  Immediate
                </TabsTrigger>
                <TabsTrigger 
                  value="environmental" 
                  className="data-[state=active]:bg-orange-600 data-[state=active]:text-white text-gray-300"
                >
                  <Globe className="mr-2" size={16} />
                  Environmental
                </TabsTrigger>
                <TabsTrigger 
                  value="humanImpact" 
                  className="data-[state=active]:bg-orange-600 data-[state=active]:text-white text-gray-300"
                >
                  <Users className="mr-2" size={16} />
                  Human Impact
                </TabsTrigger>
                <TabsTrigger 
                  value="timeline" 
                  className="data-[state=active]:bg-orange-600 data-[state=active]:text-white text-gray-300"
                >
                  <Clock className="mr-2" size={16} />
                  Timeline
                </TabsTrigger>
              </TabsList>

              <TabsContent value="immediate" className="space-y-6">
                <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {Object.entries(simulationResults.immediate).map(([key, metric]) => 
                    renderMetricCard(key, metric, key === 'craterDiameter' ? 'crater' : 
                                   key === 'energy' ? 'energy' : 
                                   key === 'temperature' ? 'temperature' : 'fireball')
                  )}
                </div>
              </TabsContent>

              <TabsContent value="environmental" className="space-y-6">
                <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {Object.entries(simulationResults.environmental).map(([key, metric]) => 
                    renderMetricCard(key, metric, key === 'shockwaveRadius' ? 'shockwave' : 
                                   key === 'debrisFieldRadius' ? 'debris' : 
                                   key === 'seismicMagnitude' ? 'seismic' : 'dust')
                  )}
                </div>
              </TabsContent>

              <TabsContent value="humanImpact" className="space-y-6">
                <div className="grid md:grid-cols-2 gap-6">
                  {Object.entries(simulationResults.humanImpact).map(([key, metric]) => 
                    renderMetricCard(key, metric, key === 'casualtiesImmediate' ? 'casualties' : 
                                   key === 'infrastructureDamage' ? 'infrastructure' : 
                                   key === 'economicLoss' ? 'economic' : 'refugees')
                  )}
                </div>
              </TabsContent>

              <TabsContent value="timeline" className="space-y-6">
                <Card className="bg-black/60 border-orange-500/30 backdrop-blur-md">
                  <CardHeader>
                    <CardTitle className="text-white">Impact Timeline</CardTitle>
                    <CardDescription className="text-gray-300">
                      Sequence of events following the asteroid impact
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {Object.entries(simulationResults.timeline).map(([key, event], index) => (
                        <div key={key} className="flex gap-4 items-start">
                          <div className="flex flex-col items-center">
                            <div className="w-3 h-3 bg-orange-500 rounded-full" />
                            {index < Object.keys(simulationResults.timeline).length - 1 && (
                              <div className="w-0.5 h-12 bg-gray-600 mt-2" />
                            )}
                          </div>
                          <div className="flex-1 pb-8">
                            <div className="font-semibold text-orange-400">{event.time}</div>
                            <div className="text-white">{event.event}</div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
          </div>
        )}

        {/* Saved Simulations */}
        {savedSimulations.length > 0 && (
          <Card className="mt-8 bg-black/60 border-orange-500/30 backdrop-blur-md">
            <CardHeader>
              <CardTitle className="text-white">Saved Simulations</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                {savedSimulations.map(sim => (
                  <div key={sim.id} className="p-4 bg-black/40 rounded border border-orange-500/30 backdrop-blur-sm">
                    <h4 className="font-semibold text-white">{sim.name}</h4>
                    <p className="text-sm text-gray-300">
                      {sim.params.diameter}m {sim.params.composition} → {sim.params.location.name}
                    </p>
                    <p className="text-xs text-gray-500">{sim.timestamp}</p>
                    <Button 
                      onClick={() => {
                        setAsteroidParams(sim.params);
                        setSimulationResults(sim.results);
                        setCustomMode(true);
                      }}
                      size="sm" 
                      className="mt-2 bg-orange-600 hover:bg-orange-700 text-white"
                    >
                      Load Simulation
                    </Button>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

export default Simulator;