# Supervisor Dashboard

A real-time thermal inspection dashboard for the DreamVision Smart Factory platform.

## Features

- **Real-time Thermal Monitoring**: Live thermal camera feed display
- **Inspection History**: View all component inspections with detailed metrics
- **Anomaly Detection**: AI-powered defect identification and classification
- **Digital Twin Integration**: Interactive factory layout visualization
- **WebSocket Streaming**: Real-time data updates from thermal sensors
- **RESTful API**: Complete API for inspection data management

## Quick Start

### Prerequisites
- Python 3.8+
- Node.js (optional, for additional frontend features)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/Nadeem-Shaikh12/SupervisorDashboard.git
cd SupervisorDashboard
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Start the dashboard server:
```bash
python edge_server/api/server.py
```

4. Open your browser and navigate to:
```
http://localhost:8002/app/index.html
```

## Architecture

### Frontend
- `index.html` - Main dashboard interface
- `style.css` - Dashboard styling
- `script.js` - Frontend logic and WebSocket handling
- `digital_twin.js` - Digital twin visualization

### Backend
- `edge_server/api/server.py` - FastAPI server with WebSocket support
- `dashboard/api/dashboard_routes.py` - Dashboard-specific API endpoints

## API Endpoints

### Inspections
- `GET /inspections` - List all inspections
- `GET /inspection/{part_uid}` - Get specific inspection details

### Real-time Updates
- WebSocket: `/ws/inspections` - Real-time inspection updates

## Configuration

The dashboard connects to thermal inspection devices and displays real-time data. Configure your ESP32 thermal sensors to send data to the dashboard server.

## Development

### Project Structure
```
SupervisorDashboard/
├── edge_server/
│   └── api/
│       └── server.py          # Main FastAPI server
├── dashboard/
│   └── api/
│       └── dashboard_routes.py # Dashboard API routes
├── index.html                 # Main dashboard page
├── script.js                  # Frontend JavaScript
├── style.css                  # Dashboard styles
├── digital_twin.js           # Digital twin logic
└── requirements.txt          # Python dependencies
```

### Adding New Features
1. Frontend changes: Modify HTML/CSS/JS files
2. Backend changes: Update FastAPI routes in `dashboard_routes.py`
3. Real-time features: Use WebSocket connections for live updates

## License

This project is part of the DreamVision Smart Factory platform.