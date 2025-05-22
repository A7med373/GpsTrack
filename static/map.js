// Define the bounds of the building in GPS coordinates
// Adding a buffer zone of 0.0003 degrees (approx. 30-40 meters) to account for GPS inaccuracy
const GPS_BUFFER = 0.0003;

const BUILDING_BOUNDS = {
    'min_lat': 55.750182 - GPS_BUFFER,  // Minimum latitude with buffer
    'max_lat': 55.750400 + GPS_BUFFER,  // Maximum latitude with buffer
    'min_lng': 49.273466 - GPS_BUFFER,  // Minimum longitude with buffer
    'max_lng': 49.273876 + GPS_BUFFER   // Maximum longitude with buffer
};

// Calculate the center of the building
const centerLat = (BUILDING_BOUNDS.min_lat + BUILDING_BOUNDS.max_lat) / 2;
const centerLng = (BUILDING_BOUNDS.min_lng + BUILDING_BOUNDS.max_lng) / 2;

// Initialize map with simple coordinate system for the image
const map = L.map('map', {
    crs: L.CRS.Simple,  // Use simple coordinate system for the image
    minZoom: -2,
    maxZoom: 2
});

// Define the image bounds in the simple coordinate system
// This will be used to map GPS coordinates to image positions
const imageBounds = [
    [0, 0],  // Bottom left corner
    [1000, 1000]  // Top right corner (adjust based on your image dimensions)
];

// Add the floor plan image overlay
const imageUrl = '/static/floor_plan.jpg';
const floorPlan = L.imageOverlay(imageUrl, imageBounds).addTo(map);

// Fit the map to the image bounds
map.fitBounds(imageBounds);

// Keep track of the current marker
let currentMarker = null;

// Define custom icons for different point types
const buildingIcon = L.icon({
    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
});

const bufferIcon = L.icon({
    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-orange.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
});

// Function to convert GPS coordinates to image coordinates
function gpsToImageCoords(lat, lng) {
    // Calculate the percentage position within the building bounds
    const latPercent = (lat - BUILDING_BOUNDS.min_lat) / 
                      (BUILDING_BOUNDS.max_lat - BUILDING_BOUNDS.min_lat);
    const lngPercent = (lng - BUILDING_BOUNDS.min_lng) / 
                      (BUILDING_BOUNDS.max_lng - BUILDING_BOUNDS.min_lng);

    // Map the percentage to image coordinates
    const y = imageBounds[1][0] * (1 - latPercent);  // Invert Y-axis because GPS lat increases northward
    const x = imageBounds[1][1] * lngPercent;

    return [y, x];
}

// Function to create a popup with point information
function createPopup(point) {
    // Determine location status text and style
    const locationStatus = point.in_actual_building === 1 
        ? '<span style="color: green;">Inside Building</span>' 
        : '<span style="color: orange;">In Buffer Zone</span>';

    return `
        <div>
            <strong>IMEI:</strong> ${point.imei}<br>
            <strong>Speed:</strong> ${point.speed} km/h<br>
            <strong>Signal:</strong> ${new Date(point.signal).toLocaleString()}<br>
            <strong>Recorded:</strong> ${new Date(point.timestamp).toLocaleString()}<br>
            <strong>Location:</strong> ${locationStatus}
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

                // Convert GPS coordinates to image coordinates
                const imageCoords = gpsToImageCoords(
                    latestPoint.lat_google, 
                    latestPoint.lng_google
                );

                // Remove existing marker if any
                if (currentMarker) {
                    map.removeLayer(currentMarker);
                }

                // Select the appropriate icon based on whether the point is in the actual building or buffer zone
                const markerIcon = latestPoint.in_actual_building === 1 ? buildingIcon : bufferIcon;

                // Add new marker on the floor plan with the appropriate icon
                currentMarker = L.marker(imageCoords, { icon: markerIcon })
                    .bindPopup(createPopup(latestPoint))
                    .addTo(map);
            }
        })
        .catch(error => console.error('Error fetching points:', error));
}

// Initial load
updatePoints();

// Update points every 5 seconds
setInterval(updatePoints, 5000);
