# cogs/voice_manager.py

import discord
from discord.ext import commands, tasks
from discord import app_commands
from database.config_store import get_config, set_config

class VoiceManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.update_voice_status.start()

    def cog_unload(self):
        self.update_voice_status.cancel()

    @tasks.loop(seconds=60)
    async def update_voice_status(self):
        voice_channel_id = get_config("voice_status_channel_id")
        if not voice_channel_id:
            return

        voice_channel = self.bot.get_channel(int(voice_channel_id))
        if not voice_channel or not isinstance(voice_channel, discord.VoiceChannel):
            return

        total_in_voice = sum(
            1 for vc in voice_channel.guild.voice_channels for m in vc.members
        )

        new_name = f"🔊 In Voice: {total_in_voice}"
        if voice_channel.name != new_name:
            await voice_channel.edit(name=new_name)

    @update_voice_status.before_loop
    async def before_update(self):
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if not get_config("voice_logging_enabled"):
            return

        log_channel_id = get_config("voice_log_channel_id")
        if not log_channel_id:
            return

        channel = self.bot.get_channel(int(log_channel_id))
        if channel and isinstance(channel, discord.TextChannel):
            if not before.channel and after.channel:
                await channel.send(f"✅ **{member.display_name}** joined voice: `{after.channel.name}`")
            elif before.channel and not after.channel:
                await channel.send(f"❌ **{member.display_name}** left voice: `{before.channel.name}`")
            elif before.channel != after.channel:
                await channel.send(f"🔁 **{member.display_name}** switched from `{before.channel.name}` to `{after.channel.name}`")

    # ───── Slash Commands ────────────────────────────

    @app_commands.command(name="set_voice_status_channel", description="Set this voice channel to show current voice stats.")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_status_channel(self, interaction: discord.Interaction):
        if isinstance(interaction.channel, discord.VoiceChannel):
            set_config("voice_status_channel_id", interaction.channel.id)
            await interaction.response.send_message("✅ Voice status channel set.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ This command must be used in a voice channel.", ephemeral=True)

    @app_commands.command(name="set_voice_log_channel", description="Set the current text channel for voice activity logs.")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_log_channel(self, interaction: discord.Interaction):
        if isinstance(interaction.channel, discord.TextChannel):
            set_config("voice_log_channel_id", interaction.channel.id)
            await interaction.response.send_message("📃 Voice log channel set to this text channel.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ This must be used in a text channel.", ephemeral=True)

    @app_commands.command(name="toggle_voice_logging", description="Enable or disable voice join/leave logging.")
    @app_commands.checks.has_permissions(administrator=True)
    async def toggle_logging(self, interaction: discord.Interaction):
        current = get_config("voice_logging_enabled") or False
        new_value = not current
        set_config("voice_logging_enabled", new_value)
        await interaction.response.send_message(f"🛠️ Voice logging is now set to `{new_value}`.", ephemeral=True)

    @app_commands.command(name="show_voice_stats", description="Show how many users are in voice channels.")
    async def show_stats(self, interaction: discord.Interaction):
        guild = interaction.guild
        total = sum(len(vc.members) for vc in guild.voice_channels)
        await interaction.response.send_message(f"🔊 There are currently `{total}` users in voice.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(VoiceManager(bot))
