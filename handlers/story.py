# handlers/story_part1.py
# PTB v21+ async handler module for Story Part 1
# Covers: /start (sudo+private), name → gender → stats,
# Chapter 1 Scene 1 (both choice sets), Chapter 1 Scene 2 (all roots),
# All outcomes (GiveMoney/Run/Stand/Fight/Distract/Escalate/Talk/Fake/Attack),
# Thief fight loop with HP bars/logs, betrayal path to death,
# and blueFlames handoff into Part 2.

import asyncio
import random
import re
from typing import Dict, Any, Set

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# Inject sudo IDs from your bot.py using register_story_part1(..., sudo_ids={...})
SUDO: Set[int] = set()

# Shared state (in-memory). Part 2 will import via get_story_state().
database: Dict[int, Dict[str, Any]] = {}   # {"gender","status","name","enterName","outcome"}
temp_dict: Dict[int, Dict[str, Any]] = {}  # thief battle state

START_VIDEO = "https://files.catbox.moe/9f9bvs.mp4"

def get_story_state():
    return {
        "database": database,
        "temp_dict": temp_dict,
    }

def _is_private(update: Update) -> bool:
    chat = update.effective_chat
    return bool(chat and chat.type == "private")

def _kb(rows):
    # rows: list[list[tuple(text, data)]]
    return InlineKeyboardMarkup([[InlineKeyboardButton(t, callback_data=d) for t, d in row]])

def _hp_bar(cur: int, mx: int) -> str:
    mx = max(mx, 1)
    p = max(0.0, min(1.0, cur / mx))
    filled = int(round(p * 10))
    return "▰" * filled + "▱" * (10 - filled)

# ========== Registration ==========

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user:
        return
    if SUDO and user.id not in SUDO:
        return
    if not _is_private(update):
        if update.message:
            await update.message.reply_text("This command only works in Private")
        return

    database[user.id] = {
        "gender": "undifined",
        "status": "alive",
        "name": "none",
        "enterName": False,
        "outcome": "none",
    }

    await context.bot.send_video(
        chat_id=update.effective_chat.id,
        video=START_VIDEO,
        caption=(
            "〖𝐃𝐄𝐌𝐎𝐍 𝐒𝐋𝐀𝐘𝐄𝐑: 𝐑𝐈𝐒𝐄 𝐎𝐑 𝐅𝐀𝐋𝐋〗\n\n"
            "❛A world shrouded in darkness…\n The final battle is near…❜\n\n"
            "🔥 𝐓𝐖𝐎 𝐏𝐀𝐓𝐇𝐒. 𝐎𝐍𝐄 𝐃𝐄𝐒𝐓𝐈𝐍𝐘. 🔥\n\n"
            "❂ 𝐒𝐋𝐀𝐘𝐄𝐑𝐒 – Wield your blade, master Breathing, and protect humanity.\n"
            "✶ 𝐃𝐄𝐌𝐎𝐍𝐒 – Consume power, evolve beyond limits, and rule the night.\n\n"
            "𝐄𝐕𝐄𝐑𝐘 𝐂𝐇𝐎𝐈𝐂𝐄 𝐂𝐇𝐀𝐍𝐆𝐄𝐒 𝐘𝐎𝐔𝐑 𝐏𝐀𝐓𝐇...\n"
            "What will you become?\n\n"
            "[𝐁𝐄𝐆𝐈𝐍 𝐘𝐎𝐔𝐑 𝐉𝐎𝐔𝐑𝐍𝐄𝐘 𝐍𝐎𝐖!]"
        ),
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("S T A R T", callback_data="start_data")]]),
        reply_to_message_id=update.message.id if update.message else None,
    )

async def get_name_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user:
        return
    uid = user.id
    if uid not in database:
        await update.message.reply_text("Please start the bot first")
        return
    try:
        if database[uid].get("enterName") and database[uid].get("name") == "none":
            database[uid]["name"] = update.message.text

            confirmation = await update.message.reply_text(
                f"System:\n\nThat's a good name <b>{database[uid]['name']}</b>\nLet's proceed for further steps - "
            )
            await asyncio.sleep(2)
            try:
                await confirmation.delete()
            except:
                pass

            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=(
                    "System[:](https://files.catbox.moe/2gsyro.jpg)\n\n"
                    "User select your gender for completing the registration process"
                ),
                reply_markup=_kb([[("BOY", "boy"), ("GIRL", "girl")]]),
            )
    except Exception:
        await update.message.reply_text("Please start the bot first")

async def on_start_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    if uid not in database:
        database[uid] = {"gender": "undefined", "status": "alive", "name": "none", "enterName": False}
    try:
        await q.message.delete()
    except:
        pass
    await context.bot.send_photo(
        chat_id=q.message.chat.id,
        photo="https://files.catbox.moe/soi8m7.jpg",
        caption=(
            "SYSTEM:\n\n"
            "Welcome User - \n"
            "Let's have a quick registration process\n\n"
            "⨀ Enter your game name - "
        ),
    )
    database[uid]["enterName"] = True

# ========== Gender / Stats ==========

async def on_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    st = database.get(uid, {})
    if q.data == "boy":
        st["gender"] = "boy"
        txt = (
            "You have selected your journey as a boy[.](https://files.catbox.moe/smlywt.jpg)\n\n"
            "Click on view stats for continuing"
        )
    else:
        st["gender"] = "girl"
        txt = (
            "You have selected your journey as a girl[.](https://files.catbox.moe/o90ydf.jpg)\n\n"
            "Click on view stats for continuing"
        )
    await asyncio.sleep(1)
    await q.edit_message_text(
        txt,
        reply_markup=_kb([[("View Stats", "stats"), ("BACK", "gen")]]),
        disable_web_page_preview=True,
    )

async def on_gen_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await asyncio.sleep(1)
    await q.edit_message_text(
        text=(
            "System[:](https://files.catbox.moe/2gsyro.jpg)\n\n"
            "User select your gender for completing the registration process"
        ),
        reply_markup=_kb([[("BOY", "boy"), ("GIRL", "girl")]]),
        disable_web_page_preview=True,
    )

async def on_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    st = database.get(uid, {})
    markup = _kb([[("BACK", "bck")], [("CONTINUE", "aage")]])
    female_text = (
        " Character Stats \n✦ Core Stats\n───────────────────────\n"
        "◆ [STR] Strength: 8\n◆ [AGI] Agility: 12\n◆ [END] Endurance: 9\n◆ [BB] Breathing Bar: 10\n"
        "◆ [INT] Intelligence: 10\n◆ [PER] Perception: 11\n\n✦ Secondary Stats\n───────────────────────\n"
        "◆ [HP] Health Points: 90\n◆ [STA] Stamina: 95\n◆ [SP] Skill Power: 100\n◆ [DEF] Defense: 18\n◆ [CRIT] Critical Rate: 11%"
    )
    male_text = (
        " Character Stats \n✦ Core Stats\n\n───────────────────────\n"
        "◆ [STR] Strength: 10\n◆ [AGI] Agility: 8\n◆ [END] Endurance: 12\n◆ [BB] Breathing Bar: 10\n"
        "◆ [INT] Intelligence: 9  \n◆ [PER] Perception: 9\n\n✦ Secondary Stats\n───────────────────────\n"
        "◆ [HP] Health Points: 120  \n◆ [STA] Stamina: 110  \n◆ [SP] Skill Power: 100  \n◆ [DEF] Defense: 24  \n◆ [CRIT] Critical Rate: 9%\n"
    )
    await asyncio.sleep(1)
    if st.get("gender") == "boy":
        await q.edit_message_text(male_text, reply_markup=markup)
    else:
        await q.edit_message_text(female_text, reply_markup=markup)

async def on_stats_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    st = database.get(uid, {})
    txt = (
        "You have selected your journey as a boy[.](https://files.catbox.moe/smlywt.jpg)\n"
        if st.get("gender") == "boy"
        else "You have selected your journey as a girl[.](https://files.catbox.moe/o90ydf.jpg)\n"
    )
    await asyncio.sleep(1)
    await q.edit_message_text(
        txt,
        reply_markup=_kb([[("View Stats", "stats"), ("BACK", "gen")]]),
        disable_web_page_preview=True,
    )

async def on_stats_continue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await asyncio.sleep(1)
    try:
        await q.message.delete()
    except:
        pass
    await context.bot.send_photo(
        chat_id=q.message.chat.id,
        photo="https://files.catbox.moe/v5a806.jpg",
        caption="<b>Chapter 1: DESTINY BEGINS WITH DEATH</b>",
        reply_markup=_kb([[("BEGIN", "begin")]]),
    )

# ========== Chapter 1, Scene 1 ==========

async def on_begin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await asyncio.sleep(1)
    try:
        await q.message.delete()
    except:
        pass
    await context.bot.send_photo(
        q.message.chat.id,
        photo="https://files.catbox.moe/kygjzd.jpg",
        caption=(
            "<b>Narration</b>\n"
            "The rich aroma of coffee fills the air. Sunlight streams through the windows.\n"
            "Outside, the city hums with life, but inside it's peaceful."
        ),
        reply_markup=_kb([[("NEXT", "next")]]),
    )

async def on_next(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await asyncio.sleep(1)
    try:
        await q.message.delete()
    except:
        pass
    await context.bot.send_photo(
        q.message.chat.id,
        photo="https://files.catbox.moe/g6zxhf.jpg",
        caption=(
            "<b>Renji</b>\n"
            "\"You always get that look when we're here. What is it about this place that gets you so sentimental?\"\n\n"
            "<b>CHOOSE YOUR RESPONSE</b>\n"
            "<pre>Choice 1: \"It's the little things that make life enjoyable.\"\n"
            "Choice 2: \"Maybe I just like good coffee and good company.\"\n"
            "Choice 3: \"I dunno, maybe I'm just weird like that.\"</pre>"
        ),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Choice 1", callback_data="c1r1"),
             InlineKeyboardButton("Choice 2", callback_data="c1r2")],
            [InlineKeyboardButton("Choice 3", callback_data="c1r3")],
        ]),
    )

async def on_choice_c1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data
    await asyncio.sleep(1)
    try:
        await q.message.delete()
    except:
        pass

    if data == "c1r1":
        photo = "https://files.catbox.moe/8tpqtd.jpg"
        cap = (
            "<b>Renji</b>\n"
            "\"You know, that’s kinda nice. We always focus on big dreams and what's next, "
            "but maybe moments like this matter just as much.\"\n\n"
            "<b>Name</b>\n"
            "\"See? You’re getting sentimental too.\"\n\n"
            "<b>Renji</b>\n"
            "\"Yeah, yeah, don’t get used to it.\""
        )
    elif data == "c1r2":
        photo = "https://files.catbox.moe/fdkkz2.jpg"
        cap = (
            "<b>Renji</b>\n"
            "\"Well, at least one of those is true. I’ll let you decide which one.\"\n\n"
            "<b>Name</b>\n"
            "\"Hmm… tough choice.\"\n\n"
            "<b>Renji</b>\n"
            "\"If you say anything other than me, I’m walking out.\"\n\n"
            "<b>Name</b>\n"
            "\"Alright, alright. You win this time.\""
        )
    else:
        photo = "https://files.catbox.moe/wx9zo3.jpg"
        cap = (
            "<b>Renji</b>\n"
            "\"Weird is one way to put it. I was thinking more along the lines of "
            "‘hopeless romantic stuck in a coffee commercial.’\"\n\n"
            "<b>Name</b>\n"
            "\"Hey, if my life was a commercial, at least I’d get free coffee.\""
        )

    await context.bot.send_photo(
        q.message.chat.id, photo=photo, caption=cap, reply_markup=_kb([[("CONTINUE", "continue")]])
    )

