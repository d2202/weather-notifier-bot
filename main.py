import telebot
import datetime
from time import sleep
import func.config as config
# import func.forecast as forecast
import func.mongo_users as mongo

import func.weather as weather
from threading import Thread
import schedule


bot = telebot.TeleBot(config.bot_token)

# userForecast = forecast.ForecastSingletone()


def schedule_checker():
    while True:
        schedule.run_pending()
        sleep(1)

def log(message, answer):
    print("\n -------- ")
    print(datetime.datetime.now())
    print("Сообщение от {0} {1}. (id = {2}) \nТекст - {3}".format(message.from_user.first_name, message.from_user.last_name, str(message.from_user.id), message.text))
    print("Ответ - ", answer)
    print("\n -------- ")


def errors_log(error_msg):
    red_color = "\033[1;31m"
    reset_color = "\033[0;0m"
    print("\n -------- ")
    print(datetime.datetime.now())
    print(red_color + error_msg + reset_color)
    print("\n -------- ")


@bot.message_handler(commands=['start'])
def handle_start(message):
    name = message.from_user.first_name
    user_id = message.from_user.id
    answer = """Привет, {}!\nЯ буду присылать тебе погоду на день каждое утро.
Выбери город и утром будешь получать свежий прогноз :) """.format(name)
    log(message, answer)
    bot.send_message(user_id, answer)
    mongo.add_user(user_id)
    get_help(message)


@bot.message_handler(commands=['help'])
def get_help(message):
    help_message = """Прежде всего нужно выбрать город, для которого будет находиться прогноз.
Для этого отправь мне название своего города.
    """
    log(message, help_message)
    bot.send_message(message.from_user.id, help_message)


@bot.message_handler(commands=['now'])
def get_now_forecast(message):
    user_id = message.from_user.id
    # forecasts_list = userForecast.get_users_data()
    forecasts_list = mongo.get_users()
    answer = ''
    for user in forecasts_list:
        # if user['user_id'] == user_id:
        if user['_id'] == user_id:
            current_weather = weather.request_weather_now(user['city'])
            forecast_now = weather.make_now_forecast(current_weather, user_id)
            answer = """Прямо сейчас в городе {0}:
\n{1}
Температура: {2}
Ощущается как: {3}""".format(forecast_now['city'], forecast_now['weather_desc'], forecast_now['temp_actual'], forecast_now['temp_feels'])
    bot.send_message(user_id, answer)


@bot.message_handler(content_types=['text'])
def parse_city(message):
    print('parse_city function')
    city = message.text
    user_id = message.from_user.id
    weather_data = weather.request_weather_dayly(city)
    if weather_data:
        answer = 'Твой город - {}. Теперь я буду искать прогноз погоды для него.'.format(city)
        bot.send_message(message.from_user.id, answer)
        log(message, answer)
        weather.make_dayly_forecast(weather_data, user_id)
        #TODO:
        # спрашивать хочет ли пользователь запомнить город, либо прислать прогноз на текущий час
        # выбор времени, по которому будет присылаться прогноз
    else:
        answer = 'Прости, я не нашел такой город. Может, попробуем еще раз? '
        bot.send_message(message.from_user.id, answer)
        log(message, answer)

'''
def remember_city(answer):
    user_markup = telebot.types.ReplyKeyboardMarkup()
    user_markup.row('Да', 'Нет')
    if answer == 'Да':
        return True
    return False
'''

def send_forecast():
    current_time = datetime.datetime.now().time().replace(second=0, microsecond=0)
    print(current_time)
    print('scheduller in progress..')
    print('users:')
    # print(userForecast.get_users_data())
    print(mongo.get_users())
    update_time = datetime.time(3, 0) # время, когда будут происходить обновления прогнозов для всех юзеров, 6 утра
    if current_time == update_time:
        weather.update_dayly_forecast()
        print('updated dayly forecasts!')
        # print(userForecast.get_users_data())
        print(mongo.get_users())
    # users_forecasts = userForecast.get_users_data()
    users_forecasts = mongo.get_users()
    for user in users_forecasts:
        '''
        оказывается, mongodb не умеет хранить время в формате datetime,
        поэтому приходится изобретать костыли.
        '''
        hours, minutes = user['sending_time'].split(':')
        sending_time = datetime.time(int(hours), int(minutes))
        #if current_time == user['sending_time']:
        if current_time == sending_time:
            answer = """Сегодня днём в городе {0} ожидается:
\n{1}
Температура: {2}
Ощущается как: {3}""".format(user['city'], user['weather_desc'], user['temp_actual'], user['temp_feels'])
            print('sended message to user!', user['_id'])
            # bot.send_message(user['user_id'], answer)
            bot.send_message(user['_id'], answer)


if __name__ == '__main__':
    schedule.every().minute.do(send_forecast)
    Thread(target=schedule_checker).start()
    bot.polling(none_stop=True)
