# Nuclear Reactor Time Series Frontend

This React frontend provides a US map visualization for nuclear reactor data, consuming the Django REST API.

## Features

- **Interactive US Map**: Shows nuclear reactors across the United States
- **Real-time Data**: Fetches reactor status data from the Django API
- **Color-coded Visualization**: 
  - 🔴 Red: Offline reactors (0% power)
  - 🟠 Orange: Low power reactors 
  - 🟡 Yellow: Medium power reactors
  - 🟢 Green: Full power reactors
- **Date Selection**: Choose any date to view historical reactor status
- **Interactive Details**: Click reactors for more information

## Setup Instructions

### Prerequisites
- Node.js (v16 or higher)
- Django backend running on port 8000

### Installation

1. **Navigate to the frontend directory:**
   ```bash
   cd nucleartimeseries_api/nucleartimeseries_frontend/my-app
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start the development server:**
   ```bash
   npm run dev
   ```

4. **Open your browser to:**
   ```
   http://localhost:5173
   ```

### Backend Setup

Make sure your Django backend is running:

1. **Install backend dependencies:**
   ```bash
   cd nucleartimeseries_api
   pip install -r requirements.txt
   ```

2. **Start Django server:**
   ```bash
   python manage.py runserver
   ```

The backend should be accessible at `http://localhost:8000`

## API Endpoints Used

- `GET /api/reactor/{date}/` - Get all reactors for a specific date
- `GET /api/reactor/{date}/{reactor_id}/` - Get detailed reactor information

## Technology Stack

- **React 19** with TypeScript
- **Vite** for fast development
- **Plotly.js** for interactive maps
- **Axios** for API calls
- **Django REST Framework** backend

## Usage

1. **Select a Date**: Use the date picker to choose which day's reactor data to visualize
2. **View the Map**: See all nuclear reactors plotted on the US map
3. **Interpret Colors**: Reactor power levels are color-coded for easy understanding
4. **Click for Details**: Click any reactor marker for additional information
5. **View Statistics**: See totals for online/offline reactors at the top

## Data Notes

- Reactor data is sourced from NRC (Nuclear Regulatory Commission) historical records
- Power levels are shown as percentages (0-100%)
- Geographic coordinates show approximate reactor locations
- Data availability varies by date (some dates may have limited data)

## Troubleshooting

### Common Issues

1. **CORS Errors**: Make sure the Django backend has CORS properly configured
2. **API Connection**: Verify the Django server is running on port 8000
3. **No Data**: Check that you have reactor data for the selected date
4. **Map Not Loading**: Ensure Plotly.js dependencies are properly installed

### Debug Steps

1. Open browser developer tools (F12)
2. Check the Console tab for error messages
3. Check the Network tab to see if API calls are successful
4. Verify the backend API returns data: `http://localhost:8000/api/reactor/2025-01-10/`

## Development

To modify the visualization:

- **Map Configuration**: Edit `src/components/ReactorMap.tsx`
- **Styling**: Modify `src/App.css`
- **API Calls**: Update the axios requests in ReactorMap component

## Future Enhancements

- Add reactor detail modal on click
- Historical trend charts
- Filtering by reactor region
- Export map as image
- Real-time updates via WebSocket 