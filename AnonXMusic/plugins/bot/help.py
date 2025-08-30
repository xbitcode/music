import random
import aiohttp
from typing import Union

from pyrogram import filters, types
from pyrogram.types import InlineKeyboardMarkup, Message, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import MessageNotModified
from pyrogram.enums import ParseMode

from AnonXMusic import app
from AnonXMusic.misc import SUDOERS
from AnonXMusic.utils import help_pannel
from AnonXMusic.utils.database import get_lang, get_model_settings, update_model_settings
from AnonXMusic.utils.decorators.language import LanguageStart, languageCB
from AnonXMusic.utils.inline.help import help_back_markup, private_help_panel
from config import BANNED_USERS, START_IMG_URL, SUPPORT_CHAT, YTPROXY_URL
import config
from strings import get_string, helpers


async def fetch_tts_models():
    """Fetch TTS models from the API"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{YTPROXY_URL}/tts/models") as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("speakers", [])
                return []
    except Exception as e:
        print(f"Error fetching TTS models: {e}")
        return []


async def fetch_image_models():
    """Fetch image models from the API"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{YTPROXY_URL}/image/models") as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("models", [])
                return []
    except Exception as e:
        print(f"Error fetching image models: {e}")
        return []


async def fetch_ai_models():
    """Fetch AI models from the API"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{YTPROXY_URL}/ai/models") as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("models", [])
                return []
    except Exception as e:
        print(f"Error fetching AI models: {e}")
        return []

@app.on_message(filters.command(["help"]) & filters.private & ~BANNED_USERS)
@app.on_callback_query(filters.regex("settings_back_helper") & ~BANNED_USERS)
async def helper_private(
    client, update: Union[types.Message, types.CallbackQuery]
):
    is_callback = isinstance(update, types.CallbackQuery)
    is_sudo = update.from_user.id in SUDOERS
    if is_callback:
        try:
            await update.answer()
        except:
            pass
        chat_id = update.message.chat.id
        language = await get_lang(chat_id)
        _ = get_string(language)
        keyboard = help_pannel(_, is_sudo, True)
        await update.edit_message_text(
            _["help_1"].format(SUPPORT_CHAT), reply_markup=keyboard
        )
    else:
        try:
            await update.delete()
        except:
            pass
        language = await get_lang(update.chat.id)
        _ = get_string(language)
        keyboard = help_pannel(_, is_sudo)
        await update.reply_photo(
            photo=random.choice(config.START_IMG_URL),
            caption=_["help_1"].format(SUPPORT_CHAT),
            reply_markup=keyboard,
        )


@app.on_message(filters.command(["help"]) & filters.group & ~BANNED_USERS)
@LanguageStart
async def help_com_group(client, message: Message, _):
    keyboard = private_help_panel(_)
    await message.reply_text(_["help_2"], reply_markup=InlineKeyboardMarkup(keyboard))


@app.on_callback_query(filters.regex("help_callback") & ~BANNED_USERS)
@languageCB
async def helper_cb(client, CallbackQuery:CallbackQuery, _):
    callback_data = CallbackQuery.data.strip()
    cb = callback_data.split(None, 1)[1]
    keyboard = help_back_markup(_)
    if cb == "hb1":
        await CallbackQuery.edit_message_text(helpers.HELP_1, reply_markup=keyboard)
    elif cb == "hb2":
        await CallbackQuery.edit_message_text(helpers.HELP_2, reply_markup=keyboard)
    elif cb == "hb3":
        await CallbackQuery.edit_message_text(helpers.HELP_3, reply_markup=keyboard)
    elif cb == "hb4":
        await CallbackQuery.edit_message_text(helpers.HELP_4, reply_markup=keyboard)
    elif cb == "hb5":
        await CallbackQuery.edit_message_text(helpers.HELP_5, reply_markup=keyboard)
    elif cb == "hb6":
        await CallbackQuery.edit_message_text(helpers.HELP_6, reply_markup=keyboard)
    elif cb == "hb7":
        await CallbackQuery.edit_message_text(helpers.HELP_7, reply_markup=keyboard)
    elif cb == "hb8":
        await CallbackQuery.edit_message_text(helpers.HELP_8, reply_markup=keyboard)
    elif cb == "hb9":
        await CallbackQuery.edit_message_text(helpers.HELP_9, reply_markup=keyboard)
    elif cb == "hb10":
        await CallbackQuery.edit_message_text(helpers.HELP_10, reply_markup=keyboard)
    elif cb == "hb11":
        await CallbackQuery.edit_message_text(helpers.HELP_11, reply_markup=keyboard)
    elif cb == "hb12":
        await CallbackQuery.edit_message_text(helpers.HELP_12, reply_markup=keyboard)
    elif cb == "hb13":
        await CallbackQuery.edit_message_text(helpers.HELP_13, reply_markup=keyboard)
    elif cb == "hb14":
        await CallbackQuery.edit_message_text(helpers.HELP_14, reply_markup=keyboard)
    elif cb == "hb15":
        await CallbackQuery.edit_message_text(helpers.HELP_15, reply_markup=keyboard)
    elif cb == "hb16":
        btn = [
            [
                InlineKeyboardButton(
                    text="Ai Model Setting",
                    callback_data="help_callback hb19",
                )
            ],
            [
                InlineKeyboardButton(
                    text="TTS Model Setting",
                    callback_data="help_callback hb17",
                )
            ],
            [
                InlineKeyboardButton(
                    text="IMAGE Model Setting",
                    callback_data="help_callback hb18",
                )
            ],
            [
                InlineKeyboardButton(
                    text=_["BACK_BUTTON"],
                    callback_data=f"settings_back_helper",
                )
            ]
        ]
        await CallbackQuery.edit_message_text(f"AI, TTS and Image Model Settings \n\n[Check Docs here]({YTPROXY_URL}/docs)", reply_markup=InlineKeyboardMarkup(btn),parse_mode=ParseMode.DEFAULT)
    elif cb == "hb17":
        model_settings = await get_model_settings()
        current_tts = model_settings.get("tts", "athena")
        
        # Fetch TTS models
        speakers = await fetch_tts_models()
        
        if not speakers:
            try:
                await CallbackQuery.edit_message_text(
                    "❌ Unable to fetch TTS models. Please try again later.",
                    reply_markup=InlineKeyboardMarkup([[
                                    InlineKeyboardButton(
                                        text=_["BACK_BUTTON"],
                                        callback_data="help_callback hb16"
                                    )
                                ]]),
                                parse_mode=ParseMode.DEFAULT
                )
            except MessageNotModified:
                pass
            return
        
        buttons = []
        row = []
        for speaker in speakers:
            speaker_id = speaker["speaker"]
            name = speaker["name"]
            
            if speaker_id == current_tts:
                button_text = f"✅ {name}"
            else:
                button_text = f"{name}"
            
            row.append(InlineKeyboardButton(
                text=button_text,
                callback_data=f"tts_model_{speaker_id}"
            ))

            if len(row) == 2:
                buttons.append(row)
                row = []

        if row:
            buttons.append(row)

        buttons.append([
            InlineKeyboardButton(
                text=_["BACK_BUTTON"],
                callback_data="help_callback hb16"
            )
        ])
        
        try:
            await CallbackQuery.edit_message_text(
                "🎤 **TTS Model Settings**\n\nSelect a voice model \n\n [Check out the samples here](https://t.me/amigr8/27)",
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.DEFAULT
            )
        except MessageNotModified:
            pass
    elif cb == "hb18":
        model_settings = await get_model_settings()
        current_image = model_settings.get("image", "stable-diffusion")
        
        # Fetch image models
        models = await fetch_image_models()
        
        if not models:
            try:
                await CallbackQuery.edit_message_text(
                    "❌ Unable to fetch image models. Please try again later.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton(
                            text=_["BACK_BUTTON"],
                            callback_data="help_callback hb16"
                        )
                    ]]),
                    parse_mode=ParseMode.DEFAULT
                )
            except MessageNotModified:
                pass
            return
        
        # Create buttons for each model
        buttons = []
        for model in models:
            if model == current_image:
                button_text = f"✅ {model}"
            else:
                button_text = f"{model}"
            
            buttons.append([
                InlineKeyboardButton(
                    text=button_text,
                    callback_data=f"image_model_{model}"
                )
            ])
        
        # Add back button
        buttons.append([
            InlineKeyboardButton(
                text=_["BACK_BUTTON"],
                callback_data="help_callback hb16"
            )
        ])
        
        try:
            await CallbackQuery.edit_message_text(
                "🎨 **Image Model Settings**\n\nSelect an image generation model:",
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.DEFAULT
            )
        except MessageNotModified:
            pass
    elif cb == "hb19":
        model_settings = await get_model_settings()
        current_ai = model_settings.get("ai", "GPT4")
        
        # Fetch AI models
        models = await fetch_ai_models()
        
        if not models:
            try:
                await CallbackQuery.edit_message_text(
                    "❌ Unable to fetch AI models. Please try again later.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton(
                            text=_["BACK_BUTTON"],
                            callback_data="help_callback hb16"
                        )
                    ]]),
                    parse_mode=ParseMode.DEFAULT
                )
            except MessageNotModified:
                pass
            return
        
        # Create buttons for each model
        buttons = []
        for model in models:
            if model == current_ai:
                button_text = f"✅ {model}"
            else:
                button_text = f"{model}"
            
            buttons.append([
                InlineKeyboardButton(
                    text=button_text,
                    callback_data=f"ai_model_{model}"
                )
            ])
        
        # Add back button
        buttons.append([
            InlineKeyboardButton(
                text=_["BACK_BUTTON"],
                callback_data="help_callback hb16"
            )
        ])
        
        try:
            await CallbackQuery.edit_message_text(
                "🤖 **AI Model Settings**\n\nSelect an AI model:",
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.DEFAULT
            )
        except MessageNotModified:
            pass


@app.on_callback_query(filters.regex(r"tts_model_") & ~BANNED_USERS)
@languageCB
async def tts_model_callback(client, CallbackQuery:CallbackQuery, _):
    """Handle TTS model selection"""
    try:
        await CallbackQuery.answer()
    except:
        pass
    
    callback_data = CallbackQuery.data
    model_name = callback_data.replace("tts_model_", "")
    
    success = await update_model_settings({"tts": model_name})
    
    if success:
        model_settings = await get_model_settings()
        current_tts = model_settings.get("tts", "athena")
        
        speakers = await fetch_tts_models()
        
        if speakers:
            buttons = []
            row = []
            for speaker in speakers:
                speaker_id = speaker["speaker"]
                name = speaker["name"]
                
                if speaker_id == current_tts:
                    button_text = f"✅ {name}"
                else:
                    button_text = f"{name}"

                row.append([
                    InlineKeyboardButton(
                        text=button_text,
                        callback_data=f"tts_model_{speaker_id}"
                    )
                ])
                if len(row) == 2:
                    buttons.append(row)
                    row = []

            if row:
                buttons.append(row)

            buttons.append([
                InlineKeyboardButton(
                    text=_["BACK_BUTTON"],
                    callback_data="help_callback hb16"
                )
            ])
            
            try:
                await CallbackQuery.edit_message_text(
                    f"✅ **TTS Model Updated!**\n\nCurrent model: **{model_name}**",
                    reply_markup=InlineKeyboardMarkup(buttons),
                    parse_mode=ParseMode.DEFAULT
                )
            except MessageNotModified:
                pass
        else:
            try:
                await CallbackQuery.edit_message_text(
                    "❌ Unable to fetch TTS models. Please try again later.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton(
                            text=_["BACK_BUTTON"],
                            callback_data="help_callback hb16"
                        )
                    ]]),
                    parse_mode=ParseMode.DEFAULT
                )
            except MessageNotModified:
                pass
    else:
        try:
            await CallbackQuery.edit_message_text(
                "❌ Failed to update TTS model. Please try again.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton(
                        text=_["BACK_BUTTON"],
                        callback_data="help_callback hb16"
                    )
                ]]),
                parse_mode=ParseMode.DEFAULT
            )
        except MessageNotModified:
            pass


@app.on_callback_query(filters.regex(r"image_model_") & ~BANNED_USERS)
@languageCB
async def image_model_callback(client, CallbackQuery: CallbackQuery, _):
    """Handle image model selection"""
    try:
        await CallbackQuery.answer()
    except:
        pass
    
    # Extract model name from callback data
    callback_data = CallbackQuery.data
    model_name = callback_data.replace("image_model_", "")
    
    success = await update_model_settings({"image": model_name})
    
    if success:
        model_settings = await get_model_settings()
        current_image = model_settings.get("image", "stable-diffusion")
        
        models = await fetch_image_models()
        
        if models:
            buttons = []
            for model in models:
                if model == current_image:
                    button_text = f"✅ {model}"
                else:
                    button_text = f"{model}"
                
                buttons.append([
                    InlineKeyboardButton(
                        text=button_text,
                        callback_data=f"image_model_{model}"
                    )
                ])
            
            buttons.append([
                InlineKeyboardButton(
                    text=_["BACK_BUTTON"],
                    callback_data="help_callback hb16"
                )
            ])
            
            try:
                await CallbackQuery.edit_message_text(
                    f"✅ **Image Model Updated!**\n\nCurrent model: **{model_name}**",
                    reply_markup=InlineKeyboardMarkup(buttons),
                    parse_mode=ParseMode.DEFAULT
                )
            except MessageNotModified:
                pass
        else:
            try:
                await CallbackQuery.edit_message_text(
                    "❌ Unable to fetch image models. Please try again later.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton(
                            text=_["BACK_BUTTON"],
                            callback_data="help_callback hb16"
                        )
                    ]]),
                    parse_mode=ParseMode.DEFAULT
                )
            except MessageNotModified:
                pass
    else:
        try:
            await CallbackQuery.edit_message_text(
                "❌ Failed to update image model. Please try again.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton(
                        text=_["BACK_BUTTON"],
                        callback_data="help_callback hb16"
                    )
                ]]),
                parse_mode=ParseMode.DEFAULT
            )
        except MessageNotModified:
            pass


@app.on_callback_query(filters.regex(r"ai_model_") & ~BANNED_USERS)
@languageCB
async def ai_model_callback(client, CallbackQuery: CallbackQuery, _):
    """Handle AI model selection"""
    try:
        await CallbackQuery.answer()
    except:
        pass
    
    # Extract model name from callback data
    callback_data = CallbackQuery.data
    model_name = callback_data.replace("ai_model_", "")
    
    success = await update_model_settings({"ai": model_name})
    
    if success:
        model_settings = await get_model_settings()
        current_ai = model_settings.get("ai", "GPT4")
        
        models = await fetch_ai_models()
        
        if models:
            buttons = []
            for model in models:
                if model == current_ai:
                    button_text = f"✅ {model}"
                else:
                    button_text = f"{model}"
                
                buttons.append([
                    InlineKeyboardButton(
                        text=button_text,
                        callback_data=f"ai_model_{model}"
                    )
                ])
            
            buttons.append([
                InlineKeyboardButton(
                    text=_["BACK_BUTTON"],
                    callback_data="help_callback hb16"
                )
            ])
            
            try:
                await CallbackQuery.edit_message_text(
                    f"✅ **AI Model Updated!**\n\nCurrent model: **{model_name}**",
                    reply_markup=InlineKeyboardMarkup(buttons),
                    parse_mode=ParseMode.DEFAULT
                )
            except MessageNotModified:
                pass
        else:
            try:
                await CallbackQuery.edit_message_text(
                    "❌ Unable to fetch AI models. Please try again later.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton(
                            text=_["BACK_BUTTON"],
                            callback_data="help_callback hb16"
                        )
                    ]]),
                    parse_mode=ParseMode.DEFAULT
                )
            except MessageNotModified:
                pass
    else:
        try:
            await CallbackQuery.edit_message_text(
                "❌ Failed to update AI model. Please try again.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton(
                        text=_["BACK_BUTTON"],
                        callback_data="help_callback hb16"
                    )
                ]]),
                parse_mode=ParseMode.DEFAULT
            )
        except MessageNotModified:
            pass
