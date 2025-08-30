## ADDED AI FROM xbitcode api.

import requests
import json
import time
from datetime import datetime, timedelta
from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from pyrogram.enums import ParseMode
from pyrogram.errors import FloodWait
from AnonXMusic import app ## make sure you use your own repo module name 
from AnonXMusic.utils.database import get_model_settings
from config import BANNED_USERS
from config import YT_API_KEY as AI_KEY 
from config import YTPROXY_URL as AI_ENDPOINT
import random
import logging
import asyncio
import aiohttp
import io

# Set up logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

user_last_request = {}
RATE_LIMIT_SECONDS = 5  

AI_COMMANDS = ["ai", "gpt", "chatgpt", "gpt4", "gemini", "ami"]
USAGE_CMDS = ["api", "apikey", "usage"]

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

TTS_PROCESSING_MESSAGES = [
    "🎵 Generating your audio...",
    "🎤 Converting text to speech...",
    "🔊 Creating voice output...",
    "🎧 Processing your text...",
    "📣 Synthesizing speech...",
    "🎼 Composing audio...",
    "🔈 Building sound waves...",
    "🎶 Crafting your voice message...",
    "📢 Converting to audio...",
    "🎙️ Preparing voice output..."
]

IMAGE_PROCESSING_MESSAGES = [
    "🎨 Creating your image...",
    "🖼️ Generating artwork...",
    "🎭 Crafting visual masterpiece...",
    "🖌️ Painting with AI...",
    "📸 Capturing imagination...",
    "🎨 Designing your vision...",
    "🖼️ Building visual content...",
    "🎭 Composing digital art...",
    "🖌️ Rendering image...",
    "📸 Processing visual request..."
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

async def handle_flood_wait(func, *args, **kwargs):
    while True:
        try:
            return await func(*args, **kwargs)
        except FloodWait as e:
            await asyncio.sleep(e.value)

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
            
        # Get current AI model from database
        model_settings = await get_model_settings()
        ai_model = model_settings.get("ai", "GPT4")
            
        url = f"{AI_ENDPOINT}/ai/chat"
        headers = {
            "Content-Type": "application/json",
            "x-api-key": AI_KEY,
            "model": ai_model
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
        await handle_flood_wait(message.reply_text,
            f"⏱️ Please wait {RATE_LIMIT_SECONDS} seconds between AI requests.",
            quote=True
        )
        return
    
    if len(message.command) < 2:
        await handle_flood_wait(message.reply_text, random.choice(INSTANT_REPLIES), quote=True)
        return
    
    query = message.text.split(None, 1)[1].strip()
    
    if is_short_query(query):
        await handle_flood_wait(message.reply_text, random.choice(INSTANT_REPLIES), quote=True)
        return
    
    processing_msg = await handle_flood_wait(message.reply_text, random.choice(PROCESSING_MESSAGES), quote=True)
    
    try:
        success, response = await make_ai_request(query)
        
        if success:
            formatted_response = response[:4000]  
            if len(response) > 4000:
                formatted_response += "\n\n📝 *Response truncated due to length limit.*"
            
            await handle_flood_wait(processing_msg.edit_text, formatted_response, parse_mode=ParseMode.MARKDOWN)
        else:
            await handle_flood_wait(processing_msg.edit_text, response)
            
    except Exception as e:
        logger.error(f"Error in ai_chat: {e}")
        await handle_flood_wait(processing_msg.edit_text,
            "❌ An unexpected error occurred. Please try again later.",
            parse_mode=ParseMode.MARKDOWN
        )

@app.on_message(filters.command(USAGE_CMDS) & ~BANNED_USERS)
async def api_stats(client, message: Message):
    """Check AI API status and usage (Available to all users)"""
    start_time = datetime.now()
    
    try:
        if not AI_ENDPOINT or not AI_KEY:
            await handle_flood_wait(message.reply_text, "❌ Not using xBit API endpoint please contact @amigr8bot.")
            return
            
        status_msg = await handle_flood_wait(message.reply_text, "🔍 Checking API status...", quote=True)
        
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

**API KEY STATUS**
```
{json.dumps(data, indent=2)}
```
            """
        except json.JSONDecodeError:
            status_text = f"""
🔧 **AI API Status**

✅ **Status:** Unknown
⏱️ **Response Time:** {response_time:.2f}s
📡 **Endpoint:** `{AI_ENDPOINT}`

**Raw Response:**
```
{response.text[:500]}
```
            """
        
        await handle_flood_wait(status_msg.edit_text, status_text, parse_mode=ParseMode.MARKDOWN)
        
    except requests.exceptions.Timeout:
        await handle_flood_wait(status_msg.edit_text, "⏰ API request timed out.")
    except requests.exceptions.ConnectionError:
        await handle_flood_wait(status_msg.edit_text, "🌐 Connection error - API might be down.")
    except requests.exceptions.HTTPError as e:
        await handle_flood_wait(status_msg.edit_text, f"🚫 HTTP Error: {e.response.status_code}")
    except Exception as e:
        logger.error(f"Error in api_stats: {e}")
        await handle_flood_wait(status_msg.edit_text, f"❌ Unexpected error: {str(e)[:100]}")

@app.on_message(filters.command("tts") & ~BANNED_USERS)
async def tts_command(client, message: Message):
    """Handle TTS commands"""
    user_id = message.from_user.id
    if not check_rate_limit(user_id):
        await handle_flood_wait(message.reply_text,
            f"⏱️ Please wait {RATE_LIMIT_SECONDS} seconds between TTS requests.",
            quote=True,
            parse_mode=ParseMode.MARKDOWN
        )
        return

    if len(message.command) < 2:
        await handle_flood_wait(message.reply_text, "Please provide a text to convert to speech.", quote=True, parse_mode=ParseMode.MARKDOWN)
        return

    text = message.text.split(None, 1)[1].strip()
    processing_msg = await handle_flood_wait(message.reply_text, "🔄 Processing your request...", quote=True, parse_mode=ParseMode.MARKDOWN)

    task = asyncio.create_task(make_tts_request(text))

    # Loop updating message while waiting
    while not task.done():
        await asyncio.sleep(5)  # Wait 5 seconds
        if not task.done():
            await handle_flood_wait(processing_msg.edit_text, random.choice(TTS_PROCESSING_MESSAGES), parse_mode=ParseMode.MARKDOWN)

    # Get the result
    try:
        success, audio_bytes, model = task.result()
        if success:
            # Send the audio file
            audio_bytes_io = io.BytesIO(audio_bytes)
            audio_bytes_io.name = "tts_audio.mp3"
            await handle_flood_wait(message.reply_audio,
                audio=audio_bytes_io,
                title=f"{message.from_user.id}_{time.time()}",
                caption=f"🎤 **Model:** {model}\n📝 **Text:** {text[:100]}{'...' if len(text) > 100 else ''}",
                quote=True,
                parse_mode=ParseMode.MARKDOWN
            )
            await handle_flood_wait(processing_msg.delete)
        else:
            await handle_flood_wait(processing_msg.edit_text, audio_bytes, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        logger.error(f"Error in tts_command: {e}")
        await handle_flood_wait(processing_msg.edit_text, "❌ An unexpected error occurred. Please try again later.", parse_mode=ParseMode.MARKDOWN)

async def make_tts_request(text: str) -> tuple[bool, bytes | str, str]:
    """Make TTS API request with proper error handling"""
    try:
        if not AI_ENDPOINT or not AI_KEY:
            return False, "❌ TTS configuration is missing. Please contact administrator.", ""

        # Get current TTS model from database if not provided
        model_settings = await get_model_settings()
        model = model_settings.get("tts", "athena")

        url = f"{AI_ENDPOINT}/tts/generate"
        headers = {
            "Content-Type": "application/json",
            "x-api-key": AI_KEY,
            "model": model

        }

        body = {
            "text": text,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=body, timeout=aiohttp.ClientTimeout(total=60)) as response:
                response.raise_for_status()
                
                audio_bytes = await response.read()
                if audio_bytes:
                    return True, audio_bytes, model
                else:
                    return False, "❌ TTS generation failed. Empty audio response.", ""

    except asyncio.TimeoutError:
        return False, "⏰ TTS request timed out. Please try again.", ""
    except aiohttp.ClientConnectionError:
        return False, "🌐 Connection error. Please check your internet connection.", ""
    except aiohttp.ClientResponseError as e:
        if e.status == 400:
            return False, "❌ Invalid request. Please check your text length and try again.", ""
        elif e.status == 401:
            return False, "❌ Invalid API key. Please contact administrator.", ""
        elif e.status == 429:
            return False, "⏱️ Rate limit exceeded. Please wait a moment and try again.", ""
        else:
            return False, f"🚫 Server error: {e.status}. Please try again later.", ""
    except Exception as e:
        logger.error(f"Unexpected error in TTS request: {e}")
        return False, "❌ An unexpected error occurred. Please try again later.", ""

@app.on_message(filters.command("image") & ~BANNED_USERS)
async def image_command(client, message: Message):
    """Handle image generation commands"""
    user_id = message.from_user.id
    if not check_rate_limit(user_id):
        await handle_flood_wait(message.reply_text,
            f"⏱️ Please wait {RATE_LIMIT_SECONDS} seconds between image requests.",
            quote=True,
            parse_mode=ParseMode.MARKDOWN
        )
        return

    if len(message.command) < 2:
        await handle_flood_wait(message.reply_text, "Please provide a description for the image.", quote=True, parse_mode=ParseMode.MARKDOWN)
        return

    text = message.text.split(None, 1)[1].strip()
    processing_msg = await handle_flood_wait(message.reply_text, "🎨 Processing your image request...", quote=True, parse_mode=ParseMode.MARKDOWN)

    task = asyncio.create_task(make_image_request(text))

    # Loop updating message while waiting
    while not task.done():
        await asyncio.sleep(5)  # Wait 5 seconds
        if not task.done():
            await handle_flood_wait(processing_msg.edit_text, random.choice(IMAGE_PROCESSING_MESSAGES), parse_mode=ParseMode.MARKDOWN)

    # Get the result
    try:
        success, image_bytes = task.result()
        if success:
            # Send the image file
            image_bytes_io = io.BytesIO(image_bytes)
            image_bytes_io.name = "ai_generated_image.png"
            await handle_flood_wait(message.reply_photo,
                photo=image_bytes_io,
                caption=f"🎨 **AI Generated Image**\n📝 **Prompt:** {text[:200]}{'...' if len(text) > 200 else ''}",
                quote=True,
                parse_mode=ParseMode.MARKDOWN
            )
            await handle_flood_wait(processing_msg.delete)
        else:
            await handle_flood_wait(processing_msg.edit_text, image_bytes, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        logger.error(f"Error in image_command: {e}")
        await handle_flood_wait(processing_msg.edit_text, "❌ An unexpected error occurred. Please try again later.")

async def make_image_request(text: str) -> tuple[bool, bytes | str]:
    """Make image generation API request with proper error handling"""
    try:
        if not AI_ENDPOINT or not AI_KEY:
            return False, "❌ Image generation configuration is missing. Please contact administrator."
        
        model_settings = await get_model_settings()
        model = model_settings.get("image", "stable-diffusion")

        url = f"{AI_ENDPOINT}/image/generate"
        headers = {
            "Content-Type": "application/json",
            "x-api-key": AI_KEY,
            "model": model
        }

        body = {
            "prompt": text,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=body, timeout=aiohttp.ClientTimeout(total=120)) as response:
                response.raise_for_status()
                
                image_bytes = await response.read()
                if image_bytes:
                    return True, image_bytes
                else:
                    return False, "❌ Image generation failed. Empty image response."

    except asyncio.TimeoutError:
        return False, "⏰ Image generation timed out. Please try again."
    except aiohttp.ClientConnectionError:
        return False, "🌐 Connection error. Please check your internet connection."
    except aiohttp.ClientResponseError as e:
        if e.status == 400:
            return False, "❌ Invalid request. Please check your prompt and try again."
        elif e.status == 401:
            return False, "❌ Invalid API key. Please contact administrator."
        elif e.status == 429:
            return False, "⏱️ Rate limit exceeded. Please wait a moment and try again."
        else:
            return False, f"🚫 Server error: {e.status}. Please try again later."
    except Exception as e:
        logger.error(f"Unexpected error in image request: {e}")
        return False, "❌ An unexpected error occurred. Please try again later."