import requests
import datetime
import time

GOOGLE_API_KEY = os.environ["GOOGLE_API_KEY"] 
ORIGIN = "Portland,OR"
DESTINATION = "Hillsboro,OR"

def get_travel_time(departure_time):
    url = "https://maps.googleapis.com/maps/api/directions/json"
    params = {
        "origin": ORIGIN,
        "destination": DESTINATION,
        "departure_time": departure_time,
        "traffic_model": "best_guess",
        "key": GOOGLE_API_KEY
    }
    resp = requests.get(url, params=params).json()
    leg = resp["routes"][0]["legs"][0]
    baseline = leg["duration"]["value"] / 60  # minutes
    in_traffic = leg["duration_in_traffic"]["value"] / 60  # minutes

    ratio = in_traffic / baseline if baseline > 0 else None

    return in_traffic, baseline, round(ratio, 2)


def analyze_travel_times(date, origin=ORIGIN, destination=DESTINATION):
    """
    Check travel times every hour between 6 AM and 10 PM.
    Returns:
      - results: list of (time_str, in_traffic, baseline, ratio)
      - worst_times: top 2 peak traffic hours to avoid
    """
    results = []

    for hour in range(6, 23):  # 6 AM → 10 PM
        dt = datetime.datetime.combine(date, datetime.time(hour, 0))
        timestamp = int(time.mktime(dt.timetuple()))
        in_traffic_time, baseline_time, ratio = get_travel_time(timestamp)
        results.append((dt.strftime("%H:%M"), in_traffic_time, baseline_time, ratio))

    # Sort by ratio (worst delays compared to baseline)
    worst_times_traffic = sorted(results, key=lambda x: x[3], reverse=True)[:2]
    worst_times = sorted(worst_times_traffic, key=lambda x: x[0])
    return results, worst_times


# Example usage
if __name__ == "__main__":
    date = datetime.date(2025, 9, 9)
    results, worst_times = analyze_travel_times(date)

    print("Hourly traffic predictions:")
    for t, traffic, baseline, ratio in results:
        print(f"{t}: {traffic:.1f} mins (baseline {baseline:.1f}), ratio={ratio}")

    print("\n🚦 Peak traffic times to avoid:")
    for t, traffic, baseline, ratio in worst_times:
        delay = traffic - baseline
        print(f"{t} → {traffic:.1f} mins (baseline {baseline:.1f}), delay +{delay:.1f} mins, ratio={ratio}")

