import { useState } from 'react'
import ReactorMap from './components/ReactorMap'
import './App.css'

function App() {
  const [selectedDate, setSelectedDate] = useState('2025-01-10')

  return (
    <div style={{ padding: '1rem' }}>
      <header style={{ textAlign: 'center', marginBottom: '2rem' }}>
        <h1>Nuclear Reactor Time Series Dashboard</h1>
        <div style={{ marginBottom: '1rem' }}>
          <label htmlFor="date-picker" style={{ marginRight: '0.5rem' }}>
            Select Date:
          </label>
          <input
            id="date-picker"
            type="date"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            style={{ padding: '0.5rem', fontSize: '1rem' }}
          />
        </div>
      </header>
      
      <main>
        <ReactorMap date={selectedDate} />
      </main>
    </div>
  )
}

export default App
