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

    "Tunnel Route Step 0": {  # Entry point alias to Spider's Market
        "lore": "The beginning of the damp tunnel leading away from Spider's Market.",
        "connected_routes": ["Tunnel Route Step 1"], 
        "encounters": {
            "demons": [],
            "loot": [],
            "events": [],
            "nothing": []
        }
    },

    "Tunnel Route Step 1": {
        "lore": "A dimly lit section of the Tunnel Route.",
        "connected_routes": ["Tunnel Route Step 0", "Tunnel Route Step 2"],
        "encounters": {
            "demons": ["Tunnel Crawler", "Webbed Stalker"],
            "loot": ["Stale Rations", "Broken Dagger"],
            "events": [
                "You find a secret door etched with spider glyphs.",
                "Whispers echo through the tunnels."
            ],
            "nothing": ["Only dripping water breaks the silence."]
        }
    },

    "Tunnel Route Step 2": {
        "lore": "A deeper and more dangerous area of the tunnels.",
        "connected_routes": ["Tunnel Route Step 1", "Tunnel Route Step 3"],
        "encounters": {
            "demons": ["Webbed Stalker", "Poisonous Spider"],
            "loot": ["Cracked Lantern", "Spider Venom"],
            "events": [
                "Cobwebs block narrow pathways.",
                "The sound of distant skittering unsettles you."
            ],
            "nothing": ["The passage feels eerily quiet."]
        }
    },

    "Tunnel Route Step 3": {
        "lore": "The exit tunnel leading towards Moonlit Ravine.",
        "connected_routes": ["Tunnel Route Step 2", "Moonlit Ravine"],
        "encounters": {
            "demons": ["Night Crawler"],
            "loot": ["Moonlit Stone"],
            "events": [
                "The faint moonlight filters in from ahead.",
                "You can almost see the path to Moonlit Ravine."
            ],
            "nothing": ["A calm settles over the tunnel."]
        }
    },

    "Moonlit Ravine": {
        "lore": "A moon-drenched gorge shimmering with mystical energy, connecting many forbidden places.",
        "connected_routes": ["Tunnel Route Step 3", "Silken Hollow Village (Hidden Route)", "Night Route"],
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

    "Silken Hollow Village": {
        "lore": "A haunted, abandoned village consumed by silk and memories. Some say it is a haven to outcasts.",
        "connected_routes": ["Spider's Market", "Moonlit Ravine (Hidden Route)"],
        "encounters": {
            "demons": ["Silk Phantom", "Lost Villager"],
            "loot": ["Silken Cloak", "Forgotten Relic"],
            "events": [
                "You find a child’s doll tangled in a web.",
                "A spirit warns you not to linger after dusk."
            ],
            "nothing": ["Cobwebs drift in the ghostly wind."]
        }
    },

    # Include other regions similarly...
}
