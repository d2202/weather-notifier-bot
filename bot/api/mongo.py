import logging

from pymongo import MongoClient, errors

from bot import settings
from bot.api.openweather import OpenWeatherAPIService

logger = logging.getLogger(__name__)


class MongoDBServiceException(BaseException):
    """
    Для обработки исключений на уровне базы
    """

    pass


class MongoDBService:
    def __init__(self):
        self.cluster_url = settings.DB_CLUSTER_URL
        self.cluster = MongoClient(self.cluster_url)
        self.db = self.cluster[settings.DB_NAME]
        self.collection = self.db[settings.DB_COLLECTION]
        self.openweather_service = OpenWeatherAPIService()

    def add_user(self, user_id):
        logger.info(f"Adding new user in Mongo.. user_id: {user_id}")
        user = {
            "_id": user_id,
            "weather_desc": None,
            "wind": None,
            "temp_actual": None,
            "temp_feels": None,
            "sending_time": None,
        }
        try:
            self.collection.insert_one(user)
            logger.info(f"Successfully added user to database. user_id: {user_id}")
        except errors.DuplicateKeyError:
            logger.warning(f"User already exists, skipping.. user_id: {user_id}")

    def update_or_insert_user_data(self, data):
        logger.info(f"Updating users data.. data: {data}")
        user_data = {
            "_id": data["user_id"],
            "city": data["city"],
            "weather_desc": data["weather_desc"],
            "wind": data["wind"],
            "temp_actual": data["temp_actual"],
            "temp_feels": data["temp_feels"],
        }
        if not self.is_user(data["user_id"]):
            logger.warning(f"User not in DB, adding... user_id: {data['user_id']}")
            self.collection.insert_one(user_data)
        else:
            logger.info(f"Updating user data... user_id: {data['user_id']}")
            self.collection.update_one({"_id": data["user_id"]}, {"$set": user_data})

    def delete_user_by_id(self, user_id):
        if self.is_user(user_id):
            logger.info(f"Deleting user from database... user_id: {user_id}")
            self.collection.delete_one({"_id": user_id})
        else:
            logger.warning(f"User not found in database, user_id: {user_id}")
            raise MongoDBServiceException("Пользователь не найден в базе")

    def get_all_users(self):
        users_list = []
        mongo_users = self.collection.find({})
        for user in mongo_users:
            users_list.append(user)
        return users_list

    def update_user_city(self, user_id, city):
        if self.is_user(user_id):
            self.collection.update_one({"_id": user_id}, {"$set": {"city": city}})
        else:
            logger.error(f"User not found in database user_id: {user_id}")
            raise MongoDBServiceException("Пользователь не найден в базе")

    def update_user_sending_time(self, user_id, new_time):
        if self.is_user(user_id):
            self.collection.update_one({"_id": user_id}, {"$set": {"sending_time": new_time}})
            logger.info(f"Updated sending time for user_id: {user_id}")
        else:
            logger.error(f"User not found in database user_id: {user_id}")
            raise MongoDBServiceException("Пользователь не найден в базе")

    def is_user(self, user_id):
        return True if self.collection.find_one({"_id": user_id}) else False

    def update_forecast_for_users(self, users_list):
        for user in users_list:
            user_id = user["_id"]
            forecast_for_today = self.openweather_service.get_daily_forecast(user["city"])
            forecast_data = self.openweather_service.get_daily_forecast_message(forecast_for_today, user_id)
            logger.info(f"Updated daily forecast for user_id: {user_id}")
            self.update_or_insert_user_data(forecast_data)
