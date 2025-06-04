# cogs/config_menu.py

import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Select, ChannelSelect
from database.config_store import get_config, set_config


class ConfigSelect(Select):
    OPTIONS = [
        discord.SelectOption(
            label="Set Counting Channel",
            description="Choose which text channel is the counting channel",
            value="set_counting_channel"
        ),
        discord.SelectOption(
            label="Toggle Counting Game",
            description="Enable or disable the counting game",
            value="toggle_counting"
        ),
        discord.SelectOption(
            label="Set Welcome Channel",
            description="Choose which text channel is for welcome messages",
            value="set_welcome_channel"
        ),
        discord.SelectOption(
            label="Toggle Welcome Messages",
            description="Enable or disable welcome messages",
            value="toggle_welcome"
        ),
        discord.SelectOption(
            label="Set Voice Status Channel",
            description="Choose which voice channel shows live stats",
            value="set_voice_status_channel"
        ),
        discord.SelectOption(
            label="Toggle Voice Logging",
            description="Enable or disable voice join/leave logs",
            value="toggle_voice_logging"
        ),
        discord.SelectOption(
            label="Set Voice Log Channel",
            description="Choose which text channel logs voice activity",
            value="set_voice_log_channel"
        ),
        discord.SelectOption(
            label="Set Reddit Channel",
            description="Choose which text channel is for Reddit mirror",
            value="set_reddit_channel"
        ),
        discord.SelectOption(
            label="Toggle Reddit Mirror",
            description="Enable or disable the Reddit mirror feature",
            value="toggle_reddit"
        ),
        discord.SelectOption(
            label="Set Dune News Channel",
            description="Choose which text channel posts Dune Awakening updates",
            value="set_dune_news_channel"
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
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message(
                "❌ You must be an administrator to use this menu.",
                ephemeral=True
            )

        choice = self.values[0]

        if choice == "set_counting_channel":
            await open_channel_select(
                interaction,
                config_key="counting_channel_id",
                channel_types=[discord.ChannelType.text],
                prompt="Select the **text channel** to be the counting channel."
            )

        elif choice == "set_welcome_channel":
            await open_channel_select(
                interaction,
                config_key="welcome_channel_id",
                channel_types=[discord.ChannelType.text],
                prompt="Select the **text channel** for welcome messages."
            )

        elif choice == "set_voice_status_channel":
            await open_channel_select(
                interaction,
                config_key="voice_status_channel_id",
                channel_types=[discord.ChannelType.voice],
                prompt="Select the **voice channel** for auto‐rename stats."
            )

        elif choice == "set_voice_log_channel":
            await open_channel_select(
                interaction,
                config_key="voice_log_channel_id",
                channel_types=[discord.ChannelType.text],
                prompt="Select the **text channel** to log voice activity."
            )

        elif choice == "set_reddit_channel":
            await open_channel_select(
                interaction,
                config_key="reddit_channel_id",
                channel_types=[discord.ChannelType.text],
                prompt="Select the **text channel** for Reddit mirror posts."
            )

        elif choice == "set_dune_news_channel":
            await open_channel_select(
                interaction,
                config_key="dune_news_channel_id",
                channel_types=[discord.ChannelType.text],
                prompt="Select the **text channel** for Dune: Awakening news updates."
            )

        elif choice == "toggle_counting":
            current = get_config("counting_paused") or False
            new = not current
            set_config("counting_paused", new)
            state = "paused" if new else "resumed"
            await interaction.response.send_message(f"⏹️ Counting game is now **{state}**.", ephemeral=True)

        elif choice == "toggle_welcome":
            current = get_config("welcome_enabled") or False
            new = not current
            set_config("welcome_enabled", new)
            state = "enabled" if new else "disabled"
            await interaction.response.send_message(f"👋 Welcome messages are now **{state}**.", ephemeral=True)

        elif choice == "toggle_voice_logging":
            current = get_config("voice_logging_enabled") or False
            new = not current
            set_config("voice_logging_enabled", new)
            state = "enabled" if new else "disabled"
            await interaction.response.send_message(f"📝 Voice logging is now **{state}**.", ephemeral=True)

        elif choice == "toggle_reddit":
            current = get_config("reddit_enabled") or False
            new = not current
            set_config("reddit_enabled", new)
            state = "enabled" if new else "disabled"
            await interaction.response.send_message(f"📡 Reddit mirror is now **{state}**.", ephemeral=True)

        else:
            await interaction.response.send_message(
                f"❓ Unhandled configuration option: `{choice}`",
                ephemeral=True
            )


class ChannelSelectView(View):
    def __init__(self, config_key: str, channel_types: list[discord.ChannelType], prompt: str):
        super().__init__(timeout=60)
        self.config_key = config_key
        self.prompt = prompt

        select = ChannelSelect(
            placeholder="Choose a channel…",
            channel_types=channel_types,
            min_values=1,
            max_values=1
        )
        select.callback = self.select_channel
        self.add_item(select)

    async def select_channel(self, interaction: discord.Interaction):
        selected = interaction.data["values"][0]  # channel ID as string
        channel_id = int(selected)
        channel = interaction.guild.get_channel(channel_id)

        set_config(self.config_key, channel_id)
        mention = channel.mention if hasattr(channel, "mention") else f"<#{channel_id}>"
        label = self.config_key.replace("_id", "").replace("_", " ").title()

        await interaction.response.send_message(
            f"✅ {label} set to {mention}.", ephemeral=True
        )
        self.stop()


async def open_channel_select(interaction, config_key, channel_types, prompt):
    view = ChannelSelectView(config_key=config_key, channel_types=channel_types, prompt=prompt)
    await interaction.response.send_message(prompt, view=view, ephemeral=True)


class ConfigMenu(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="setup",
        description="Open the setup menu to configure bot features."
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def setup(self, interaction: discord.Interaction):
        view = View()
        view.add_item(ConfigSelect())
        await interaction.response.send_message(
            "🔧 **Bot Setup Menu**\nSelect an option below to configure a feature:",
            view=view,
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(ConfigMenu(bot))
