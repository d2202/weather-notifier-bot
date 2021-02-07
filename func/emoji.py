# Emoji list:
TIME = '\U0001F556'
SUN_CLOUD = '\U000026C5'
HELP = '\U0001F198'
STOP = '\U0001F6AB'
RADIO_BUTTON = '\U0001F518'
CHECK = '\U00002714'
BLUE_MARK = '\U0001F539'
WIND = '\U0001F4A8'
THERMOMETER = '\U0001F321'

# Openweather icons to emoji
weather_conditions = {
    '01d': '\U00002600',
    '01n': '\U0001F316',
    '02d': '\U0001F325',
    '02n': '\U0001F325',
    '03d': '\U00002601',
    '03n': '\U00002601',
    '04d': '\U00002601',
    '04n': '\U00002601',
    '09d': '\U0001F327',
    '09n': '\U0001F327',
    '10d': '\U0001F326',
    '10n': '\U0001F326',
    '11d': '\U000026C8',
    '11n': '\U000026C8',
    '13d': '\U00002744',
    '13n': '\U00002744',
    '50d': '\U0001F32B',
    '50n': '\U0001F32B'
}

def return_emoji(openweather_icon):
    try:
        return weather_conditions[openweather_icon]
    except KeyError:
        return BLUE_MARK
