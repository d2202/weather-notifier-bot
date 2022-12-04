import logging
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENWEATHER_TOKEN = os.getenv("OPENWEATHER_TOKEN")
MONGO_USER = os.getenv("MONGO_USER")
MONGO_PASSWD = os.getenv("MONGO_PASSWD")
DB_NAME = os.getenv("DB_NAME")
DB_COLLECTION = os.getenv("DB_COLLECTION")
DB_CLUSTER_URL = (
    f"mongodb+srv://{MONGO_USER}:{MONGO_PASSWD}@weather-bot.g2wrn.mongodb.net/{DB_NAME}?retryWrites=true&w=majority"
)

logging.basicConfig(
    format="%(filename)s[LINE:%(lineno)d]#%(levelname)-8s[%(asctime)s] [FUNC: %(funcName)s] %(message)s",
    level=logging.INFO,
)
