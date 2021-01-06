bot_token = '1470059803:AAFXWn7_WbNh50W_AmQjNSRtRqitX-7sL7g'
weather_token = '755b75d5118c5741fb355e027ec288b4'


def get_bot_api_url():
    url = 'https://api.telegram.org/bot{0}/'.format(bot_token)
    return url


def get_weather_api_url():
    url = 'http://api.openweathermap.org/data/2.5/weather?'
    params = {
        'lang': 'ru',
        'units': 'metric',
        'q': None,
        'appid': None
    }
    return [url, params]
