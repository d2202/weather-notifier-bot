import telebot
from datetime import datetime
import requests
import config


url = 'https://api.telegram.org/bot{0}/'.format(config.bot_token)
print(config.weather_token, config.bot_token)
print(url)

bot = telebot.TeleBot(config.bot_token)


def log(message, answer):
    print("\n -------- ")
    print(datetime.now())
    print("Сообщение от {0} {1}. (id = {2}) \nТекст - {3}".format(message.from_user.first_name, message.from_user.last_name, str(message.from_user.id), message.text))
    print("Ответ - ", answer)
    print("\n -------- ")


@bot.message_handler(commands=['start'])
def handle_start(message):
    name = message.from_user.first_name
    answer = """Привет, {}!\nЯ буду присылать тебе погоду на день каждое утро. 
Выбери город и каждый день в 9 утра будешь получать свежий прогноз :) """.format(name)
    log(message, answer)
    bot.send_message(message.from_user.id, answer)
    get_help(message)


@bot.message_handler(commands=['help'])
def get_help(message):
    help_message = """Прежде всего нужно выбрать город, для которого будет находиться прогноз.
Для этого отправь мне название своего города.
    """
    log(message, help_message)
    bot.send_message(message.from_user.id, help_message)


@bot.message_handler(commands=['city'])
def set_city(message):
    bot.send_message(message.from_user.id, 'Отправь мне название города.')


@bot.message_handler(content_types=['text'])
def get_city(message):
    city = message.text
    bot.send_message(message.from_user.id, 'Ты отправил {}. Теперь я буду искать прогноз погоды для этого города.'.format(city))
    # TODO: парсинг города в openweather, разбор json на нужные данные, формирование ответа.
    request_weather(city)


def request_weather(city):
    openweather_url = 'http://api.openweathermap.org/data/2.5/weather?'
    params = {
        'lang': 'ru',
        'units': 'metric',
        'q': city,
        'appid': config.weather_token
    }
    r = requests.get(openweather_url, params=params)
    data_json = r.json()
    return data_json


if __name__ == '__main__':
    bot.polling(none_stop=True)

