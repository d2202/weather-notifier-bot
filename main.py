import telebot
import datetime
from time import sleep
import func.emoji as emoji
import func.config as config
import func.mongo_users as mongo
import func.weather as weather
from threading import Thread
import schedule
import re
import logging


bot = telebot.TeleBot(config.bot_token)
logging.basicConfig(format = u'%(filename)s[LINE:%(lineno)d]#\
%(levelname)-8s[%(asctime)s] [FUNC: %(funcName)s] %(message)s', level = logging.INFO)


def schedule_checker():
    while True:
        schedule.run_pending()
        sleep(1)


@bot.message_handler(commands=['start'])
def handle_start(message):
    name = message.from_user.first_name
    user_id = message.from_user.id
    answer = f"""Привет, {name}!\nЯ буду присылать тебе погоду на день каждое утро.
Выбери город и утром будешь получать свежий прогноз :) """
    logging.info(f'Started new session with user {user_id}')
    bot.send_message(user_id, answer)
    get_help(message)


@bot.message_handler(commands=['help'])
def get_help(message):
    logging.info(f'Sended help message to user {message.from_user.id}')
    help_message = f"""Прежде всего нужно выбрать город, для которого будет\
 находиться прогноз. Для этого отправь мне название своего города, после этого я пришлю тебе\
 прогноз на текущий час.
 {emoji.RADIO_BUTTON} Если захочешь, могу запомнить город и присылать в выбранное время прогноз на день.
 {emoji.RADIO_BUTTON} Для этого нажми кнопку {emoji.CHECK} "Запомнить *твой город*" после введения города,\
 а затем выбери время, в которое тебе удобно будет получать прогноз.

 Список комманд, которые должны тебе помочь (учти, я должен знать город!):\n
 {emoji.TIME} /time - позволяет изменить время получения утреннего прогноза
 {emoji.SUN_CLOUD} /now - выведет пронгоз на текущий час
 {emoji.HELP} /help - выведет еще раз эту подсказку
 {emoji.STOP} /stop - отписаться от рассылки прогноза (для повторной рассылки нужно будет\
 заново указать свой город.)
    """
    bot.send_message(message.from_user.id, help_message)


@bot.message_handler(commands=['now'])
def get_now_forecast(message):
    user_id = message.from_user.id
    if mongo.is_user(user_id):
        forecasts_list = mongo.get_users()
        for user in forecasts_list:
            if user['_id'] == user_id:
                current_weather = weather.request_weather_now(user['city'])
                forecast_now = weather.make_now_forecast(current_weather)
                bot.send_message(user_id, forecast_now)
                logging.info(f'User {user_id} requested now forecast')
                logging.info(f'Answer: \n{forecast_now}')
    else:
        bot.send_message(user_id, 'Для начала мне нужно узнать твой город...')
        logging.error(f'{user_id} is trying to request now forecast,\
                        but user\'s city  not in db')


@bot.message_handler(commands=['time'])
def command_set_time(message):
    if mongo.is_user(message.from_user.id):
        logging.info(f'user {message.from_user.id} call TIME function handler')
        user_markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        user_markup.row('7:00')
        user_markup.row('7:30')
        user_markup.row('8:00')
        user_markup.row('8:30')
        user_markup.row('9:00')
        msg = bot.send_message(message.from_user.id, 'Выбери время получения прогноза.', reply_markup = user_markup)
        bot.register_next_step_handler(msg, set_time)
    else:
        hide_markup = telebot.types.ReplyKeyboardRemove()
        bot.send_message(message.from_user.id, 'Для начала мне надо узнать твой город...', reply_markup = hide_markup)
        logging.error(f'user {message.from_user.id} call TIME but there is no user info in Mongo!')


@bot.message_handler(commands=['stop'])
def stop_working(message):
    if mongo.delete_user(message.from_user.id):
        logging.info(f'user {message.from_user.id} data deleted from Mongo')
        bot.send_message(message.from_user.id, 'Спасибо за использование! Твои данные удалены из рассылки.\
        \nНадеюсь, ты вернешься:)')
    else:
        logging.info(f'user {message.from_user.id} has no data in Mongo, just say "bye"')
        bot.send_message(message.from_user.id, 'Спасибо за использование!')


@bot.message_handler(content_types=['text'])
def parse_city(message):
    logging.info(f'user {message.from_user.id} trying to get forecast.\
                    \nmessage: {message.text}')
    city = message.text
    user_id = message.from_user.id
    weather_data = weather.request_weather_dayly(city)
    user_markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    if weather_data:
        logging.info(f'{message.text} is a valid city. Making forecast.')
        weather_now = weather.request_weather_now(city)
        forecast_now = weather.make_now_forecast(weather_now)
        bot.send_message(user_id, forecast_now)
        answer = f'Запомнить город {city}?'
        user_markup.row(f'Запомнить: {city}')
        user_markup.row('Не запоминать')
        msg = bot.send_message(user_id, answer, reply_markup=user_markup)
        bot.register_next_step_handler(msg, update_city)
    else:
        answer = 'Прости, я не нашел такой город. Может, попробуем еще раз? '
        bot.send_message(user_id, answer)


