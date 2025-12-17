import sqlite3
import json
import os
import tempfile
import time
import re
import threading
from urllib.parse import urlparse, urlencode
from datetime import datetime

import requests
import telebot
from telebot import types

# ==================== CONFIGURATION ====================
BOT_TOKEN = "992348406:AAHD77Fah3y5D73o3x3cohG_fNxZGkRFRII"
DB_FILE = 'users.db'
CHANNEL_USERNAME = "@day3_00"
CHANNEL_LINK = f"https://t.me/{CHANNEL_USERNAME[1:]}"

# Initialize bot
bot = telebot.TeleBot(BOT_TOKEN, parse_mode='HTML')

# User language storage (in-memory, you can save to DB if needed)
user_languages = {}

# ==================== TEXT MESSAGES ====================
MESSAGES = {
    'en': {
        'welcome': "Welcome to Video Downloader Bot! Please select your language:",
        'choose_lang': "Choose your preferred language:",
        'join_channel': "📢 Please join our channel to use this bot:\n{channel}\n\nAfter joining, click the button below.",
        'joined_check': "✅ I've checked - you've joined the channel!",
        'not_joined': "❌ You haven't joined the channel yet. Please join first.",
        'welcome_after_join': "🎉 Welcome to Video Downloader Bot!\n\n📥 Just send me any video URL and I'll download it for you.\n\n✅ Supported: YouTube, TikTok, Instagram, Facebook, Twitter/X\n\n⚠️ Max file size: 50MB",
        'send_url': "📥 Please send me a video URL to download.",
        'invalid_url': "❌ Please send a valid video URL.\n\nSupported: YouTube, TikTok, Instagram, Facebook, Twitter/X",
        'processing': "⏳ Processing your request...",
        'downloading': "📥 Downloading video... Please wait.",
        'converting': "⚙️ Converting video...",
        'uploading': "📤 Uploading to Telegram...",
        'success': "✅ Video downloaded successfully!\n\nSend another URL to download more.",
        'file_too_large': "❌ Video is too large. Telegram limit is 50MB.\nPlease try with a shorter video.",
        'download_failed': "❌ Download failed. Please try again.",
        'error_occurred': "❌ An error occurred. Please try again later.",
        'try_again': "🔄 Trying again...",
        'max_retries': "❌ Failed after multiple attempts. Please try a different URL.",
        'status': "🤖 Bot Status\n\n✅ Online\n📊 Ready to download\n⚡ Fast service",
        'help': "📖 Help Guide\n\n1. Send any video URL\n2. Wait for download\n3. Receive video\n\nSupported sites: YouTube, TikTok, Instagram, Facebook, Twitter/X\n\n⚠️ Note: Max file size 50MB",
        'checking_membership': "🔍 Checking channel membership...",
        'channel_required': "📢 Join required channel to use this bot."
    },
    'ar': {
        'welcome': "مرحبًا بكم في بوت تحميل الفيديوهات! الرجاء اختيار لغتك:",
        'choose_lang': "اختر لغتك المفضلة:",
        'join_channel': "📢 الرجاء الانضمام إلى قناتنا لاستخدام هذا البوت:\n{channel}\n\nبعد الانضمام، انقر على الزر أدناه.",
        'joined_check': "✅ لقد تحققت - لقد انضممت إلى القناة!",
        'not_joined': "❌ لم تنضم إلى القناة بعد. الرجاء الانضمام أولاً.",
        'welcome_after_join': "🎉 مرحبًا بكم في بوت تحميل الفيديوهات!\n\n📥 فقط أرسل لي رابط أي فيديو وسأقوم بتحميله لك.\n\n✅ المدعوم: يوتيوب، تيك توك، إنستجرام، فيسبوك، تويتر/اكس\n\n⚠️ الحد الأقصى لحجم الملف: 50 ميجابايت",
        'send_url': "📥 الرجاء إرسال رابط الفيديو للتحميل.",
        'invalid_url': "❌ الرجاء إرسال رابط فيديو صالح.\n\nالمدعوم: يوتيوب، تيك توك، إنستجرام، فيسبوك، تويتر/اكس",
        'processing': "⏳ جاري معالجة طلبك...",
        'downloading': "📥 جاري تحميل الفيديو... الرجاء الانتظار.",
        'converting': "⚙️ جاري تحويل الفيديو...",
        'uploading': "📤 جاري الرفع إلى تليجرام...",
        'success': "✅ تم تحميل الفيديو بنجاح!\n\nأرسل رابط آخر لتحميل المزيد.",
        'file_too_large': "❌ الفيديو كبير جدًا. الحد الأقصى في تليجرام هو 50 ميجابايت.\nالرجاء المحاولة مع فيديو أقصر.",
        'download_failed': "❌ فشل التحميل. الرجاء المحاولة مرة أخرى.",
        'error_occurred': "❌ حدث خطأ. الرجاء المحاولة مرة أخرى لاحقًا.",
        'try_again': "🔄 جاري المحاولة مرة أخرى...",
        'max_retries': "❌ فشل بعد عدة محاولات. الرجاء تجربة رابط مختلف.",
        'status': "🤖 حالة البوت\n\n✅ متصل\n📊 جاهز للتحميل\n⚡ خدمة سريعة",
        'help': "📖 دليل المساعدة\n\n1. أرسل أي رابط فيديو\n2. انتظر التحميل\n3. استلم الفيديو\n\nالمواقع المدعومة: يوتيوب، تيك توك، إنستجرام، فيسبوك، تويتر/اكس\n\n⚠️ ملاحظة: الحد الأقصى لحجم الملف 50 ميجابايت",
        'checking_membership': "🔍 جاري التحقق من العضوية في القناة...",
        'channel_required': "📢 الانضمام إلى القناة المطلوبة لاستخدام هذا البوت."
    }
}

