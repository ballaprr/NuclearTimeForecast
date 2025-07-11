// ReactorMap.tsx
import React, { useEffect, useState } from "react";
import Plot from "react-plotly.js";
import axios from "axios";

interface ReactorStatus {
  report_date: string;
  unit: string;
  power: number;
}

interface Reactor {
  name: string;
  region: string;
  latitude: number;
  longitude: number;
  reactorstatus: ReactorStatus[];
}

interface ReactorMapProps {
  date?: string;
}

export default function ReactorMap({ date = "2025-01-10" }: ReactorMapProps) {
  const [reactors, setReactors] = useState<Reactor[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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
  const reactorData = reactors.flatMap(reactor => 
    reactor.reactorstatus.map(status => ({
      name: reactor.name,
      latitude: reactor.latitude,
      longitude: reactor.longitude,
      power: status.power,
      unit: status.unit,
      region: reactor.region
    }))
  );

  // Color reactors based on power level
  const getMarkerColor = (power: number) => {
    if (power === 0) return '#ef4444'; // Red for offline
    if (power < 25) return '#f97316'; // Orange for low power
    if (power < 75) return '#eab308'; // Yellow for medium power
    return '#22c55e'; // Green for full power
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
            text: reactorData.map(
              (r) => `${r.unit}<br>Power: ${r.power}%<br>Region: ${r.region}<br>Plant: ${r.name}`
            ),
            hoverinfo: "text",
            marker: {
              color: reactorData.map(r => getMarkerColor(r.power)),
              size: 8,
              line: {
                color: 'rgba(255, 255, 255, 0.3)',
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
            landcolor: "rgb(15, 20, 25)",
            coastlinecolor: "rgb(25, 30, 35)",
            subunitcolor: "rgb(30, 35, 40)",
            subunitwidth: 1,
            countrywidth: 1,
            bgcolor: "rgb(8, 12, 18)",
            showlakes: true,
            lakecolor: "rgb(12, 16, 22)"
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
            console.log(`Clicked on ${reactor.unit} at ${reactor.name}`);
            // You can implement navigation to detailed view here
            // window.location.href = `/reactor/${reactor.name.replace(/ /g, "_")}`;
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
    </div>
  );
}
