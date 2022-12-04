import datetime
import logging
import re
from threading import Thread
from time import sleep

import pytz
import schedule
import telebot

from bot import settings
from bot.api.mongo import MongoDBService, MongoDBServiceException
from bot.api.openweather import OpenWeatherAPIException, OpenWeatherAPIService
from bot.emoji import Emoji

bot = telebot.TeleBot(settings.BOT_TOKEN)
openweather_service = OpenWeatherAPIService()
emoji = Emoji()
db_service = MongoDBService()
logger = logging.getLogger(__name__)

# время, когда будут происходить обновления прогнозов для всех юзеров
update_time = datetime.time(hour=6, minute=0, tzinfo=pytz.timezone("Europe/Moscow"))


def schedule_checker():
    while True:
        schedule.run_pending()
        sleep(1)


@bot.message_handler(commands=["start"])
def handle_start(message):
    name = message.from_user.first_name
    user_id = message.from_user.id
    answer = f"""Привет, {name}!\nЯ буду присылать тебе погоду на день каждое утро.
Выбери город и утром будешь получать свежий прогноз :) """
    logging.info("Started new session with user", extra={"user_id": user_id})
    bot.send_message(user_id, answer)
    get_help(message)


@bot.message_handler(commands=["help"])
def get_help(message):
    logging.info(f"Sent help message to user {message.from_user.id}")
    help_message = f"""
Прежде всего нужно выбрать город, для которого будет
 находиться прогноз. Для этого отправь мне название своего города, после этого я пришлю тебе прогноз на текущий час.
 {emoji.RADIO_BUTTON} Если захочешь, могу запомнить город и присылать в выбранное время прогноз на день.
 {emoji.RADIO_BUTTON} Для этого нажми кнопку {emoji.CHECK} "Запомнить *твой город*" после введения города,
а затем выбери время, в которое тебе удобно будет получать прогноз.

 Список команд, которые должны тебе помочь (учти, я должен знать город!):\n
 {emoji.TIME} /time - позволяет изменить время получения утреннего прогноза
 {emoji.SUN_CLOUD} /now - выведет пронгоз на текущий час
 {emoji.HELP} /help - выведет еще раз эту подсказку
 {emoji.STOP} /stop - отписаться от рассылки прогноза (для повторной рассылки нужно будет\
 заново указать свой город.)
    """
    bot.send_message(message.from_user.id, help_message)


@bot.message_handler(commands=["now"])
def get_now_forecast(message):
    user_id = message.from_user.id
    if db_service.is_user(user_id):
        forecasts_user_list = db_service.get_all_users()
        for user in forecasts_user_list:
            if user["_id"] == user_id:
                current_weather = openweather_service.get_weather_now(user["city"])
                forecast_msg = openweather_service.make_now_forecast_message(current_weather, user["city"])
                bot.send_message(user_id, forecast_msg)
                logging.info(f"User requested now forecast {user_id}")
    else:
        bot.send_message(user_id, "Для начала мне нужно узнать твой город...")
        logging.error(f"User is trying to request now forecast but city not in db {user_id}")


@bot.message_handler(commands=["time"])
def command_set_time(message):
    if db_service.is_user(message.from_user.id):
        logging.info(f"User called TIME function handler {message.from_user.id}")
        user_markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        user_markup.row("7:00")
        user_markup.row("7:30")
        user_markup.row("8:00")
        user_markup.row("8:30")
        user_markup.row("9:00")
        msg = bot.send_message(
            message.from_user.id,
            "Выбери время получения прогноза.",
            reply_markup=user_markup,
        )
        bot.register_next_step_handler(msg, _set_time)
    else:
        hide_markup = telebot.types.ReplyKeyboardRemove()
        bot.send_message(
            message.from_user.id,
            "Для начала мне надо узнать твой город.",
            reply_markup=hide_markup,
        )
        logging.error(
            f"User call TIME but there is no user info in DB {message.from_user.id}",
        )


@bot.message_handler(commands=["stop"])
def stop_working(message):
    user_id = message.from_user.id
    try:
        db_service.delete_user_by_id(user_id=user_id)
        logging.info(f"user_id: {user_id} data deleted from Mongo")
        bot.send_message(
            message.from_user.id,
            "Спасибо за использование! Твои данные удалены из рассылки.\nНадеюсь, ты вернешься:)",
        )
    except MongoDBServiceException as e:
        logging.info(str(e))
        bot.send_message(message.from_user.id, "Спасибо за использование!")


