from pyrogram.errors import UserNotParticipant
import json

with open('config.json', 'r') as f:
    config = json.load(f)

CHANNEL_USER = config['bot']['channel_user']
OWNER_ID = config['bot']['owner_id']

async def is_subscribed(client, user_id):
    if user_id == OWNER_ID:
        return True
    try:
        await client.get_chat_member(CHANNEL_USER, user_id)
        return True
    except UserNotParticipant:
        return False
    except Exception:
        return True

async def send_sub_msg(client, message):
    from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Subscribe Here to Continue", url=f"https://t.me/{CHANNEL_USER}")]
    ])
    await message.reply("<b>Sorry dear, you must subscribe to the channel to use the bot.</b>", reply_markup=keyboard)