import requests
from datetime import datetime
import json
from models import Session, GpsPoint
from apscheduler.schedulers.blocking import BlockingScheduler
import urllib3
import warnings
import os
from dotenv import load_dotenv


# Disable all warnings
warnings.filterwarnings('ignore')

# Configuration
IMEI = "861261027896790"
PASSWORD = "1234567"
LOGIN_URL = "https://www.365gps.net/npost_login.php"
MARKER_URL = "https://www.365gps.net/post_map_marker_list.php?timezonemins=-180"

# Get interval from environment variable or use default (15 seconds)
FETCH_INTERVAL = 5  # in seconds

# Define building boundaries using the provided coordinates
BUILDING_BOUNDS = {
    'min_lat': 55.750182,  # Minimum latitude of the building (right-bottom)
    'max_lat': 55.750400,  # Maximum latitude of the building (left-upper)
    'min_lng': 49.273466,  # Minimum longitude of the building (left-bottom)
    'max_lng': 49.273876   # Maximum longitude of the building (right-upper)
}

# Define a buffer (in degrees) to expand the building boundaries
# Adjust this value based on your GPS accuracy needs
GPS_BUFFER = 0.0003  # Approximately 30-40 meters

# Create expanded building boundaries with buffer
EXPANDED_BUILDING_BOUNDS = {
    'min_lat': BUILDING_BOUNDS['min_lat'] - GPS_BUFFER,
    'max_lat': BUILDING_BOUNDS['max_lat'] + GPS_BUFFER,
    'min_lng': BUILDING_BOUNDS['min_lng'] - GPS_BUFFER,
    'max_lng': BUILDING_BOUNDS['max_lng'] + GPS_BUFFER
}

def is_point_inside_building(lat, lng):
    """Check if a GPS point is inside the building boundaries or buffer zone."""
    # Check if point is inside the actual building
    inside_actual_building = (
        BUILDING_BOUNDS['min_lat'] <= lat <= BUILDING_BOUNDS['max_lat'] and
        BUILDING_BOUNDS['min_lng'] <= lng <= BUILDING_BOUNDS['max_lng']
    )

    # If inside actual building, return True
    if inside_actual_building:
        return True

    # If not in actual building, check if it's within the buffer zone
    inside_buffer = (
        EXPANDED_BUILDING_BOUNDS['min_lat'] <= lat <= EXPANDED_BUILDING_BOUNDS['max_lat'] and
        EXPANDED_BUILDING_BOUNDS['min_lng'] <= lng <= EXPANDED_BUILDING_BOUNDS['max_lng']
    )

    return inside_buffer

def fetch_gps_data():
    session = requests.Session()
    session.verify = False  # Disable SSL verification

    # Login
    login_data = {
        "demo": "F",
        "username": IMEI,
        "password": PASSWORD,
        "form_type": "0"
    }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "en-US,en;q=0.9",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        # Perform login
        login_response = session.post(LOGIN_URL, data=login_data, headers=headers)
        login_response.raise_for_status()

        # Get GPS data
        marker_response = session.post(MARKER_URL, headers=headers)
        marker_response.raise_for_status()

        # Handle response encoding
        try:
            # Try to decode with utf-8-sig first
            content = marker_response.content.decode('utf-8-sig')
        except UnicodeDecodeError:
            # Fallback to regular utf-8
            content = marker_response.content.decode('utf-8')

        data = json.loads(content)

        # Process and save points
        db_session = Session()
        try:
            for point in data.get("aaData", []):
                # Parse signal datetime
                signal_dt = datetime.strptime(point["signal"], "%Y/%m/%d %H:%M:%S")

                # Get coordinates
                lat = float(point["lat_google"])
                lng = float(point["lng_google"])

                # Check if point is inside the actual building
                inside_actual = (
                    BUILDING_BOUNDS['min_lat'] <= lat <= BUILDING_BOUNDS['max_lat'] and
                    BUILDING_BOUNDS['min_lng'] <= lng <= BUILDING_BOUNDS['max_lng']
                )

                # Only save points that are inside the building or buffer zone
                if is_point_inside_building(lat, lng):
                    # Create new GPS point
                    gps_point = GpsPoint(
                        lat_google=lat,
                        lng_google=lng,
                        imei=point["imei"],
                        speed=float(point["speed"]),
                        signal=signal_dt,
                        in_actual_building=1 if inside_actual else 0  # Set flag based on location
                    )

                    db_session.add(gps_point)

                    if inside_actual:
                        print(f"Point inside actual building - saved: ({lat}, {lng})")
                    else:
                        print(f"Point in buffer zone - saved: ({lat}, {lng})")
                else:
                    print(f"Point outside expanded boundaries - ignored: ({lat}, {lng})")

            db_session.commit()
            print(f"Successfully saved {len(data.get('aaData', []))} points at {datetime.now()}")

        except Exception as e:
            db_session.rollback()
            print(f"Database error: {e}")
        finally:
            db_session.close()

    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        print(f"Response content: {marker_response.text[:200]}")  # Print first 200 chars of response

if __name__ == "__main__":
    print(f"Starting GPS tracking with {FETCH_INTERVAL} second interval")

    # Run immediately on start
    fetch_gps_data()

    # Schedule to run at specified interval
    scheduler = BlockingScheduler()
    scheduler.add_job(fetch_gps_data, 'interval', seconds=FETCH_INTERVAL)
    scheduler.start() 
