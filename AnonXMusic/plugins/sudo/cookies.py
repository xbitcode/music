from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton as Button
from AnonXMusic import app
from config import COOKIES_URL , OWNER_ID
import asyncio
import os
import requests
import json
## Cookies folder will be current file path cookies

async def set_cookies(url):
    try:
        response = requests.get(url)
        cookies_dir = f"{os.getcwd()}/cookies"
        os.makedirs(cookies_dir, exist_ok=True)
        cookies_path = os.path.join(cookies_dir, "cookies.txt")
        response.raise_for_status()  # Check for HTTP errors
        with open(cookies_path, "wb") as file:
            file.write(response.content)
        return f"Updated bot cookies and stored in {cookies_path}"
    except requests.exceptions.RequestException as e:
        return f"An error occurred while downloading cookies: {str(e)}"
    except Exception as e:
        return f"An error occurred: {str(e)}"


@app.on_message(
    filters.command(["updatecookies", "updatecookie", "getc"])
    & filters.user(OWNER_ID)
)
async def update_cookies(client, message: Message):
    # Check if a URL is provided with the command
    if len(message.command) > 1:
        url = message.command[1]
        if not url.startswith("https://gist.github.com/"):
            return await message.reply_text("Invalid cookies URL.\nOnly gust raw urls are supported...")
    else:
        url = COOKIES_URL

    res = await set_cookies(url)
    return await message.reply_text(res)
