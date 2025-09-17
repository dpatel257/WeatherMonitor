#!/bin/bash
source <<PATH>>/WeatherMonitor/weather_env/bin/activate
python3 <<PATH>>/WeatherMonitor/collectAndPush.py
deactivate
