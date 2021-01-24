import pymongo
from pymongo import MongoClient
import func.config as config

cluster_url = 'mongodb+srv://{0}:{1}@weather-bot.g2wrn.mongodb.net/{2}?retryWrites=true&w=majority'.format(config.mongo_user, config.mongo_passwd, config.mongo_db)
print(cluster_url)
cluster = MongoClient(cluster_url)
db = cluster[config.mongo_db]
collection = db[config.mongo_collection]

def add_user(user_id):
    print('add user function from mongo')
    user = {
        '_id': user_id
    }
    try:
        collection.insert_one(user)
        print('added user ', user_id)
        print(collection.find_one({'_id': user_id}))
    except pymongo.errors.DuplicateKeyError:
        print('user {} already exist, skipping..'.format(user_id))


def update_user_data(data):
    user_data = {
        'city': data['city'],
        'weather_desc': data['weather_desc'],
        'temp_actual': data['temp_actual'],
        'temp_feels': data['temp_feels'],
        'sending_time': data['sending_time']
    }
    try:
        collection.update_one({'_id': data['user_id']}, {'$set': user_data})
    except:
        add_user(data['user_id'])
        collection.update_one({'_id': data['user_id']}, {'$set': user_data})


def delete_user(user_id):
    collection.delete_one({'_id': user_id})

def get_users():
    users_list = []
    mongo_users = collection.find({})
    for user in mongo_users:
        users_list.append(user)
    return users_list
