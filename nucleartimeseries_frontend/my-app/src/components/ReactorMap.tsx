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
    return <div style={{ textAlign: 'center', padding: '2rem' }}>Loading reactor data...</div>;
  }

  if (error) {
    return <div style={{ textAlign: 'center', padding: '2rem', color: 'red' }}>Error: {error}</div>;
  }

  if (reactors.length === 0) {
    return <div style={{ textAlign: 'center', padding: '2rem' }}>No reactor data found for {date}</div>;
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

  return (
    <div>
      <h2 style={{ textAlign: 'center', marginBottom: '1rem' }}>
        US Nuclear Reactor Status - {date}
      </h2>
      <div style={{ marginBottom: '1rem', textAlign: 'center' }}>
        <strong>Total Reactors:</strong> {reactorData.length} | 
        <strong> Online:</strong> {reactorData.filter(r => r.power > 0).length} | 
        <strong> Offline:</strong> {reactorData.filter(r => r.power === 0).length}
      </div>
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
            marker: {
              size: reactorData.map((r) => r.power === 0 ? 8 : 12),
              color: reactorData.map((r) => r.power),
              colorscale: [
                [0, "red"],      // Offline reactors in red
                [0.1, "orange"], // Low power in orange  
                [0.5, "yellow"], // Medium power in yellow
                [1, "green"]     // Full power in green
              ],
                             colorbar: { 
                 title: { text: "Power (%)" }
               },
              line: {
                color: "black",
                width: 1
              }
            },
            hoverinfo: "text",
          },
        ]}
        layout={{
          geo: {
            scope: "usa",
            projection: { type: "albers usa" },
            showland: true,
            landcolor: "rgb(243, 243, 243)",
            coastlinecolor: "rgb(204, 204, 204)",
            subunitcolor: "rgb(217, 217, 217)",
            subunitwidth: 1,
            countrywidth: 1,
          },
          title: {
            text: `Nuclear Reactor Power Output Map`,
            x: 0.5,
            font: { size: 16 }
          },
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
      />
    </div>
  );
}
