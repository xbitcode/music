## ADDED AI FROM xbitcode api.

import requests
import json
import time
from datetime import datetime, timedelta
from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from pyrogram.enums import ParseMode
from AnonXMusic import app ## make sure you use your own repo module name 
from AnonXMusic.misc import SUDOERS
from config import BANNED_USERS
from config import YT_API_KEY as AI_KEY 
from config import YTPROXY_URL as AI_ENDPOINT
import random
import logging

# Set up logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

user_last_request = {}
RATE_LIMIT_SECONDS = 5  

AI_COMMANDS = ["ai", "gpt", "chatgpt", "gpt4", "gemini", "ami"]

INSTANT_REPLIES = [
    "Hey there! How can I help you today?",
    "Hello! Need something?",
    "Hi! What's up?",
    "Hey! How's it going?",
    "Yo! How can I assist?",
    "Hola! How can I help?",
    "Sup! Need any info?",
    "Greetings! What can I do for you?",
    "Hiya! Ask me anything!",
    "Hey! Ready to chat!"
]

SHORT_QUERIES = {
    # English
    "hi", "hello", "ok", "hey", "yo", "hola", "sup", "hii", "hlo", "hyy", 
    "yes", "no", "hmm", "hmmm", "hru", "fine", "good", "nice", "cool", 
    "hbd", "gm", "gn", "bye", "thanks", "thank you", "welcome", "okay",
    
    # Hindi
    "namaste", "namaskar", "kaise ho", "kaisi ho", "thik hu", "thik hoon", 
    "accha", "acha", "shukriya", "dhanyavad", "haan", "nahi", "theek hai", 
    "kya haal hai", "bhai", "bhaiya", "didi", "thik",
    
    # Spanish
    "buenos dias", "buenas noches", "adios", "gracias", "vale", "si", 
    "que tal", "como estas", "bien", "mal",
    
    # French
    "salut", "bonjour", "bonsoir", "merci", "oui", "non", "ça va",
    
    # Other languages
    "ciao", "ola", "aloha", "wassup", "yo yo"
}

PROCESSING_MESSAGES = [
    "🤖 Thinking hard...",
    "💡 Cooking up a smart reply...",
    "⏳ Let me ask my AI brain...",
    "🔍 Searching the AI universe...",
    "🧠 Crunching some neural numbers...",
    "✨ Generating a clever response...",
    "📡 Contacting the AI mothership...",
    "🛠️ Building your answer...",
    "🚀 Launching my thoughts...",
    "🤔 Let me ponder that for a sec..."
]

ERROR_MESSAGES = [
    "🚫 Oops! Something went wrong with the AI service.",
    "⚠️ AI is taking a coffee break. Try again in a moment.",
    "🔧 Technical difficulties detected. Please retry.",
    "🤖 AI brain needs a restart. Give it another shot!",
    "📡 Connection to AI mothership lost. Retrying..."
]

def check_rate_limit(user_id: int) -> bool:
    """Check if user is within rate limit"""
    now = time.time()
    if user_id in user_last_request:
        if now - user_last_request[user_id] < RATE_LIMIT_SECONDS:
            return False
    user_last_request[user_id] = now
    return True

def clean_query(text: str) -> str:
    """Clean and normalize query text"""
    return text.strip().lower().rstrip('!?.')

def is_short_query(query: str) -> bool:
    """Check if query is too short or in short queries list"""
    clean = clean_query(query)
    return len(clean) <= 3 or clean in SHORT_QUERIES