@bot.message_handler(content_types=["text"])
def parse_city(message):
    logging.info(f"User tried to get forecast. {message.text}")
    city = message.text
    user_id = message.from_user.id

    try:
        openweather_service.get_daily_forecast(city)
        user_markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        weather_now = openweather_service.get_weather_now(city)
        forecast_now = openweather_service.make_now_forecast_message(weather_now, city)
        bot.send_message(user_id, forecast_now)
        answer = f"Запомнить город {city}?"
        user_markup.row(f"Запомнить: {city}")
        user_markup.row("Не запоминать")
        msg = bot.send_message(user_id, answer, reply_markup=user_markup)
        bot.register_next_step_handler(msg, _update_city)
    except OpenWeatherAPIException as e:
        logging.error(f"An error occurred calling OpenWeatherAPI: \n{str(e)}")
        answer = "Прости, я не нашел такой город. Может, попробуем еще раз? "
        bot.send_message(user_id, answer)


def _update_city(message):
    user_id = message.from_user.id
    logging.info(f"Updating city for user {user_id}")

    hide_markup = telebot.types.ReplyKeyboardRemove()
    user_markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    user_markup.row("7:00")
    user_markup.row("7:30")
    user_markup.row("8:00")
    user_markup.row("8:30")
    user_markup.row("9:00")

    if re.match(r"Запомнить:\s(\w+)", message.text):
        if not db_service.is_user(user_id=user_id):
            logging.warning(f"Adding user to db {user_id}")
            db_service.add_user(user_id=user_id)

        markup_message = message.text.split(": ")
        new_city = markup_message[1]
        logging.info(f"Remembering new city {new_city}")

        try:
            db_service.update_user_city(user_id=user_id, city=new_city)
            logging.info(f"City updated for user_id {user_id}")
            bot.send_message(
                user_id,
                f"Теперь я буду искать прогноз погоды для города {new_city}.",
            )
            weather_data = openweather_service.get_daily_forecast(new_city)
            forecast_msg = openweather_service.get_daily_forecast_message(weather_data, message.from_user.id)
            db_service.update_or_insert_user_data(forecast_msg)
            msg = bot.send_message(
                message.from_user.id,
                "Выбери время получения прогноза.",
                reply_markup=user_markup,
            )
            bot.register_next_step_handler(msg, _set_time)
        except MongoDBServiceException as e:
            logging.error(str(e))

    elif message.text == "Не запоминать":
        bot.send_message(
            message.from_user.id,
            "Я не буду запоминать этот город для тебя.",
            reply_markup=hide_markup,
        )

    else:
        logging.error(f"Incorrect input {message.from_user.id} \n{message.text}")
        bot.send_message(
            message.from_user.id,
            "Введи город и выбери один из вариантов.",
            reply_markup=hide_markup,
        )


def _set_time(message):
    hide_markup = telebot.types.ReplyKeyboardRemove()
    if re.match(r"[7,8,9,10]:[0,3]0", message.text):
        hours, minutes = message.text.split(":")
        logging.info(f"New time for user {message.from_user.id}, {hours}:{minutes}")

        new_time_string = f"{int(hours)}:{minutes}"

        answer = "Прогноз будет приходить в указанное время каждый день."
        bot.send_message(message.from_user.id, answer, reply_markup=hide_markup)

        try:
            db_service.update_user_sending_time(message.from_user.id, new_time_string)
            logging.info(f"Updated sending time for user {message.from_user.id}")
        except MongoDBServiceException as e:
            logging.error(str(e))

    else:
        logging.error(f"Incorrect input {message.from_user.id}, \n{message.text}")
        bot.send_message(message.from_user.id, "Попробуй еще раз и выбери один из вариантов.")


def _send_forecast():
    current_time = datetime.datetime.now().time().replace(second=0, microsecond=0)
    logging.info("Scheduler in progress..")
    logging.info(f"Users list: \n{db_service.get_all_users()}")

    all_users = db_service.get_all_users()
    if current_time == update_time:
        db_service.update_forecast_for_users(users_list=all_users)
        logging.info("Updating daily forecasts.")

    for user in all_users:
        user_id = user["_id"]
        hours, minutes = user["sending_time"].split(":")
        sending_time = datetime.time(int(hours), int(minutes), tzinfo=pytz.timezone("Europe/Moscow"))

        if current_time == sending_time:
            message = openweather_service.make_user_daily_forecast_message(user=user)
            bot.send_message(user_id, message)
            logging.info(f"Sent message with daily forecast to user {user_id}")


if __name__ == "__main__":
    schedule.every().minute.do(_send_forecast)
    Thread(target=schedule_checker).start()
    bot.polling(none_stop=True)
