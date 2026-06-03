from pyrogram import Client, filters
import requests
import platform
import socket
import time

OWNER_ID = 988757303  # حط آيدي المطور

START_TIME = time.time()

@Client.on_message(filters.command("test"))
async def test_cmd(client, message):

    if message.from_user.id != OWNER_ID:
        return

    uptime = int(time.time() - START_TIME)

    try:
        data = requests.get(
            "https://ipinfo.io/json",
            timeout=10
        ).json()

        txt = f"""
✅ Bot Online

🌐 IP: {data.get('ip')}
🏙 City: {data.get('city')}
📍 Region: {data.get('region')}
🌎 Country: {data.get('country')}
🏢 ISP: {data.get('org')}

💻 Host: {socket.gethostname()}
🖥 System: {platform.system()}
📦 Release: {platform.release()}

⏱ Uptime: {uptime} sec
"""

    except Exception as e:
        txt = f"❌ Error:\n{e}"

    await message.reply_text(txt)
