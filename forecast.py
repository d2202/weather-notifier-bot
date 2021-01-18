class ForecastSingleton(object):
    user_id = None
    city = ''
    weather_desc = ''
    temp_actual = None
    temp_feels = None

    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(ForecastSingleton, cls).__new__(cls)
        return cls.instance

    def set_user_id(self, user_id):
        self.user_id = user_id

    def set_city(self, city):
        self.city = city

    def set_weather_desc(self, desc):
        self.weather_desc = desc

    def set_temp_actual(self, temp_actual):
        self.temp_actual = temp_actual

    def set_temp_feels(self, temp_feels):
        self.temp_feels = temp_feels

    def get_user_id(self):
        return self.user_id

    def get_city(self):
        return self.city

    def get_weather_desc(self):
        return self.weather_desc

    def get_temp_actual(self):
        return self.temp_actual

    def get_temp_feels(self):
        return self.temp_feels
