import func.mongo_users as mongo
import func.config as config
import requests
import datetime
import logging


logging.basicConfig(format = u'%(filename)s[LINE:%(lineno)d]#\
%(levelname)-8s[%(asctime)s] [FUNC: %(funcName)s] %(message)s', level = logging.INFO)


def request_weather_now(city):
    openweather_url = 'http://api.openweathermap.org/data/2.5/weather?'
    params = {
        'lang': 'ru',
        'units': 'metric',
        'q': city,
        'appid': '755b75d5118c5741fb355e027ec288b4'
    }
    r = requests.get(openweather_url, params=params)
    logging.info(f'Request for {city} is: {r}')
    data_json = r.json()
    if int(data_json['cod']) != 200:
        logging.error(f'{city} is not a valid city, \
                        openweather returned 404 or service is unavaliable.')
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
        logging.error(f'{city} is not a valid city, \
                        openweather returned 404 or service is unavaliable.')
        return None
    return data_json


def make_now_forecast(data):
    city_name = data['name']
    weather_desc = data['weather'][0]['description']
    actual_temp = int(data['main']['temp'])
    feels_temp = int(data['main']['feels_like'])
    wind = round(data['wind']['speed'])
    forecast = f"""Прямо сейчас в городе {city_name}:
\n{weather_desc}
{config.BLUE_MARK}Ветер: {wind} м/с
{config.BLUE_MARK}Температура: {actual_temp}
{config.BLUE_MARK}Ощущается как: {feels_temp}"""
    return forecast


def make_dayly_forecast(data, user_id):
    city_name = data['city']['name']
    weather_data_element = len(data['list']) - 1 # выбираем элемент, где время = 15.00
    weather_desc = data['list'][weather_data_element]['weather'][0]['description']
    actual_temp = int(data['list'][weather_data_element]['main']['temp'])
    feels_temp = int(data['list'][weather_data_element]['main']['feels_like'])
    wind = round(data['list'][weather_data_element]['wind']['speed'])
    forecast_dayly = {
        'user_id': user_id,
        'city': city_name,
        'weather_desc': weather_desc,
        'wind': wind,
        'temp_actual': actual_temp,
        'temp_feels': feels_temp
    }
    logging.info(f'Just made another dayly forecast: \n{forecast_dayly}')
    mongo.update_user_data(forecast_dayly)


def update_dayly_forecast():
    users_forecasts = mongo.get_users()
    for user in users_forecasts:
        user_id = user['_id']
        forecast_for_today = request_weather_dayly(user['city'])
        make_dayly_forecast(forecast_for_today, user_id)
        logging.info(f'Updated dayly forecast for user {user_id}!')


def make_reaction(temp):
    if (26 <= temp):
        return 'Ого, вот это жара! Старайся не проводить много времени на солнце и пей больше воды!'
    if (15 <= temp <= 25):
        return 'Наслаждайся замечательной теплой погодой! :)'
    elif (5 <= temp <= 14):
        return 'Не простудись! Не забывай надевать легкую куртку:)'
    elif (-5 <= temp <= 4):
        return 'Береги горло. В такую прохладу это особенно важно.'
    elif (-15 <= temp <= -6):
        return 'Надеюсь, у тебя есть шарф. Он определенно понадобится!'
    elif (-30 <= temp <= -16):
        return 'Не забывай о теплых носках, когда выходишь на улицу! \nИли, может, лучше вообще остаться дома?:)'
