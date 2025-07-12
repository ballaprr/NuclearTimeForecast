import { useState } from 'react'
import ReactorMap from './components/ReactorMap'
import './App.css'

function App() {
  const [selectedDate, setSelectedDate] = useState('2025-07-11')

  return (
    <div style={{ 
      padding: '1rem', 
      minHeight: '100vh', 
      backgroundColor: 'rgb(30, 35, 45)',
      color: 'rgba(255, 255, 255, 0.95)'
    }}>
      
      <main>
        <ReactorMap date={selectedDate} />
      </main>
    </div>
  )
}

export default App
