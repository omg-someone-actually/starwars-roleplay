from discord import Intents, Member, Embed
from discord.ext.commands import Bot, cooldown, is_owner, BucketType
from discord.ext.tasks import loop

from json import load, dump
from collections import defaultdict
from typing import MutableMapping, TypedDict

from requests import post
from random import randint
from asyncio import sleep

client = Bot(command_prefix="your_prefix", intents=Intents.all())

def reset_character(user: Member) -> str:
    user_id = format(user.id, "d")
    _user_database[user_id] = {
        "active_profile": "profile_1",
        "profile_1": {"character": "stormtrooper", "skin": f"Default {randint(1, 9999)}", "skin_url": "https://www.tornado-studios.com/sites/default/files/blog/stormtrooper_largeportrait_0.jpg"}, 
    }
    save_users()

def change_character(user: Member, character: str, skin: str) -> str:
    user_id = format(user.id, "d")
    user_profile = _user_database[user_id][get_active_profile(user)]
    user_profile["character"] = character
    user_profile["skin"] = (skin + " " + str(randint(1, 10000)))
    user_profile["skin_url"] = characters()[get_character(user)[0]][skin]
    user_profile["nsfw_skin_url"] = characters()[get_character(user)[0]]["nsfw"]
    save_users()

def get_character(user: Member) -> str:
    user_id = format(user.id, "d")
    return [
        _user_database[user_id][get_active_profile(user)]["character"],
        _user_database[user_id][get_active_profile(user)]["skin"],
        _user_database[user_id][get_active_profile(user)]["skin_url"]
    ]

def get_nsfw_skin(user: Member) -> str:
    user_id = format(user.id, "d")
    return _user_database[user_id][get_active_profile(user)]["nsfw_skin_url"]

def characters() -> str:
    with open("starwars-skins.json") as all_characters:
        return load(all_characters)

def get_active_profile(user: Member) -> str:
    user_id = format(user.id, "d")
    return _user_database[user_id]["active_profile"]

def change_profile(user: Member, profile_number: int) -> str:
    user_id = format(user.id, "d")
    _user_database[user_id]["active_profile"] = f"profile_{profile_number}"
    if len(_user_database[user_id]) - 1 == profile_number:
        _user_database[user_id][f"profile_{profile_number}"] = {"character": "stormtrooper", "skin": f"Default {randint(1, 10000)}", "skin_url": "https://www.tornado-studios.com/sites/default/files/blog/stormtrooper_largeportrait_0.jpg", "nsfw_skin_url": "https://st3.depositphotos.com//2398103/13668/v/450/depositphotos_136681634-stock-illustration-nsfw-text-buffered.jpg"}
    save_users()

def all_profiles(user: Member) -> str:
    user_id = format(user.id, "d")
    return _user_database[user_id]

def add_previous_character(user: Member, character: str) -> str:
    user_id = format(user.id, "d")
    _user_database[user_id]["previous_characters"] += f", {character}"
    save_users()

class UserRecord(TypedDict):
    previous_characters: str
    active_profile: str
    profile_1: dict

UserDatabase = MutableMapping[str, UserRecord]

def make_user_record() -> UserRecord:
    return {
        "previous_characters": "",
        "active_profile": "profile_1",
        "profile_1": {"character": "stormtrooper", "skin": f"Default {randint(1, 10000)}", "skin_url": "https://www.tornado-studios.com/sites/default/files/blog/stormtrooper_largeportrait_0.jpg", "nsfw_skin_url": "https://st3.depositphotos.com//2398103/13668/v/450/depositphotos_136681634-stock-illustration-nsfw-text-buffered.jpg"}, 
    }

def load_users() -> UserDatabase:
    try:
        with open("users-characters.json") as fp:
           return defaultdict(make_user_record, load(fp))
    except Exception:
        return defaultdict(make_user_record)

_user_database = load_users()

def save_users():
    with open("users-characters.json", "w") as fp:
        dump(_user_database, fp, sort_keys=True, indent=4)



@client.event
async def on_ready():
    print(f"{client.user} has logged in.")
    await _roleplayers()
    await _reset_past.start()

