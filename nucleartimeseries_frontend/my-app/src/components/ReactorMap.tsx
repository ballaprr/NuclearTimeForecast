// ReactorMap.tsx
import React, { useEffect, useState } from "react";
import Plot from "react-plotly.js";
import axios from "axios";

interface ReactorStatus {
  report_date: string;
  unit: string;
  power: number;
  reactor: number;
}

interface Reactor {
  name: string;
  region: string;
  latitude: number;
  longitude: number;
  reactorstatus: ReactorStatus[];
}

interface ReactorForecast {
  df: string;
  yhat: number;
  yhat_lower: number;
  yhat_upper: number;
  image_url: string;
}

interface ReactorDetail {
  report_date: string;
  unit: string;
  power: number;
  reactorforecast_set: ReactorForecast[];
  stuboutage_set: any[];
  stuboutage: boolean;
}

interface ReactorMapProps {
  date?: string;
}

export default function ReactorMap({ date = "2025-01-10" }: ReactorMapProps) {
  const [reactors, setReactors] = useState<Reactor[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedReactor, setSelectedReactor] = useState<ReactorDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [showModal, setShowModal] = useState(false);

  useEffect(() => {
    setLoading(true);
    setError(null);
    
    axios.get(`http://localhost:8000/api/reactor/${date}/`)
      .then((res) => {
        setReactors(res.data);
        setLoading(false);
      })
      .catch((err) => {
        setError(`Failed to fetch data: ${err.message}`);
        setLoading(false);
      });
  }, [date]);

  if (loading) {
    return <div style={{ 
      textAlign: 'center', 
      padding: '2rem',
      color: 'rgba(255, 255, 255, 0.90)',
      backgroundColor: 'rgb(35, 40, 50)',
      borderRadius: '8px',
      border: '1px solid rgba(255, 255, 255, 0.1)'
    }}>Loading reactor data...</div>;
  }

  if (error) {
    return <div style={{ 
      textAlign: 'center', 
      padding: '2rem', 
      color: '#ff6b6b',
      backgroundColor: 'rgb(35, 40, 50)',
      borderRadius: '8px',
      border: '1px solid rgba(255, 107, 107, 0.2)'
    }}>Error: {error}</div>;
  }

  if (reactors.length === 0) {
    return <div style={{ 
      textAlign: 'center', 
      padding: '2rem',
      color: 'rgba(255, 255, 255, 0.90)',
      backgroundColor: 'rgb(35, 40, 50)',
      borderRadius: '8px',
      border: '1px solid rgba(255, 255, 255, 0.1)'
    }}>No reactor data found for {date}</div>;
  }

  // Extract reactor data with power levels
  const rawReactorData = reactors.flatMap(reactor => 
    reactor.reactorstatus.map(status => ({
      name: reactor.name,
      latitude: reactor.latitude,
      longitude: reactor.longitude,
      power: status.power,
      unit: status.unit,
      region: reactor.region
    }))
  );

  // Group reactors by location and apply offset pattern
  const locationGroups = new Map();
  rawReactorData.forEach(reactor => {
    const key = `${reactor.latitude},${reactor.longitude}`;
    if (!locationGroups.has(key)) {
      locationGroups.set(key, []);
    }
    locationGroups.get(key).push(reactor);
  });

  const reactorData = Array.from(locationGroups.values()).flatMap(group => {
    if (group.length === 1) {
      return group;
    }
    // Apply offset pattern for multiple units
    const offsetDistance = 0.02;
    const patterns = [[0, 0], [offsetDistance, 0], [0, offsetDistance], [-offsetDistance, 0], [0, -offsetDistance]];
    
    return group.map((reactor: any, index: number) => ({
      ...reactor,
      latitude: reactor.latitude + (patterns[index] || [0, 0])[1],
      longitude: reactor.longitude + (patterns[index] || [0, 0])[0]
    }));
  });

  const fetchReactorDetail = async (reactorId: number) => {
    setDetailLoading(true);
    try {
      const response = await axios.get(`http://localhost:8000/api/reactor/${date}/${reactorId}/`);
      setSelectedReactor(response.data);
      setShowModal(true);
    } catch (error) {
      console.error('Failed to fetch reactor details:', error);
    } finally {
      setDetailLoading(false);
    }
  };

  const ReactorDetailModal = () => {
    if (!showModal || !selectedReactor) return null;

    return (
      <div style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        zIndex: 1000
      }}>
        <div style={{
          backgroundColor: 'rgb(35, 40, 50)',
          padding: '2rem',
          borderRadius: '12px',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          maxWidth: '600px',
          width: '90%',
          maxHeight: '80vh',
          overflowY: 'auto',
          color: 'white'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
            <h2 style={{ margin: 0, color: 'rgba(255, 255, 255, 0.95)' }}>
              {selectedReactor.unit}
            </h2>
            <button
              onClick={() => setShowModal(false)}
              style={{
                background: 'none',
                border: 'none',
                color: 'rgba(255, 255, 255, 0.7)',
                fontSize: '1.5rem',
                cursor: 'pointer',
                padding: '0.5rem'
              }}
            >
              ×
            </button>
          </div>

          <div style={{ marginBottom: '1.5rem' }}>
            <h3 style={{ color: 'rgba(255, 255, 255, 0.9)', marginBottom: '0.5rem' }}>Current Status</h3>
            <p style={{ margin: '0.25rem 0', color: 'rgba(255, 255, 255, 0.8)' }}>
              <strong>Power:</strong> {selectedReactor.power}%
            </p>
            <p style={{ margin: '0.25rem 0', color: 'rgba(255, 255, 255, 0.8)' }}>
              <strong>Report Date:</strong> {selectedReactor.report_date}
            </p>
            <p style={{ margin: '0.25rem 0', color: 'rgba(255, 255, 255, 0.8)' }}>
              <strong>Stub Outage:</strong> {selectedReactor.stuboutage ? 'Yes' : 'No'}
            </p>
          </div>

          {selectedReactor.reactorforecast_set.length > 0 && (
            <div style={{ marginBottom: '1.5rem' }}>
              <h3 style={{ color: 'rgba(255, 255, 255, 0.9)', marginBottom: '0.5rem' }}>Forecast Data</h3>
              {selectedReactor.reactorforecast_set.map((forecast, index) => (
                <div key={index} style={{
                  backgroundColor: 'rgba(255, 255, 255, 0.05)',
                  padding: '1rem',
                  borderRadius: '8px',
                  marginBottom: '0.5rem'
                }}>
                  <p style={{ margin: '0.25rem 0', color: 'rgba(255, 255, 255, 0.8)' }}>
                    <strong>Date:</strong> {forecast.df}
                  </p>
                  <p style={{ margin: '0.25rem 0', color: 'rgba(255, 255, 255, 0.8)' }}>
                    <strong>Predicted Power:</strong> {forecast.yhat.toFixed(1)}%
                  </p>
                  <p style={{ margin: '0.25rem 0', color: 'rgba(255, 255, 255, 0.8)' }}>
                    <strong>Range:</strong> {forecast.yhat_lower.toFixed(1)}% - {forecast.yhat_upper.toFixed(1)}%
                  </p>
                  <a 
                    href={forecast.image_url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    style={{
                      color: '#7dd3fc',
                      textDecoration: 'none',
                      fontSize: '0.9rem'
                    }}
                  >
                    View Forecast Chart →
                  </a>
                </div>
              ))}
            </div>
          )}

          {selectedReactor.stuboutage_set.length > 0 && (
            <div>
              <h3 style={{ color: 'rgba(255, 255, 255, 0.9)', marginBottom: '0.5rem' }}>Stub Outages</h3>
              {selectedReactor.stuboutage_set.map((outage, index) => (
                <div key={index} style={{
                  backgroundColor: 'rgba(255, 107, 107, 0.1)',
                  padding: '1rem',
                  borderRadius: '8px',
                  marginBottom: '0.5rem',
                  border: '1px solid rgba(255, 107, 107, 0.2)'
                }}>
                  <p style={{ margin: '0.25rem 0', color: 'rgba(255, 255, 255, 0.8)' }}>
                    {JSON.stringify(outage)}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div style={{ 
      backgroundColor: 'rgb(35, 40, 50)',
      padding: '1.5rem',
      borderRadius: '8px',
      border: '1px solid rgba(255, 255, 255, 0.1)'
    }}>
      <h2 style={{ 
        textAlign: 'center', 
        marginBottom: '1rem',
        color: 'rgba(255, 255, 255, 0.95)',
        fontSize: '1.8rem'
      }}>
        US Nuclear Reactor Status - {date}
      </h2>
      <Plot
        data={[
          {
            type: "scattergeo",
            mode: "markers",
            locationmode: "USA-states",
            lon: reactorData.map((r) => r.longitude),
            lat: reactorData.map((r) => r.latitude),
            text: reactorData.map(r => 
              `${r.unit}<br/>Power: ${r.power}%<br/>Region: ${r.region}<br/>Plant: ${r.name}`
            ),
            hoverinfo: "text",
                          marker: {
                size: 8,
                color: reactorData.map(r => r.power),
                colorscale: [
                  [0, "red"],      // Offline reactors in red
                  [0.1, "orange"], // Low power in orange  
                  [0.5, "yellow"], // Medium power in yellow
                  [1, "green"]     // Full power in green
                ],
                line: {
                  color: 'white',
                  width: 1
                }
              }
          },
        ]}
        layout={{
          geo: {
            scope: "usa",
            projection: { type: "albers usa" },
            showland: true,
            landcolor: "rgb(35, 45, 55)",
            coastlinecolor: "rgb(50, 60, 70)",
            subunitcolor: "rgb(60, 70, 80)",
            subunitwidth: 1,
            countrywidth: 1,
            bgcolor: "rgb(25, 30, 40)",
            showlakes: true,
            lakecolor: "rgb(30, 40, 50)"
          },
          title: {
            text: `Nuclear Reactor Power Output Map`,
            x: 0.5,
            font: { 
              size: 16, 
              color: 'rgba(255, 255, 255, 0.95)' 
            }
          },
          paper_bgcolor: "rgb(35, 40, 50)",
          plot_bgcolor: "rgb(35, 40, 50)",
          margin: { t: 60, b: 20, l: 20, r: 20 },
        }}
        onClick={(event: any) => {
          const pointIndex = event.points?.[0]?.pointIndex;
          if (pointIndex !== undefined && reactorData[pointIndex]) {
            const reactor = reactorData[pointIndex];
            const reactorId = reactors.find(r => r.name === reactor.name)?.reactorstatus.find(s => s.unit === reactor.unit)?.reactor;
            if (reactorId) {
              fetchReactorDetail(reactorId);
            }
          }
        }}
        style={{ width: "100%", height: "80vh" }}
        config={{
          displayModeBar: true,
          modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d'],
          displaylogo: false,
          toImageButtonOptions: {
            format: 'png',
            filename: 'nuclear_reactor_map',
            height: 500,
            width: 700,
            scale: 1
          }
        }}
      />
      <ReactorDetailModal />
      
      {detailLoading && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.5)',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          zIndex: 999
        }}>
          <div style={{
            backgroundColor: 'rgb(35, 40, 50)',
            padding: '2rem',
            borderRadius: '8px',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            color: 'white'
          }}>
            Loading reactor details...
          </div>
        </div>
      )}
    </div>
  );
}
