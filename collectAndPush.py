import os
from influxdb_client import InfluxDBClient, Point, WriteOptions, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import requests, datetime
from openWeatherAndPleasantness import fetch_current_temperature, fetch_weather_points
from peakTravelTime import analyze_travel_times
import psycopg2
from psycopg2.extras import execute_values


OWM_API_KEY = os.environ['OWM_API_KEY']
DB_HOST = os.environ['POSTGRES_HOST']
DB_PORT = os.environ['POSTGRES_PORT']
DB_NAME = os.environ['POSTGRES_DB_NAME']
DB_USER = os.environ['POSTGRES_USER']
DB_PASSWORD = os.environ['POSTGRES_PASSWORD']


client = InfluxDBClient(url=INFLUX_URL, token=TOKEN, org=ORG)
write_api = client.write_api(write_options=SYNCHRONOUS)

def get_weather(city):
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={OWM_API_KEY}&units=metric"
    return requests.get(url).json()

def push_weather_entry(location, entry):

    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    cur = conn.cursor()

    temp_f = fetch_current_temperature(OWM_API_KEY, location)


    upsert_query = """
        INSERT INTO latest_temperature (location, temperature)
        VALUES (%s, %s)
        ON CONFLICT (location)
        DO UPDATE SET
            temperature = EXCLUDED.temperature;
        """
    cur.execute(upsert_query, (location, temp_f))

    sql = """
    INSERT INTO weather_forecast_3h (
                forecast_time, location, day_of_week,
                temp_f, temp_min_f, temp_max_f,
                humidity_percent, cloudiness_percent, rain_percent,
                wind_mph, weather, pleasantness_score
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (forecast_time, location)
            DO UPDATE SET
                day_of_week        = EXCLUDED.day_of_week,
                temp_f             = EXCLUDED.temp_f,
                temp_min_f         = EXCLUDED.temp_min_f,
                temp_max_f         = EXCLUDED.temp_max_f,
                humidity_percent   = EXCLUDED.humidity_percent,
                cloudiness_percent = EXCLUDED.cloudiness_percent,
                rain_percent       = EXCLUDED.rain_percent,
                wind_mph           = EXCLUDED.wind_mph,
                weather            = EXCLUDED.weather,
                pleasantness_score = EXCLUDED.pleasantness_score;
    """

    values = (
            entry["forecast_time"],
            location,
            entry["day_of_week"],
            entry["temp_f"],
            entry["temp_min_f"],
            entry["temp_max_f"],
            entry["humidity_percent"],
            entry["cloudiness_percent"],
            entry["chance_of_rain_percent"],
            entry["wind_mph"],
            entry["weather"],
            entry["pleasantness_score"],
        )

    cur.execute(sql, values)


    conn.commit()
    cur.close()
    conn.close()


def push_traffic_entry(origin, destination, date, dow, peak_entry):

    time_obj = datetime.datetime.strptime(f"{date} {peak_entry['hour']}", "%Y-%m-%d %H:%M")
    point = Point("traffic_peak") \
        .tag("origin", origin) \
        .tag("destination", destination) \
        .tag("day_of_week", dow) \
        .tag("hour", peak_entry["hour"]) \
        .field("in_traffic_mins", peak_entry["in_traffic"]) \
        .field("baseline_mins", peak_entry["baseline"]) \
        .field("delay_mins", peak_entry["delay"]) \
        .field("ratio", peak_entry["ratio"]) \
        .time(time_obj, WritePrecision.NS)

    write_api.write(bucket=BUCKET, org=ORG, record=point)
    write_api.__del__()


if __name__ == "__main__":

    home = "Beaverton, US"
    location = "Portland, US"

    forecast = fetch_weather_points(OWM_API_KEY, location)


    for row in forecast:  # first 5 entries
        print(row)

        push_weather_entry(location, row)



        # Calculate travel times
        #date_obj = datetime.datetime.strptime(row["date"], "%Y-%m-%d").date()
        #results, worst_times = analyze_travel_times(date_obj, home, location)

        print("\n🚦 Peak traffic times to avoid:")
       # for t, traffic, baseline, ratio in worst_times:
        #    delay = traffic - baseline
        #    print(f"{t} → {traffic:.1f} mins (baseline {baseline:.1f}), delay +{delay:.1f} mins, ratio={ratio}")

    '''
    date = datetime.date(2025, 9, 9)
    results, worst_times = analyze_travel_times(date)

    print("Hourly traffic predictions:")
    for t, traffic, baseline, ratio in results:
        print(f"{t}: {traffic:.1f} mins (baseline {baseline:.1f}), ratio={ratio}")

    print("\n🚦 Peak traffic times to avoid:")
    for t, traffic, baseline, ratio in worst_times:
        delay = traffic - baseline
        print(f"{t} → {traffic:.1f} mins (baseline {baseline:.1f}), delay +{delay:.1f} mins, ratio={ratio}")
    '''

