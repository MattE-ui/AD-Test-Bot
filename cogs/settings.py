# cogs/settings.py

import discord
from discord.ext import commands
from discord import app_commands

from database.config_store import get_config, set_config, get_all_config

class Settings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="show_settings", description="Show all current bot settings.")
    @app_commands.checks.has_permissions(administrator=True)
    async def show_settings(self, interaction: discord.Interaction):
        config = get_all_config()
        embed = discord.Embed(title="🔧 Bot Settings", color=discord.Color.blurple())
        for key, value in config.items():
            embed.add_field(name=key, value=str(value), inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="toggle_setting", description="Toggle a boolean setting (true/false).")
    @app_commands.describe(key="The config key to toggle (must be a boolean)")
    @app_commands.checks.has_permissions(administrator=True)
    async def toggle_setting(self, interaction: discord.Interaction, key: str):
        value = get_config(key)
        if not isinstance(value, bool):
            await interaction.response.send_message(f"❌ `{key}` is not a toggleable boolean.", ephemeral=True)
            return
        new_value = not value
        set_config(key, new_value)
        await interaction.response.send_message(f"✅ `{key}` is now set to `{new_value}`.", ephemeral=True)

    @app_commands.command(name="set_counting_channel", description="Set this channel as the counting channel.")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_counting_channel(self, interaction: discord.Interaction):
        set_config("counting_channel_id", interaction.channel.id)
        await interaction.response.send_message(
            f"🔢 Counting channel set to {interaction.channel.mention}.", ephemeral=True
        )

    @app_commands.command(name="set_config", description="Set a config key manually.")
    @app_commands.describe(key="The config key to set", value="The value to store")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_config_command(self, interaction: discord.Interaction, key: str, value: str):
        try:
            # Evaluate string input safely
            parsed_value = eval(value, {"__builtins__": {}}, {})
        except Exception:
            parsed_value = value
        set_config(key, parsed_value)
        await interaction.response.send_message(
            f"🛠️ `{key}` updated to `{parsed_value}`.", ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(Settings(bot))
