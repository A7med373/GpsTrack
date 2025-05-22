from flask import Flask, jsonify, render_template, send_from_directory
from models import Session, GpsPoint
from datetime import datetime
import os

app = Flask(__name__, 
    static_folder='static',
    template_folder='templates'
)

@app.route('/')
def index():
    return render_template('map.html')

@app.route('/api/coords')
def get_coords():
    session = Session()
    try:
        points = session.query(GpsPoint).all()
        return jsonify([{
            'lat_google': point.lat_google,
            'lng_google': point.lng_google,
            'imei': point.imei,
            'speed': point.speed,
            'signal': point.signal.isoformat(),
            'timestamp': point.timestamp.isoformat()
        } for point in points])
    finally:
        session.close()

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

if __name__ == '__main__':
    # Ensure the static and templates directories exist
    os.makedirs('static', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    
    app.run(debug=True, host='0.0.0.0', port=5000) 