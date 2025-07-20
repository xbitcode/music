## ADDED AI FROM xbitcode api.

import requests
import json
from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from pyrogram.enums import ParseMode
from AnonXMusic import app ## make sure you use your own repo module name 
from AnonXMusic.misc import SUDOERS
import os
import asyncio
import glob
from config import BANNED_USERS
from config import YT_API_KEY as AI_KEY 
from config import YTPROXY_URL as AI_ENDPOINT
import subprocess
import random
import logging

AI_COMMANDS = ["ai", "/ai", "ami", "/ami", "gpt", "/gpt", "chatgpt", "/gpt4", "gemini", "/gok"]

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
SHORT_QUERIES = [
    # English
    "hi", "hello", "ok", "hey", "yo", "hola", "sup", "hii", "hlo", "hyy", "yes", "no", "hmm", "hmmm", "hru", "fine", "good", "nice", "cool", "hbd", "gm", "gn", "bye", "thanks", "thank you", "welcome", "yo!", "ok!", "okay", "hru?", "hello!", "hi!", "hey!", "sup?", "yo?", "hlo!", "hii!", "hyy!", "hmm.", "hmmm.", "hmm!", "hmmm!", "ok.", "ok!", "okay!", "fine.", "fine!", "good.", "good!", "nice.", "nice!", "cool.", "cool!", "yes.", "yes!", "no.", "no!", "bye!", "bye.", "thanks!", "thanks.", "welcome!", "welcome.",

    # Hindi
    "namaste", "namaskar", "kaise ho", "kaisi ho", "thik hu", "thik hoon", "accha", "acha", "shukriya", "dhanyavad", "haan", "nahi", "theek hai", "kya haal hai", "bhai", "bhaiya", "didi", "bhaiya!", "didi!", "haan!", "nahi!", "shukriya!", "dhanyavad!", "accha!", "acha!", "thik!", "thik hai!", "kaise ho?", "kaisi ho?", "kya haal hai?",

    # Spanish using AI 
    "hola", "buenos dias", "buenas noches", "adios", "gracias", "vale", "si", "no", "que tal", "como estas", "bien", "mal", "hola!", "adios!", "gracias!", "vale!", "si!", "no!", "bien!", "mal!",

    # French using AI 
    "salut", "bonjour", "bonsoir", "merci", "oui", "non", "ça va", "bien", "mal", "salut!", "bonjour!", "merci!", "oui!", "non!", "ça va?", "bien!", "mal!",

    # Other as told by Ai not sure wth they are .
    "ciao", "ola", "yo!", "sup!", "aloha", "wassup", "wassup?", "yo yo", "yo yo!", "yo!", "sup!", "hey!", "hi!", "hello!", "bye!", "ok!", "okay!", "fine!", "good!", "nice!", "cool!", "yes!", "no!", "thanks!", "welcome!", "ciao!", "ola!", "aloha!", "wassup!", "wassup?", "yo yo!", "yo yo!", "yo!", "sup!", "hey!", "hi!", "hello!", "bye!", "ok!", "okay!", "fine!", "good!", "nice!", "cool!", "yes!", "no!", "thanks!", "welcome!"
][:100]

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

@app.on_message(filters.command(["ai", "gpt", "ami"]))
async def ai_chat(client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text(random.choice(INSTANT_REPLIES), quote=True)
    query = message.text.split(None, 1)[1].strip().lower()
    if len(query) <= 3 or query in SHORT_QUERIES:
        return await message.reply_text(random.choice(INSTANT_REPLIES), quote=True)
    processing_msg = await message.reply_text(random.choice(PROCESSING_MESSAGES), quote=True)

    url = f"{AI_ENDPOINT}/ai"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": AI_KEY
    }
    data = {
        "message": query
    }
    response = requests.post(url, headers=headers, json=data, timeout=120)
    data = response.json()
    aiReply = data.get("response", "Sorry, Seems ai is down.\nPlease contact author @amigr8bot")
    await processing_msg.edit_text(aiReply, parse_mode=ParseMode.MARKDOWN)


## Status check ok API key only for sudo users..
@app.on_message(filters.command(["api", "apikey", "usage"]) & SUDOERS)
async def api_stats(client, message: Message):
    start = datetime.now()
    url = f"{AI_ENDPOINT}/status"
    headers = {
      'x-api-key': AI_KEY
    }
  
    response = requests.request("GET", url, headers=headers)
    await message.reply_text(response)



  




    
