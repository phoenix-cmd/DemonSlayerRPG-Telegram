# models/player.py

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
    gender: str  # 'male' or 'female'

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
    location: str = "Spider's Market"
    region_unlocks: List[str] = field(default_factory=list)
    inventory: List[Dict[str, Any]] = field(default_factory=list)  # Items, gear, etc.
    equipped: Dict[str, str] = field(default_factory=dict)
    gold: int = 0
    
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_active: datetime = field(default_factory=datetime.utcnow)

    # New Fields for route progression
    current_route: Optional[str] = None      # e.g., 'Tunnel Route'
    path_progress: int = 0                   # 0 = at region, >0 = steps along route
    has_explored: bool = False               # Whether player has explored current step

    @classmethod
    def create_new(cls, telegram_id: int, name: str, gender: str, background: str = "", location: str = "Spider's Market") -> "Player":
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
        return asdict(self)

    @classmethod
    def from_dict(cls, doc: dict) -> "Player":
        """Create a Player from a MongoDB document."""
        kwargs = dict(doc)
        # Handle datetime fields conversion if needed
        for dt_field in ("created_at", "last_active"):
            if isinstance(kwargs.get(dt_field), str):
                try:
                    from datetime import datetime
                    kwargs[dt_field] = datetime.fromisoformat(kwargs[dt_field])
                except Exception:
                    kwargs[dt_field] = datetime.utcnow()
            elif kwargs.get(dt_field) is None:
                kwargs[dt_field] = datetime.utcnow()
        # Provide defaults for new fields if missing
        if "current_route" not in kwargs:
            kwargs["current_route"] = None
        if "path_progress" not in kwargs:
            kwargs["path_progress"] = 0
        if "has_explored" not in kwargs:
            kwargs["has_explored"] = False
        return cls(**kwargs)

