# main.py

import os
import discord
import logging
import asyncio

from discord.ext import commands
from dotenv import load_dotenv

# ─── Load .env ───────────────────────────────────────
load_dotenv()
TOKEN     = os.getenv("DISCORD_TOKEN")
GUILD_ID  = os.getenv("GUILD_ID")
SYNC_MODE = os.getenv("SYNC_MODE", "global").lower()

# ─── Logging Setup ──────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")

# ─── Intents ────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
intents.members         = True
intents.guilds          = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ─── Initialize SQLite ────────────────────────────
from database.config_store import init_config_db
from database.stats_store import init_stats_db

init_config_db()
init_stats_db()

# ─── All Cogs ──────────────────────────────────────
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
    logger.info(f"Logged in as {bot.user} (ID: {bot.user.id}).")
    print(f"{bot.user} is now online.")

    # 1) Print out exactly which commands are in bot.tree:
    print("───────── Registered slash commands in bot.tree ─────────")
    for cmd in bot.tree.get_commands():
        print(f" • /{cmd.name} — {cmd.description}")
    print("────────────────────────────────────────────────────────────\n")

    # 2) Do the appropriate sync:
    try:
        if SYNC_MODE == "dev" and GUILD_ID:
            guild = discord.Object(id=int(GUILD_ID))

            # Copy EVERY global command into this guild
            bot.tree.copy_global_to(guild=guild)
            synced = await bot.tree.sync(guild=guild)
            logger.info(f"🧪 Synced {len(synced)} slash command(s) to dev guild {guild.id}.")
            print(f"🧪 Synced {len(synced)} slash command(s) to dev guild {guild.id}.\n")
        else:
            synced = await bot.tree.sync()
            logger.info(f"🌍 Synced {len(synced)} slash command(s) globally.")
            print(f"🌍 Synced {len(synced)} slash command(s) globally.\n")
    except Exception as e:
        logger.error(f"❌ Slash command sync failed: {e}")
        print(f"❌ Slash command sync failed: {e}\n")

async def load_extensions():
    for cog in COGS:
        try:
            await bot.load_extension(cog)
            logger.info(f"✅ Loaded extension: {cog}")
        except Exception as e:
            logger.error(f"❌ Failed to load extension {cog}: {e}")

async def main():
    async with bot:
        await load_extensions()
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
