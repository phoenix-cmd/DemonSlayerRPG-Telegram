# config/regions.py

REGIONS = {
    "Spider's Market": {
        "lore": "A clandestine hub where demon-kind trades the rarest goods, veiled in webs and secrets.",
        "connected_routes": ["Tunnel Route", "Silken Hollow Village"],
        "encounters": {
            "demons": ["Spider Merchant", "Suspicious Demon Peddler"],
            "loot": ["Spider Silk Pouch", "Curious Talisman", "Market Coin"],
            "events": [
                "A hooded demon whispers rumors about the Midnight Thread.",
                "You catch a glimpse of a forbidden artifact behind the stalls."
            ],
            "nothing": ["Only the creak of silk and hushed bartering surrounds you."]
        }
    },

    "Tunnel Route": {
        "lore": "A damp, winding tunnel linking Spider's Market and Moonlit Ravine; rumors of ambushes persist.",
        "connected_routes": ["Spider's Market", "Moonlit Ravine"],
        "encounters": {
            "demons": ["Tunnel Crawler", "Webbed Stalker"],
            "loot": ["Stale Rations", "Broken Dagger"],
            "events": [
                "You find a secret door etched with spider glyphs.",
                "You hear whispers echoing through the tunnels."
            ],
            "nothing": ["The silence is broken only by dripping water."]
        }
    },

    "Silken Hollow Village": {
        "lore": "A haunted, long-abandoned village consumed by silk and memories. Some say it is a haven to outcasts.",
        "connected_routes": ["Spider's Market", "Moonlit Ravine (Hidden Route)"],
        "encounters": {
            "demons": ["Silk Phantom", "Lost Villager"],
            "loot": ["Silken Cloak", "Forgotten Relic"],
            "events": [
                "You find a child’s doll tangled in web.",
                "A spirit warns you not to linger after dusk."
            ],
            "nothing": ["Cobwebs drift in the ghostly wind."]
        }
    },

    "Moonlit Ravine": {
        "lore": "A moon-drenched gorge shimmering with mystical energy, connecting many forbidden places.",
        "connected_routes": ["Tunnel Route", "Silken Hollow Village (Hidden Route)", "Night Route"],
        "encounters": {
            "demons": ["Moonlit Specter", "Ravine Lurker"],
            "loot": ["Moonstone Shard", "Silvered Webbing"],
            "events": [
                "The air grows cold as the moonlight pulses.",
                "A crow cries out, announcing a new challenge."
            ],
            "nothing": ["The moon reveals nothing—tonight."]
        }
    },

    "Night Route": {
        "lore": "A dangerous ravine trail navigable only after sundown, leading to dark secrets.",
        "connected_routes": ["Moonlit Ravine", "Abandoned Shrine of Threads"],
        "encounters": {
            "demons": ["Twilight Weaver", "Nightshade Demon"],
            "loot": ["Shadow Amulet", "Night Herb"],
            "events": [
                "The wind howls. You sense you are not alone.",
                "You stumble upon a torn prayer scroll."
            ],
            "nothing": ["Your torch flickers, but there is only darkness."]
        }
    },

    "Abandoned Shrine of Threads": {
        "lore": "Forgotten by time, this ancient shrine is shrouded in haunted webs and secrets best left untouched.",
        "connected_routes": ["Night Route"],
        "encounters": {
            "demons": ["Thread Priest", "Shrine Guardian"],
            "loot": ["Sacred Thread", "Shrine Talisman"],
            "events": [
                "A spirit beckons you closer to an altar.",
                "The wall murals ripple as if alive."
            ],
            "nothing": ["A ghostly hush hangs in the shrine’s air."]
        }
    },
}
