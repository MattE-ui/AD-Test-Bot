# cogs/reddit_mirror.py

import discord
from discord.ext import commands, tasks
import praw
import os
from dotenv import load_dotenv

from database.config_store import get_config

load_dotenv()

class RedditMirror(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.subreddit_name = os.getenv("REDDIT_SUBREDDIT")
        self.channel_id = int(os.getenv("REDDIT_CHANNEL_ID"))

        # Initialize PRAW
        try:
            self.reddit = praw.Reddit(
                client_id=os.getenv("REDDIT_CLIENT_ID"),
                client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
                username=os.getenv("REDDIT_USERNAME"),
                password=os.getenv("REDDIT_PASSWORD"),
                user_agent=os.getenv("REDDIT_USER_AGENT")
            )
        except Exception as e:
            print(f"[RedditMirror] PRAW initialization failed: {e}")
            self.reddit = None

        self.posted_ids = set()
        self.check_reddit.start()

    def cog_unload(self):
        self.check_reddit.cancel()

    @tasks.loop(minutes=1.5)
    async def check_reddit(self):
        # Only run if reddit_enabled is True
        if not get_config("reddit_enabled"):
            return

        if self.reddit is None:
            # If PRAW failed to initialize, skip
            return

        try:
            subreddit = self.reddit.subreddit(self.subreddit_name)
            # Attempt to fetch new submissions
            submissions = []
            try:
                submissions = list(subreddit.new(limit=3))
            except Exception as e:
                print(f"[RedditMirror] Failed to fetch subreddit posts: {e}")
                return

            channel = self.bot.get_channel(self.channel_id)
            if channel is None or not isinstance(channel, discord.TextChannel):
                return

            for submission in submissions:
                if submission.id in self.posted_ids:
                    continue

                self.posted_ids.add(submission.id)

                title = submission.title
                url = submission.url
                post_url = f"https://reddit.com{submission.permalink}"

                embed = discord.Embed(
                    title=title,
                    url=post_url,
                    color=discord.Color.orange()
                )
                embed.set_author(name="Reddit /r/" + self.subreddit_name)
                embed.set_footer(text=f"Posted by u/{submission.author}")

                if submission.selftext and len(submission.selftext) < 1024:
                    embed.description = submission.selftext

                # If the post URL is an image, set it as embed image
                if url.lower().endswith((".jpg", ".png", ".gif", ".jpeg", ".webp")):
                    embed.set_image(url=url)

                try:
                    await channel.send(embed=embed)
                except Exception as e:
                    print(f"[RedditMirror] Failed to send embed for {submission.id}: {e}")
        except Exception as e:
            print(f"[RedditMirror] Unexpected error in check_reddit loop: {e}")

    @check_reddit.before_loop
    async def before_check_reddit(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(RedditMirror(bot))
