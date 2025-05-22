// Initialize map centered on a default location
const map = L.map('map').setView([55.75, 49.27], 10);

// Add OpenStreetMap tiles
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors'
}).addTo(map);

// Function to create a popup with point information
function createPopup(point) {
    return `
        <div>
            <strong>IMEI:</strong> ${point.imei}<br>
            <strong>Speed:</strong> ${point.speed} km/h<br>
            <strong>Signal:</strong> ${new Date(point.signal).toLocaleString()}<br>
            <strong>Recorded:</strong> ${new Date(point.timestamp).toLocaleString()}
        </div>
    `;
}

// Fetch and display points
function updatePoints() {
    fetch('/api/coords')
        .then(response => response.json())
        .then(points => {
            // Clear existing markers
            map.eachLayer((layer) => {
                if (layer instanceof L.Marker) {
                    map.removeLayer(layer);
                }
            });

            // Add new markers
            points.forEach(point => {
                L.marker([point.lat_google, point.lng_google])
                    .bindPopup(createPopup(point))
                    .addTo(map);
            });

            // If we have points, center the map on the last point
            if (points.length > 0) {
                const lastPoint = points[points.length - 1];
                map.setView([lastPoint.lat_google, lastPoint.lng_google], 13);
            }
        })
        .catch(error => console.error('Error fetching points:', error));
}

// Initial load
updatePoints();

// Update points every minute
setInterval(updatePoints, 60000); 