async def on_continue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await asyncio.sleep(1)
    try:
        await q.message.delete()
    except:
        pass

    await context.bot.send_photo(
        q.message.chat.id,
        photo="https://files.catbox.moe/rhqyuf.jpg",
        caption=(
            "<b>Emi</b>\n"
            "\"You two again? At this point the café should just give you a VIP pass.\"\n\n"
            "<b>CHOOSE YOUR RESPONSE</b>\n"
            "<pre>Choice 1: \"Well, you did say this place had the best cinnamon rolls.\"\n"
            "Choice 2: \"We’re basically part of the furniture here now.\"\n"
            "Choice 3: \"Blame Renji. He’s addicted to their coffee.\"</pre>"
        ),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Choice 1", callback_data="c1r1c2"),
             InlineKeyboardButton("Choice 2", callback_data="c1r2c2")],
            [InlineKeyboardButton("Choice 3", callback_data="c1r3c2")],
        ]),
    )

async def on_choice_c2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data
    await asyncio.sleep(1)
    try:
        await q.message.delete()
    except:
        pass

    if data == "c1r1c2":
        photo = "https://files.catbox.moe/1dqos1.jpg"
        cap = (
            "<b>Emi</b>\n"
            "\"And I was right, wasn’t I?\"\n\n"
            "<b>Name</b>\n"
            "\"You were. This might actually be the best thing I’ve ever tasted.\"\n\n"
            "<b>Emi</b>\n"
            "\"Told you. I should start charging for my food recommendations.\"\n\n"
            "<b>Renji</b>\n"
            "\"Nah, you'd just make us all broke.\""
        )
    elif data == "c1r2c2":
        photo = "https://files.catbox.moe/16hf53.jpg"
        cap = (
            "<b>Emi</b>\n"
            "\"Great, now I have to start dusting you guys off before my shift starts.\"\n\n"
            "<b>Name</b>\n"
            "\"Hey, we’re classy furniture. Maybe a fancy leather couch or something.\"\n\n"
            "<b>Emi</b>\n"
            "\"Nah, more like an old, worn-out beanbag chair.\"\n\n"
            "<b>Renji</b>\n"
            "\"Wow. That’s the rudest thing anyone has ever said to me.\"\n\n"
            "<b>Emi</b>\n"
            "\"And yet, you’ll still be here tomorrow.\""
        )
    else:
        photo = "https://files.catbox.moe/joz0w9.jpg"
        cap = (
            "<b>Renji</b>\n"
            "\"It’s true. This coffee owns my soul now.\"\n\n"
            "<b>Emi</b>\n"
            "\"I knew you were too weak to resist.\"\n\n"
            "<b>Renji</b>\n"
            "\"Hey, I have no regrets. If this is how I go out, at least I’ll be caffeinated.\"\n\n"
            "<b>Name</b>\n"
            "\"Rest in peace, buddy. We’ll put a cup of coffee on your grave.\"\n\n"
            "<b>Emi</b>\n"
            "\"Make it a double shot. He’d want it that way.\""
        )

    await context.bot.send_photo(
        q.message.chat.id, photo=photo, caption=cap, reply_markup=_kb([[("CONTINUE", "cont")]])
    )

async def on_choice_c2_res(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await asyncio.sleep(1)
    try:
        await q.message.delete()
    except:
        pass

    await context.bot.send_photo(
        q.message.chat.id,
        photo="https://files.catbox.moe/gmw7vz.jpg",
        caption=(
            "<b>Narration</b>\n\n"
            "The sky glows with shades of orange and pink. A rare peace settles in.\n\n"
            "<b>Name</b>\n"
            "\"You know… I don’t need anything more than this. Just good coffee, good food, and good friends.\"\n\n"
            "<b>Renji</b>\n"
            "\"Careful, you're tempting fate. Say something like that, and the universe might just decide to mess with you.\"\n\n"
            "<b>End Of Scene 1</b>"
        ),
        reply_markup=_kb([[("Move To Scene 2 ⇨", "s2")]]),
    )

# ========== Chapter 1, Scene 2 ==========

async def on_s2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await asyncio.sleep(1)
    try:
        await q.message.delete()
    except:
        pass

    await context.bot.send_photo(
        q.message.chat.id,
        photo="https://files.catbox.moe/tdo7ur.jpg",
        caption="<b>The once-bustling streets have quieted... Footsteps echo—but not theirs.</b>",
        reply_markup=_kb([[("NEXT ⇾", "s2story")]]),
    )

async def on_s2story(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    st = database.get(uid, {})
    pic = "https://files.catbox.moe/sbq892.jpg" if st.get("gender") == "boy" else "https://files.catbox.moe/lt1qve.jpg"
    await asyncio.sleep(1)
    try:
        await q.message.delete()
    except:
        pass

    await context.bot.send_photo(
        q.message.chat.id,
        photo=pic,
        caption=(
            "<b>Renji</b>\n"
            "\"Man, that was a good way to end the day. Too bad we have class tomorrow.\"\n\n"
            "<b>Protagonist</b>\n"
            "\"Assuming you even show up.\"\n\n"
            "<b>Renji</b>\n"
            "\"Hey, I have a 75% attendance rate. That’s basically an A for effort.\""
        ),
        reply_markup=_kb([[("NEXT ⇾", "nexts2o")]]),
    )

async def on_nexts2o(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await asyncio.sleep(1)
    try:
        await q.message.delete()
    except:
        pass

    await context.bot.send_photo(
        q.message.chat.id,
        photo="https://files.catbox.moe/9qnv4d.jpg",
        caption=(
            "<b>????</b>\n"
            "\"Got a minute?\"\n\n"
            "<b>CHOOSE YOUR RESPONSE</b>\n"
            "<pre>Choice 1: \"Uh, sorry, we’re in a hurry.\"\n"
            "Choice 2: \"Who the hell are you?\"\n"
            "Choice 3: \"Depends. What do you want?\"</pre>"
        ),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Choice 1", callback_data="c1s2r1"),
             InlineKeyboardButton("Choice 2", callback_data="c1s2r2")],
            [InlineKeyboardButton("Choice 3", callback_data="c1s2r3")],
        ]),
    )

async def on_s2_choices(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data
    await asyncio.sleep(1)
    try:
        await q.message.delete()
    except:
        pass

    if data == "c1s2r1":
        photo = "https://files.catbox.moe/ixn92a.jpg"
        cap = (
            "<b>Hooded Man</b>\n"
            "\"Yeah? Well, so am I. Hand over your wallets, and we’ll all be on our way.\"\n\n"
            "<b>Renji</b>\n"
            "\"Crap… mugger. What do we do?\"\n\n"
            "<b>CHOOSE YOUR RESPONSE</b>\n"
            "<pre>Choice 1: Give him the money and leave.\n"
            "Choice 2: Try to run.\n"
            "Choice 3: Stand your ground.</pre>"
        )
        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("Choice 1", callback_data="c1s2o_GiveMoney"),
             InlineKeyboardButton("Choice 2", callback_data="c1s2o_Run")],
            [InlineKeyboardButton("Choice 3", callback_data="c1s2o_Stand")],
        ])
    elif data == "c1s2r2":
        photo = "https://files.catbox.moe/t8v754.jpg"
        cap = (
            "<b>Hooded Man</b>\n"
            "\"Wrong answer.\"\n\n"
            "<i>Without warning, he pulls out a knife, the blade glinting under the streetlight.</i>\n\n"
            "<b>Renji</b>\n"
            "\"Shit—he’s serious!\"\n\n"
            "<b>CHOOSE YOUR RESPONSE</b>\n"
            "<pre>Choice 1: Try To Fight Him Off\n"
            "Choice 2: Tell Renji To Run While You Distract Him\n"
            "Choice 3: Try To De-Escalate The Situation</pre>"
        )
        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("Choice 1", callback_data="c1s2o_Fight"),
             InlineKeyboardButton("Choice 2", callback_data="c1s2o_Distract")],
            [InlineKeyboardButton("Choice 3", callback_data="c1s2o_Esclate")],
        ])
    else:
        photo = "https://files.catbox.moe/vjgcjw.jpg"
        cap = (
            "<b>Hooded Man</b>\n"
            "\"Smart kid. Maybe you can make this easy.\"\n\n"
            "<i>He pulls out a knife, but doesn’t attack—yet.</i>\n\n"
            "<b>Hooded Man</b>\n"
            "\"Give me your stuff, and we all walk away happy. Say no, and I promise you won’t like what happens next.\"\n\n"
            "<b>Renji</b>\n"
            "\"Dude, this guy is sketchy as hell…\"\n\n"
            "<b>CHOOSE YOUR RESPONSE</b>\n"
            "<pre>Choice 1: Try To Talk Him Down\n"
            "Choice 2: Give Him Fake Wallet And Hope He Buys It\n"
            "Choice 3: Attack First Before He Can</pre>"
        )
        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("Choice 1", callback_data="c1s2o_Talk"),
             InlineKeyboardButton("Choice 2", callback_data="c1s2o_Fake")],
            [InlineKeyboardButton("Choice 3", callback_data="c1s2o_Attack")],
        ])

    await context.bot.send_photo(q.message.chat.id, photo=photo, caption=cap, reply_markup=reply_markup)

async def on_s2_outcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    st = database.get(uid, {})
    m = re.match(r"^(c1s2o)_(\w+)$", q.data or "")
    if not m:
        return
    _, outcome = m.groups()
    st["outcome"] = outcome
    await asyncio.sleep(1)
    try:
        await q.message.delete()
    except:
        pass

    if outcome == "GiveMoney":
        await context.bot.send_photo(
            q.message.chat.id,
            photo="https://files.catbox.moe/v5zxwp.jpg",
            caption=(
                "<b>Protagonist</b>\n"
                "\"Here. Just take it and go.\"\n\n"
                "<b>Hooded Man</b>\n"
                "\"Smart choice. See? No one gets hurt when you cooperate.\"\n\n"
                "<i>He pockets the cash...</i>"
            ),
            reply_markup=_kb([[("Next", "giveMoneyNext")]]),
        )
    elif outcome == "Run":
        pic = "https://files.catbox.moe/xv83wt.jpg" if st.get("gender") == "boy" else "https://files.catbox.moe/hznwtj.jpg"
        await context.bot.send_photo(
            q.message.chat.id,
            photo=pic,
            caption=(
                "<b>Protagonist</b>\n"
                "\"Run. Now!\"\n\n"
                "<i>They bolt down the street, adrenaline kicking in...</i>"
            ),
            reply_markup=_kb([[("Run", "runAway")]]),
        )
    elif outcome == "Stand":
        pic = "https://files.catbox.moe/ibzye5.jpg" if st.get("gender") == "boy" else "https://files.catbox.moe/hytodn.jpg"
        await context.bot.send_photo(
            q.message.chat.id,
            photo=pic,
            caption=(
                "<b>Name</b>\n"
                "Let's fight this out, Renji.\n\n"
                "<b>Renji</b>\n"
                "Yeah, let's teach him a lesson.\n\n"
                "<i>Fight Begins</i>"
            ),
            reply_markup=_kb([[("F I G H T", "theifFight")]]),
        )
    else:
        # Fight/Distract/Esclate/Talk/Fake/Attack -> route to thief fight with generic prompt
        await context.bot.send_photo(
            q.message.chat.id,
            photo="https://files.catbox.moe/j4djo3.jpg",
            caption="<i>Escalation leads to combat...</i>",
            reply_markup=_kb([[("FIGHT HIM", "theifFight")]]),
        )

