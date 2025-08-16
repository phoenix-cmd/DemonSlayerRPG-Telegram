# bot.py
import os
import asyncio
import random
import re
from typing import Dict, Any

from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    InputMediaPhoto,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# ========== CONFIG ==========
BOT_TOKEN = os.getenv("BOT_TOKEN") or "PUT_YOUR_TOKEN"
# Add real admin IDs here
SUDO = {123456789}

# ========== STATE (in-memory; replace with DB later) ==========
database: Dict[int, Dict[str, Any]] = {}
temp_dict: Dict[int, Dict[str, Any]] = {}      # thief/demon simple battles
count_dict: Dict[int, Dict[str, Any]] = {}
aazaList: list[int] = []
testDict: Dict[int, Dict[str, int]] = {}
focusDict: Dict[int, Dict[str, int]] = {}
focusList: list[int] = []
attactDict: Dict[int, Dict[str, Any]] = {}
ongoing_puzzles: Dict[int, list[str]] = {}
damage_taken: list[int] = []

# ========== UTILS ==========
def is_private(update: Update) -> bool:
    chat = update.effective_chat
    return bool(chat and chat.type == "private")

def hp_bar(cur: int, mx: int) -> str:
    mx = max(mx, 1)
    p = max(0.0, min(1.0, cur / mx))
    filled = int(round(p * 10))
    return "▰" * filled + "▱" * (10 - filled)

def kb(rows):
    return InlineKeyboardMarkup([[InlineKeyboardButton(text, callback_data=data) for text, data in row] for row in rows])

# ========== HANDLERS ==========
START_VIDEO = "https://files.catbox.moe/9f9bvs.mp4"

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user:
        return
    if user.id not in SUDO:
        return
    if not is_private(update):
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
                f"System:\n\nThat's a good name {database[uid]['name']}\nLet's proceed for further steps - "
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
                    "User select your gender for compleating the regestration processes"
                ),
                reply_markup=kb([["BOY", "boy"], ["GIRL", "girl"]]),
            )
    except Exception:
        await update.message.reply_text("Please start the bot first")

# start_data
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
            "Let's have a quick regestration processes\n\n"
            "⨀ Enter your game name - "
        ),
    )
    database[uid]["enterName"] = True

# gender selection
async def on_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    data = q.data
    st = database.get(uid, {})
    if data == "boy":
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
        reply_markup=kb([["View Stats", "stats"], ["BACK", "gen"]]),
        disable_web_page_preview=True,
    )

async def on_gen_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await asyncio.sleep(1)
    await q.edit_message_text(
        text=(
            "System[:](https://files.catbox.moe/2gsyro.jpg)\n\n"
            "User select your gender for compleating the regestration processes"
        ),
        reply_markup=kb([["BOY", "boy"], ["GIRL", "girl"]]),
        disable_web_page_preview=True,
    )

async def on_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    st = database.get(uid, {})
    markup = kb([["BACK", "bck"], ["CONTINUE", "aage"]])
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
    if st.get("gender") == "boy":
        txt = "You have selected your journey as a boy[.](https://files.catbox.moe/smlywt.jpg)\n"
    else:
        txt = "You have selected your journey as a girl[.](https://files.catbox.moe/o90ydf.jpg)\n"
    await asyncio.sleep(1)
    await q.edit_message_text(
        txt,
        reply_markup=kb([["View Stats", "stats"], ["BACK", "gen"]]),
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
        caption="<blockquote>Chapter 1: DESTINY BEGINS WITH DEATH</blockquote>",
        reply_markup=kb([["BEGIN", "begin"]]),
    )

