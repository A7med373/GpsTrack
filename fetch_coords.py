import requests
from datetime import datetime
import json
from models import Session, GpsPoint
from apscheduler.schedulers.blocking import BlockingScheduler
import urllib3
import warnings
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Disable all warnings
warnings.filterwarnings('ignore')

# Configuration
IMEI = "861261027896790"
PASSWORD = "1234567"
LOGIN_URL = "https://www.365gps.net/npost_login.php"
MARKER_URL = "https://www.365gps.net/post_map_marker_list.php?timezonemins=-180"

# Get interval from environment variable or use default (15 seconds)
FETCH_INTERVAL = 30  # in seconds

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
                
                # Create new GPS point
                gps_point = GpsPoint(
                    lat_google=float(point["lat_google"]),
                    lng_google=float(point["lng_google"]),
                    imei=point["imei"],
                    speed=float(point["speed"]),
                    signal=signal_dt
                )
                
                db_session.add(gps_point)
            
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