# Nuclear Reactor Time Series Forecasting & Visualization

A comprehensive web application for visualizing and forecasting U.S. nuclear reactor power output data. Features an interactive map interface, real-time status monitoring, and Prophet-based time series forecasting.

## Features

- **Interactive US Map**: Real-time visualization of nuclear reactor locations and power levels
- **Time Series Forecasting**: Prophet-based predictions for reactor power output
- **Reactor Detail Views**: Click any reactor for detailed status, forecasts, and interactive charts
- **Color-coded Status Indicators**: Visual power level representation (red=offline, orange=low, yellow=medium, green=full)
- **Offset Positioning**: Smart positioning for reactors sharing coordinates
- **AWS S3 Integration**: Cloud-hosted interactive forecast charts
- **REST API**: Django-based API for data access and forecasting
- **Responsive Design**: Modern React TypeScript frontend

## Technology Stack

- **Backend**: Django 4.0.6, Django REST Framework, SQLite/PostgreSQL
- **Frontend**: React 19, TypeScript, Vite, Plotly.js
- **Forecasting**: Prophet (Facebook's time series forecasting library)
- **Map Visualization**: Plotly.js with custom US map styling
- **Cloud Storage**: AWS S3 for forecast chart hosting
- **Task Queue**: Celery with Redis for background processing

## Project Structure

```
NuclearTimeSeries/
├── README.md                          # This file
├── requirements.txt                   # Root dependencies
├── Extract.ipynb                      # Data exploration notebook
├── Notes.txt                          # Development notes
├── nucleartimeseries_api/            # Django backend
│   ├── manage.py                     # Django management script
│   ├── requirements.txt              # Backend dependencies
│   ├── db.sqlite3                   # SQLite database
│   ├── nrc_data/                    # Main Django app
│   │   ├── models.py                # Database models
│   │   ├── views.py                 # API endpoints
│   │   ├── urls.py                  # URL routing
│   │   ├── serializers.py           # API serializers
│   │   ├── forecast.py              # Prophet forecasting logic
│   │   ├── outage_detection.py      # Outage detection algorithms
│   │   └── management/commands/     # Django management commands
│   └── nucleartimeseries_api/       # Django project settings
└── nucleartimeseries_frontend/       # React frontend
    └── my-app/                      # Vite React app
        ├── src/components/          # React components
        │   └── ReactorMap.tsx       # Main map component
        ├── package.json             # Frontend dependencies
        └── vite.config.ts           # Vite configuration
```

## Installation & Setup

### Prerequisites

- Python 3.8+
- Node.js 16+
- Redis (for Celery task queue)

### Backend Setup (Django API)

1. **Navigate to the API directory:**
   ```bash
   cd nucleartimeseries_api
   ```

2. **Create and activate virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install backend dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run database migrations:**
   ```bash
   python manage.py migrate
   ```

5. **Seed the database with reactor data (optional):**
   ```bash
   python manage.py seed --start-year 2025 --end-year 2025 --max-dates 30
   ```

6. **Start the Django development server:**
   ```bash
   python manage.py runserver
   ```
   
   The API will be available at `http://localhost:8000`

### Frontend Setup (React App)

1. **Navigate to the frontend directory:**
   ```bash
   cd nucleartimeseries_frontend/my-app
   ```

2. **Install Node.js dependencies:**
   ```bash
   npm install
   ```

3. **Start the development server:**
   ```bash
   npm run dev
   ```
   
   The frontend will be available at `http://localhost:5173`

## Database Schema

The application uses Django models with the following structure:

### Reactor Model
```python
class Reactor(models.Model):
    name = models.CharField(max_length=100, unique=True)
    region = models.CharField(max_length=3, choices=REGION_CHOICES)  # I, II, III, IV
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
```

### ReactorStatus Model
```python
class ReactorStatus(models.Model):
    reactor = models.ForeignKey('Reactor', on_delete=models.CASCADE)
    report_date = models.DateField()
    unit = models.CharField(max_length=30)  # e.g., "Beaver Valley 1"
    power = models.IntegerField()  # Power level 0-100%
    down_date = models.DateField(null=True, blank=True)
    reason = models.CharField(max_length=255, null=True, blank=True)
    changed = models.BooleanField(default=False)
    scrams = models.IntegerField(null=True, blank=True)
```

### ReactorForecast Model
```python
class ReactorForecast(models.Model):
    reactor = models.ForeignKey('Reactor', on_delete=models.CASCADE)
    df = models.DateField()  # Forecast date
    yhat = models.FloatField()  # Predicted power
    yhat_lower = models.FloatField()  # Lower confidence interval
    yhat_upper = models.FloatField()  # Upper confidence interval
    image_url = models.URLField()  # S3 URL for interactive chart
    reactorstatus = models.ForeignKey('ReactorStatus', on_delete=models.CASCADE)
```

### StubOutage Model
```python
class StubOutage(models.Model):
    reactor = models.ForeignKey('Reactor', on_delete=models.CASCADE)
    date_detected = models.DateField()
    description = models.TextField(blank=True)
    auto_detected = models.BooleanField(default=False)
    confirmed = models.BooleanField(default=False)
    reactorstatus = models.ForeignKey('ReactorStatus', on_delete=models.CASCADE)
```

## API Endpoints

### Reactor Data
- `GET /api/reactor/{date}/` - Get all reactors for a specific date (YYYY-MM-DD format)
  ```json
  [
    {
      "name": "Beaver Valley 1",
      "region": "I",
      "latitude": 40.6219,
      "longitude": -80.4336,
      "reactorstatus": [
        {
          "report_date": "2025-07-11",
          "unit": "Beaver Valley 1",
          "power": 100,
          "reactor": 1
        }
      ]
    }
  ]
  ```

- `GET /api/reactor/{date}/{reactor_id}/` - Get detailed reactor information including forecasts
  ```json
  {
    "report_date": "2025-07-11",
    "unit": "Beaver Valley 1",
    "power": 100,
    "stuboutage": false,
    "reactorforecast_set": [
      {
        "df": "2025-07-12",
        "yhat": 98.5,
        "yhat_lower": 85.2,
        "yhat_upper": 100.0,
        "image_url": "https://nuclearforecast.s3.us-east-1.amazonaws.com/..."
      }
    ],
    "stuboutage_set": []
  }
  ```

## Frontend Features

### Interactive Map
- **US Geographic Map**: Plotly-powered map with custom dark theme styling
- **Reactor Markers**: Color-coded dots representing power levels:
  - 🔴 **Red**: Offline reactors (0% power)
  - 🟠 **Orange**: Low power reactors (1-25%)
  - 🟡 **Yellow**: Medium power reactors (26-75%)
  - 🟢 **Green**: High power reactors (76-100%)
- **Smart Positioning**: Reactors at the same location are offset for visibility
- **Hover Information**: Plant name, unit, power level, and region

### Reactor Detail Modal
Click any reactor marker to view:
- **Current Status**: Power level, report date, stub outage status
- **Forecast Data**: Prophet predictions with confidence intervals
- **Interactive Charts**: Embedded S3-hosted forecast visualizations
- **Historical Context**: Stub outage detection results

### Dark Theme Design
- **Modern UI**: Dark blue-gray color scheme optimized for data visualization
- **High Contrast**: White text and bright markers for excellent readability
- **Professional Styling**: Consistent with nuclear industry dashboards

## Forecasting System

The application uses Facebook's Prophet library for time series forecasting:

### Features
- **Automatic Seasonality Detection**: Handles daily, weekly, and yearly patterns
- **Trend Analysis**: Identifies long-term power output trends
- **Confidence Intervals**: Provides uncertainty bounds for predictions
- **Outlier Handling**: Robust to missing data and anomalies

### Chart Generation
- **Interactive Plotly Charts**: Generated and stored on AWS S3
- **Real-time Embedding**: Charts are embedded directly in the React modal
- **Date-specific URLs**: S3 paths include forecast dates for organization

## Usage Examples

### Starting the Application
```bash
# Terminal 1: Start Django backend
cd nucleartimeseries_api
python manage.py runserver

# Terminal 2: Start React frontend  
cd nucleartimeseries_frontend/my-app
npm run dev
```

### Viewing Reactor Data
1. Open `http://localhost:5173` in your browser
2. Select a date using the date picker
3. View reactor locations on the interactive US map
4. Click any reactor marker for detailed information
5. Explore forecast charts and historical data

### API Usage
```bash
# Get all reactors for July 11, 2025
curl http://localhost:8000/api/reactor/2025-07-11/

# Get detailed info for reactor ID 1
curl http://localhost:8000/api/reactor/2025-07-11/1/
```

## Development Notes

### Key Components
- **ReactorMap.tsx**: Main map visualization component with click handlers
- **forecast.py**: Prophet-based forecasting logic and S3 chart generation
- **outage_detection.py**: Algorithms for detecting reactor outages
- **models.py**: Django ORM models for reactor data

### Offset Algorithm
For reactors sharing coordinates (e.g., multi-unit plants):
```typescript
const offsetDistance = 0.02; // degrees
const patterns = [
  [0, 0],           // First unit: no offset
  [offsetDistance, 0],     // Second unit: east
  [0, offsetDistance],     // Third unit: north
  [-offsetDistance, 0],    // Fourth unit: west
  [0, -offsetDistance]     // Fifth unit: south
];
```

### AWS Integration
Forecast charts are generated as interactive HTML files and uploaded to S3:
```
https://nuclearforecast.s3.us-east-1.amazonaws.com/forecasts/Reactor_Name_2025-07-11.html
```

## Configuration

### Environment Variables
Create a `.env` file in the Django directory:
```bash
DEBUG=True
SECRET_KEY=your-secret-key
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
AWS_STORAGE_BUCKET_NAME=nuclearforecast
```

### CORS Settings
The Django backend is configured to allow cross-origin requests from the React development server.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Make your changes
4. Run tests: `python manage.py test`
5. Commit your changes (`git commit -am 'Add new feature'`)
6. Push to the branch (`git push origin feature/new-feature`)
7. Create a Pull Request

## Data Sources

- **Nuclear Regulatory Commission**: Reactor status data and power output reports
- **Plant Coordinates**: Manual geocoding of nuclear facility locations
- **Regional Classifications**: NRC regional boundaries

## Legal Notice

This application visualizes publicly available data from the U.S. Nuclear Regulatory Commission. Always:
- Verify critical information with official NRC sources
- Respect data usage terms and conditions
- Cite the NRC as the original data source in any publications

---

*This application is not affiliated with or endorsed by the U.S. Nuclear Regulatory Commission.* 