# Chapter 1, Scene 1
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
            "<blockquote>Narration</blockquote>"
            "<b>The rich aroma of coffee fill the air. Sunlight streams through the windows, casting a warm glow. "
            "Outside, the city hums with life, but in here-it's peceful.</b>\n\n"
            "<b>The protagonist leans back, sipping their drink. Across from them, Renji stirs his coffee, a faint smile playing on his lips. "
            "For now, outside doens't matter</b>"
        ),
        reply_markup=kb([["NEXT", "next"]]),
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
            "<blockquote>Renji</blockquote>\n\n"
            "<b>\"You always get that look when we're here. What is it about this place that gets you so sentimental\"</b>\n\n"
            "<blockquote>CHOOSE YOUR RESPONCE</blockquote>\n"
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
            "<blockquote>Renji</blockquote>\n"
            "\"<b>You know, that’s kinda nice. We always focus on big dreams and what’s next, but maybe moments like this matter just as much.</b>\"\n\n"
            "<blockquote>Name</blockquote>\n"
            "\"<b>See? You’re getting sentimental too.</b>\"\n\n"
            "<blockquote>Renji</blockquote>\n"
            "\"<b>Yeah, yeah, don’t get used to it.</b>\""
        )
    elif data == "c1r2":
        photo = "https://files.catbox.moe/fdkkz2.jpg"
        cap = (
            "<blockquote>Renji</blockquote>\n"
            "\"<b>Well, at least one of those is true. I’ll let you decide which one.</b>\"\n\n"
            "<blockquote>Name</blockquote>\n"
            "\"<b>Hmm… tough choice.</b>\"\n\n"
            "<blockquote>Renji</blockquote>\n"
            "\"<b>If you say anything other than me, I’m walking out.</b>\"\n\n"
            "<blockquote>Name</blockquote>\n"
            "\"<b>Alright, alright. You win this time.</b>\""
        )
    else:
        photo = "https://files.catbox.moe/wx9zo3.jpg"
        cap = (
            "<blockquote>Renji</blockquote>\n"
            "\"<b>Weird is one way to put it. I was thinking more along the lines of ‘hopeless romantic stuck in a coffee commercial.’</b>\"\n\n"
            "<blockquote>Name</blockquote>\n"
            "\"<b>Hey, if my life was a commercial, at least I’d get free coffee.</b>\"\n\n"
        )
    await context.bot.send_photo(q.message.chat.id, photo=photo, caption=cap, reply_markup=kb([["CONTINUE", "continue"]]))

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
            ">Emi\n"
            "\"<b>You two again? At this point café should just give you a VIP pass.</b>\"\n\n"
            ">CHOOSE YOUR RESPONCE\n"
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
            ">Emi\n"
            "\"<b>And I was right, wasn’t I?</b>\"\n\n"
            ">Name\n"
            "\"<b>You were. This might actually be the best thing I’ve ever tasted.</b>\"\n\n"
            ">Emi\n"
            "\"<b>Told you. I should start charging for my food recommendations.</b>\"\n\n"
            ">Renji\n"
            "\"Nah, you'd just make us all broke.</b>\"\n\n"
        )
    elif data == "c1r2c2":
        photo = "https://files.catbox.moe/16hf53.jpg"
        cap = (
            ">Emi\n"
            "\"<b>Great, now I have to start dusting you guys off before my shift starts.</b>\"\n\n"
            ">Name\n"
            "\"<b>Hey, we’re classy furniture. Maybe a fancy leather couch or something.</b>\"\n\n"
            ">Emi\n"
            "\"<b>Nah, more like an old, worn-out beanbag chair.</b>\"\n\n"
            ">Renji\n"
            "\"<b>Wow. That’s the rudest thing anyone has ever said to me.</b>\"\n\n"
            ">Emi\n"
            "\"<b>And yet, you’ll still be here tomorrow.</b>\""
        )
    else:
        photo = "https://files.catbox.moe/joz0w9.jpg"
        cap = (
            ">Renji\n"
            "\"<b>It’s true. This coffee owns my soul now.</b>\"\n\n"
            ">Emi\n"
            "\"<b>I knew you were too weak to resist.</b>\"\n\n"
            ">Renji\n"
            "\"<b>Hey, I have no regrets. If this is how I go out, at least I’ll be caffeinated.</b>\"\n\n"
            ">Name\n"
            "\"<b>Rest in peace, buddy. We’ll put a cup of coffee on your grave.</b>\"\n\n"
            ">Emi\n"
            "\"<b>Make it a double shot. He’d want it that way.</b>\"\n\n"
        )
    await context.bot.send_photo(q.message.chat.id, photo=photo, caption=cap, reply_markup=kb([["CONTINUE", "cont"]]))

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
            ">Narration\n\n"
            "<b>The sky glows with shades of orange and pink. The protagonist leans back, a rare sense of peace settling in.</b>\n\n"
            ">Name\n"
            "\"<b>You know… I don’t need anything more than this. Just good coffee, good food, and good friends.</b>\"\n\n"
            ">Renji\n"
            "<b>\"Careful, you're tempting fate. Say something like that, and the universe might just decide to mess with you.</b>\"\n\n"
            "<b>End Of Scene 1</b>"
        ),
        reply_markup=kb([["Move To Scene 2 ⇨", "s2"]]),
    )

