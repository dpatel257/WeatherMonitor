import requests
import datetime
from collections import defaultdict

def calculate_temperature_score(temp_f):
    """Score based on how close the temperature is to 65–72°F."""
    ideal_min, ideal_max = 65, 72
    hard_min, hard_max = 45, 90

    if ideal_min <= temp_f <= ideal_max:
        return 1.0
    elif temp_f < ideal_min:
        return max(0, 1 - (ideal_min - temp_f) / (ideal_min - hard_min))
    else:  # temp_f > ideal_max
        return max(0, 1 - (temp_f - ideal_max) / (hard_max - ideal_max))


def calculate_wind_score(wind_speed):
    """Score decreases linearly with wind speed up to 22 mph."""
    max_wind = 22
    return max(0, 1 - (wind_speed / max_wind))


def calculate_weather_score(weather_main):
    """Sky condition scoring."""
    weather_main = weather_main.lower()
    if "clear" in weather_main:
        return 1.0
    elif "cloud" in weather_main:
        return 0.8
    elif any(word in weather_main for word in ["rain", "drizzle", "thunderstorm", "snow"]):
        return 0.0
    else:
        return 0.5  # neutral for unhandled cases


def calculate_pleasantness(temp_f, wind_speed, weather_main):
    """Weighted pleasantness score from 0–100."""
    temp_score = calculate_temperature_score(temp_f) * 0.7
    wind_score = calculate_wind_score(wind_speed) * 0.2
    weather_score = calculate_weather_score(weather_main) * 0.1

    total_score = (temp_score + wind_score + weather_score) * 100
    return round(total_score, 2)

def fetch_current_temperature(api_key, location):
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": location,
        "appid": api_key,
        "units": "imperial"  # use "metric" for Celsius
    }

    resp = requests.get(url, params=params)
    data = resp.json()

    if resp.status_code != 200:
        raise Exception(f"API Error: {data.get('message', 'Unknown error')}")

    # Main weather measurements
    main = data.get("main", {})
    wind = data.get("wind", {})
    clouds = data.get("clouds", {})
    weather_info = data.get("weather", [{}])[0]

    rain_volume = data.get("rain", {}).get("1h", 0.0)
    chance_of_rain = 100.0 if rain_volume > 0 else 0.0

    return {
        "temp_f": main.get("temp"),
        "temp_min_f": main.get("temp_min"),
        "temp_max_f": main.get("temp_max"),
        "humidity_percent": main.get("humidity"),
        "cloudiness_percent": clouds.get("all"),
        "chance_of_rain_percent": chance_of_rain,
        "wind_mph": wind.get("speed"),
        "weather": weather_info.get("main"),
        "weather_description": weather_info.get("description"),
    }


def fetch_weather_points(api_key, location):
    """
    Fetch 3-hour forecast points (no aggregation) for the next ~5 days,
    including a calculated pleasantness_score for each.
    """
    url = "https://api.openweathermap.org/data/2.5/forecast"
    params = {"q": location, "appid": api_key, "units": "imperial"}

    resp = requests.get(url, params=params)
    data = resp.json()

    if data.get("cod") != "200":
        raise Exception(f"API Error: {data.get('message')}")

    results = []
    for entry in data["list"]:
        dt_txt = entry["dt_txt"]  # "YYYY-MM-DD HH:MM:SS"
        dt_obj = datetime.datetime.strptime(dt_txt, "%Y-%m-%d %H:%M:%S")

        temp_f = entry["main"]["temp"]
        wind_mph = entry["wind"]["speed"]
        weather_main = entry["weather"][0]["main"]
        chance_of_rain = round(entry.get("pop", 0) * 100, 1)

        results.append({
            "forecast_time": dt_obj,
            "location": location,
            "day_of_week": dt_obj.strftime("%A"),
            "temp_f": temp_f,
            "temp_min_f": entry["main"]["temp_min"],
            "temp_max_f": entry["main"]["temp_max"],
            "humidity_percent": entry["main"]["humidity"],
            "cloudiness_percent": entry["clouds"]["all"],
            "chance_of_rain_percent": chance_of_rain,
            "wind_mph": wind_mph,
            "weather": weather_main,
            "weather_description": entry["weather"][0]["description"],
            "pleasantness_score": calculate_pleasantness(temp_f, wind_mph, weather_main)
        })

    return results