def update_city(message):
    logging.info(f'User {message.from_user.id} called update city func')
    hide_markup = telebot.types.ReplyKeyboardRemove()
    user_markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    user_markup.row('7:00')
    user_markup.row('7:30')
    user_markup.row('8:00')
    user_markup.row('8:30')
    user_markup.row('9:00')
    if re.match(r'Запомнить:\s(\w+)', message.text):
        if not mongo.is_user(message.from_user.id):
            logging.warning(f'{message.from_user.id} is not in Mongo, adding..')
            mongo.add_user(message.from_user.id)
        markup_message = message.text.split(': ')
        new_city = markup_message[1]
        logging.info(f'Remembering new city - {new_city}')
        if mongo.update_city(message.from_user.id, new_city):
            logging.info(f'City updated for user {message.from_user.id}.')
            bot.send_message(message.from_user.id, f'Теперь я буду искать прогноз погоды для города {new_city}.')
            weather_data = weather.request_weather_dayly(new_city)
            weather.make_dayly_forecast(weather_data, message.from_user.id)
            msg = bot.send_message(message.from_user.id, 'Выбери время получения прогноза.', reply_markup = user_markup)
            bot.register_next_step_handler(msg, set_time)
    elif message.text == 'Не запоминать':
        logging.info(f'NOT remembering new city')
        bot.send_message(message.from_user.id, 'Я не буду запоминать этот город для тебя.', reply_markup = hide_markup)
    else:
        logging.error(f'{message.from_user.id} Incorrect input: \n{message.text}')
        bot.send_message(message.from_user.id, 'Введи город и выбери один из вариантов.', reply_markup = hide_markup)


def set_time(message):
    hide_markup = telebot.types.ReplyKeyboardRemove()
    if re.match(r'[7,8,9,10]:[0,3]0', message.text):
        hours, minutes = message.text.split(':')
        logging.info(f'New time for user {message.from_user.id}: {hours}:{minutes}')
        new_time_string = f'{int(hours) - 3}:{minutes}'
        answer = 'Прогноз будет приходить в указанное время каждый день.'
        bot.send_message(message.from_user.id, answer, reply_markup=hide_markup)
        if mongo.update_sending_time(message.from_user.id, new_time_string):
            logging.info(f'user {message.from_user.id} found, time updated. \
                        new time: {new_time_string}')
        else:
            logging.error(f'user {message.from_user.id} not found in Mongo!')
    else:
        logging.error(f'{message.from_user.id} Incorrect input: \n{message.text}')
        msg = 'Попробуй еще раз и выбери один из вариантов.'
        bot.send_message(message.from_user.id, msg)


def send_forecast():
    current_time = datetime.datetime.now().time().replace(second=0, microsecond=0)
    logging.info('Scheduler in progress..')
    logging.info(f'Users list: \n{mongo.get_users()}')
    update_time = datetime.time(3, 0)  # время, когда будут происходить обновления прогнозов для всех юзеров, 6 утра
    if current_time == update_time:
        weather.update_dayly_forecast()
        logging.info('The time has come! UPDATE DAYLY FORECASTS!')
    users_forecasts = mongo.get_users()
    for user in users_forecasts:
        user_id = user['_id']
        user_city = user['city']
        user_weather_desc = user['weather_desc']
        user_wind = user['wind']
        user_temp_actual = user['temp_actual']
        user_temp_feels = user['temp_feels']
        '''
        оказывается, mongodb не умеет хранить время в формате datetime,
        поэтому приходится изобретать костыли.
        '''
        hours, minutes = user['sending_time'].split(':')
        sending_time = datetime.time(int(hours), int(minutes))
        if current_time == sending_time:
            answer = f"""Сегодня днём в городе {user_city} ожидается:
\n{emoji.BLUE_MARK} {user_weather_desc}
{emoji.WIND}Ветер: {user_wind} м/с
{emoji.THERMOMETER}Температура: {user_temp_actual}
{emoji.THERMOMETER}Ощущается как: {user_temp_feels}\n\n
{weather.make_reaction(int(user_temp_actual))}"""
            bot.send_message(user_id, answer)
            logging.info(f'Sended message with dayly forecast to user {user_id}')


if __name__ == '__main__':
    schedule.every().minute.do(send_forecast)
    Thread(target=schedule_checker).start()
    bot.polling(none_stop=True)
