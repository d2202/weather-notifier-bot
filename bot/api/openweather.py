import logging

import requests

from bot import settings
from bot.emoji import Emoji

logger = logging.getLogger(__name__)


class OpenWeatherAPIException(BaseException):
    """
    Для обработки ошибок на уровне API OpenWeather
    """

    pass


class OpenWeatherAPIService:
    def __init__(self):
        self.openweather_base_url = "http://api.openweathermap.org/data/2.5/"
        self.emoji_service = Emoji()

    def get_weather_now(self, city):
        weather_url = self.openweather_base_url + "weather?"
        params = {
            "lang": "ru",
            "units": "metric",
            "q": city,
            "appid": settings.OPENWEATHER_TOKEN,
        }
        response = requests.get(weather_url, params=params)
        data_json = response.json()
        if int(data_json["cod"]) != 200:
            logger.error(
                "Error on request to OpenWeather API",
                response=response.json,
                status=data_json["cod"],
            )
            raise OpenWeatherAPIException("Произошла ошибка при обращении к сервису OpenWeather")
        return data_json

    def get_daily_forecast(self, city):
        forecast_url = self.openweather_base_url + "forecast?"
        params = {
            "lang": "ru",
            "units": "metric",
            "q": city,
            "cnt": 4,  # вернет в поле list список из трёх временных промежутков: 9, 12, 15 часов
            "appid": settings.OPENWEATHER_TOKEN,
        }
        response = requests.get(forecast_url, params=params)
        data_json = response.json()
        if int(data_json["cod"]) != 200:
            logger.error(
                f"Error on request to OpenWeather API \nresponse: {response.json()}, status: {data_json['cod']}",
            )
            raise OpenWeatherAPIException("Произошла ошибка при обращении к сервису OpenWeather")
        return data_json

    def make_now_forecast_message(self, data, user_city):
        weather_icon = data["weather"][0]["icon"]
        weather_descr = data["weather"][0]["description"]
        wind = round(data["wind"]["speed"])
        actual_temp = int(data["main"]["temp"])
        feels_temp = int(data["main"]["feels_like"])
        emoji_icon = self.emoji_service.get_weather_emoji(weather_icon)

        message = f"""
        Прямо сейчас в городе {user_city}
\n{emoji_icon} {weather_descr}
{self.emoji_service.WIND} Ветер: {wind} м/с
{self.emoji_service.THERMOMETER} Температура: {actual_temp}
{self.emoji_service.THERMOMETER} Ощущается как: {feels_temp}
        """
        return message

    @staticmethod
    def get_daily_forecast_message(data, user_id):
        city_name = data["city"]["name"]
        weather_data_element = len(data["list"]) - 2  # выбираем элемент, где время = 15.00
        weather_descr = data["list"][weather_data_element]["weather"][0]["description"]

        temperatures_today = [round(item["main"]["temp"]) for item in data["list"][1:]]
        feels_temp_today = [round(item["main"]["feels_like"]) for item in data["list"][1:]]
        min_temp, max_temp = min(temperatures_today), max(temperatures_today)
        min_feels, max_feels = min(feels_temp_today), max(feels_temp_today)
        actual_temp = f"{min_temp} - {max_temp}"
        feels_temp = f"{min_feels} - {max_feels}"
        wind = round(data["list"][weather_data_element]["wind"]["speed"])

        message = {
            "user_id": user_id,
            "city": city_name,
            "weather_desc": weather_descr,
            "wind": wind,
            "temp_actual": actual_temp,
            "temp_feels": feels_temp,
        }
        logger.info(f"Just made another daily forecast for user {user_id}")
        return message

    def make_user_daily_forecast_message(self, user):
        user_city = user["city"]
        user_weather_desc = user["weather_desc"]
        user_wind = user["wind"]
        user_temp_actual = user["temp_actual"]
        user_temp_feels = user["temp_feels"]

        message = f"""Сегодня днём в городе {user_city} ожидается:
\n{self.emoji_service.BLUE_MARK} {user_weather_desc}
{self.emoji_service.WIND}Ветер: {user_wind} м/с
{self.emoji_service.THERMOMETER}Температура: {user_temp_actual}
{self.emoji_service.THERMOMETER}Ощущается как: {user_temp_feels}\n"""

        return message
