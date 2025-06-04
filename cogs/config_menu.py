# cogs/config_menu.py

import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Select
from database.config_store import get_config, set_config

class ConfigSelect(Select):
    """
    A single dropdown (Select) containing all configurable actions.
    When the user selects one, the corresponding logic runs.
    """
    OPTIONS = [
        discord.SelectOption(
            label="Set Counting Channel",
            description="Register this channel as the counting channel",
            value="set_counting_channel"
        ),
        discord.SelectOption(
            label="Toggle Counting Game",
            description="Enable or disable the counting game",
            value="toggle_counting"
        ),
        discord.SelectOption(
            label="Set Welcome Channel",
            description="Register this channel as the welcome channel",
            value="set_welcome_channel"
        ),
        discord.SelectOption(
            label="Toggle Welcome Messages",
            description="Enable or disable welcome messages",
            value="toggle_welcome"
        ),
        discord.SelectOption(
            label="Set Voice Status Channel",
            description="Register this voice channel for auto‐rename stats",
            value="set_voice_status_channel"
        ),
        discord.SelectOption(
            label="Toggle Voice Logging",
            description="Enable or disable voice join/leave logs",
            value="toggle_voice_logging"
        ),
        discord.SelectOption(
            label="Set Voice Log Channel",
            description="Register this text channel for voice logs",
            value="set_voice_log_channel"
        ),
        discord.SelectOption(
            label="Set Reddit Channel",
            description="Register this channel for Reddit mirror posts",
            value="set_reddit_channel"
        ),
        discord.SelectOption(
            label="Toggle Reddit Mirror",
            description="Enable or disable the Reddit mirror feature",
            value="toggle_reddit"
        ),
    ]

    def __init__(self):
        super().__init__(
            placeholder="Choose a setting to configure…",
            min_values=1,
            max_values=1,
            options=self.OPTIONS
        )

    async def callback(self, interaction: discord.Interaction):
        """
        Called when a user selects one of the dropdown options.
        We handle each 'value' by inspecting self.values[0].
        """
        choice = self.values[0]
        user = interaction.user
        channel = interaction.channel

        # Only administrators can use this menu
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message(
                "❌ You must be an administrator to use this menu.",
                ephemeral=True
            )

        # For logging / debugging, you might uncomment:
        # print(f"[ConfigMenu] {user} selected {choice} in {channel}")

        # 1) Set Counting Channel
        if choice == "set_counting_channel":
            if not isinstance(channel, discord.TextChannel):
                return await interaction.response.send_message(
                    "❌ Please run this command in a **text channel**.", ephemeral=True
                )
            set_config("counting_channel_id", channel.id)
            await interaction.response.send_message(
                f"🔢 Counting channel set to {channel.mention}.", ephemeral=True
            )

        # 2) Toggle Counting
        elif choice == "toggle_counting":
            current = get_config("counting_paused") or False
            # In our design, we use 'counting_paused'—True means paused
            new_value = not current
            set_config("counting_paused", new_value)
            state = "paused" if new_value else "resumed"
            await interaction.response.send_message(
                f"⏹️ Counting game is now **{state}**.", ephemeral=True
            )

        # 3) Set Welcome Channel
        elif choice == "set_welcome_channel":
            if not isinstance(channel, discord.TextChannel):
                return await interaction.response.send_message(
                    "❌ Please run this command in a **text channel**.", ephemeral=True
                )
            set_config("welcome_channel_id", channel.id)
            await interaction.response.send_message(
                f"📬 Welcome channel set to {channel.mention}.", ephemeral=True
            )

        # 4) Toggle Welcome Messages
        elif choice == "toggle_welcome":
            current = get_config("welcome_enabled") or False
            new_value = not current
            set_config("welcome_enabled", new_value)
            state = "enabled" if new_value else "disabled"
            await interaction.response.send_message(
                f"👋 Welcome messages are now **{state}**.", ephemeral=True
            )

        # 5) Set Voice Status Channel
        elif choice == "set_voice_status_channel":
            # Must be run in a voice channel
            if not isinstance(channel, discord.VoiceChannel):
                return await interaction.response.send_message(
                    "❌ Please run this command **in a voice channel**.", ephemeral=True
                )
            set_config("voice_status_channel_id", channel.id)
            await interaction.response.send_message(
                f"🔊 Voice status channel set (auto‐rename enabled).", ephemeral=True
            )

        # 6) Toggle Voice Logging
        elif choice == "toggle_voice_logging":
            current = get_config("voice_logging_enabled") or False
            new_value = not current
            set_config("voice_logging_enabled", new_value)
            state = "enabled" if new_value else "disabled"
            await interaction.response.send_message(
                f"📝 Voice logging is now **{state}**.", ephemeral=True
            )

        # 7) Set Voice Log Channel
        elif choice == "set_voice_log_channel":
            if not isinstance(channel, discord.TextChannel):
                return await interaction.response.send_message(
                    "❌ Please run this command in a **text channel**.", ephemeral=True
                )
            set_config("voice_log_channel_id", channel.id)
            await interaction.response.send_message(
                f"📃 Voice log channel set to {channel.mention}.", ephemeral=True
            )

        # 8) Set Reddit Channel
        elif choice == "set_reddit_channel":
            if not isinstance(channel, discord.TextChannel):
                return await interaction.response.send_message(
                    "❌ Please run this command in a **text channel**.", ephemeral=True
                )
            set_config("reddit_channel_id", channel.id)
            await interaction.response.send_message(
                f"📡 Reddit mirror channel set to {channel.mention}.", ephemeral=True
            )

        # 9) Toggle Reddit Mirror
        elif choice == "toggle_reddit":
            current = get_config("reddit_enabled") or False
            new_value = not current
            set_config("reddit_enabled", new_value)
            state = "enabled" if new_value else "disabled"
            await interaction.response.send_message(
                f"🚀 Reddit mirror is now **{state}**.", ephemeral=True
            )

        # In case you add more options later, you can chain them here:
        else:
            await interaction.response.send_message(
                f"❓ Unhandled configuration option: `{choice}`", ephemeral=True
            )


class ConfigMenu(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="config_menu",
        description="Open the dropdown menu to configure all bot features."
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def config_menu(self, interaction: discord.Interaction):
        """
        Sends an ephemeral message containing the dropdown (ConfigSelect).
        Only administrators can invoke this.
        """
        view = View()
        view.add_item(ConfigSelect())
        await interaction.response.send_message(
            "🔧 **Configuration Menu**\nSelect an option below to configure that feature:",
            view=view,
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(ConfigMenu(bot))
