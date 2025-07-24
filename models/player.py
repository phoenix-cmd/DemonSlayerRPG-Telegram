
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
from datetime import datetime

# Stat presets for gender (customize as needed)
STARTING_STATS = {
    "male":   {"hp": 120, "mana": 60, "atk": 15, "def_": 12, "spd": 10},
    "female": {"hp": 100, "mana": 80, "atk": 12, "def_": 10, "spd": 14},
}

@dataclass
class Player:
    telegram_id: int
    name: str
    gender: str # 'male' or 'female'

    # RPG core fields
    mode: str = "explore"
    level: int = 1
    exp: int = 0
    core_type: str = "Stable"
    element: str = "None"
    
    hp: int = 100
    mana: int = 50
    atk: int = 10
    def_: int = 10
    spd: int = 10
    status_effects: List[Dict[str, Any]] = field(default_factory=list)
    
    faction: Optional[str] = None
    faction_rank: int = 0
    alignment: Optional[str] = None
    background: Optional[str] = ""
    quests: List[Dict[str, Any]] = field(default_factory=list)
    location: str = ""
    region_unlocks: List[str] = field(default_factory=list)
    inventory: List[Dict[str, Any]] = field(default_factory=list) # Items, gear, etc.
    equipped: Dict[str, str] = field(default_factory=dict)
    gold: int = 0
    
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_active: datetime = field(default_factory=datetime.utcnow)

    @classmethod
    def create_new(cls, telegram_id: int, name: str, gender: str, background: str = "", location: str = "Mount Natagumo") -> "Player":
        """Factory for a new player with gender-based stats."""
        stats = STARTING_STATS.get(gender.lower())
        if not stats:
            stats = STARTING_STATS["male"]  # Default/fallback
        
        return cls(
            telegram_id=telegram_id,
            name=name,
            gender=gender,
            background=background,
            location=location,
            hp=stats["hp"],
            mana=stats["mana"],
            atk=stats["atk"],
            def_=stats["def_"],
            spd=stats["spd"]
        )

    def to_dict(self) -> dict:
        """Serialize Player for MongoDB storage."""
        data = asdict(self)
        # Datetime fields: explicitly stored as datetime objects (pymongo handles this)
        return data

    @classmethod
    def from_dict(cls, doc: dict) -> "Player":
        """Create a Player from a MongoDB document."""
        kwargs = dict(doc)
        # Ensure datetime fields are present/converted correctly
        for dt_field in ("created_at", "last_active"):
            if isinstance(kwargs.get(dt_field), str):  # If stored as ISO string
                kwargs[dt_field] = datetime.fromisoformat(kwargs[dt_field])
            elif kwargs.get(dt_field) is None:
                kwargs[dt_field] = datetime.utcnow()
        return cls(**kwargs)

# --- Example Usage ---

# Creating a new player (for registration)
"""
new_player = Player.create_new(
    telegram_id=123456789,
    name="Tanjiro",
    gender="male",  # or "female"
    background="A humble villager seeking vengeance.",
    location="Mount Natagumo"
)
players_collection.insert_one(new_player.to_dict())
"""

# Loading from MongoDB
"""
doc = players_collection.find_one({"telegram_id": 123456789})
player = Player.from_dict(doc)
"""

# Always use player.to_dict() before saving, and Player.from_dict() when loading from DB.

# --- End of player.py ---
