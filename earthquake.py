import requests
import time
import subprocess
import json
from datetime import datetime, timedelta

x_hours = 24
x_minutes = 60 * x_hours
previous_quakes = set()
previous_query = None

# Linux command to show an alert on screen
ALERT_CMD = ["lgtv", "LG", "createAlert"]
# Linux command to close an alert on screen
CLOSE_CMD = ["lgtv", "LG", "closeAlert"]

first_run = True

while True:
    x_minutes_ago = datetime.utcnow() - timedelta(minutes=x_minutes)
    start_time = x_minutes_ago.strftime("%Y-%m-%dT%H:%M:%S")

    response = requests.get("https://earthquake.usgs.gov/fdsnws/event/1/query", params={
        "format": "geojson",
        "minmagnitude": 1,
        "maxradiuskm": 6000,
        "latitude": 31.0461,   # Latitude of Israel
        "longitude": 34.8516,  # Longitude of Israel
        "starttime": start_time,
    })

    if response.status_code == 200:
        data = response.json()
        new_quakes = set()
        if data.get("features"):
            for feature in data["features"]:
                eq_id = feature['id']
                if eq_id not in previous_quakes:
                    date_time = datetime.fromtimestamp(feature['properties']['time'] / 1000)
                    mag = feature['properties']['mag']
                    place = feature['properties']['place']
                    # Print the earthquake alert to the console
                    if first_run == False:
                        print(f"{date_time.strftime('%d/%m/%y %H:%M:%S')}: Magnitude {mag} earthquake detected at {place}")
                        # Pass the earthquake alert to a Linux command to display it on a screen
                        message = f"רעידת אדמה בעוצמה [{mag}] ריכטר הורגשה ב {place}"
                        cmd = ALERT_CMD + [message, "OK"]
                        try:
                            result = subprocess.run(cmd, capture_output=True, text=True, timeout=3)
                            # Extract the alertId value from the command output
                            output = result.stdout.strip()
                            response_dict = json.loads(output.split('\n')[0])
                            alert_id = response_dict["payload"]["alertId"]
                            # Wait for 15 seconds
                            time.sleep(15)
                            # Pass a close message to the same Linux command to remove the alert from the screen
                            cmd = CLOSE_CMD + [alert_id]
                            result = subprocess.run(cmd, capture_output=True, text=True, timeout=3)
                            time.sleep(3)
                        except Exception as e:
                            print("--- TV if Off or Offline ---")
                    else:
                        print(f"{date_time.strftime('%d/%m/%y %H:%M:%S')}: Magnitude {mag} earthquake detected at {place}")
                    new_quakes.add(eq_id)
        else:
            current_query = f"{start_time}-->{datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')}"
            if current_query != previous_query:
                print(f"{datetime.now().strftime('%d/%m/%y %H:%M:%S')}: No earthquakes detected within 600km of Israel in the past {x_hours} hour")
                previous_query = current_query

        # Update the previous_quakes set with new_quakes
        previous_quakes.update(new_quakes)
    #else:
    #    print(f"{datetime.now().strftime('%d/%m/%y %H:%M:%S')}: Error fetching earthquake data: {response.status_code}")

    if response.status_code == 200 and first_run == True:
        first_run = False
    time.sleep(10)