# Chapter 1, Scene 2
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
        reply_markup=kb([["NEXT ⇾", "s2story"]]),
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
            ">Renji\n"
            "\"<b>Man, that was a good way to end the day. Too bad we have class tomorrow.</b>\"\n\n"
            ">Protagonist\n"
            "\"<b>Assuming you even show up.</b>\"\n\n"
            ">Renji\n"
            "\"<b>Hey, I have a 75% attendance rate. That’s basically an A for effort.</b>\""
        ),
        reply_markup=kb([["NEXT ⇾", "nexts2o"]]),
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
            ">????\n<b>\"Got a minute?\"</b>\n\n"
            ">CHOOSE YOUR RESPONSE\n"
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
            ">Hooded Man\n<b>\"Yeah? Well, so am I. Hand over your wallets, and we’ll all be on our way.\"</b>\n\n"
            ">Renji\n<b>\"Crap… mugger. What do we do?\"</b>\n\n"
            ">CHOOSE YOUR RESPONSE\n"
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
            ">Hooded Man\n<b>\"Wrong answer.\"</b>\n\n"
            "<i>Without warning, he pulls out a knife, the blade glinting under the streetlight.</i>\n\n"
            ">Renji\n<b>\"Shit—he’s serious!\"</b>\n\n"
            ">CHOOSE YOUR RESPONSE\n"
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
            ">Hooded Man\n<b>\"Smart kid. Maybe you can make this easy.\"</b>\n\n"
            "<i>He pulls out a knife, but doesn’t attack—yet.</i>\n\n"
            ">Hooded Man\n<b>\"Give me your stuff, and we all walk away happy. Say no, and I promise you won’t like what happens next.\"</b>\n\n"
            ">Renji\n<b>\"Dude, this guy is sketchy as hell…\"</b>\n\n"
            ">CHOOSE YOUR RESPONSE\n"
            "<pre>Choice 1: Try To Talk Him Down\n"
            "Choice 2: Give Him Fake Wallet And Hopes He Buys It\n"
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

    # Route outcomes (thief fight or alternate branches)
    if outcome == "GiveMoney":
        await context.bot.send_photo(
            q.message.chat.id,
            photo="https://files.catbox.moe/v5zxwp.jpg",
            caption=(
                ">Protagonist\n<b>\"Here. Just take it and go.\"</b>\n\n"
                ">Hooded Man\n<b>\"Smart choice. See? No one gets hurt when you cooperate.\"</b>\n\n"
                "<i>He pockets the cash...</i>"
            ),
            reply_markup=kb([["Next", "giveMoneyNext"]]),
        )
    elif outcome == "Run":
        pic = "https://files.catbox.moe/xv83wt.jpg" if st.get("gender") == "boy" else "https://files.catbox.moe/hznwtj.jpg"
        await context.bot.send_photo(
            q.message.chat.id,
            photo=pic,
            caption=(">Protagonist\n<b>\"Run. Now!\"</b>\n\n<i>They bolt down the street...</i>"),
            reply_markup=kb([["Run", "runAway"]]),
        )
    elif outcome == "Stand":
        pic = "https://files.catbox.moe/ibzye5.jpg" if st.get("gender") == "boy" else "https://files.catbox.moe/hytodn.jpg"
        await context.bot.send_photo(
            q.message.chat.id,
            photo=pic,
            caption=(">Name\n<b>Let's fight this out Renji </b>\n\n>Renji\n<b>Yeah let's teach him a lesson</b>\n\n<i>Fight Begins</i>"),
            reply_markup=kb([["F I G H T", "theifFight"]]),
        )
    else:
        # Fight/Distract/Esclate/Talk/Fake/Attack -> send to thief fight
        await context.bot.send_photo(
            q.message.chat.id,
            photo="https://files.catbox.moe/j4djo3.jpg",
            caption="<i>Escalation leads to combat...</i>",
            reply_markup=kb([["FIGHT HIM", "theifFight"]]),
        )

