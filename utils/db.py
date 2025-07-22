from pymongo import MongoClient
import os

def get_db():
    mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
    client = MongoClient(mongo_uri)
    return client['demon_slayer_rpg']

def get_players():
    db = get_db()
    return db.players
