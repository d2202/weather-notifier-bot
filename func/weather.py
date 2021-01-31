import func.mongo_users as mongo
import requests
import datetime


def request_weather_now(city):
    openweather_url = 'http://api.openweathermap.org/data/2.5/weather?'
    params = {
        'lang': 'ru',
        'units': 'metric',
        'q': city,
        'appid': '755b75d5118c5741fb355e027ec288b4'
    }
    r = requests.get(openweather_url, params=params)
    data_json = r.json()
    if int(data_json['cod']) != 200:
        return None
    return data_json


def request_weather_dayly(city):
    openweather_url = 'http://api.openweathermap.org/data/2.5/forecast?'
    params = {
        'lang': 'ru',
        'units': 'metric',
        'q': city,
        'cnt': 3, # вернет в поле list список из трёх временных промежутков: 9, 12, 15 часов
        'appid': '755b75d5118c5741fb355e027ec288b4'
    }
    r = requests.get(openweather_url, params=params)
    data_json = r.json()
    if int(data_json['cod']) != 200:
        return None
    return data_json


def make_now_forecast(data, user_id):
    print('make_now_forecast function')
    city_name = data['name']
    weather_desc = data['weather'][0]['description']
    actual_temp = int(data['main']['temp'])
    feels_temp = int(data['main']['feels_like'])
    forecast = """Прямо сейчас в городе {0}:
\n{1}
Температура: {2}
Ощущается как: {3}""".format(city_name, weather_desc, actual_temp, feels_temp)
    return forecast


def make_dayly_forecast(data, user_id):
    print('make_dayly_forecast function.')
    city_name = data['city']['name']
    weather_data_element = len(data['list']) - 1 # выбираем элемент, где время = 15.00
    weather_desc = data['list'][weather_data_element]['weather'][0]['description']
    actual_temp = int(data['list'][weather_data_element]['main']['temp'])
    feels_temp = int(data['list'][weather_data_element]['main']['feels_like'])
    forecast_dayly = {
        'user_id': user_id,
        'city': city_name,
        'weather_desc': weather_desc,
        'temp_actual': actual_temp,
        'temp_feels': feels_temp,
        # 'sending_time': '5:00'
    }
    print(forecast_dayly)
    mongo.update_user_data(forecast_dayly)


def update_dayly_forecast():
    users_forecasts = mongo.get_users()
    for user in users_forecasts:
        forecast_for_today = request_weather_dayly(user['city'])
        make_dayly_forecast(forecast_for_today, user['_id'])