async def make_ai_request(query: str) -> tuple[bool, str]:
    """Make AI API request with proper error handling"""
    try:
        if not AI_ENDPOINT or not AI_KEY:
            return False, "❌ AI configuration is missing. Please contact administrator."
            
        url = f"{AI_ENDPOINT}/ai"
        headers = {
            "Content-Type": "application/json",
            "x-api-key": AI_KEY
        }
        data = {"message": query}
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status() 
        
        result = response.json()
        ai_reply = result.get("response")
        
        if not ai_reply:
            return False, "❌ AI returned an empty response. Please try again."
            
        return True, ai_reply
        
    except requests.exceptions.Timeout:
        return False, "⏰ Request timed out. The AI is taking too long to respond."
    except requests.exceptions.ConnectionError:
        return False, "🌐 Connection error. Please check your internet connection."
    except requests.exceptions.HTTPError as e:
        return False, f"🚫 Server error: {e.response.status_code}. Please try again later."
    except json.JSONDecodeError:
        return False, "📄 Invalid response format from AI service."
    except Exception as e:
        logger.error(f"Unexpected error in AI request: {e}")
        return False, random.choice(ERROR_MESSAGES)

@app.on_message(filters.command(AI_COMMANDS) & ~BANNED_USERS)
async def ai_chat(client, message: Message):
    """Enhanced AI chat handler with better error handling and rate limiting"""
    user_id = message.from_user.id
    
    if not check_rate_limit(user_id):
        await message.reply_text(
            f"⏱️ Please wait {RATE_LIMIT_SECONDS} seconds between AI requests.",
            quote=True
        )
        return
    
    if len(message.command) < 2:
        return await message.reply_text(random.choice(INSTANT_REPLIES), quote=True)
    
    query = message.text.split(None, 1)[1].strip()
    
    if is_short_query(query):
        return await message.reply_text(random.choice(INSTANT_REPLIES), quote=True)
    
    processing_msg = await message.reply_text(random.choice(PROCESSING_MESSAGES), quote=True)
    
    try:
        success, response = await make_ai_request(query)
        
        if success:
            formatted_response = response[:4000]  
            if len(response) > 4000:
                formatted_response += "\n\n📝 *Response truncated due to length limit.*"
            
            await processing_msg.edit_text(formatted_response, parse_mode=ParseMode.MARKDOWN)
        else:
            await processing_msg.edit_text(response)
            
    except Exception as e:
        logger.error(f"Error in ai_chat: {e}")
        await processing_msg.edit_text(
            "❌ An unexpected error occurred. Please try again later.",
            parse_mode=ParseMode.MARKDOWN
        )



@app.on_message(filters.command(["api", "apikey", "usage"]) & SUDOERS)
async def api_stats(client, message: Message):
    """Check AI API status and usage (SUDO only)"""
    start_time = datetime.now()
    
    try:
        if not AI_ENDPOINT or not AI_KEY:
            await message.reply_text("❌ AI configuration is missing.")
            return
            
        status_msg = await message.reply_text("🔍 Checking API status...", quote=True)
        
        url = f"{AI_ENDPOINT}/status"
        headers = {'x-api-key': AI_KEY}
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        response_time = (datetime.now() - start_time).total_seconds()
        
        try:
            data = response.json()
            status_text = f"""
🔧 **AI API Status**

✅ **Status:** Online
⏱️ **Response Time:** {response_time:.2f}s
📡 **Endpoint:** `{AI_ENDPOINT}`
🔑 **API Key:** `{"*" * (len(AI_KEY)-8) + AI_KEY[-4:] if len(AI_KEY) > 8 else "****"}`

**Raw Response:**
```json
{json.dumps(data, indent=2)}
```
            """
        except json.JSONDecodeError:
            status_text = f"""
🔧 **AI API Status**

✅ **Status:** Online (Non-JSON Response)
⏱️ **Response Time:** {response_time:.2f}s
📡 **Endpoint:** `{AI_ENDPOINT}`

**Raw Response:**
```
{response.text[:500]}
```
            """
        
        await status_msg.edit_text(status_text, parse_mode=ParseMode.MARKDOWN)
        
    except requests.exceptions.Timeout:
        await status_msg.edit_text("⏰ API request timed out.")
    except requests.exceptions.ConnectionError:
        await status_msg.edit_text("🌐 Connection error - API might be down.")
    except requests.exceptions.HTTPError as e:
        await status_msg.edit_text(f"🚫 HTTP Error: {e.response.status_code}")
    except Exception as e:
        logger.error(f"Error in api_stats: {e}")
        await status_msg.edit_text(f"❌ Unexpected error: {str(e)[:100]}")