# Alternate branches (stubs to wire full text later)
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
            ">Hooded Man\n<b>\"Let’s hope we don’t run into each other again.\"</b>\n\n"
            "<i>He disappears into the alley.</i>"
        ),
        reply_markup=kb([["Next", "next1"]]),
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
            ">Renji\n<b>“Well, that was pathetic.”</b>\n\n"
            ">Name\n<b>“Yeah? What did you want me to do? Get stabbed?”</b>\n\n"
            "Renji stops walking. There’s something… off."
        ),
        reply_markup=kb([["What Happned Renji ??", "whatHappned"]]),
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
            ">Renji\n<b>\"Holy crap… we actually made it.\"</b>\n\n"
            ">Name\n<b>\"Yeah… but let’s not push our luck. Come on, let’s get home.\"</b>\n\n"
            "<i>The tension lingers, but they’re safe—for now.</i>"
        ),
        reply_markup=kb([["Let's Get Going", "goToHome"]]),
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
            ">Renji\n<b>“But I can’t let you leave, you know?”</b>\n\n"
            "<i>Before the protagonist can react, Renji stabs them.</i>"
        ),
        reply_markup=kb([["Let's Get Going", "renjiKilling2"]]),
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
            ">Renji\n<b>“Maybe that would’ve been better.”</b>\n\n"
            ">Name\n<b>“What?”</b>\n\n"
            "<i>A flash of silver.</i>"
        ),
        reply_markup=kb([["Stop It", "renjiKilling"]]),
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
            "<i>Renji plunges a knife straight into their stomach.</i>\n\n"
            ">Renji\n<b>“Nothing personal.”</b>"
        ),
        reply_markup=kb([["CONTINUE", "deathScene"]]),
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
            ">Renji\n<b>“You’ll understand soon enough… This world isn’t real. And you don’t belong here.”</b>"
        ),
        reply_markup=kb([["CONTINUE", "deathScene"]]),
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
            ">Narration\n"
            "<b>The cold pavement presses against the protagonist’s cheek... Then—darkness.</b>"
        ),
        reply_markup=kb([["CONTINUE", "blueFlames"]]),
    )

# ========== THIEF FIGHT ==========
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
            "<b>Theif :</b>\n"
            f"<blockquote>{hp_bar(bd['theif_health'], bd['theif_max_health'])}</blockquote>\n\n"
            "<b>Name :</b>\n"
            f"<blockquote>{hp_bar(bd['user_health'], bd['user_max_health'])}</blockquote>\n\n"
        ),
        reply_markup=kb([["P U N C H", "punchTheif"]]),
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
        dec = f"Theif has dodged your attack.\nAnd delt you {thef_dmg} damage"
    else:
        thef_dmg = random.randint(30, 50)
        user_dmg = random.randint(20, 30)
        bd["user_health"] -= thef_dmg
        bd["theif_health"] -= user_dmg
        dec = f"Theif has delt you {thef_dmg} damage.\nYou have delt {user_dmg} damage to theif"

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
                "<b>Punches weren't enough against the thief's blade\n"
                "You couldn't survive this tragedy\n"
                "This calamity took you in an instant, sendig you to an eternal sleep...</b>"
            ),
            reply_markup=kb([["CONTINUE", "userLost"]]),
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
                "You have won against the theif\n"
                "But it looks like you have preety badly injured loosing conciousness leading your way to death.."
            ),
            reply_markup=kb([["CONTINUE", "userLost"]]),
        )
        return

    msg = await q.edit_message_text("Please wait the attacks are in progress ...")
    await asyncio.sleep(1)
    await msg.edit_text(
        text=(
            "<b>Battle Begins</b>\n\n"
            "<b>Thif :</b>\n"
            f"<blockquote>{hp_bar(bd['theif_health'], bd['theif_max_health'])}</blockquote>\n\n"
            "<b>Name :</b>\n"
            f"<blockquote>{hp_bar(bd['user_health'], bd['user_max_health'])}</blockquote>\n\n"
            f"<pre>Logs\n{dec}</pre>"
        ),
        reply_markup=kb([["P U N C H", "punchTheif"]]),
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
            ">Narration\n"
            "<b>...You’re glad Renji is safe—yet sorrow clings to you...</b>"
        )
    else:
        cap = (
            ">Narration\n"
            "<b>...Renji stands nearby, unmoving. The night swallows everything. Then—darkness.</b>"
        )
    await context.bot.send_photo(q.message.chat.id, photo=pic, caption=cap, reply_markup=kb([["CONTINUE", "blueFlames"]]))

