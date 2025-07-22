from pymongo import MongoClient

def get_db():
    client = MongoClient("mongodb://localhost:27017/")
    return client['demon_slayer_rpg']

def get_players():
    db = get_db()
    return db.players

