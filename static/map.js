// Initialize map centered on a default location
const map = L.map('map').setView([55.75, 49.27], 10);

// Add OpenStreetMap tiles
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors'
}).addTo(map);

// Keep track of the current marker
let currentMarker = null;

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
            if (points.length > 0) {
                // Get the latest point
                const latestPoint = points[points.length - 1];
                
                // Remove existing marker if any
                if (currentMarker) {
                    map.removeLayer(currentMarker);
                }
                
                // Add new marker
                currentMarker = L.marker([latestPoint.lat_google, latestPoint.lng_google])
                    .bindPopup(createPopup(latestPoint))
                    .addTo(map);
                
                // Center map on the latest point
                map.setView([latestPoint.lat_google, latestPoint.lng_google], 13);
                
                // Open popup
                currentMarker.openPopup();
            }
        })
        .catch(error => console.error('Error fetching points:', error));
}

// Initial load
updatePoints();

// Update points every 5 seconds
setInterval(updatePoints, 5000); 