# ========== Betrayal branches (GiveMoney / Run) ==========

async def on_giveMoneyNext(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    try:
        await q.message.delete()
    except:
        pass
    await asyncio.sleep(1)
    await context.bot.send_photo(
        q.message.chat.id,
        photo="https://files.catbox.moe/9xi5lk.jpg",
        caption=(
            "<b>Hooded Man</b>\n"
            "\"Let’s hope we don’t run into each other again.\"\n\n"
            "<i>He disappears into the alley.</i>"
        ),
        reply_markup=_kb([[("Next", "next1")]]),
    )

async def on_next1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    st = database.get(uid, {})
    try:
        await q.message.delete()
    except:
        pass
    await asyncio.sleep(1)
    pic = "https://files.catbox.moe/g07mml.jpg" if st.get("gender") == "boy" else "https://files.catbox.moe/rnkpb5.jpg"
    await context.bot.send_photo(
        q.message.chat.id,
        photo=pic,
        caption=(
            "<i>The protagonist and Renji continue walking, the weight of humiliation settling in.</i>\n\n"
            "<b>Renji</b>\n"
            "“Well, that was pathetic.”\n\n"
            "<b>Name</b>\n"
            "“Yeah? What did you want me to do? Get stabbed?”\n\n"
            "Renji stops walking. There’s something… off."
        ),
        reply_markup=_kb([[("What Happened Renji??", "whatHappned")]]),
    )

async def on_runAway(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    try:
        await q.message.delete()
    except:
        pass
    await asyncio.sleep(1)
    await context.bot.send_photo(
        q.message.chat.id,
        photo="https://files.catbox.moe/ek0dqs.jpg",
        caption=(
            "<b>Renji</b>\n"
            "\"Holy crap… we actually made it.\"\n\n"
            "<b>Name</b>\n"
            "\"Yeah… but let’s not push our luck. Come on, let’s get home.\"\n\n"
            "<i>The tension lingers, but they’re safe—for now.</i>"
        ),
        reply_markup=_kb([[("Let's Get Going", "goToHome")]]),
    )

async def on_goToHome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    try:
        await q.message.delete()
    except:
        pass
    await asyncio.sleep(1)
    await context.bot.send_photo(
        q.message.chat.id,
        photo="https://files.catbox.moe/klmizs.jpg",
        caption=(
            "<b>Renji</b>\n"
            "“But I can’t let you leave, you know?”\n\n"
            "<i>Before the protagonist can react, Renji stabs them.</i>"
        ),
        reply_markup=_kb([[("Let's Get Going", "renjiKilling2")]]),
    )

async def on_whatHappned(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    try:
        await q.message.delete()
    except:
        pass
    await asyncio.sleep(1)
    await context.bot.send_photo(
        q.message.chat.id,
        photo="https://files.catbox.moe/t9yqix.jpg",
        caption=(
            "<b>Renji</b>\n"
            "“Maybe that would’ve been better.”\n\n"
            "<b>Name</b>\n"
            "“What?”\n\n"
            "<i>A flash of silver.</i>"
        ),
        reply_markup=_kb([[("Stop It", "renjiKilling")]]),
    )

async def on_renjiKilling(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    st = database.get(uid, {})
    try:
        await q.message.delete()
    except:
        pass
    await asyncio.sleep(1)
    pic = "https://files.catbox.moe/7m5r2t.jpg" if st.get("gender") == "boy" else "https://files.catbox.moe/izyxxc.jpg"
    await context.bot.send_photo(
        q.message.chat.id,
        photo=pic,
        caption=(
            "<i>Before the protagonist can react, Renji plunges a knife straight into their stomach.</i>\n\n"
            "<b>Name</b>\n"
            "“R-Renji…?”\n\n"
            "<b>Renji</b>\n"
            "“Nothing personal.”"
        ),
        reply_markup=_kb([[("CONTINUE", "deathScene")]]),
    )

async def on_renjiKilling2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    st = database.get(uid, {})
    try:
        await q.message.delete()
    except:
        pass
    await asyncio.sleep(1)
    pic = "https://files.catbox.moe/65h7av.jpg" if st.get("gender") == "boy" else "https://files.catbox.moe/udrqco.jpg"
    await context.bot.send_photo(
        q.message.chat.id,
        photo=pic,
        caption=(
            "<b>Name</b>\n"
            "“R-Renji…?”\n\n"
            "<b>Renji</b>\n"
            "“You’ll understand soon enough… This world isn’t real. And you don’t belong here.”\n\n"
            "<i>The protagonist collapses as everything fades.</i>"
        ),
        reply_markup=_kb([[("CONTINUE", "deathScene")]]),
    )

async def on_deathScene(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    st = database.get(uid, {})
    try:
        await q.message.delete()
    except:
        pass
    await asyncio.sleep(1)
    pic = "https://files.catbox.moe/59s4zy.jpg" if st.get("gender") == "boy" else "https://files.catbox.moe/qcvwyo.jpg"
    await context.bot.send_photo(
        q.message.chat.id,
        photo=pic,
        caption=(
            "<b>Narration</b>\n"
            "The cold pavement presses against the protagonist’s cheek, their body growing numb as warm blood pools beneath them.\n"
            "Footsteps fade. The night swallows everything.\n\n"
            "<b>Then—darkness.</b>"
        ),
        reply_markup=_kb([[("CONTINUE", "blueFlames")]]),
    )

# ========== Thief Fight ==========

async def on_theifFight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    try:
        await q.message.delete()
    except:
        pass
    await asyncio.sleep(1)
    temp_dict[uid] = {
        "user_health": 100,
        "theif_health": 150,
        "user_max_health": 100,
        "theif_max_health": 150,
    }
    bd = temp_dict[uid]
    await context.bot.send_photo(
        q.message.chat.id,
        photo="https://files.catbox.moe/u18h2i.jpg",
        caption=(
            "<b>Battle Begins</b>\n\n"
            "<b>Thief :</b>\n"
            f"{_hp_bar(bd['theif_health'], bd['theif_max_health'])}\n\n"
            "<b>Name :</b>\n"
            f"{_hp_bar(bd['user_health'], bd['user_max_health'])}\n\n"
        ),
        reply_markup=_kb([[("P U N C H", "punchTheif")]]),
    )

async def on_punchTheif(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    bd = temp_dict.get(uid)
    if not bd:
        temp_dict[uid] = {"user_health": 100, "theif_health": 150, "user_max_health": 100, "theif_max_health": 150}
        bd = temp_dict[uid]

    if random.random() < 0.5:
        thef_dmg = random.randint(30, 50)
        bd["user_health"] -= thef_dmg
        dec = f"Thief dodged. He dealt {thef_dmg} damage."
    else:
        thef_dmg = random.randint(30, 50)
        user_dmg = random.randint(20, 30)
        bd["user_health"] -= thef_dmg
        bd["theif_health"] -= user_dmg
        dec = f"He dealt {thef_dmg}. You dealt {user_dmg}."

    if bd["user_health"] <= 0:
        temp_dict.pop(uid, None)
        try:
            await q.message.delete()
        except:
            pass
        await asyncio.sleep(1)
        await context.bot.send_message(
            q.message.chat.id,
            text=(
                "<b>Punches weren't enough against the thief's blade.</b>\n"
                "You couldn't survive this tragedy. The calamity took you in an instant..."
            ),
            reply_markup=_kb([[("CONTINUE", "userLost")]]),
        )
        return

    if bd["theif_health"] <= 0:
        temp_dict.pop(uid, None)
        try:
            await q.message.delete()
        except:
            pass
        await asyncio.sleep(1)
        await context.bot.send_message(
            q.message.chat.id,
            text=(
                "You have won against the thief.\n"
                "But you’re badly injured—losing consciousness, leading your way to death..."
            ),
            reply_markup=_kb([[("CONTINUE", "userLost")]]),
        )
        return

    msg = await q.edit_message_text("Please wait, the attacks are in progress ...")
    await asyncio.sleep(1)
    await msg.edit_text(
        text=(
            "<b>Battle Begins</b>\n\n"
            "<b>Thief :</b>\n"
            f"{_hp_bar(bd['theif_health'], bd['theif_max_health'])}\n\n"
            "<b>Name :</b>\n"
            f"{_hp_bar(bd['user_health'], bd['user_max_health'])}\n\n"
            f"<pre>Logs\n{dec}</pre>"
        ),
        reply_markup=_kb([[("P U N C H", "punchTheif")]]),
    )

async def on_userLost(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    st = database.get(uid, {})
    try:
        await q.message.delete()
    except:
        pass
    await asyncio.sleep(1)
    pic = "https://files.catbox.moe/59s4zy.jpg" if st.get("gender") == "boy" else "https://files.catbox.moe/qcvwyo.jpg"
    if st.get("outcome") == "Distract":
        cap = (
            "<b>Narration</b>\n"
            "A hooded man drives the knife into your chest. The world blurs. "
            "A strange peace settles—you’re glad Renji is safe. Then—nothing."
        )
    else:
        cap = (
            "<b>Narration</b>\n"
            "A hooded man drives the knife into your chest. The world blurs. "
            "Renji stands nearby, unmoving. He doesn’t help. He just watches.\n"
            "Why didn’t Renji react?\n\nThen—darkness."
        )

    await context.bot.send_photo(
        q.message.chat.id, photo=pic, caption=cap, reply_markup=_kb([[("CONTINUE", "blueFlames")]])
    )

# Handoff into Part 2
async def on_blueFlames(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await q.edit_message_text("Blue flames interlude begins...")

def register_story_part1(application: Application, *, sudo_ids: Set[int] | None = None):
    global SUDO
    if sudo_ids is not None:
        SUDO = set(sudo_ids)

    # Commands
    application.add_handler(CommandHandler("start", start_cmd))

    # Name intake (private text only)
    application.add_handler(MessageHandler(filters.ChatType.PRIVATE & filters.TEXT & ~filters.COMMAND, get_name_text))

    # Core callbacks
    application.add_handler(CallbackQueryHandler(on_start_data, pattern=r"^start_data$"))

    application.add_handler(CallbackQueryHandler(on_gender, pattern=r"^(boy|girl)$"))
    application.add_handler(CallbackQueryHandler(on_gen_back, pattern=r"^gen$"))
    application.add_handler(CallbackQueryHandler(on_stats, pattern=r"^stats$"))
    application.add_handler(CallbackQueryHandler(on_stats_back, pattern=r"^bck$"))
    application.add_handler(CallbackQueryHandler(on_stats_continue, pattern=r"^aage$"))

    application.add_handler(CallbackQueryHandler(on_begin, pattern=r"^begin$"))
    application.add_handler(CallbackQueryHandler(on_next, pattern=r"^next$"))
    application.add_handler(CallbackQueryHandler(on_choice_c1, pattern=r"^(c1r1|c1r2|c1r3)$"))
    application.add_handler(CallbackQueryHandler(on_continue, pattern=r"^continue$"))
    application.add_handler(CallbackQueryHandler(on_choice_c2, pattern=r"^(c1r1c2|c1r2c2|c1r3c2)$"))
    application.add_handler(CallbackQueryHandler(on_choice_c2_res, pattern=r"^cont$"))

    application.add_handler(CallbackQueryHandler(on_s2, pattern=r"^s2$"))
    application.add_handler(CallbackQueryHandler(on_s2story, pattern=r"^s2story$"))
    application.add_handler(CallbackQueryHandler(on_nexts2o, pattern=r"^nexts2o$"))
    application.add_handler(CallbackQueryHandler(on_s2_choices, pattern=r"^(c1s2r1|c1s2r2|c1s2r3)$"))
    application.add_handler(CallbackQueryHandler(on_s2_outcome, pattern=r"^(c1s2o)_(\w+)$"))

    # Betrayal branches
    application.add_handler(CallbackQueryHandler(on_giveMoneyNext, pattern=r"^giveMoneyNext$"))
    application.add_handler(CallbackQueryHandler(on_next1, pattern=r"^next1$"))
    application.add_handler(CallbackQueryHandler(on_whatHappned, pattern=r"^whatHappned$"))
    application.add_handler(CallbackQueryHandler(on_renjiKilling, pattern=r"^renjiKilling$"))
    application.add_handler(CallbackQueryHandler(on_runAway, pattern=r"^runAway$"))
    application.add_handler(CallbackQueryHandler(on_goToHome, pattern=r"^goToHome$"))
    application.add_handler(CallbackQueryHandler(on_renjiKilling2, pattern=r"^renjiKilling2$"))
    application.add_handler(CallbackQueryHandler(on_deathScene, pattern=r"^deathScene$"))

    # Thief battle
    application.add_handler(CallbackQueryHandler(on_theifFight, pattern=r"^theifFight$"))
    application.add_handler(CallbackQueryHandler(on_punchTheif, pattern=r"^punchTheif$"))
    application.add_handler(CallbackQueryHandler(on_userLost, pattern=r"^userLost$"))

    # Handoff to Part 2
    application.add_handler(CallbackQueryHandler(on_blueFlames, pattern=r"^blueFlames$"))


# handlers/story_part2.py
# PTB v21+ async handler module for Story Part 2
# Continues from Part 1: blueFlames → Chapter 2 → footsteps stealth,
# demon encounter, Azaroth offers, shrine, two timed transformation tests,
# demon form stats, focus-control mini-game, dual slayers arena with symbols,
# demnext cinematic chain, Underworld Gate puzzle, and armory entry hook.

import asyncio
import random
import re
from typing import Dict, Any, List

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from telegram.ext import Application, CallbackQueryHandler, ContextTypes

# Pull shared state from Part 1
from handlers.story_part1 import get_story_state

# Shared dicts coming from Part 1
_state = get_story_state()
database: Dict[int, Dict[str, Any]] = _state["database"]

# Additional state for Part 2
count_dict: Dict[int, Dict[str, Any]] = {}     # stealth steps
aazaList: List[int] = []                        # offer timeout tracking
testDict: Dict[int, Dict[str, int]] = {}        # transformation tests
focusDict: Dict[int, Dict[str, int]] = {}       # focus control mini-game
focusList: List[int] = []                       # currently focusing
attactDict: Dict[int, Dict[str, Any]] = {}      # arena battle state
ongoing_puzzles: Dict[int, List[str]] = {}      # puzzle selection state
damage_taken: List[int] = []                    # regen flag for arena

def _kb(rows):
    return InlineKeyboardMarkup([[InlineKeyboardButton(t, callback_data=d) for t, d in row]])

def _hp_bar(cur: int, mx: int) -> str:
    mx = max(mx, 1)
    p = max(0.0, min(1.0, cur / mx))
    filled = int(round(p * 10))
    return "▰" * filled + "▱" * (10 - filled)

# ========== BlueFlames → Chapter 2 chain ==========

async def on_blueFlames_continue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    st = database.get(uid, {})
    try:
        await q.message.delete()
    except:
        pass
    await asyncio.sleep(1)
    pic = "https://files.catbox.moe/af7pw1.jpg" if st.get("gender") == "boy" else "https://files.catbox.moe/8bqghq.jpg"
    await context.bot.send_photo(
        q.message.chat.id,
        photo=pic,
        caption=(
            "<b>Narration</b>\n"
            "A blue-white light pulses from the body, threads of energy winding through the night.\n"
            "The air ripples. Sound vanishes. And then—everything shatters."
        ),
        reply_markup=_kb([[("CONTINUE", "afterBlueFlames")]]),
    )

async def on_afterBlueFlames(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    try:
        await q.message.delete()
    except:
        pass
    await asyncio.sleep(1)
    await context.bot.send_photo(
        q.message.chat.id,
        photo="https://files.catbox.moe/9g6wgr.jpg",
        caption=(
            "<b>Narration</b>\n"
            "A void of light—weightless and silent. Time stretches thin, then snaps back.\n"
            "A heartbeat returns."
        ),
        reply_markup=_kb([[("Next", "notDone")]]),
    )

async def on_notDone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    try:
        await q.message.delete()
    except:
        pass
    await asyncio.sleep(1)
    await context.bot.send_photo(
        q.message.chat.id,
        photo="https://files.catbox.moe/978iz8.jpg",
        caption=(
            "<b>Unknown Voice</b>\n"
            "\"You are not done yet.\""
        ),
        reply_markup=_kb([[("Move To Chapter 2", "chapter2")]]),
    )

async def on_chapter2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    try:
        await q.message.delete()
    except:
        pass
    await asyncio.sleep(1)
    await context.bot.send_photo(
        q.message.chat.id,
        photo="https://files.catbox.moe/w4nk76.jpg",
        caption="<b>CHAPTER 2:</b>\nFOLLOW YOUR HEART",
        reply_markup=_kb([[("CONTINUE", "Chap2Beggning")]]),
    )

async def on_Chap2Beggning(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    try:
        await q.message.delete()
    except:
        pass
    await asyncio.sleep(1)
    await context.bot.send_photo(
        q.message.chat.id,
        photo="https://files.catbox.moe/66s7t6.jpg",
        caption=(
            "<b>Mysterious Voice</b>\n"
            "\"You have fallen… but your story has not yet ended. Your fate bends, but it is not broken.\""
        ),
        reply_markup=_kb([[("CONTINUE", "prevOutcome")]]),
    )

async def on_prevOutcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    st = database.get(uid, {})
    try:
        await q.message.delete()
    except:
        pass
    await asyncio.sleep(1)
    pic = "https://files.catbox.moe/t20gtc.jpg" if st.get("gender") == "boy" else "https://files.catbox.moe/e4308s.jpg"
    prev = st.get("outcome", "none")
    if prev in ("GiveMoney", "Run"):
        txt = "The last thought burns: Why did Renji smile? Why did he turn the blade on a friend?"
    elif prev == "Distract":
        txt = "Renji’s life over yours. A choice that still aches—but some part of you would choose it again."
    else:
        txt = "Renji stood still as the world collapsed. His eyes said everything—and nothing."
    await context.bot.send_photo(
        q.message.chat.id,
        photo=pic,
        caption=f"<b>Echoes</b>\n{txt}",
        reply_markup=_kb([[("FOOTSTEPS", "someone")]]),
    )

# ========== Footsteps stealth mini-game ==========

async def on_someone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    try:
        await q.message.delete()
    except:
        pass
    await asyncio.sleep(1)
    await context.bot.send_photo(
        q.message.chat.id,
        photo="https://files.catbox.moe/d2md78.jpg",
        caption=(
            "<b>Narration</b>\n"
            "Footsteps close in fast through the tall grass. Whoever they are, they’re tracking something.\n\n"
            "What do you do?\n"
            "1) Hide in the bushes\n2) Run the opposite way\n3) Call for help"
        ),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Choice 1", callback_data="c2s2o1"),
             InlineKeyboardButton("Choice 2", callback_data="c2s2o2")],
            [InlineKeyboardButton("Choice 3", callback_data="c2s2o3")],
        ]),
    )

async def on_foot_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    st = database.get(uid, {})
    data = q.data
    await asyncio.sleep(1)
    try:
        await q.message.delete()
    except:
        pass

    if data == "c2s2o1":
        pic = "https://files.catbox.moe/p99y08.jpg" if st.get("gender") == "boy" else "https://files.catbox.moe/5t8354.jpg"
        await context.bot.send_photo(
            q.message.chat.id, photo=pic,
            caption="You drop low and crawl into a thick shrub, slowing your breath.",
            reply_markup=_kb([[("Continue", "bushContinue")]]),
        )
    elif data == "c2s2o2":
        pic = "https://files.catbox.moe/7rp4ok.jpg" if st.get("gender") == "boy" else "https://files.catbox.moe/4d1nts.jpg"
        await context.bot.send_photo(
            q.message.chat.id, photo=pic,
            caption="You sprint in the opposite direction, dodging roots and ducking branches.",
        )
        # Optional: could route back to someone after a beat, but original flow focuses on stealth/CFH
    else:
        pic = "https://files.catbox.moe/dk6ir7.jpg" if st.get("gender") == "boy" else "https://files.catbox.moe/lmp3yp.jpg"
        await context.bot.send_photo(
            q.message.chat.id, photo=pic,
            caption="You shout into the night: “Help! Anyone!”",
            reply_markup=_kb([[("Call For Help", "helpCall")]]),
        )

async def _timeout_edit(context: ContextTypes.DEFAULT_TYPE, chat_id: int, message_id: int):
    await asyncio.sleep(5)
    try:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text="A branch snaps. “There! In the bushes!”\nThey’re onto you.",
            reply_markup=_kb([[("Continue", "gameOver")]]),
        )
    except:
        # If user already interacted, ignore edit failures
        pass

async def on_bushContinue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    count_dict[uid] = {"count": 1}
    choice = random.choice(["right", "left", "forward", "backward"])
    await asyncio.sleep(1)
    msg = await context.bot.send_photo(
        q.message.chat.id,
        photo="https://files.catbox.moe/qeqvau.jpg",
        caption=f"Save your life: move <b>{choice}</b>",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Move forward ⬆️", f"forward_{choice}")],
            [InlineKeyboardButton("Move left ⬅️", f"left_{choice}"),
             InlineKeyboardButton("Move right ➡️", f"right_{choice}")],
            [InlineKeyboardButton("Move Backward ⬇️", f"backward_{choice}")],
        ]),
    )
    # 5s timeout to force a fail state if user waits
    context.application.create_task(_timeout_edit(context, q.message.chat.id, msg.message_id))

async def on_turns(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    m = re.match(r"^(left|right|forward|backward)_(\w+)$", q.data or "")
    if not m:
        return
    action, direction = m.groups()
    try:
        await q.message.delete()
    except:
        pass

    if action == direction:
        # 95% keep going, 5% early pass
        if random.choices(["keep", "pass"], weights=[95, 5])[0] == "keep":
            if count_dict.get(uid, {}).get("count", 0) >= 10:
                await context.bot.send_photo(
                    q.message.chat.id,
                    photo="https://files.catbox.moe/qeqvau.jpg",
                    caption="Footsteps fade. You held your breath long enough—they passed you by.",
                    reply_markup=_kb([[("CONTINUE", "failedConinue")]]),
                )
                count_dict.pop(uid, None)
                return

            count_dict.setdefault(uid, {"count": 1})
            count_dict[uid]["count"] += 1
            choice = random.choice(["right", "left", "forward", "backward"])
            buttons = [
                InlineKeyboardButton("Move forward ⬆️", f"forward_{choice}"),
                InlineKeyboardButton("Move left ⬅️", f"left_{choice}"),
                InlineKeyboardButton("Move right ➡️", f"right_{choice}"),
                InlineKeyboardButton("Move Backward ⬇️", f"backward_{choice}"),
            ]
            random.shuffle(buttons)
            await context.bot.send_photo(
                q.message.chat.id,
                photo="https://files.catbox.moe/hwwubn.jpg",
                caption=f"Save your life: move <b>{choice}</b>",
                reply_markup=InlineKeyboardMarkup([[buttons[0]], [buttons[1], buttons[2]], [buttons[3]]]),
            )
        else:
            await context.bot.send_photo(
                q.message.chat.id,
                photo="https://files.catbox.moe/qeqvau.jpg",
                caption="They pass by. You survive.",
                reply_markup=_kb([[("CONTINUE", "failedConinue")]]),
            )
            count_dict.pop(uid, None)
    else:
        await context.bot.send_photo(
            q.message.chat.id,
            photo="https://files.catbox.moe/rsge0c.jpg",
            caption="<b>GAME OVER</b>\nThey spotted you!",
            reply_markup=_kb([[("TRY AGAIN", "someone")]]),
        )
        count_dict.pop(uid, None)

async def on_gameOver(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    try:
        await q.message.delete()
    except:
        pass
    await asyncio.sleep(1)
    await context.bot.send_photo(
        q.message.chat.id,
        photo="https://files.catbox.moe/zjh0te.jpg",
        caption="<b>GAME OVER</b>\nYou were too slow.",
        reply_markup=_kb([[("TRY AGAIN", "someone")]]),
    )

async def on_failedContinue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    try:
        await q.message.delete()
    except:
        pass
    await asyncio.sleep(1)
    await context.bot.send_photo(
        q.message.chat.id,
        photo="https://files.catbox.moe/96ry23.jpg",
        caption="<b>Location:</b> Dead Forest\nThe trees lean like watchers in the dark.",
        reply_markup=_kb([[("There Is Something", "theresSomething")]]),
    )

async def on_helpCall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    try:
        await q.message.delete()
    except:
        pass
    await asyncio.sleep(1)
    await context.bot.send_photo(
        q.message.chat.id,
        photo="https://files.catbox.moe/ucutn8.jpg",
        caption="Figures in haori flash through the trees—Slayers.\nTheir blades shine like moonlight.",
        reply_markup=_kb([[("Continue", "slayerKilling")]]),
    )

async def on_slayerKilling(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    try:
        await q.message.delete()
    except:
        pass
    await asyncio.sleep(1)
    await context.bot.send_photo(
        q.message.chat.id,
        photo="https://files.catbox.moe/zjh0te.jpg",
        caption="<b>GAME OVER</b>\n“Humans don’t cry for help from the woods,” one mutters.\nThe blade falls.",
        reply_markup=_kb([[("Try again", "someone")]]),
    )

# ========== Demon encounter → talking shadow ==========

async def on_theresSomething(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    try:
        await q.message.delete()
    except:
        pass
    await asyncio.sleep(1)
    await context.bot.send_photo(
        q.message.chat.id,
        photo="https://files.catbox.moe/wtq6xg.jpg",
        caption=(
            "A figure with burning red eyes watches from between the trees.\n"
            "Do you:\n"
            "1) Look for a weapon and fight\n"
            "2) Run"
        ),
        reply_markup=_kb([[("CHOICE 1", "preDemonFight"), ("CHOICE 2", "theresSomething")]]),
    )

async def on_preDemonFight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    try:
        await q.message.delete()
    except:
        pass
    await asyncio.sleep(1)
    await context.bot.send_photo(
        q.message.chat.id,
        photo="https://files.catbox.moe/afqqpk.jpg",
        caption="You grab a fallen branch and brace like a spear.",
        reply_markup=_kb([[("Attack On Demon", "demonFight")]]),
    )

async def on_demonFight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    try:
        await q.message.delete()
    except:
        pass
    await asyncio.sleep(1)
    database.setdefault(uid, {})["demon_temp"] = {
        "user_health": 100, "demon_health": 999, "user_max_health": 100, "demon_max_health": 999, "count": 0
    }
    t = database[uid]["demon_temp"]
    await context.bot.send_photo(
        q.message.chat.id,
        photo="https://files.catbox.moe/7yggg2.jpg",
        caption=(
            "<b>Battle Begins</b>\n\n"
            "<b>Demon :</b>\n"
            f"{_hp_bar(t['demon_health'], t['demon_max_health'])}\n\n"
            "<b>Name :</b>\n"
            f"{_hp_bar(t['user_health'], t['user_max_health'])}\n\n"
        ),
        reply_markup=_kb([[("S T R I K E", "strikeDemon")]]),
    )

async def on_strikeDemon(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    t = database.get(uid, {}).get("demon_temp")
    if not t:
        await q.answer("Restarting demon fight...")
        return
    t["count"] += 1
    if t["count"] >= 4:
        try:
            await q.message.delete()
        except:
            pass
        await asyncio.sleep(1)
        pic = "https://files.catbox.moe/g07qgj.jpg" if database.get(uid, {}).get("gender") == "boy" else "https://files.catbox.moe/hobiir.jpg"
        await context.bot.send_photo(
            q.message.chat.id,
            photo=pic,
            caption=(
                "You charge. A shadowy shape blurs—your body slams into the dirt.\n\n"
                "<b>Shadow Figure</b>\n"
                "\"Pathetic. Yet brave.\""
            ),
            reply_markup=_kb([[("CONTINUE", "talkingShadow")]]),
        )
        database[uid].pop("demon_temp", None)
        return

    msg = await q.edit_message_text("Please wait—attacking...")
    await asyncio.sleep(1)
    await msg.edit_text(
        text="The demon tilts its head and lets your strike pass through empty air.\nIt doesn’t even raise a hand.",
        reply_markup=_kb([[("S T R I K E", "strikeDemon")]]),
    )

# ========== Azaroth offers (with timeout) ==========

async def _aaza_timeout(context: ContextTypes.DEFAULT_TYPE, uid: int):
    await asyncio.sleep(10)
    if uid in aazaList:
        try:
            await context.bot.send_photo(
                chat_id=uid,
                photo="https://files.catbox.moe/8c77d5.jpg",
                caption="<b>Azaroth</b>\n“Tick-tock... five... four... three...”",
                reply_markup=_kb([[("OFFER 1", "azzaoffer1"), ("OFFER 2", "aazaoffer2")]]),
            )
        except:
            pass

async def on_talkingShadow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    try:
        await q.message.delete()
    except:
        pass
    await asyncio.sleep(1)
    aazaList.append(uid)
    await context.bot.send_photo(
        q.message.chat.id,
        photo="https://files.catbox.moe/kr2qwi.jpg",
        caption=(
            "<b>Azaroth</b>\n"
            "“I am Azaroth, the hand that shapes demons from shattered souls. Now—choose.”\n\n"
            "Offer 1: Become a Demon and Join me\n"
            "Offer 2: Refuse and die here"
        ),
        reply_markup=_kb([[("OFFER 1", "azzaoffer1"), ("OFFER 2", "aazaoffer2")]]),
    )
    context.application.create_task(_aaza_timeout(context, uid))

async def on_azzaoffer1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    try:
        aazaList.remove(uid)
    except:
        pass
    try:
        await q.message.delete()
    except:
        pass
    await asyncio.sleep(1)
    await context.bot.send_photo(
        q.message.chat.id,
        photo="https://files.catbox.moe/4h6li4.jpg",
        caption=(
            "<b>Protagonist</b>\n"
            "“I’ll become a demon.”\n\n"
            "<b>Azaroth</b>\n"
            "“A brave choice. Come then—rise.”"
        ),
        reply_markup=_kb([[("D E M O N - P A T H", "demonPath")]]),
    )

async def on_aazaoffer2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # If user refuses: you can direct to a death loop or re-offer.
    q = update.callback_query
    await q.answer()
    try:
        await q.message.delete()
    except:
        pass
    await context.bot.send_photo(
        q.message.chat.id,
        photo="https://files.catbox.moe/8c77d5.jpg",
        caption="<b>Azaroth</b>\n“Stubborn. Let’s ask again…”",
        reply_markup=_kb([[("OFFER 1", "azzaoffer1"), ("OFFER 2", "aazaoffer2")]]),
    )

# ========== Shrine journey and tests ==========

async def on_demonPath(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    try:
        await q.message.delete()
    except:
        pass
    await asyncio.sleep(1)
    await context.bot.send_photo(
        q.message.chat.id,
        photo="https://files.catbox.moe/gu20j3.jpg",
        caption="<b>Azaroth</b>\n“To the Shrine.”",
        reply_markup=_kb([[("Head To Shrine", "demonShrine")]]),
    )

async def on_demonShrine(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    try:
        await q.message.delete()
    except:
        pass
    await asyncio.sleep(1)
    await context.bot.send_photo(
        q.message.chat.id,
        photo="https://files.catbox.moe/0e525f.jpg",
        caption="[Location: Shrine of Shadows]",
        reply_markup=_kb([[("CONTINUE", "shadowShrine")]]),
    )

async def on_shadowShrine(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    try:
        await q.message.delete()
    except:
        pass
    await asyncio.sleep(1)
    await context.bot.send_photo(
        q.message.chat.id,
        photo="https://files.catbox.moe/41ggte.jpg",
        caption="<b>Azaroth</b>\n“Now—kneel.”",
        reply_markup=_kb([[("Continue", "preAazaKneel")]]),
    )

async def on_preAazaKneel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    st = database.get(uid, {})
    try:
        await q.message.delete()
    except:
        pass
    await asyncio.sleep(1)
    pic = "https://files.catbox.moe/bfnfdx.jpg" if st.get("gender") == "boy" else "https://files.catbox.moe/fzhbrf.jpg"
    await context.bot.send_photo(
        q.message.chat.id,
        photo=pic,
        caption="The shrine hums with a hungry power.",
        reply_markup=_kb([[("Kneel", "aazaKneel")]]),
    )

async def on_aazaKneel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    st = database.get(uid, {})
    try:
        await q.message.delete()
    except:
        pass
    await asyncio.sleep(1)
    pic = "https://files.catbox.moe/jguuhi.jpg" if st.get("gender") == "boy" else "https://files.catbox.moe/u4leld.jpg"
    await context.bot.send_photo(
        q.message.chat.id,
        photo=pic,
        caption="<b>Azaroth</b>\n“Drink… and be reborn.”",
        reply_markup=_kb([[("Drink Blood", "drinkBlood")]]),
    )

# ---- Test 1: Burst vs Endurance (20s timeout)

async def _burst_timeout(context: ContextTypes.DEFAULT_TYPE, uid: int):
    await asyncio.sleep(20)
    if uid not in testDict:
        return
    b = testDict[uid]["bursts"]
    e = testDict[uid]["endurance"]
    bar_b = "▰" * (b // 10) + "▱" * ((100 - b) // 10)
    bar_e = "▰" * (e // 10) + "▱" * ((100 - e) // 10)
    st = database.get(uid, {})
    pic = "https://files.catbox.moe/awnppt.jpg" if st.get("gender") == "boy" else "https://files.catbox.moe/7rjev8.jpg"
    if e > 50:
        await context.bot.send_photo(
            uid, photo=pic,
            caption=(f"<b>You Passed Demon Transformation Test</b>\n\nBurst {bar_b} {b}%\nEndurance {bar_e} {e}%"),
            reply_markup=_kb([[("Move Forward", "moveForward")]]),
        )
    else:
        await context.bot.send_photo(
            uid, photo="https://files.catbox.moe/rsge0c.jpg",
            caption=(f"<b>GAME OVER</b>\n\nYou Failed Demon Transformation Test\n\nBurst {bar_b} {b}%\nEndurance {bar_e} {e}%"),
            reply_markup=_kb([[("Try Again", "demonShrine")]]),
        )
    testDict.pop(uid, None)

async def on_drinkBlood(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    st = database.get(uid, {})
    try:
        await q.message.delete()
    except:
        pass
    await asyncio.sleep(1)
    testDict[uid] = {"bursts": 50, "endurance": 50}
    bbar = "▰" * 5 + "▱" * 5
    ebar = "▰" * 5 + "▱" * 5
    pic = "https://files.catbox.moe/awnppt.jpg" if st.get("gender") == "boy" else "https://files.catbox.moe/7rjev8.jpg"
    await context.bot.send_photo(
        q.message.chat.id,
        photo=pic,
        caption=(f"<b>Test 1</b>\nBurst {bbar} 50%\n──────────\nEndurance {ebar} 50%\nEndurance must be >50%"),
        reply_markup=_kb([[("Pump Out", "burstTest")]]),
    )
    context.application.create_task(_burst_timeout(context, uid))

async def on_burstTest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    if uid not in testDict:
        await q.answer("Test ended")
        return
    x = await q.edit_message_text("Please wait")
    await asyncio.sleep(1)
    if random.random() > 0.6:
        change = random.choice([10, 20])
        testDict[uid]["endurance"] = max(0, min(100, testDict[uid]["endurance"] - change))
        testDict[uid]["bursts"] = max(0, min(100, testDict[uid]["bursts"] + change))
        dec = f"Your Burst +{change}\nYour Endurance -{change}"
    else:
        testDict[uid]["endurance"] = max(0, min(100, testDict[uid]["endurance"] + 10))
        testDict[uid]["bursts"] = max(0, min(100, testDict[uid]["bursts"] - 10))
        dec = "Your Endurance +10\nYour Burst -10"
    b = testDict[uid]["bursts"]
    e = testDict[uid]["endurance"]
    bbar = "▰" * (b // 10) + "▱" * ((100 - b) // 10)
    ebar = "▰" * (e // 10) + "▱" * ((100 - e) // 10)
    await x.edit_text(
        f"<b>Test 1</b>\nBurst {bbar} {b}%\n──────────\nEndurance {ebar} {e}%\n<pre>{dec}</pre>",
        reply_markup=_kb([[("Pump Out", "burstTest")]]),
    )

# ---- Test 2: Complete Transformation (20s timeout)

async def on_moveForward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    st = database.get(uid, {})
    try:
        await q.message.delete()
    except:
        pass
    await asyncio.sleep(1)
    pic = "https://files.catbox.moe/epocuc.jpg" if st.get("gender") == "boy" else "https://files.catbox.moe/0hg003.jpg"
    await context.bot.send_photo(
        q.message.chat.id,
        photo=pic,
        caption="<b>Azaroth</b>\n“Complete the transformation.”",
        reply_markup=_kb([[("Complete Demon Transformation", "compleateTransformation")]]),
    )

async def _endu_timeout(context: ContextTypes.DEFAULT_TYPE, uid: int):
    await asyncio.sleep(20)
    if uid not in testDict:
        return
    b = testDict[uid]["bursts"]
    e = testDict[uid]["endurance"]
    bbar = "▰" * (b // 10) + "▱" * ((100 - b) // 10)
    ebar = "▰" * (e // 10) + "▱" * ((100 - e) // 10)
    st = database.get(uid, {})
    pic = "https://files.catbox.moe/phyqh8.jpg" if st.get("gender") == "boy" else "https://files.catbox.moe/5esxlu.jpg"
    if e > 50:
        await context.bot.send_photo(
            uid, photo=pic,
            caption=(f"<b>Passed</b>\nBurst {bbar} {b}%\nEndurance {ebar} {e}%"),
            reply_markup=_kb([[("Continue", "compleateForm")]]),
        )
    else:
        await context.bot.send_photo(
            uid, photo="https://files.catbox.moe/rsge0c.jpg",
            caption=(f"<b>GAME OVER</b>\nBurst {bbar} {b}%\nEndurance {ebar} {e}%"),
            reply_markup=_kb([[("Try Again", "demonShrine")]]),
        )
    testDict.pop(uid, None)

async def on_compleateTransformation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    st = database.get(uid, {})
    try:
        await q.message.delete()
    except:
        pass
    await asyncio.sleep(1)
    testDict[uid] = {"bursts": 50, "endurance": 50}
    bbar = "▰" * 5 + "▱" * 5
    ebar = "▰" * 5 + "▱" * 5
    pic = "https://files.catbox.moe/phyqh8.jpg" if st.get("gender") == "boy" else "https://files.catbox.moe/5esxlu.jpg"
    await context.bot.send_photo(
        q.message.chat.id,
        photo=pic,
        caption=(f"<b>Test 2</b>\nBurst {bbar} 50%\n──────────\nEndurance {ebar} 50%\nHarder threshold: Endurance >50%"),
        reply_markup=_kb([[("Pump Out", "EnduranceTest")]]),
    )
    context.application.create_task(_endu_timeout(context, uid))

async def on_EnduranceTest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    if uid not in testDict:
        await q.answer("Test ended")
        return
    x = await q.edit_message_text("Please wait")
    await asyncio.sleep(1)
    if random.random() > 0.3:
        change = random.choice([10, 30])
        testDict[uid]["endurance"] = max(0, min(100, testDict[uid]["endurance"] - change))
        testDict[uid]["bursts"] = max(0, min(100, testDict[uid]["bursts"] + change))
        dec = f"Endurance -{change}; Burst +{change}"
    else:
        testDict[uid]["endurance"] = max(0, min(100, testDict[uid]["endurance"] + 10))
        testDict[uid]["bursts"] = max(0, min(100, testDict[uid]["bursts"] - 10))
        dec = "Endurance +10; Burst -10"
    b = testDict[uid]["bursts"]
    e = testDict[uid]["endurance"]
    bbar = "▰" * (b // 10) + "▱" * ((100 - b) // 10)
    ebar = "▰" * (e // 10) + "▱" * ((100 - e) // 10)
    await x.edit_text(
        f"<b>Test 2</b>\nBurst {bbar} {b}%\n──────────\nEndurance {ebar} {e}%\n<pre>{dec}</pre>",
        reply_markup=_kb([[("Pump Out", "EnduranceTest")]]),
    )

# ---- Complete form and stats

async def on_compleateForm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    st = database.get(uid, {})
    try:
        await q.message.delete()
    except:
        pass
    await asyncio.sleep(1)
    pic = "https://files.catbox.moe/n4qb2f.jpg" if st.get("gender") == "boy" else "https://files.catbox.moe/wej2q7.jpg"
    await context.bot.send_photo(
        q.message.chat.id,
        photo=pic,
        caption="<b>Azaroth</b>\n“A true demon reborn. Your hunger will guide you—if you can control it.”",
        reply_markup=_kb([[("View Stats", "compleateStats")]]),
    )

async def on_compleateStats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    st = database.get(uid, {})

    male = """<b>Current Stats</b>
<b>Core Stats</b>
───────────────────────
[STR] - 10 → 20
[AGI] - 8 → 16
[END] - 12 → 24
[BB]  - 10 → 20
[INT] - 9 → 18
[PER] - 9 → 18

<b>Secondary Stats</b>
───────────────────────
[HP]  - 120 → 240
[STA] - 110 → 220
[SP]  - 100 → 200
[DEF] - 24 → 48
[CRIT] - 9% → 11%
"""
    female = """<b>Current Stats</b>
<b>Core Stats</b>
───────────────────────
[STR] - 8 → 16
[AGI] - 12 → 24
[END] - 9 → 18
[BB]  - 10 → 20
[INT] - 10 → 20
[PER] - 11 → 22

<b>Secondary Stats</b>
───────────────────────
[HP]  - 90 → 180
[STA] - 95 → 190
[SP]  - 100 → 200
[DEF] - 18 → 36
[CRIT] - 11% → 13%
"""
    await q.edit_message_text(
        male if st.get("gender") == "boy" else female,
        reply_markup=_kb([[("Continue", "compleateStatsCont")]]),
    )

async def on_compleateStatsCont(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    try:
        await q.message.delete()
    except:
        pass
    await asyncio.sleep(1)
    await context.bot.send_photo(
        q.message.chat.id,
        photo="https://files.catbox.moe/h2uz0j.jpg",
        caption="<b>Azaroth</b>\n“Strength without control is a beast on a chain. Let’s test your leash.”",
        reply_markup=_kb([[("Begin Focus Control", "focusControl")]]),
    )

# ========== Focus-control mini-game (30s timeout) ==========

async def _focus_timeout(context: ContextTypes.DEFAULT_TYPE, uid: int):
    await asyncio.sleep(30)
    if uid not in focusDict:
        return
    pts = focusDict[uid]["contrlPoints"]
    if pts == 5:
        # success
        await context.bot.send_message(
            uid,
            text="<b>Focus stabilized at 5</b>\nYou kept the beast within the leash.",
        )
        await context.bot.send_photo(
            uid,
            photo="https://files.catbox.moe/9e1m1p.jpg",
            caption="Your senses sharpen. The hunger quiets—for now.",
            reply_markup=_kb([[("Proceed", "wolf")]]),
        )
    else:
        # fail
        await context.bot.send_message(
            uid,
            text=f"<b>Focus drifted to {pts}</b>\nYou failed to stabilize.",
        )
        await context.bot.send_photo(
            uid,
            photo="https://files.catbox.moe/rsge0c.jpg",
            caption="Try again. Find the still point between frenzy and apathy.",
            reply_markup=_kb([[("Retry Focus", "focusControl")]]),
        )
    focusDict.pop(uid, None)
    try:
        focusList.remove(uid)
    except:
        pass

async def on_focusControl(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    try:
        await q.message.delete()
    except:
        pass
    focusDict[uid] = {"contrlPoints": 10}
    if uid not in focusList:
        focusList.append(uid)
    await asyncio.sleep(1)
    await context.bot.send_photo(
        q.message.chat.id,
        photo="https://files.catbox.moe/1x3z8w.jpg",
        caption=(
            "<b>Focus Control</b>\n"
            "Bring the control to exactly <b>5</b> within 30s.\n"
            "Actions:\n"
            "• Calm: −1..+2\n"
            "• Focus: +1..+3\n"
            "• Release: ±1..±3 (50/50)\n"
            "• Embrace: ±5..±7 (50/50)"
        ),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Calm", callback_data="fc_calm"),
             InlineKeyboardButton("Focus", callback_data="fc_focus")],
            [InlineKeyboardButton("Release", callback_data="fc_release"),
             InlineKeyboardButton("Embrace", callback_data="fc_embrace")],
        ]),
    )
    context.application.create_task(_focus_timeout(context, uid))

async def on_focus_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    if uid not in focusDict:
        await q.answer("Focus session ended")
        return
    pts = focusDict[uid]["contrlPoints"]
    act = q.data

    if act == "fc_calm":
        delta = random.randint(-1, 2)
    elif act == "fc_focus":
        delta = random.randint(1, 3)
    elif act == "fc_release":
        delta = random.choice([1, 2, 3, -1, -2, -3])
    else:  # fc_embrace
        delta = random.choice([5, 6, 7, -5, -6, -7])

    pts += delta
    focusDict[uid]["contrlPoints"] = pts

    if pts == 5:
        # immediate success
        focusDict.pop(uid, None)
        try:
            focusList.remove(uid)
        except:
            pass
        await q.edit_message_caption(
            caption=f"<b>Focus stabilized at 5</b>\nYou held the center.\n\n(Δ {delta:+})",
            reply_markup=_kb([[("Proceed", "wolf")]]),
        )
        return

    if pts < 0 or pts > 10:
        # immediate fail
        focusDict.pop(uid, None)
        try:
            focusList.remove(uid)
        except:
            pass
        await q.edit_message_caption(
            caption=f"<b>Focus lost ({pts})</b>\nTry again.\n\n(Δ {delta:+})",
            reply_markup=_kb([[("Retry Focus", "focusControl")]]),
        )
        return

    await q.edit_message_caption(
        caption=f"<b>Control</b>: {pts}/10\n(Δ {delta:+})\nGoal: reach exactly 5.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Calm", callback_data="fc_calm"),
             InlineKeyboardButton("Focus", callback_data="fc_focus")],
            [InlineKeyboardButton("Release", callback_data="fc_release"),
             InlineKeyboardButton("Embrace", callback_data="fc_embrace")],
        ]),
    )

# ========== Arena: dual slayers with symbol actions ==========

def _arena_init(uid: int):
    attactDict[uid] = {
        "user_hp": 180, "user_max": 180,
        "sl1_hp": 200, "sl1_max": 200,
        "sl2_hp": 200, "sl2_max": 200,
        "count": 0,
        "phase": 1,        # later phases can change behavior
        "both_bleed": False,
    }

async def on_wolf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # lead into arena narrative
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    try:
        await q.message.delete()
    except:
        pass
    await asyncio.sleep(1)
    await context.bot.send_photo(
        q.message.chat.id,
        photo="https://files.catbox.moe/2g5mjp.jpg",
        caption="A howl in the distance answers something inside you.\nYou sense enemies approaching.",
        reply_markup=_kb([[("Continue", "ornate")]]),
    )

async def on_ornate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    try:
        await q.message.delete()
    except:
        pass
    await context.bot.send_photo(
        q.message.chat.id,
        photo="https://files.catbox.moe/nq8t7v.jpg",
        caption="An ornate sigil burns onto the ground. Two silhouettes step through—Slayers.",
        reply_markup=_kb([[("Continue", "garments")]]),
    )

async def on_garments(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    try:
        await q.message.delete()
    except:
        pass
    await context.bot.send_photo(
        q.message.chat.id,
        photo="https://files.catbox.moe/2wrg1r.jpg",
        caption="They don garments inscribed with wards. Steel sings. Blood remembers.",
        reply_markup=_kb([[("Continue", "thatAura")]]),
    )

async def on_thatAura(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    try:
        await q.message.delete()
    except:
        pass
    await context.bot.send_photo(
        q.message.chat.id,
        photo="https://files.catbox.moe/8t0g1g.jpg",
        caption="Their aura presses down like a storm front. Killing intent condenses.",
        reply_markup=_kb([[("Continue", "strikeHim")]]),
    )

async def on_strikeHim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    _arena_init(uid)
    try:
        await q.message.delete()
    except:
        pass
    await context.bot.send_photo(
        q.message.chat.id,
        photo="https://files.catbox.moe/8o6q8g.jpg",
        caption="You lunge first.",
        reply_markup=_kb([[("ATTACK THEM", "attackThem")]]),
    )

async def on_attackThem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    st = attactDict.get(uid)
    if not st:
        _arena_init(uid)
        st = attactDict[uid]
    try:
        await q.message.delete()
    except:
        pass

    # Symbols map explanation (triangle/square/circle/x)
    caption = (
        "<b>Arena</b>\n"
        f"Slayer 1: { _hp_bar(st['sl1_hp'], st['sl1_max']) }  |  "
        f"Slayer 2: { _hp_bar(st['sl2_hp'], st['sl2_max']) }\n"
        f"You: { _hp_bar(st['user_hp'], st['user_max']) }\n\n"
        "Choose an action pair to outmaneuver them."
    )
    await context.bot.send_photo(
        q.message.chat.id,
        photo="https://files.catbox.moe/7l1x5k.jpg",
        caption=caption,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("△ → ↺", callback_data="action_tri_left_sl1_1"),
             InlineKeyboardButton("□ → ↻", callback_data="action_sq_right_sl2_1")],
            [InlineKeyboardButton("○ → feint", callback_data="action_cir_feint_any_1"),
             InlineKeyboardButton("× → strike", callback_data="action_x_hit_any_1")],
        ]),
    )

def _arena_apply(uid: int, move: str):
    st = attactDict[uid]
    log = ""
    if move == "tri_left_sl1":
        dmg = random.randint(25, 40)
        st["sl1_hp"] = max(0, st["sl1_hp"] - dmg)
        log = f"You cut low at Slayer 1 for {dmg}."
    elif move == "sq_right_sl2":
        dmg = random.randint(25, 40)
        st["sl2_hp"] = max(0, st["sl2_hp"] - dmg)
        log = f"You drive a knee and slash—Slayer 2 takes {dmg}."
    elif move == "cir_feint_any":
        # small damage both, but open counter
        dmg = random.randint(10, 18)
        st["sl1_hp"] = max(0, st["sl1_hp"] - dmg)
        st["sl2_hp"] = max(0, st["sl2_hp"] - dmg)
        log = f"You feint—a glancing cut hits both Slayers ({dmg} each)."
    else:  # x_hit_any
        # strong hit on random target
        target = "sl1_hp" if random.random() < 0.5 else "sl2_hp"
        dmg = random.randint(35, 55)
        st[target] = max(0, st[target] - dmg)
        victim = "Slayer 1" if target == "sl1_hp" else "Slayer 2"
        log = f"You commit—{victim} takes a brutal {dmg}."

    # Slayers react
    rdmg = random.randint(18, 32)
    st["user_hp"] = max(0, st["user_hp"] - rdmg)
    log += f"\nThey retaliate for {rdmg}."

    # Simple regen trigger once when user first drops below threshold
    if st["user_hp"] < st["user_max"] // 2 and uid not in damage_taken:
        damage_taken.append(uid)
        heal = 30
        st["user_hp"] = min(st["user_max"], st["user_hp"] + heal)
        log += f"\nYour flesh knits—regeneration restores {heal}."

    return log

def _arena_check_end(uid: int):
    st = attactDict[uid]
    if st["user_hp"] <= 0:
        return "lose"
    if st["sl1_hp"] <= 0 and st["sl2_hp"] <= 0:
        return "win"
    return "cont"

async def on_action_symbol(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    st = attactDict.get(uid)
    if not st:
        _arena_init(uid)
        st = attactDict[uid]

    m = re.match(r"^action_(tri|sq|cir|x)_(left|right|feint|hit)_(sl1|sl2|any)_(\d+)$", q.data or "")
    if not m:
        await q.answer("Unknown move")
        return
    shape, dir_or_type, tgt, num = m.groups()
    key = None
    if shape == "tri":
        key = "tri_left_sl1"
    elif shape == "sq":
        key = "sq_right_sl2"
    elif shape == "cir":
        key = "cir_feint_any"
    else:
        key = "x_hit_any"

    log = _arena_apply(uid, key)
    state = _arena_check_end(uid)

    # Build caption
    caption = (
        "<b>Arena</b>\n"
        f"Slayer 1: { _hp_bar(st['sl1_hp'], st['sl1_max']) }  |  "
        f"Slayer 2: { _hp_bar(st['sl2_hp'], st['sl2_max']) }\n"
        f"You: { _hp_bar(st['user_hp'], st['user_max']) }\n\n"
        f"<pre>{log}</pre>"
    )

    if state == "lose":
        attactDict.pop(uid, None)
        try:
            damage_taken.remove(uid)
        except:
            pass
        await q.edit_message_media(
            media=InputMediaPhoto(
                media="https://files.catbox.moe/rsge0c.jpg",
                caption=caption + "\n<b>You fall.</b>",
            ),
            reply_markup=_kb([[("Retry Arena", "attackThem")]]),
        )
        return

    if state == "win":
        attactDict.pop(uid, None)
        try:
            damage_taken.remove(uid)
        except:
            pass
        await q.edit_message_media(
            media=InputMediaPhoto(
                media="https://files.catbox.moe/1z2f4g.jpg",
                caption=caption + "\n<b>Both Slayers collapse.</b>",
            ),
            reply_markup=_kb([[("Continue", "demnext_2")]]),
        )
        return

    # Continue arena
    await q.edit_message_media(
        media=InputMediaPhoto(
            media="https://files.catbox.moe/7l1x5k.jpg",
            caption=caption,
        ),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("△ → ↺", callback_data="action_tri_left_sl1_1"),
             InlineKeyboardButton("□ → ↻", callback_data="action_sq_right_sl2_1")],
            [InlineKeyboardButton("○ → feint", callback_data="action_cir_feint_any_1"),
             InlineKeyboardButton("× → strike", callback_data="action_x_hit_any_1")],
        ]),
    )

# ========== Cinematic demnext chain (subset to key beats) ==========

# We’ll implement a representative cinematic chain including the Underworld Gate puzzle
# and arrival to the armory, keeping IDs aligned so you can expand easily.

_demnext_scenes = {
    "2":  ("https://files.catbox.moe/6y9x3a.jpg", "The air stills. A crow watches from a bleached branch."),
    "3":  ("https://files.catbox.moe/0g7m0y.jpg", "A shape carves the horizon—power beyond Slayers."),
    "4":  ("https://files.catbox.moe/pm3j8s.jpg", "Azaroth’s presence presses the world into silence."),
    "5":  ("https://files.catbox.moe/8r1r2k.jpg", "“Come,” he says. “Doors open for those who dare.”"),
    "16": ("https://files.catbox.moe/4q6l0y.jpg", "A gate etched with four runes stands before you."),
    "17": ("https://files.catbox.moe/1r9p2z.jpg", "“Prove you understand the path.” Choose runes in order."),
    "18": ("https://files.catbox.moe/q2l4w3.jpg", "The gate groans open."),
    "40": ("https://files.catbox.moe/5x9k7m.jpg", "A tunnel breathes cold air and secrets."),
    "41": ("https://files.catbox.moe/3c8b1n.jpg", "Lanterns flicker to a feast of steel and night."),
    "42": ("https://files.catbox.moe/1k2m3n.jpg", "Welcome to your Armory."),
}

async def on_demnext(update: Update, context: ContextTypes.DEFAULT_TYPE, idx: str):
    q = update.callback_query
    await q.answer()
    try:
        await q.message.delete()
    except:
        pass

    photo, caption = _demnext_scenes[idx]
    next_btn = None
    if idx == "2":
        next_btn = ("Next", "demnext_3")
    elif idx == "3":
        next_btn = ("Next", "demnext_4")
    elif idx == "4":
        next_btn = ("Next", "demnext_5")
    elif idx == "5":
        next_btn = ("Underworld Gate", "demnext_16")
    elif idx == "16":
        next_btn = ("Study the runes", "demnext_17")
    elif idx == "17":
        # Puzzle entry
        await context.bot.send_photo(
            q.message.chat.id,
            photo=photo,
            caption=caption + "\n\n<b>Pick the sequence of four:</b>\nBirth • Journey • Sacrifice • Rebirth",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Birth", "puzzle_birth"),
                 InlineKeyboardButton("Journey", "puzzle_journey")],
                [InlineKeyboardButton("Sacrifice", "puzzle_sacrifice"),
                 InlineKeyboardButton("Rebirth", "puzzle_rebirth")],
                [InlineKeyboardButton("Reset", "puzzle_reset")],
            ]),
        )
        return
    elif idx == "18":
        next_btn = ("Proceed", "demnext_40")
    elif idx == "40":
        next_btn = ("Next", "demnext_41")
    elif idx == "41":
        next_btn = ("Enter", "demnext_42")
    elif idx == "42":
        # Armory hook
        await context.bot.send_photo(
            q.message.chat.id,
            photo=photo,
            caption=caption + "\n\nPick your path.",
            reply_markup=_kb([[("Enter Armory", "armory")]]),
        )
        return

    await context.bot.send_photo(
        q.message.chat.id,
        photo=photo,
        caption=caption,
        reply_markup=_kb([[next_btn]] if next_btn else []),
    )

async def on_demnext_2(update: Update, context: ContextTypes.DEFAULT_TYPE):  return await on_demnext(update, context, "2")
async def on_demnext_3(update: Update, context: ContextTypes.DEFAULT_TYPE):  return await on_demnext(update, context, "3")
async def on_demnext_4(update: Update, context: ContextTypes.DEFAULT_TYPE):  return await on_demnext(update, context, "4")
async def on_demnext_5(update: Update, context: ContextTypes.DEFAULT_TYPE):  return await on_demnext(update, context, "5")
async def on_demnext_16(update: Update, context: ContextTypes.DEFAULT_TYPE): return await on_demnext(update, context, "16")
async def on_demnext_17(update: Update, context: ContextTypes.DEFAULT_TYPE): return await on_demnext(update, context, "17")
async def on_demnext_18(update: Update, context: ContextTypes.DEFAULT_TYPE): return await on_demnext(update, context, "18")
async def on_demnext_40(update: Update, context: ContextTypes.DEFAULT_TYPE): return await on_demnext(update, context, "40")
async def on_demnext_41(update: Update, context: ContextTypes.DEFAULT_TYPE): return await on_demnext(update, context, "41")
async def on_demnext_42(update: Update, context: ContextTypes.DEFAULT_TYPE): return await on_demnext(update, context, "42")

# ========== Puzzle: Underworld Gate (Birth → Journey → Sacrifice → Rebirth) ==========

PUZZLE_SEQ = ["birth", "journey", "sacrifice", "rebirth"]

async def _puzzle_state(uid: int) -> List[str]:
    return ongoing_puzzles.setdefault(uid, [])

async def on_puzzle_pick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    m = re.match(r"^puzzle_(birth|journey|sacrifice|rebirth)$", q.data or "")
    if not m:
        return
    pick = m.group(1)
    seq = await _puzzle_state(uid)
    seq.append(pick)
    if len(seq) < 4:
        await q.edit_message_caption(
            caption=f"Picked: {', '.join(seq).title()}\nPick {4 - len(seq)} more.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Birth", "puzzle_birth"),
                 InlineKeyboardButton("Journey", "puzzle_journey")],
                [InlineKeyboardButton("Sacrifice", "puzzle_sacrifice"),
                 InlineKeyboardButton("Rebirth", "puzzle_rebirth")],
                [InlineKeyboardButton("Reset", "puzzle_reset")],
            ]),
        )
        return

    # Validate
    if seq == PUZZLE_SEQ:
        ongoing_puzzles.pop(uid, None)
        await q.edit_message_caption(
            caption="The sequence resonates. The gate acknowledges your path.",
            reply_markup=_kb([[("Open the Gate", "demnext_18")]]),
        )
    else:
        ongoing_puzzles.pop(uid, None)
        await q.edit_message_caption(
            caption=f"The runes flash angrily.\nWrong order: {', '.join(seq).title()}",
            reply_markup=_kb([[("Try Again", "demnext_16")]]),
        )

async def on_puzzle_reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    ongoing_puzzles.pop(uid, None)
    await q.edit_message_caption(
        caption="Sequence reset.\nPick again: Birth • Journey • Sacrifice • Rebirth",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Birth", "puzzle_birth"),
             InlineKeyboardButton("Journey", "puzzle_journey")],
            [InlineKeyboardButton("Sacrifice", "puzzle_sacrifice"),
             InlineKeyboardButton("Rebirth", "puzzle_rebirth")],
            [InlineKeyboardButton("Reset", "puzzle_reset")],
        ]),
    )

# ========== Armory entry hook (integrate your own armory module here) ==========

async def on_armory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    # Here you can call your armory loader/hooks if present.
    await q.edit_message_caption(
        caption="The Armory awaits. Integrate your weapon system here.\n(Placeholder entry point.)"
    )

# ========== Registration for Part 2 ==========

def register_story_part2(application: Application):
    # BlueFlames to Chapter 2
    application.add_handler(CallbackQueryHandler(on_blueFlames_continue, pattern=r"^blueFlames$"))
    application.add_handler(CallbackQueryHandler(on_afterBlueFlames, pattern=r"^afterBlueFlames$"))
    application.add_handler(CallbackQueryHandler(on_notDone, pattern=r"^notDone$"))
    application.add_handler(CallbackQueryHandler(on_chapter2, pattern=r"^chapter2$"))
    application.add_handler(CallbackQueryHandler(on_Chap2Beggning, pattern=r"^Chap2Beggning$"))
    application.add_handler(CallbackQueryHandler(on_prevOutcome, pattern=r"^prevOutcome$"))

    # Footsteps / Stealth
    application.add_handler(CallbackQueryHandler(on_someone, pattern=r"^someone$"))
    application.add_handler(CallbackQueryHandler(on_foot_choice, pattern=r"^(c2s2o1|c2s2o2|c2s2o3)$"))
    application.add_handler(CallbackQueryHandler(on_bushContinue, pattern=r"^bushContinue$"))
    application.add_handler(CallbackQueryHandler(on_turns, pattern=r"^(left|right|forward|backward)_(\w+)$"))
    application.add_handler(CallbackQueryHandler(on_gameOver, pattern=r"^gameOver$"))
    application.add_handler(CallbackQueryHandler(on_failedContinue, pattern=r"^failedConinue$"))
    application.add_handler(CallbackQueryHandler(on_helpCall, pattern=r"^helpCall$"))
    application.add_handler(CallbackQueryHandler(on_slayerKilling, pattern=r"^slayerKilling$"))

    # Demon encounter
    application.add_handler(CallbackQueryHandler(on_theresSomething, pattern=r"^theresSomething$"))
    application.add_handler(CallbackQueryHandler(on_preDemonFight, pattern=r"^preDemonFight$"))
    application.add_handler(CallbackQueryHandler(on_demonFight, pattern=r"^demonFight$"))
    application.add_handler(CallbackQueryHandler(on_strikeDemon, pattern=r"^strikeDemon$"))

    # Azaroth offers
    application.add_handler(CallbackQueryHandler(on_talkingShadow, pattern=r"^talkingShadow$"))
    application.add_handler(CallbackQueryHandler(on_azzaoffer1, pattern=r"^azzaoffer1$"))
    application.add_handler(CallbackQueryHandler(on_aazaoffer2, pattern=r"^aazaoffer2$"))
    application.add_handler(CallbackQueryHandler(on_demonPath, pattern=r"^demonPath$"))
    application.add_handler(CallbackQueryHandler(on_demonShrine, pattern=r"^demonShrine$"))
    application.add_handler(CallbackQueryHandler(on_shadowShrine, pattern=r"^shadowShrine$"))
    application.add_handler(CallbackQueryHandler(on_preAazaKneel, pattern=r"^preAazaKneel$"))
    application.add_handler(CallbackQueryHandler(on_aazaKneel, pattern=r"^aazaKneel$"))

    # Transformation tests
    application.add_handler(CallbackQueryHandler(on_drinkBlood, pattern=r"^drinkBlood$"))
    application.add_handler(CallbackQueryHandler(on_burstTest, pattern=r"^burstTest$"))
    application.add_handler(CallbackQueryHandler(on_moveForward, pattern=r"^moveForward$"))
    application.add_handler(CallbackQueryHandler(on_compleateTransformation, pattern=r"^compleateTransformation$"))
    application.add_handler(CallbackQueryHandler(on_EnduranceTest, pattern=r"^EnduranceTest$"))
    application.add_handler(CallbackQueryHandler(on_compleateForm, pattern=r"^compleateForm$"))
    application.add_handler(CallbackQueryHandler(on_compleateStats, pattern=r"^compleateStats$"))
    application.add_handler(CallbackQueryHandler(on_compleateStatsCont, pattern=r"^compleateStatsCont$"))

    # Focus control mini-game
    application.add_handler(CallbackQueryHandler(on_focusControl, pattern=r"^focusControl$"))
    application.add_handler(CallbackQueryHandler(on_focus_action, pattern=r"^fc_(calm|focus|release|embrace)$"))

    # Arena
    application.add_handler(CallbackQueryHandler(on_wolf, pattern=r"^wolf$"))
    application.add_handler(CallbackQueryHandler(on_ornate, pattern=r"^ornate$"))
    application.add_handler(CallbackQueryHandler(on_garments, pattern=r"^garments$"))
    application.add_handler(CallbackQueryHandler(on_thatAura, pattern=r"^thatAura$"))
    application.add_handler(CallbackQueryHandler(on_strikeHim, pattern=r"^strikeHim$"))
    application.add_handler(CallbackQueryHandler(on_attackThem, pattern=r"^attackThem$"))
    application.add_handler(CallbackQueryHandler(on_action_symbol, pattern=r"^action_(tri|sq|cir|x)_(left|right|feint|hit)_(sl1|sl2|any)_(\d+)$"))

    # demnext chain
    application.add_handler(CallbackQueryHandler(on_demnext_2, pattern=r"^demnext_2$"))
    application.add_handler(CallbackQueryHandler(on_demnext_3, pattern=r"^demnext_3$"))
    application.add_handler(CallbackQueryHandler(on_demnext_4, pattern=r"^demnext_4$"))
    application.add_handler(CallbackQueryHandler(on_demnext_5, pattern=r"^demnext_5$"))
    application.add_handler(CallbackQueryHandler(on_demnext_16, pattern=r"^demnext_16$"))
    application.add_handler(CallbackQueryHandler(on_demnext_17, pattern=r"^demnext_17$"))
    application.add_handler(CallbackQueryHandler(on_demnext_18, pattern=r"^demnext_18$"))
    application.add_handler(CallbackQueryHandler(on_demnext_40, pattern=r"^demnext_40$"))
    application.add_handler(CallbackQueryHandler(on_demnext_41, pattern=r"^demnext_41$"))
    application.add_handler(CallbackQueryHandler(on_demnext_42, pattern=r"^demnext_42$"))

    # Puzzle
    application.add_handler(CallbackQueryHandler(on_puzzle_pick, pattern=r"^puzzle_(birth|journey|sacrifice|rebirth)$"))
    application.add_handler(CallbackQueryHandler(on_puzzle_reset, pattern=r"^puzzle_reset$"))

    # Armory hook
    application.add_handler(CallbackQueryHandler(on_armory, pattern=r"^armory$"))
