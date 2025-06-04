# cogs/dune_news.py

import asyncio
import sqlite3
import re
from datetime import datetime

import discord
from discord.ext import commands, tasks
from discord import app_commands
import requests
from bs4 import BeautifulSoup

from database.config_store import get_config  # ✅ ADDED

DB_PATH = "dune_news.sqlite3"
NEWS_URL = "https://www.duneawakening.com/en/news"
CHECK_INTERVAL_SECONDS = 600
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

BANNED_LINES = {
    "home", "game", "betasignup", "wishlistonsteam", "preordernow",
    "alldunegames", "wishlist", "preorder", "media", "news", "share",
    "linkcopied", "englishfrançaisespañoldeutsch中文", "pre-ordernow"
}


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS posted_articles (
            url TEXT PRIMARY KEY,
            posted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def has_been_posted(url: str) -> bool:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT 1 FROM posted_articles WHERE url = ?", (url,))
    result = c.fetchone()
    conn.close()
    return result is not None


def mark_as_posted(url: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO posted_articles (url) VALUES (?)", (url,))
    conn.commit()
    conn.close()


async def fetch_dune_news():
    headers = {"User-Agent": USER_AGENT}
    try:
        response = await asyncio.get_event_loop().run_in_executor(
            None, lambda: requests.get(NEWS_URL, headers=headers, timeout=10)
        )
        if response.status_code != 200:
            return None, f"Failed to fetch news (status {response.status_code})"
    except Exception as e:
        return None, f"Network error: {e!s}"

    soup = BeautifulSoup(response.text, "html.parser")
    selectors = [
        "a.article-card_link__XGiVr",
        ".article-card a",
        ".news-item a",
        "article a[href*='/en/news/']",
    ]
    for sel in selectors:
        articles = soup.select(sel)
        if articles:
            return articles, None

    articles = [
        a for a in soup.find_all("a", href=True)
        if "/en/news/" in a["href"] and len(a.get_text(strip=True)) > 10
    ]
    return articles if articles else None, "No news articles found."


async def fetch_article_content(url: str):
    headers = {"User-Agent": USER_AGENT}
    try:
        response = await asyncio.get_event_loop().run_in_executor(
            None, lambda: requests.get(url, headers=headers, timeout=15)
        )
        if response.status_code != 200:
            return None, None, None, None, f"Failed to fetch article (status {response.status_code})"
    except Exception as e:
        return None, None, None, None, f"Network error: {e!s}"

    soup = BeautifulSoup(response.text, "html.parser")
    title = soup.find("h1").get_text(strip=True) if soup.find("h1") else "News Update"

    publish_date = datetime.utcnow()
    date_tag = soup.find("time")
    if date_tag and date_tag.has_attr("datetime"):
        try:
            publish_date = datetime.fromisoformat(date_tag["datetime"].replace("Z", "+00:00"))
        except Exception:
            pass

    image_meta = soup.find("meta", property="og:image")
    image_url = image_meta["content"] if image_meta else None

    body = soup.find("body")
    if not body:
        return title, "Content not available.", image_url, publish_date, None

    lines = []
    for tag in body.find_all(["p", "li", "h2", "h3"], recursive=True):
        text = tag.get_text(separator=" ", strip=True)
        if not text:
            continue
        norm = text.lower().replace(" ", "")
        if any(bad in norm for bad in BANNED_LINES):
            continue
        if tag.name in {"h2", "h3"}:
            lines.append(f"**{text}**")
        elif tag.name == "li":
            lines.append(f"• {text}")
        else:
            lines.append(text)
        lines.append("")

    content = "\n".join(lines)
    content = re.sub(r"\n{3,}", "\n\n", content).strip()

    return title, content, image_url, publish_date, None


class ReadMoreView(discord.ui.View):
    def __init__(self, url: str):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(label="Read More", style=discord.ButtonStyle.link, url=url))


class DuneNews(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        init_db()
        self.auto_post_news.start()

    def cog_unload(self):
        self.auto_post_news.cancel()

    @tasks.loop(seconds=CHECK_INTERVAL_SECONDS)
    async def auto_post_news(self):
        await self.bot.wait_until_ready()

        for guild in self.bot.guilds:
            channel_id = get_config("dune_news_channel_id")
            if not channel_id:
                continue
            channel = guild.get_channel(channel_id)
            if channel is None:
                continue

            articles, error = await fetch_dune_news()
            if error or not articles:
                continue

            for article in reversed(articles[:3]):
                href = article.get("href", "")
                url = f"https://www.duneawakening.com{href}" if href.startswith("/") else href
                if has_been_posted(url):
                    continue

                title, content, img, published, err = await fetch_article_content(url)
                if err:
                    continue

                description = (content[:1800] + "…") if len(content) > 1800 else content
                embed = discord.Embed(title=title, description=description, color=0xDEB887, timestamp=published, url=url)
                if img:
                    embed.set_image(url=img)
                embed.set_footer(text="Dune: Awakening News")

                await channel.send(embed=embed, view=ReadMoreView(url))
                mark_as_posted(url)
                await asyncio.sleep(2.0)

    @app_commands.command(name="dune_news", description="Get the latest Dune: Awakening news headline.")
    async def dune_news(self, interaction: discord.Interaction):
        await interaction.response.defer()
        articles, error = await fetch_dune_news()
        if error or not articles:
            await interaction.followup.send(f"❌ {error or 'No articles found.'}")
            return

        href = articles[0].get("href", "")
        url = f"https://www.duneawakening.com{href}" if href.startswith("/") else href
        title, content, img, published, err = await fetch_article_content(url)
        if err:
            await interaction.followup.send(f"❌ {err}")
            return

        description = (content[:1800] + "…") if len(content) > 1800 else content
        embed = discord.Embed(title=title, description=description, color=0xDEB887, timestamp=published, url=url)
        if img:
            embed.set_image(url=img)
        embed.set_footer(text="Dune: Awakening News")

        await interaction.followup.send(embed=embed, view=ReadMoreView(url))

    @app_commands.command(name="dune_news_summary", description="Summaries of the last 3 Dune: Awakening posts.")
    async def dune_news_summary(self, interaction: discord.Interaction):
        await interaction.response.defer()
        articles, error = await fetch_dune_news()
        if error or not articles:
            await interaction.followup.send(f"❌ {error or 'No articles found.'}")
            return

        embeds = []
        for idx, article in enumerate(articles[:3]):
            href = article.get("href", "")
            url = f"https://www.duneawakening.com{href}" if href.startswith("/") else href
            title, content, img, published, err = await fetch_article_content(url)
            if err:
                continue

            summary = " ".join(content.split()[:90]) + "…"
            embed = discord.Embed(
                title=title,
                description=summary,
                color=0xC8860D,
                timestamp=published,
                url=url,
            )
            if img:
                embed.set_thumbnail(url=img)
            embed.set_footer(text=f"Summary {idx + 1} of {len(articles)}")
            embeds.append((embed, ReadMoreView(url)))

        if not embeds:
            await interaction.followup.send("No summaries available.")
            return

        for embed, view in embeds:
            await interaction.followup.send(embed=embed, view=view)
            await asyncio.sleep(1.0)


async def setup(bot: commands.Bot):
    await bot.add_cog(DuneNews(bot))