def get_message(user_id, key):
    """Get message in user's selected language"""
    lang = user_languages.get(user_id, 'en')
    return MESSAGES[lang][key]

# ==================== UTILITY FUNCTIONS ====================
def is_user_member(user_id):
    """Check if user is member of required channel"""
    try:
        chat_member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return chat_member.status in ['member', 'administrator', 'creator']
    except:
        return False

def is_video_url(url):
    """Check if URL is from supported video platforms"""
    try:
        url_parts = urlparse(url)
        host = url_parts.hostname.lower() if url_parts.hostname else ''
        
        video_domains = [
            'youtube.com', 'youtu.be', 
            'tiktok.com', 'vm.tiktok.com',
            'instagram.com', 'instagr.am',
            'facebook.com', 'fb.watch',
            'x.com', 'twitter.com'
        ]
        
        return any(domain in host for domain in video_domains)
    except:
        return False

def clean_caption(text, max_length=1024):
    """Clean and truncate video caption"""
    if not text:
        return "Video"
    
    # Remove HTML tags
    text = re.sub(r'<[^>]*>', '', text)
    # Remove special characters
    text = re.sub(r'[^\w\s#@.,!?-]', '', text)
    
    if len(text) > max_length:
        text = text[:max_length - 3] + '...'
    
    return text

# ==================== VIDEO DOWNLOAD FUNCTIONS ====================
def make_request_with_retry(url, method='GET', headers=None, data=None, max_retries=3):
    """Make HTTP request with retry logic"""
    headers = headers or {}
    
    for attempt in range(max_retries):
        try:
            if method.upper() == 'POST':
                response = requests.post(url, headers=headers, data=data, timeout=30)
            else:
                response = requests.get(url, headers=headers, timeout=30)
            
            response.raise_for_status()
            return response.text
            
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                raise Exception(f"Failed after {max_retries} attempts: {str(e)}")
            time.sleep(5)  # Wait 5 seconds before retry
            continue
    
    raise Exception("Max retries reached")

