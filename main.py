import os
import json
import requests

from flask import Flask, request, jsonify
import googlemaps

app = Flask(__name__)

google_geocoding_api_key = os.environ.get('GOOGLE_GEOCODING_API_KEY')
gmaps = googlemaps.Client(key=google_geocoding_api_key)

dark_sky_api_key = os.environ.get('DARK_SKY_API_KEY')

error = "I don't know the weather but I hope it's good!"


@app.route("/", methods=['POST'])
def fb_bot():
    query_result = json.loads(request.data).get('queryResult', {})
    intent = query_result.get('intent', {})
    if intent.get('displayName') != 'question_what_is_the_weather':
        return jsonify(fulfillmentText=error)

    parameters = query_result.get('parameters', {})
    query_city = parameters.get('geo-city', '')
    query_date = parameters.get('date', '')

    if query_city == '' or query_date == '':
        return jsonify(fulfillmentText=error)

    location = get_location(query_city)
    lat = location.get('lat', None)
    lng = location.get('lng', None)
    if lat is None or lng is None:
        return jsonify(fulfillmentText=error)

    weather = get_weather(lat, lng, query_city, query_date)
    if weather is None:
        return jsonify(fulfillmentText=error)

    return jsonify(fulfillmentText=weather)


def get_location(query_city):
    results = gmaps.geocode(query_city)
    if len(results) != 0:
        return results[0].get('geometry', {}).get('location', None)
    else:
        return None


def get_weather(lat, lng, query_city, query_date):
    url = 'https://api.darksky.net/forecast/%s/%f,%f,%s?' \
          'exclude=currently,minutely,hourly,alerts,flags&lang=zh-tw&units=si' \
          % (dark_sky_api_key, lat, lng, query_date)

    response = requests.get(url)
    json_response = response.json()

    data_list = json_response.get('daily', {}).get('data', [])
    if len(data_list) == 0:
        return None

    data = data_list[0]
    summary = data.get('summary', '')
    temperature_low = data.get('temperatureLow', '')
    temperature_high = data.get('temperatureHigh', '')
    apparent_temperature_low = data.get('apparentTemperatureLow', '')
    apparent_temperature_high = data.get('apparentTemperatureHigh', '')

    return '%s\n' \
           '%s\n' \
           '氣溫：%s ~ %s\n' \
           '體感溫度：%s ~ %s' \
           % (query_city, summary, temperature_low, temperature_high,
              apparent_temperature_low, apparent_temperature_high)