# Placeholder: blueFlames continues the interlude → chapter 2 (to be ported next)
async def on_blueFlames(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await q.edit_message_text("Blue flames interlude begins... (to be continued)")

# ========== APP ==========
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start_cmd))

    # Name intake in private
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE & filters.TEXT & ~filters.COMMAND, get_name_text))

    # Core callbacks
    app.add_handler(CallbackQueryHandler(on_start_data, pattern=r"^start_data$"))

    app.add_handler(CallbackQueryHandler(on_gender, pattern=r"^(boy|girl)$"))
    app.add_handler(CallbackQueryHandler(on_gen_back, pattern=r"^gen$"))
    app.add_handler(CallbackQueryHandler(on_stats, pattern=r"^stats$"))
    app.add_handler(CallbackQueryHandler(on_stats_back, pattern=r"^bck$"))
    app.add_handler(CallbackQueryHandler(on_stats_continue, pattern=r"^aage$"))

    app.add_handler(CallbackQueryHandler(on_begin, pattern=r"^begin$"))
    app.add_handler(CallbackQueryHandler(on_next, pattern=r"^next$"))
    app.add_handler(CallbackQueryHandler(on_choice_c1, pattern=r"^(c1r1|c1r2|c1r3)$"))
    app.add_handler(CallbackQueryHandler(on_continue, pattern=r"^continue$"))
    app.add_handler(CallbackQueryHandler(on_choice_c2, pattern=r"^(c1r1c2|c1r2c2|c1r3c2)$"))
    app.add_handler(CallbackQueryHandler(on_choice_c2_res, pattern=r"^cont$"))

    app.add_handler(CallbackQueryHandler(on_s2, pattern=r"^s2$"))
    app.add_handler(CallbackQueryHandler(on_s2story, pattern=r"^s2story$"))
    app.add_handler(CallbackQueryHandler(on_nexts2o, pattern=r"^nexts2o$"))
    app.add_handler(CallbackQueryHandler(on_s2_choices, pattern=r"^(c1s2r1|c1s2r2|c1s2r3)$"))
    app.add_handler(CallbackQueryHandler(on_s2_outcome, pattern=r"^(c1s2o)_(\w+)$"))

    # Alt branches (GiveMoney/Run → betrayal path)
    app.add_handler(CallbackQueryHandler(on_giveMoneyNext, pattern=r"^giveMoneyNext$"))
    app.add_handler(CallbackQueryHandler(on_next1, pattern=r"^next1$"))
    app.add_handler(CallbackQueryHandler(on_whatHappned, pattern=r"^whatHappned$"))
    app.add_handler(CallbackQueryHandler(on_renjiKilling, pattern=r"^renjiKilling$"))
    app.add_handler(CallbackQueryHandler(on_runAway, pattern=r"^runAway$"))
    app.add_handler(CallbackQueryHandler(on_goToHome, pattern=r"^goToHome$"))
    app.add_handler(CallbackQueryHandler(on_renjiKilling2, pattern=r"^renjiKilling2$"))
    app.add_handler(CallbackQueryHandler(on_deathScene, pattern=r"^deathScene$"))

    # Thief battle
    app.add_handler(CallbackQueryHandler(on_theifFight, pattern=r"^theifFight$"))
    app.add_handler(CallbackQueryHandler(on_punchTheif, pattern=r"^punchTheif$"))
    app.add_handler(CallbackQueryHandler(on_userLost, pattern=r"^userLost$"))

    # Interlude (stub)
    app.add_handler(CallbackQueryHandler(on_blueFlames, pattern=r"^blueFlames$"))

    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
