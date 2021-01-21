import datetime

class ForecastSingletone(object):
    forecasts_data = []
    # user_id = None
    # city = ''
    # weather_desc = ''
    # temp_actual = None
    # temp_feels = None

    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(ForecastSingletone, cls).__new__(cls)
        return cls.instance

    def set_data(self, data):
        # я без понятия как это оптимизировать.
        new_forecast = {}
        new_forecast['user_id'] = data['user_id']
        new_forecast['city'] = data['city']
        new_forecast['weather_desc'] = data['weather_desc']
        new_forecast['temp_actual'] = data['temp_actual']
        new_forecast['temp_feels'] = data['temp_feels']
        new_forecast['sending_time'] = datetime.time(5, 0)
        for user_data in self.forecasts_data:
            if user_data['user_id'] == data['user_id']:
                user_data['city'] = data['city']
                user_data['weather_desc'] = data['weather_desc']
                user_data['temp_actual'] = data['temp_actual']
                user_data['temp_feels'] = data['temp_feels']
                return
        self.forecasts_data.append(new_forecast)

    def get_users_data(self):
        return self.forecasts_data