async def _roleplayers():
    channel = await client.fetch_channel("your_channel_id)

    await channel.purge(limit=1000)

    with open("users-characters.json") as users_raw:
        try:
            users = load(users_raw)
        except Exception:
            return

        for user, user_details in users.items():
            member = await client.fetch_user(user)
            embed = Embed(title=member.name)

            for page_number, user_detail in user_details.items():
                if "active_profile" in page_number:
                    description_part_1 = f"Active profile: {user_detail.strip('profile_')}\nTotal profiles: {len(user_details) - 1}"
                    continue
                if "previous_characters" in page_number:
                    description_part_2 = f"Previously known as: {user_detail.removeprefix(', ')}"
                    continue
                
                embed.description = (description_part_1 + "\n" + description_part_2)

                embed.add_field(name=page_number.replace("_", " "), value=f"Character: {user_detail['character']}\nSkin: {user_detail['skin']}", inline=False)

            await channel.send(embed=embed)


@loop(hours=6)
async def _reset_past():
    with open("users-characters.json") as users_raw:
        users = load(users_raw)
        
        
        for user, user_details in users.items():
            for page_number, user_detail in user_details.items():
                if "previous_characters" in page_number:
                    _user_database[user]["previous_characters"] = ""
        save_users()

@client.command(aliases=["character_select", "cs", "character"])
async def _character_selection(ctx, character=None, skin="default"):
    if character not in characters():
        await ctx.send("Invalid character!")
        return

    if skin not in characters()[character] or skin in ["nsfw"]:
        await ctx.send("Invalid skin!")
        return
    
    user_details = get_character(ctx.author)
    add_previous_character(ctx.author, f"{user_details[0]} ({user_details[1]})")
    change_character(ctx.author, character, skin)
    await ctx.send(f"Changed your character to {character} and skin to {skin}!")
    await _roleplayers()


@client.command(aliases=["reset", "pr", "profile_reset", "reset_character"])
async def _reset_user(ctx):
    reset_character(ctx.author)
    await ctx.send("Resetted all your profiles!")
    await _roleplayers()


@client.command(aliases=["all_characters", "ac", "characters"])
@is_owner()
async def _all_characters(ctx):
    embed = Embed(title="All characters!")

    for character in characters():
        all_skins = ""

        for skin in characters()[character]:
            all_skins += f" {skin},"
    
        embed.add_field(name=character, value=all_skins.replace(", nsfw,", ""))

    await ctx.send(embed=embed)

@client.command(aliases=["session", "roleplay", "rp"])
@cooldown(1, 600, BucketType.user)
@is_owner()
async def _make_roleplay_session(ctx, type: str = None, scene: str = None, *users: Member):
    if not type or not scene:
        return await ctx.send("Invalid arguments!")

    session_channel = await client.fetch_channel(874749340663578625)

    session_message = f"Owner: {ctx.author.mention}\nType: {type}\nScene: {scene}\nAdded users: "
    
    for user in users: 
        if user == ctx.author:
            continue

        session_message += user.mention

    await session_channel.send(session_message)

@client.command(aliases=["profile", "user_profile", "change_profile", "sp", "set_profile"])
async def _change_user_profile(ctx, profile: int = None):
    if not profile or not isinstance(profile, int):
        await ctx.send("Invalid arguments!")

    change_profile(ctx.author, profile)
    profile_alert_message = await ctx.send(f"Switched to profile {profile}!")
    
    if ctx.channel.id != 874157948388130846:
        await sleep(2)
        await ctx.message.delete()
        await profile_alert_message.delete()
    await _roleplayers()

@client.command(aliases=["profiles", "my_profiles", "p"])
async def _user_profiles(ctx):
    user_profiles = all_profiles(ctx.author)

    embed = Embed(title="All of your profiles!")

    for profile_name, profile_items in user_profiles.items():
        if "active_profile" in profile_name:
            embed.description = f"Active profile: {profile_items.strip('profile_')}\nTotal profiles: {len(user_profiles) - 2}"
            continue
            
        if "previous_characters" in profile_name:
            continue

        embed.add_field(name=profile_name.replace("_", " ").replace("p", 'P'), value=f"Character: {profile_items['character']}\nSkin: {profile_items['skin']}")

    await ctx.send(embed=embed)

@client.event
async def on_message(message):
    if message.content.startswith("sw!"):
        await client.process_commands(message)
        return

    black_listed_words = ["@everyone", "@here", "@", "http", ".com", ".org", ".net", "https://"]
    supported_roleplay_channels = {
      "channel_id": "webhook_url    
    }

    if message.author.bot:
        return

    if message.channel.id in supported_roleplay_channels:
        await sleep(0.2)
        await message.delete()

        if any(black_listed_word in message.content for black_listed_word in black_listed_words):
            await message.author.send("You sent a invaid word in your message!")
            return

        users_preset = get_character(message.author)

        users_character = users_preset[0]
        users_skin = users_preset[1]
        users_skin_url = users_preset[2]

        if message.channel.id == 874759328781963315:
            users_skin_url = get_nsfw_skin(message.author)
            users_skin = f"nsfw"

        data = {
            "username": f"{users_character}({users_skin})",
            "avatar_url": users_skin_url,
            "content": message.content
        }

        post(url=supported_roleplay_channels[message.channel.id], json=data)


    

client.run("your_bot_token")
