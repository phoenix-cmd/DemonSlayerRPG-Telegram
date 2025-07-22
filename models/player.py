# models/player.py

player_schema = {
    "telegram_id": int,
    "name": str,
    "gender": str,     # 'male' or 'female'
    "mode": str,       # 'story' or 'explore'
    "level": int,
    "exp": int,
    "location": str,
    "items": list,
    "created_at": "datetime"
}
