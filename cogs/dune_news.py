# cogs/dune_news.py

import discord
from discord.ext import commands, tasks
import aiohttp
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv

from database.config_store import get_config, set_config

load_dotenv()

class DuneNews(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.channel_id = int(os.getenv("NEWS_CHANNEL_ID"))
        self.check_news.start()

    def cog_unload(self):
        self.check_news.cancel()

    @tasks.loop(minutes=5)
    async def check_news(self):
        url = "https://duneawakening.com/news"
        try:
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(url, timeout=15) as response:
                        if response.status != 200:
                            # Non-200 response; skip this cycle
                            return

                        html = await response.text()
                except Exception as e:
                    # Could be SSL error, timeout, etc.
                    print(f"[DuneNews] Failed to fetch news page: {e}")
                    return
        except Exception as e:
            # Could be failure creating session
            print(f"[DuneNews] HTTP session error: {e}")
            return

        # Parse the HTML to find the latest article
        try:
            soup = BeautifulSoup(html, "html.parser")
            article = soup.find("a", class_="NewsCard_card__H_sUC")
            if not article or "href" not in article.attrs:
                return

            post_url = f"https://duneawakening.com{article['href']}"
            title_elem = article.find("h2")
            post_title = title_elem.text.strip() if title_elem else "New Dune News"
        except Exception as e:
            print(f"[DuneNews] HTML parsing error: {e}")
            return

        last_url = get_config("last_posted_news_url")
        if post_url == last_url:
            # Already posted this news article
            return

        # Save new URL to prevent duplicates
        set_config("last_posted_news_url", post_url)

        # Build and send embed
        embed = discord.Embed(
            title=post_title,
            url=post_url,
            description="New Dune: Awakening news post is live!",
            color=discord.Color.dark_orange()
        )
        embed.set_footer(text="Source: duneawakening.com/news")

        channel = self.bot.get_channel(self.channel_id)
        if channel and isinstance(channel, discord.TextChannel):
            try:
                await channel.send(embed=embed)
            except Exception as e:
                print(f"[DuneNews] Failed to send embed: {e}")

    @check_news.before_loop
    async def before_loop(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(DuneNews(bot))
