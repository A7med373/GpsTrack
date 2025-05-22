# GPS Tracking System

A system for tracking GPS coordinates from 365gps.net and displaying them on a map.

## Setup

1. Create a virtual environment and activate it:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the GPS data fetcher (in one terminal):
```bash
python fetch_coords.py
```

4. Run the web application (in another terminal):
```bash
python app.py
```

5. Open your browser and navigate to `http://localhost:5000`

## Features

- Automatic GPS data fetching every hour
- Web interface with OpenStreetMap integration
- Real-time updates of GPS points
- Detailed information popups for each point
- SQLite database for data storage

## Configuration

The system uses the following default configuration:
- IMEI: 861261027896790
- Password: 1234567

To change these values, modify the constants in `fetch_coords.py`.

## Database

The system uses SQLite with the following schema:
- Table: gps_points
  - id (Integer, Primary Key)
  - lat_google (Float)
  - lng_google (Float)
  - imei (String)
  - speed (Float)
  - signal (DateTime)
  - timestamp (DateTime)
