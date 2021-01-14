import telebot
from datetime import datetime
from time import sleep
import requests
import config


bot = telebot.TeleBot(config.bot_token)


def log(message, answer):
    print("\n -------- ")
    print(datetime.now())
    print("Сообщение от {0} {1}. (id = {2}) \nТекст - {3}".format(message.from_user.first_name, message.from_user.last_name, str(message.from_user.id), message.text))
    print("Ответ - ", answer)
    print("\n -------- ")


def errors_log(error_msg):
    red_color = "\033[1;31m"
    reset_color = "\033[0;0m"
    print("\n -------- ")
    print(datetime.now())
    print(red_color + error_msg + reset_color)
    print("\n -------- ")


@bot.message_handler(commands=['start'])
def handle_start(message):
    name = message.from_user.first_name
    answer = """Привет, {}!\nЯ буду присылать тебе погоду на день каждое утро. 
Выбери город и каждый день утром будешь получать свежий прогноз :) """.format(name)
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


@bot.message_handler(content_types=['text'])
def get_city(message):
    city = message.text
    user_id = message.from_user.id
    weather_data = request_weather(city)
    if weather_data:
        answer = 'Твой город - {}. Теперь я буду искать прогноз погоды для него.'.format(city)
        bot.send_message(message.from_user.id, answer)
        log(message, answer)
        scheduler(user_id, weather_data)
    else:
        answer = 'Прости, я не нашел такой город. Может, попробуем еще раз? '
        bot.send_message(message.from_user.id, answer)
        log(message, answer)


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
    if data_json['cod'] != 200:
        return None
    return data_json

#TODO как запускать это в бесконечном цикле, что передавать?
def scheduler(user_chat_id, data):
    current_time = datetime.datetime.now().time().replace(second=0, microsecond=0)
    sending_time = datetime.time(11, 0) # +3 часа разницы в часовых поясах, формат H M
    print('Will send message at {} MSK'.format(sending_time))
    if (current_time == sending_time):
        send_weather(user_chat_id, data)
        print("\n -------- ")
        print(datetime.now())
        print('Message to user id {0} at time {1} MSK'.format(user_chat_id, sending_time))
    else:
        sleep(60)

def send_weather(user_chat_id, data):
    city_name = data['name']
    weather_desc = data['weather'][0]['description']
    actual_temp = int(data['main']['temp'])
    feels_temp = int(data['main']['feels_like'])
    answer = """Город: {0}
Прогноз: {1}
Температура: {2}
Ощущается как: {3}""".format(city_name, weather_desc, actual_temp, feels_temp)
    bot.send_message(user_chat_id, answer)


if __name__ == '__main__':
    bot.polling(none_stop=True)
    while(True):
        try:
            scheduler(get_city(message))
        except Exception as e:
            errors_log(e)

