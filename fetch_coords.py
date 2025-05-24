import requests
from datetime import datetime
import json
from models import Session, GpsPoint
from apscheduler.schedulers.blocking import BlockingScheduler
import urllib3
import warnings
import os
from dotenv import load_dotenv
from sqlalchemy import desc


# Отключить все предупреждения
warnings.filterwarnings('ignore')

# Конфигурация
IMEI = "861261027885199"
PASSWORD = "123456"
LOGIN_URL = "https://www.365gps.net/npost_login.php"
MARKER_URL = "https://www.365gps.net/post_map_marker_list.php?timezonemins=-180"

# Получить интервал из переменной окружения или использовать значение по умолчанию (320 секунд)
FETCH_INTERVAL = 3  # в секундах

# Определить границы здания, используя предоставленные координаты
BUILDING_BOUNDS = {
    'min_lat': 55.175553,
    'max_lat': 55.176362,
    'min_lng': 51.806189,
    'max_lng': 51.806758
}
# Определить буфер (в градусах) для расширения границ здания
# Настройте это значение в зависимости от точности GPS
GPS_BUFFER = 0.0003  # Примерно 30-40 метров

# Создать расширенные границы здания с буфером
EXPANDED_BUILDING_BOUNDS = {
    'min_lat': BUILDING_BOUNDS['min_lat'] - GPS_BUFFER,
    'max_lat': BUILDING_BOUNDS['max_lat'] + GPS_BUFFER,
    'min_lng': BUILDING_BOUNDS['min_lng'] - GPS_BUFFER,
    'max_lng': BUILDING_BOUNDS['max_lng'] + GPS_BUFFER
}

def clean_old_points():
    """Удаляет старые точки, оставляя только последние 5."""
    db_session = Session()
    try:
        # Получить общее количество точек
        total_points = db_session.query(GpsPoint).count()
        
        if total_points >= 50:
            # Получить ID последних 5 точек
            last_5_points = db_session.query(GpsPoint.id).order_by(desc(GpsPoint.id)).limit(5).all()
            last_5_ids = [point[0] for point in last_5_points]
            
            # Удалить все точки, кроме последних 5
            db_session.query(GpsPoint).filter(~GpsPoint.id.in_(last_5_ids)).delete()
            db_session.commit()
            print(f"Очистка базы данных: удалено {total_points - 5} старых точек")
    except Exception as e:
        db_session.rollback()
        print(f"Ошибка при очистке базы данных: {e}")
    finally:
        db_session.close()

def is_point_inside_building(lat, lng):
    """Проверить, находится ли GPS-точка внутри границ здания или в буферной зоне."""
    # Проверить, находится ли точка внутри фактического здания
    inside_actual_building = (
        BUILDING_BOUNDS['min_lat'] <= lat <= BUILDING_BOUNDS['max_lat'] and
        BUILDING_BOUNDS['min_lng'] <= lng <= BUILDING_BOUNDS['max_lng']
    )

    # Если внутри фактического здания, вернуть True
    if inside_actual_building:
        return True

    # Если не в фактическом здании, проверить, находится ли она в буферной зоне
    inside_buffer = (
        EXPANDED_BUILDING_BOUNDS['min_lat'] <= lat <= EXPANDED_BUILDING_BOUNDS['max_lat'] and
        EXPANDED_BUILDING_BOUNDS['min_lng'] <= lng <= EXPANDED_BUILDING_BOUNDS['max_lng']
    )

    return inside_buffer

def fetch_gps_data():
    session = requests.Session()
    session.verify = False  # Отключить проверку SSL

    # Вход в систему
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
        # Выполнить вход
        login_response = session.post(LOGIN_URL, data=login_data, headers=headers)
        login_response.raise_for_status()

        # Получить данные GPS
        marker_response = session.post(MARKER_URL, headers=headers)
        marker_response.raise_for_status()

        # Обработать кодировку ответа
        try:
            # Сначала попробовать декодировать с utf-8-sig
            content = marker_response.content.decode('utf-8-sig')
        except UnicodeDecodeError:
            # Запасной вариант - обычный utf-8
            content = marker_response.content.decode('utf-8')

        data = json.loads(content)

        # Обработать и сохранить точки
        db_session = Session()
        try:
            for point in data.get("aaData", []):
                # Разобрать дату и время сигнала
                signal_dt = datetime.strptime(point["signal"], "%Y/%m/%d %H:%M:%S")

                # Получить координаты
                lat = float(point["lat_google"])
                lng = float(point["lng_google"])

                # Проверить, находится ли точка внутри фактического здания
                inside_actual = (
                    BUILDING_BOUNDS['min_lat'] <= lat <= BUILDING_BOUNDS['max_lat'] and
                    BUILDING_BOUNDS['min_lng'] <= lng <= BUILDING_BOUNDS['max_lng']
                )

                # Сохранять только точки, которые находятся внутри здания или в буферной зоне
                if is_point_inside_building(lat, lng):
                    # Создать новую GPS-точку
                    gps_point = GpsPoint(
                        lat_google=lat,
                        lng_google=lng,
                        imei=point["imei"],
                        speed=float(point["speed"]),
                        signal=signal_dt,
                        in_actual_building=1 if inside_actual else 0  # Установить флаг на основе местоположения
                    )

                    db_session.add(gps_point)

                    if inside_actual:
                        print(f"Точка внутри фактического здания - сохранена: ({lat}, {lng})")
                    else:
                        print(f"Точка в буферной зоне - сохранена: ({lat}, {lng})")
                else:
                    print(f"Точка за пределами расширенных границ - проигнорирована: ({lat}, {lng})")

            db_session.commit()
            print(f"Успешно сохранено {len(data.get('aaData', []))} точек в {datetime.now()}")
            
            # Проверить количество точек и очистить старые, если нужно
            clean_old_points()

        except Exception as e:
            db_session.rollback()
            print(f"Ошибка базы данных: {e}")
        finally:
            db_session.close()

    except requests.exceptions.RequestException as e:
        print(f"Ошибка запроса: {e}")
    except json.JSONDecodeError as e:
        print(f"Ошибка декодирования JSON: {e}")
        print(f"Содержимое ответа: {marker_response.text[:200]}")  # Вывести первые 200 символов ответа

if __name__ == "__main__":
    print(f"Запуск отслеживания GPS с интервалом {FETCH_INTERVAL} секунд")

    # Запустить сразу при старте
    fetch_gps_data()

    # Запланировать выполнение с указанным интервалом
    scheduler = BlockingScheduler()
    scheduler.add_job(fetch_gps_data, 'interval', seconds=FETCH_INTERVAL)
    scheduler.start()