def get_video_info(video_url, max_retries=3):
    """Get video information with retry logic"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'en-US,en;q=0.9',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Referer': 'https://thevidsave.com/',
        'X-Requested-With': 'XMLHttpRequest',
        'Origin': 'https://thevidsave.com'
    }
    
    for attempt in range(max_retries):
        try:
            # Get homepage first
            make_request_with_retry('https://thevidsave.com/', 'GET', headers)
            
            # Get video data
            data = {
                'action': 'tvs_savenow_download',
                'url': video_url,
                'format': '1080'
            }
            
            response = make_request_with_retry(
                'https://thevidsave.com/wp-admin/admin-ajax.php',
                'POST',
                headers,
                urlencode(data)
            )
            
            json_data = json.loads(response)
            
            if not json_data or 'data' not in json_data or 'progress_url' not in json_data['data']:
                raise Exception("Invalid API response")
            
            # Get title
            title = "Video"
            title_data = {
                'action': 'download_video',
                'video_url': video_url,
                'nonce': ''
            }
            
            try:
                title_response = make_request_with_retry(
                    'https://thevidsave.com/wp-admin/admin-ajax.php',
                    'POST',
                    headers,
                    urlencode(title_data)
                )
                
                title_json = json.loads(title_response)
                if title_json and 'data' in title_json and 'title' in title_json['data']:
                    title = title_json['data']['title']
            except Exception:
                pass
            
            return {
                'title': title,
                'progress_url': json_data['data']['progress_url']
            }
            
        except Exception as e:
            if attempt == max_retries - 1:
                raise Exception(f"Failed to get video info: {str(e)}")
            time.sleep(5)
            continue
    
    raise Exception("Max retries reached for video info")

def get_download_url(progress_url, max_retries=5):
    """Get download URL with retry logic"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Referer': 'https://thevidsave.com/',
        'X-Requested-With': 'XMLHttpRequest'
    }
    
    data = {
        'action': 'tvs_savenow_progress',
        'progress_url': progress_url
    }
    
    for attempt in range(max_retries):
        try:
            response = make_request_with_retry(
                'https://thevidsave.com/wp-admin/admin-ajax.php',
                'POST',
                headers,
                urlencode(data)
            )
            
            json_data = json.loads(response)
            
            if (json_data and 'data' in json_data and 
                'download_url' in json_data['data'] and 
                json_data['data']['download_url']):
                return json_data['data']['download_url'].replace('\\', '')
            
            raise Exception("No download URL in response")
            
        except Exception as e:
            if attempt == max_retries - 1:
                raise Exception(f"Failed to get download URL: {str(e)}")
            time.sleep(5)
            continue
    
    raise Exception("Max retries reached for download URL")

