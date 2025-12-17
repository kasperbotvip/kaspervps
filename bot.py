import asyncio
import aiohttp
import telebot
from telebot.async_telebot import AsyncTeleBot
from telebot import types
import re
import tempfile
import os
import json

TOKEN = "992348406:AAEpUA34VTb4UVrXnKLhPcCOJD5PG-rWwIo"
CHANNEL_USERNAME = "@day3_00"
CHANNEL_LINK = f"https://t.me/{CHANNEL_USERNAME[1:]}"

bot = AsyncTeleBot(TOKEN)

class DownloadError(Exception):
    pass

async def check_channel_membership(user_id):
    try:
        chat_member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return chat_member.status in ['member', 'administrator', 'creator']
    except Exception:
        return False

async def post(session, url, data, headers):
    async with session.post(
        url,
        data=data,
        headers=headers,
        timeout=aiohttp.ClientTimeout(total=30),
        ssl=False
    ) as r:
        if r.status != 200:
            raise DownloadError(f"HTTP {r.status}")
        return await r.text()

async def get_nonce(session, headers):
    async with session.get(
        "https://thevidsave.com/",
        headers=headers,
        ssl=False
    ) as r:
        html_text = await r.text()

    match = re.search(r'"nonce":"([^"]+)"', html_text)
    return match.group(1) if match else ""

async def get_video_info(session, url, nonce, headers):
    title_data = {
        "action": "download_video",
        "video_url": url,
        "nonce": nonce
    }

    download_data = {
        "action": "tvs_savenow_download",
        "url": url,
        "format": "720"
    }

    for attempt in range(1, 6):
        try:
            title_resp = await post(
                session,
                "https://thevidsave.com/wp-admin/admin-ajax.php",
                title_data,
                headers
            )

            title_json = json.loads(title_resp)

            if not title_json.get("success"):
                raise Exception("title_failed")

            title = title_json["data"]["title"]

            download_resp = await post(
                session,
                "https://thevidsave.com/wp-admin/admin-ajax.php",
                download_data,
                headers
            )

            download_json = json.loads(download_resp)

            if not download_json.get("success"):
                raise Exception("download_failed")

            progress_url = download_json["data"]["progress_url"]
            return title, progress_url

        except Exception:
            if attempt == 5:
                raise DownloadError("Failed to get video info")
            await asyncio.sleep(2 * attempt)

async def get_download_url(session, progress_url, headers):
    data = {
        "action": "tvs_savenow_progress",
        "progress_url": progress_url
    }

    for _ in range(6):
        await asyncio.sleep(3)

        resp = await post(
            session,
            "https://thevidsave.com/wp-admin/admin-ajax.php",
            data,
            headers
        )

        js = json.loads(resp)

        if js.get("success") and js["data"].get("download_url"):
            return js["data"]["download_url"].replace("\\", "")

    raise DownloadError("Failed to get download URL")

async def download_video(url):
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": "https://thevidsave.com",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://thevidsave.com/"
    }

    async with aiohttp.ClientSession() as session:
        nonce = await get_nonce(session, headers)
        title, progress_url = await get_video_info(session, url, nonce, headers)
        download_url = await get_download_url(session, progress_url, headers)

        async with session.get(download_url, headers=headers, ssl=False) as r:
            if r.status != 200:
                raise DownloadError("Download failed")

            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as f:
                async for chunk in r.content.iter_chunked(65536):
                    f.write(chunk)
                return title, f.name

@bot.message_handler(commands=['start'])
async def start_cmd(message):
    user_id = message.from_user.id
    
    is_member = await check_channel_membership(user_id)
    
    if is_member:
        await bot.send_message(message.chat.id, "✅ Welcome! Send me any video link to download.")
    else:
        keyboard = types.InlineKeyboardMarkup()
        join_button = types.InlineKeyboardButton(
            text="📢 Join Channel", 
            url=CHANNEL_LINK
        )
        keyboard.add(join_button)
        
        await bot.send_message(
            message.chat.id, 
            "📢 Please join our channel first to use this bot.\n\nClick the button below to join:",
            reply_markup=keyboard
        )

@bot.message_handler(func=lambda message: True)
async def handle_message(message):
    url = message.text.strip()
    user_id = message.from_user.id
    
    if message.text.startswith('/'):
        return
    
    is_member = await check_channel_membership(user_id)
    
    if not is_member:
        keyboard = types.InlineKeyboardMarkup()
        join_button = types.InlineKeyboardButton(
            text="📢 Join Channel", 
            url=CHANNEL_LINK
        )
        keyboard.add(join_button)
        
        await bot.send_message(
            message.chat.id, 
            "❌ You need to join our channel first.\n\nClick the button below to join, then send your video link again.",
            reply_markup=keyboard
        )
        return
    
    if not (url.startswith("http://") or url.startswith("https://")):
        await bot.reply_to(message, "❌ Please send a valid video URL.")
        return
    
    wait_msg = await bot.reply_to(message, "⏳ Downloading your video...")
    
    try:
        title, path = await download_video(url)
        await bot.delete_message(message.chat.id, wait_msg.message_id)
        
        file_size = os.path.getsize(path)
        if file_size > 49 * 1024 * 1024:
            await bot.reply_to(message, f"⚠️ File is too large ({file_size/1024/1024:.1f}MB). Telegram limit is 50MB.")
            os.unlink(path)
            return
        
        bot_info = await bot.get_me()
        bot_username = bot_info.username
        
        with open(path, "rb") as video_file:
            await bot.send_video(
                message.chat.id,
                video_file,
                caption=f"✅ Downloaded via @{bot_username}"
            )
        
        os.unlink(path)
        
    except DownloadError as e:
        await bot.reply_to(message, f"❌ Download failed: {str(e)}")
    except Exception as e:
        await bot.reply_to(message, "❌ An error occurred. Please try again.")
        if 'path' in locals() and os.path.exists(path):
            os.unlink(path)

async def main():
    await bot.infinity_polling(timeout=60, request_timeout=60)

if __name__ == "__main__":
    asyncio.run(main())
