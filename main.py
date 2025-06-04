# main.py

import discord
from discord.ext import commands
import os
import asyncio
import logging
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = os.getenv("GUILD_ID")
SYNC_MODE = os.getenv("SYNC_MODE", "global").lower()

# Setup logging
logging.basicConfig(level=logging.INFO)

# Setup Discord intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

# Initialize the bot
bot = commands.Bot(command_prefix="!", intents=intents)

# Initialize SQLite databases
from database.config_store import init_config_db
from database.stats_store import init_stats_db

init_config_db()
init_stats_db()

# List of cogs to load
COGS = [
    "cogs.counting_game",
    "cogs.devtools",
    "cogs.dune_news",
    "cogs.reddit_mirror",
    "cogs.settings",
    "cogs.voice_manager",
    "cogs.welcome",
    "cogs.config_menu"
]

@bot.event
async def on_ready():
    logging.info(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print(f"{bot.user} is now online.")

    try:
        if SYNC_MODE == "dev" and GUILD_ID:
            guild = discord.Object(id=int(GUILD_ID))
            synced = await bot.tree.sync(guild=guild)
            logging.info(f"🧪 Synced {len(synced)} slash command(s) to dev guild {guild.id}")
        else:
            synced = await bot.tree.sync()
            logging.info(f"🌍 Synced {len(synced)} slash command(s) globally")
    except Exception as e:
        logging.error(f"❌ Slash command sync failed: {e}")

async def load_extensions():
    for cog in COGS:
        try:
            await bot.load_extension(cog)
            logging.info(f"✅ Loaded extension: {cog}")
        except Exception as e:
            logging.error(f"❌ Failed to load extension {cog}: {e}")

async def main():
    async with bot:
        await load_extensions()
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
