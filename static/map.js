// Определить границы здания в GPS-координатах
// Добавление буферной зоны 0.0003 градуса (примерно 30-40 метров) для учета неточности GPS
const GPS_BUFFER = 0.0003;

// Определить фактические границы здания (без буфера)
const ACTUAL_BUILDING_BOUNDS = {
    min_lat: 55.175553,  // Минимальная широта (левый верхний)
    max_lat: 55.176362,  // Максимальная широта (правый нижний)
    min_lng: 51.806189,  // Минимальная долгота (левый нижний)
    max_lng: 51.806758   // Максимальная долгота (правый верхний)
};

// Определить расширенные границы здания с буфером (для обнаружения)
const BUILDING_BOUNDS = {
    'min_lat': ACTUAL_BUILDING_BOUNDS.min_lat - GPS_BUFFER,  // Минимальная широта с буфером
    'max_lat': ACTUAL_BUILDING_BOUNDS.max_lat + GPS_BUFFER,  // Максимальная широта с буфером
    'min_lng': ACTUAL_BUILDING_BOUNDS.min_lng - GPS_BUFFER,  // Минимальная долгота с буфером
    'max_lng': ACTUAL_BUILDING_BOUNDS.max_lng + GPS_BUFFER   // Максимальная долгота с буфером
};

// Вычислить центр здания
const centerLat = (BUILDING_BOUNDS.min_lat + BUILDING_BOUNDS.max_lat) / 2;
const centerLng = (BUILDING_BOUNDS.min_lng + BUILDING_BOUNDS.max_lng) / 2;

// Инициализировать карту с простой системой координат для изображения
const map = L.map('map', {
    crs: L.CRS.Simple,  // Использовать простую систему координат для изображения
    minZoom: -2,
    maxZoom: 2
});

// Определить границы изображения в простой системе координат
// Это будет использоваться для отображения GPS-координат на позиции изображения
const imageBounds = [
    [0, 0],  // Левый нижний угол
    [1000, 1000]  // Правый верхний угол (настройте в зависимости от размеров вашего изображения)
];

// Добавить наложение плана этажа
const imageUrl = '/static/floor_plan.jpg';
const floorPlan = L.imageOverlay(imageUrl, imageBounds).addTo(map);

// Подогнать карту под границы изображения
map.fitBounds(imageBounds);

// Отслеживать текущий маркер
let currentMarker = null;

// Определить пользовательские иконки для разных типов точек
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

// Функция для проверки, находится ли точка внутри фактического здания
function isPointInsideActualBuilding(lat, lng) {
    return (
        ACTUAL_BUILDING_BOUNDS.min_lat <= lat && lat <= ACTUAL_BUILDING_BOUNDS.max_lat &&
        ACTUAL_BUILDING_BOUNDS.min_lng <= lng && lng <= ACTUAL_BUILDING_BOUNDS.max_lng
    );
}

// Функция для проверки, находится ли точка в буферной зоне
function isPointInBufferZone(lat, lng) {
    // Проверить, находится ли точка за пределами фактического здания
    const outsideActualBuilding = !isPointInsideActualBuilding(lat, lng);

    // Проверить, находится ли точка внутри расширенных границ здания (буферная зона)
    const insideExpandedBounds = (
        BUILDING_BOUNDS.min_lat <= lat && lat <= BUILDING_BOUNDS.max_lat &&
        BUILDING_BOUNDS.min_lng <= lng && lng <= BUILDING_BOUNDS.max_lng
    );

    // Точка находится в буферной зоне, если она за пределами фактического здания, но внутри расширенных границ
    return outsideActualBuilding && insideExpandedBounds;
}

// Функция для нахождения ближайшей точки внутри здания для точек в буферной зоне
function findNearestPointInBuilding(lat, lng) {
    // Если точка уже внутри фактического здания, вернуть её как есть
    if (isPointInsideActualBuilding(lat, lng)) {
        return { lat, lng };
    }

    // Найти ближайшую точку на границе здания
    // Ограничить координаты границами здания
    const nearestLat = Math.max(
        ACTUAL_BUILDING_BOUNDS.min_lat,
        Math.min(lat, ACTUAL_BUILDING_BOUNDS.max_lat)
    );

    const nearestLng = Math.max(
        ACTUAL_BUILDING_BOUNDS.min_lng,
        Math.min(lng, ACTUAL_BUILDING_BOUNDS.max_lng)
    );

    return { lat: nearestLat, lng: nearestLng };
}

