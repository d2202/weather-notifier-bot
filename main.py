import telebot
import datetime
import requests
import config


url = 'https://api.telegram.org/bot{0}/'.format(config.bot_token)

print(config.weather_token, config.bot_token)
print(url)

bot = telebot.TeleBot(config.bot_token)


@bot.message_handler(commands=['start', 'help'])
def welcome(message):
    answer = """Привет!\nЯ буду присылать тебе погоду на день каждое утро. \nВыбери город и каждый день в 9 утра будешь получать свежий прогноз :) """
    bot.send_message(message.chat.id, answer)


if __name__ == '__main__':
    bot.polling(none_stop=True)

