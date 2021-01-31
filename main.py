import telebot
import datetime
from time import sleep
import func.config as config
import func.mongo_users as mongo
import func.weather as weather
from threading import Thread
import schedule
import re


bot = telebot.TeleBot(config.bot_token)


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
    print('get_now_forecast function')
    user_id = message.from_user.id
    forecasts_list = mongo.get_users()
    for user in forecasts_list:
        if user['_id'] == user_id:
            current_weather = weather.request_weather_now(user['city'])
            forecast_now = weather.make_now_forecast(current_weather)
            bot.send_message(user_id, forecast_now)
            log(message, forecast_now)


@bot.message_handler(commands=['time'])
def command_set_time(message):
    print('command_send_time function')
    user_markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    user_markup.row('7:00')
    user_markup.row('7:30')
    user_markup.row('8:00')
    user_markup.row('8:30')
    user_markup.row('9:00')
    msg = bot.send_message(message.from_user.id, 'Выбери время получения прогноза.', reply_markup = user_markup)
    bot.register_next_step_handler(msg, set_time)


@bot.message_handler(commands=['stop'])
def stop_working(message):
    print('stopping forecast for user {}'.format(message.from_user.id))
    if mongo.delete_user(message.from_user.id):
        bot.send_message(message.from_user.id, 'Спасибо за использование! Твои данные удалены из рассылки. \nНадеюсь, ты вернешься:)')
    else:
        bot.send_message(message.from_user.id, 'Спасибо за использование!')


@bot.message_handler(content_types=['text'])
def parse_city(message):
    print('parse_city function')
    city = message.text
    user_id = message.from_user.id
    weather_data = weather.request_weather_dayly(city)
    user_markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    if weather_data:
        weather_now = weather.request_weather_now(city)
        forecast_now = weather.make_now_forecast(weather_now)
        bot.send_message(user_id, forecast_now)
        answer = 'Запомнить город?'.format(city)
        log(message, answer)
        user_markup.row('Запомнить: {}'.format(city))
        user_markup.row('Не запоминать')
        msg = bot.send_message(user_id, answer, reply_markup=user_markup)
        bot.register_next_step_handler(msg, update_city)
        # weather.make_dayly_forecast(weather_data, user_id)

    else:
        answer = 'Прости, я не нашел такой город. Может, попробуем еще раз? '
        bot.send_message(user_id, answer)
        log(message, answer)


def update_city(message):
    print('update_city!')
    hide_markup = telebot.types.ReplyKeyboardRemove()
    user_markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    user_markup.row('7:00')
    user_markup.row('7:30')
    user_markup.row('8:00')
    user_markup.row('8:30')
    user_markup.row('9:00')
    if re.match(r'Запомнить:\s(\w+)', message.text):
        markup_message = message.text.split(': ')
        new_city = markup_message[1]
        if mongo.update_city(message.from_user.id, new_city):
            bot.send_message(message.from_user.id, 'Теперь я буду искать прогноз погоды для города {}.'.format(new_city))
            weather_data = weather.request_weather_dayly(new_city)
            weather.make_dayly_forecast(weather_data, message.from_user.id)
            msg = bot.send_message(message.from_user.id, 'Выбери время получения прогноза.', reply_markup = user_markup)
            bot.register_next_step_handler(msg, set_time)
        else:
            bot.send_message(message.from_user.id, 'Тебя нет в базе, старина', reply_markup = hide_markup)
    elif message.text == 'Не запоминать':
        bot.send_message(message.from_user.id, 'Я не буду запоминать этот город для тебя.', reply_markup = hide_markup)
    else:
        bot.send_message(message.from_user.id, 'Введи город и выбери один из вариантов.', reply_markup = hide_markup)


def set_time(message):
    print('set_time function')
    hide_markup = telebot.types.ReplyKeyboardRemove()
    if re.match(r'[7,8,9,10]:[0,3]0', message.text):
        hours, minutes = message.text.split(':')
        new_time_string = '{0}:{1}'.format(int(hours) - 3, int(minutes))
        answer = 'Прогноз будет приходить в указанное время каждый день.'
        bot.send_message(message.from_user.id, answer, reply_markup=hide_markup)
        if mongo.update_sending_time(message.from_user.id, new_time_string):
            print('user found, time updated')
            print('new time: ' + new_time_string)
        else:
            print('user {} not found'.format(user_id))
    else:
        msg = 'Попробуй еще раз и выбери один из вариантов.'
        bot.send_message(message.from_user.id, msg)


def send_forecast():
    current_time = datetime.datetime.now().time().replace(second=0, microsecond=0)
    print(current_time)
    print('scheduller in progress..')
    print('users:')
    print(mongo.get_users())
    update_time = datetime.time(3, 0)  # время, когда будут происходить обновления прогнозов для всех юзеров, 6 утра
    if current_time == update_time:
        weather.update_dayly_forecast()
        print('updated dayly forecasts!')
        print(mongo.get_users())
    users_forecasts = mongo.get_users()
    for user in users_forecasts:
        '''
        оказывается, mongodb не умеет хранить время в формате datetime,
        поэтому приходится изобретать костыли.
        '''
        hours, minutes = user['sending_time'].split(':')
        sending_time = datetime.time(int(hours), int(minutes))
        if current_time == sending_time:
            answer = """Сегодня днём в городе {0} ожидается:
\n{1}
Температура: {2}
Ощущается как: {3}""".format(user['city'], user['weather_desc'], user['temp_actual'], user['temp_feels'])
            print('sended message to user!', user['_id'])
            bot.send_message(user['_id'], answer)


if __name__ == '__main__':
    schedule.every().minute.do(send_forecast)
    Thread(target=schedule_checker).start()
    bot.polling(none_stop=True)