// Функция для преобразования GPS-координат в координаты изображения
function gpsToImageCoords(lat, lng) {
    // Вычислить процентную позицию в пределах границ здания
    const latPercent = (lat - BUILDING_BOUNDS.min_lat) / 
                      (BUILDING_BOUNDS.max_lat - BUILDING_BOUNDS.min_lat);
    const lngPercent = (lng - BUILDING_BOUNDS.min_lng) / 
                      (BUILDING_BOUNDS.max_lng - BUILDING_BOUNDS.min_lng);

    // Отобразить процентную позицию на координаты изображения
    const y = imageBounds[1][0] * (1 - latPercent);  // Инвертировать ось Y, так как GPS широта увеличивается к северу
    const x = imageBounds[1][1] * lngPercent;

    return [y, x];
}

// Функция для создания всплывающего окна с информацией о точке
function createPopup(point) {
    // Определить текст и стиль статуса местоположения
    const locationStatus = point.in_actual_building === 1 
        ? '<span style="color: green;">Внутри здания</span>' 
        : '<span style="color: orange;">В буферной зоне (Отображается в ближайшей точке здания)</span>';

    return `
        <div>
            <strong>IMEI:</strong> ${point.imei}<br>
            <strong>Скорость:</strong> ${point.speed} км/ч<br>
            <strong>Сигнал:</strong> ${new Date(point.signal).toLocaleString()}<br>
            <strong>Записано:</strong> ${new Date(point.timestamp).toLocaleString()}<br>
            <strong>Местоположение:</strong> ${locationStatus}
        </div>
    `;
}

// Получить и отобразить точки
function updatePoints() {
    fetch('/api/coords')
        .then(response => response.json())
        .then(points => {
            if (points.length > 0) {
                // Получить последнюю точку
                const latestPoint = points[points.length - 1];

                // Проверить, находится ли точка внутри здания или в буферной зоне
                const lat = latestPoint.lat_google;
                const lng = latestPoint.lng_google;
                const isInActualBuilding = isPointInsideActualBuilding(lat, lng);
                const isInBufferZone = isPointInBufferZone(lat, lng);

                // Отображать только точки, которые находятся внутри здания или в буферной зоне
                if (isInActualBuilding || isInBufferZone) {
                    // Получить координаты для отображения
                    let displayCoords;

                    if (isInActualBuilding) {
                        // Если точка внутри фактического здания, использовать её фактические координаты
                        displayCoords = {
                            lat: lat,
                            lng: lng
                        };
                    } else {
                        // Если точка в буферной зоне, найти ближайшую точку внутри здания
                        displayCoords = findNearestPointInBuilding(lat, lng);
                    }

                    // Преобразовать координаты отображения в координаты изображения
                    const imageCoords = gpsToImageCoords(
                        displayCoords.lat,
                        displayCoords.lng
                    );

                    // Удалить существующий маркер, если есть
                    if (currentMarker) {
                        map.removeLayer(currentMarker);
                    }

                    // Выбрать соответствующую иконку в зависимости от того, находится ли точка в фактическом здании или в буферной зоне
                    const markerIcon = isInActualBuilding ? buildingIcon : bufferIcon;

                    // Добавить новый маркер на план этажа с соответствующей иконкой
                    currentMarker = L.marker(imageCoords, { icon: markerIcon })
                        .bindPopup(createPopup(latestPoint))
                        .addTo(map);
                } else {
                    // Если точка находится за пределами здания и буферной зоны, удалить существующий маркер
                    if (currentMarker) {
                        map.removeLayer(currentMarker);
                        currentMarker = null;
                    }
                    console.log("Точка за пределами здания и буферной зоны - не отображается");
                }
            }
        })
        .catch(error => console.error('Ошибка при получении точек:', error));
}

// Начальная загрузка
updatePoints();

// Обновлять точки каждые 5 секунд
setInterval(updatePoints, 5000);
