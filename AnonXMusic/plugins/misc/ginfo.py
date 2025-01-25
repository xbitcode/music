'''
Plugin : Users/Group Info.
Author: Rehanna
Usage: Sudo users can send /id to get users data & /ginfo -100xxx to get group info.
'''

from pyrogram import filters
from pyrogram.types import Message
from AnonXMusic import app
from AnonXMusic.misc import SUDOERS



@app.on_message(filters.command("ginfo") & SUDOERS)
async def groupinfo(client, message: Message):
    if len(message.command) != 2:
        return await message.reply_text("<b>Usage:</b> /ginfo [GROUP_ID/USERNAME]")
    
    group_identifier = message.command[1]
    
    try:
        try:
            group = await client.get_chat(group_identifier)
        except Exception as e:
            if "PEER_ID_INVALID" in str(e):
                return await message.reply_text("I can't access this group. Make sure:\nMake sure i am admin in this group.\n")
            return await message.reply_text(f"An error occurred: {str(e)}")

        if "SUPERGROUP" not in str(group.type) and "GROUP" not in str(group.type):
            return await message.reply_text("This is not a group!")

        try:
            bot_info = await client.get_chat_member(group.id, "me")
            if not bot_info.status:
                return await message.reply_text("I'm not a member of this group!")
        except Exception:
            return await message.reply_text("I'm not a member of this group!")

        # Get group information
        try:
            members_count = await app.get_chat_members_count(group.id)
        except Exception as e:
            members_count = "Unknown"
            print(f"Error fetching members count: {str(e)}")

        description = group.description or "No description available"
        username = f"@{group.username}" if group.username else "Private Group"
        
        # Fetch additional group information
        try:
            owner = await app.get_chat_member(chat_id=group.id, user_id=group.creator.id) if hasattr(group, 'creator') else None
            owner_username = f"@{owner.user.username}" if owner and owner.user.username else "Unknown"
            owner_id = owner.user.id if owner else "Unknown"
        except Exception as e:
            owner_username = "Unknown"
            owner_id = "Unknown"
            print(f"Error fetching owner info: {str(e)}")

        bots_count = 0
        zombies_count = 0
        try:
            async for member in app.get_chat_members(group.id):
                if member.user.is_bot:
                    bots_count += 1
                if member.user.is_deleted:
                    zombies_count += 1
        except Exception as e:
            print(f"Error fetching bots and zombies count: {str(e)}")

        # Create info message
        info_text = f"Group Information:\n\n"
        info_text += f"Title: {group.title}\n"
        info_text += f"ID: <code>{group.id}</code>\n"
        info_text += f"Username: {username}\n"
        info_text += f"Members: {members_count}\n"
        info_text += f"Description: {description}\n"
        info_text += f"Owner Username: {owner_username}\n"
        info_text += f"Owner ID: {owner_id}\n"
        info_text += f"Bots Count: {bots_count}\n"
        info_text += f"Zombies Count: {zombies_count}\n"
        
        # Add optional fields if available
        if group.invite_link:
            info_text += f"Invite Link: {group.invite_link}\n"
            
        await message.reply_text(info_text)
        
    except Exception as e:
        await message.reply_text(f"An error occurred: {str(e)}")

## /id function here to show all possbile data 

@app.on_message(filters.command(['id', 'me', 'info', 'sgb']))
async def user_info(client, message: Message):
    replied_user = message.reply_to_message.from_user if message.reply_to_message else message.from_user
    if not replied_user:
        return await message.reply_text("Cannot retrieve user information.")

    # Fetch user information
    name = replied_user.first_name or "Unknown"
    username = f"@{replied_user.username}" if replied_user.username else "Unknown"
    dc_id = replied_user.dc_id if hasattr(replied_user, 'dc_id') else "Unknown"
    bio = replied_user.bio if hasattr(replied_user, 'bio') else "Unknown"
    joined_date = replied_user.joined_date.strftime("%Y-%m-%d") if hasattr(replied_user, 'joined_date') else "Unknown"
    user_id = replied_user.id
    language_code = replied_user.language_code if hasattr(replied_user, 'language_code') else "Unknown"
    status = replied_user.status if hasattr(replied_user, 'status') else "Unknown"

    # Create info message
    info_text = f"😁User Information😁\n\n"
    info_text += f"Name: {name}\n"
    info_text += f"Username: {username}\n"
    info_text += f"DC ID: {dc_id}\n"
    info_text += f"BIO: {bio}\n"
    info_text += f"Joined Since: {joined_date}\n"
    info_text += f"User ID: <code>{user_id}</code>\n"
    info_text += f"Language Code: {language_code}\n"
    info_text += f"Status: {status}\n\n"
    info_text += f"C by @amigr8Bot\n"

    await message.reply_text(info_text)