def download_video(video_url, max_retries=3):
    """Download video with retry logic"""
    for attempt in range(max_retries):
        try:
            # Get video info
            info = get_video_info(video_url, max_retries=3)
            title = info['title']
            progress_url = info['progress_url']
            
            # Get download URL
            download_url = get_download_url(progress_url, max_retries=5)
            
            # Download video
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
            temp_file.close()
            
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get(download_url, headers=headers, stream=True, timeout=300)
            response.raise_for_status()
            
            with open(temp_file.name, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            # Check file
            if os.path.getsize(temp_file.name) == 0:
                os.unlink(temp_file.name)
                raise Exception("Downloaded file is empty")
            
            return {'title': title, 'path': temp_file.name}
            
        except Exception as e:
            if attempt == max_retries - 1:
                raise Exception(f"Video download failed: {str(e)}")
            
            # Clean up any temp file
            if 'temp_file' in locals() and os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
            
            time.sleep(5)
            continue
    
    raise Exception("Max retries reached for video download")

# ==================== BOT HANDLERS ====================
@bot.message_handler(commands=['start'])
def start_command(message):
    """Handle /start command"""
    user_id = message.from_user.id
    
    # Send language selection
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_english = types.InlineKeyboardButton("English 🇬🇧", callback_data="lang_en")
    btn_arabic = types.InlineKeyboardButton("العربية 🇮🇶", callback_data="lang_ar")
    markup.add(btn_english, btn_arabic)
    
    bot.send_message(
        message.chat.id,
        MESSAGES['en']['welcome'],
        reply_markup=markup
    )

@bot.message_handler(commands=['help'])
def help_command(message):
    """Handle /help command"""
    user_id = message.from_user.id
    msg = get_message(user_id, 'help')
    bot.send_message(message.chat.id, msg)

@bot.message_handler(commands=['status'])
def status_command(message):
    """Handle /status command"""
    user_id = message.from_user.id
    msg = get_message(user_id, 'status')
    bot.send_message(message.chat.id, msg)

@bot.callback_query_handler(func=lambda call: call.data.startswith('lang_'))
def language_selection(call):
    """Handle language selection"""
    user_id = call.from_user.id
    lang = call.data.split('_')[1]  # 'en' or 'ar'
    user_languages[user_id] = lang
    
    # Edit message to show join channel request
    markup = types.InlineKeyboardMarkup()
    channel_btn = types.InlineKeyboardButton(
        "Join Channel 📢",
        url=CHANNEL_LINK
    )
    check_btn = types.InlineKeyboardButton(
        "I've Joined ✅",
        callback_data="check_join"
    )
    markup.add(channel_btn)
    markup.add(check_btn)
    
    msg = get_message(user_id, 'join_channel').format(channel=CHANNEL_USERNAME)
    
    bot.edit_message_text(
        msg,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == 'check_join')
def check_join_channel(call):
    """Check if user joined channel"""
    user_id = call.from_user.id
    
    # Check membership
    if is_user_member(user_id):
        msg = get_message(user_id, 'joined_check')
        bot.answer_callback_query(call.id, msg, show_alert=False)
        
        # Send welcome message
        welcome_msg = get_message(user_id, 'welcome_after_join')
        send_msg = get_message(user_id, 'send_url')
        
        bot.edit_message_text(
            welcome_msg,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id
        )
        
        bot.send_message(call.message.chat.id, send_msg)
    else:
        msg = get_message(user_id, 'not_joined')
        bot.answer_callback_query(call.id, msg, show_alert=True)

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    """Handle all incoming messages"""
    user_id = message.from_user.id
    text = message.text.strip()
    
    # Check if user has selected language
    if user_id not in user_languages:
        start_command(message)
        return
    
    # Check if user is still member
    if not is_user_member(user_id):
        msg = get_message(user_id, 'channel_required')
        markup = types.InlineKeyboardMarkup()
        channel_btn = types.InlineKeyboardButton(
            "Join Channel 📢",
            url=CHANNEL_LINK
        )
        check_btn = types.InlineKeyboardButton(
            "Check Again 🔄",
            callback_data="check_join"
        )
        markup.add(channel_btn)
        markup.add(check_btn)
        
        bot.send_message(
            message.chat.id,
            msg,
            reply_markup=markup
        )
        return
    
    # Check if it's a URL
    if not is_video_url(text):
        msg = get_message(user_id, 'invalid_url')
        bot.send_message(message.chat.id, msg)
        return
    
    # Start download process in thread
    download_thread = threading.Thread(
        target=process_video_request,
        args=(message, text)
    )
    download_thread.start()

def process_video_request(message, video_url):
    """Process video download request"""
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    # Step 1: Processing message
    try:
        processing_msg = bot.send_message(
            chat_id,
            get_message(user_id, 'processing')
        )
        processing_msg_id = processing_msg.message_id
    except Exception as e:
        bot.send_message(chat_id, get_message(user_id, 'error_occurred'))
        return
    
    try:
        # Step 2: Downloading
        bot.edit_message_text(
            get_message(user_id, 'downloading'),
            chat_id=chat_id,
            message_id=processing_msg_id
        )
        bot.send_chat_action(chat_id, 'upload_video')
        
        # Download video with retry logic
        video_data = download_video(video_url, max_retries=3)
        
        # Step 3: Uploading
        bot.edit_message_text(
            get_message(user_id, 'uploading'),
            chat_id=chat_id,
            message_id=processing_msg_id
        )
        
        # Prepare caption
        clean_title = clean_caption(video_data['title'])
        caption = f"{clean_title}\n\nDownloaded via @altsavebot"
        
        # Send video
        try:
            with open(video_data['path'], 'rb') as video_file:
                bot.send_video(
                    chat_id,
                    video_file,
                    caption=caption,
                    supports_streaming=True,
                    timeout=300
                )
            
            # Delete processing message
            bot.delete_message(chat_id, processing_msg_id)
            
            # Send success message
            bot.send_message(
                chat_id,
                get_message(user_id, 'success')
            )
            
        except telebot.apihelper.ApiTelegramException as e:
            bot.delete_message(chat_id, processing_msg_id)
            if "file is too big" in str(e).lower():
                bot.send_message(
                    chat_id,
                    get_message(user_id, 'file_too_large')
                )
            else:
                bot.send_message(
                    chat_id,
                    get_message(user_id, 'download_failed')
                )
        
    except Exception as e:
        # Delete processing message
        try:
            bot.delete_message(chat_id, processing_msg_id)
        except:
            pass
        
        # Send error message
        error_msg = f"{get_message(user_id, 'download_failed')}\n\nError: {str(e)}"
        bot.send_message(chat_id, error_msg)
    
    finally:
        # Cleanup temporary file
        try:
            if 'video_data' in locals() and os.path.exists(video_data['path']):
                os.unlink(video_data['path'])
        except:
            pass

# ==================== MAIN EXECUTION ====================
def main():
    """Main function to run the bot"""
    print("=" * 50)
    print("Video Downloader Bot")
    print("=" * 50)
    print(f"Channel: {CHANNEL_USERNAME}")
    print("Bot is starting...")
    print("=" * 50)
    
    # Create requirements.txt
    requirements = """pyTelegramBotAPI==4.19.0
requests==2.31.0
"""
    
    if not os.path.exists('requirements.txt'):
        with open('requirements.txt', 'w') as f:
            f.write(requirements)
        print("requirements.txt created successfully!")
    
    print("To install dependencies: pip install -r requirements.txt")
    print("=" * 50)
    
    try:
        # Start polling
        bot.infinity_polling(timeout=30, long_polling_timeout=30)
    except KeyboardInterrupt:
        print("\nBot stopped by user.")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == '__main__':
    main()
