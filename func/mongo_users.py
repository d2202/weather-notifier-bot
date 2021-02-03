import pymongo
from pymongo import MongoClient
import func.config as config
import logging


logging.basicConfig(format = u'%(filename)s[LINE:%(lineno)d]#\
%(levelname)-8s[%(asctime)s] [FUNC: %(funcName)s] %(message)s', level = logging.INFO)

cluster_url = f'mongodb+srv://{config.mongo_user}:{config.mongo_passwd}@weather-bot.g2wrn.mongodb.net/{config.mongo_db}?retryWrites=true&w=majority'
logging.info(f'CLUSTER URL: \n{cluster_url}')
cluster = MongoClient(cluster_url)
db = cluster[config.mongo_db]
collection = db[config.mongo_collection]

def add_user(user_id):
    logging.info(f'Adding new user {user_id} in Mongo..')
    user = {
        '_id': user_id,
        'weather_desc': None,
        'temp_actual': None,
        'temp_feels': None,
        'sending_time': "5:00"  # default value
    }
    try:
        collection.insert_one(user)
        logging.info(f'Successfully added user to database.')
    except pymongo.errors.DuplicateKeyError:
        logging.warning(f'User {user_id} already exists, skipping..')


def update_user_data(data):
    logging.info('Updating users data..')
    user_id = data['user_id']
    user_data = {
        '_id': user_id,
        'city': data['city'],
        'weather_desc': data['weather_desc'],
        'temp_actual': data['temp_actual'],
        'temp_feels': data['temp_feels'],
    }
    if not is_user(user_id):
        logging.warning(f'User {user_id} not in Mongo, adding...')
        collection.insert_one(user_data)
    else:
        logging.info(f'User {user_id} found, updating data...')
        collection.update_one({'_id': data['user_id']}, {'$set': user_data})
    # try:
    #     collection.insert_one(user_data)
    # except pymongo.errors.DuplicateKeyError:
    #     print('user {} exists, updating data...'.format(data['user_id']))
    #     collection.update_one({'_id': data['user_id']}, {'$set': user_data})


def delete_user(user_id):
    if is_user(user_id):
        collection.delete_one({'_id': user_id})
        return True
    return False


def get_users():
    users_list = []
    mongo_users = collection.find({})
    for user in mongo_users:
        users_list.append(user)
    return users_list


def update_city(user_id, city):
    if is_user(user_id):
    # if collection.find_one({'_id': user_id}):
        collection.update_one({'_id': user_id}, {'$set': {'city': city}})
        return True
    return False


def update_sending_time(user_id, new_time):
    if is_user(user_id):
    # if collection.find_one({'_id': user_id}):
        collection.update_one({'_id': user_id}, {'$set': {'sending_time': new_time}})
        return True
    return False


def is_user(user_id):
    if collection.find_one({'_id': user_id}):
        return True
    return False
