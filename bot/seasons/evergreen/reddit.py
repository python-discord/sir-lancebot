import logging
import random

import discord
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType

from bot.pagination import ImagePaginator


log = logging.getLogger(__name__)


class Reddit(commands.Cog):
    """Fetches reddit posts."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def fetch(self, url: str) -> dict:
        """Send a get request to the reddit API and get json response."""
        session = self.bot.http_session
        params = {
            'limit': 50
        }
        headers = {
            'User-Agent': 'Iceman'
        }

        async with session.get(url=url, params=params, headers=headers) as response:
            return await response.json()

    @commands.command(name='reddit')
    @commands.cooldown(1, 10, BucketType.user)
    async def get_reddit(self, ctx: commands.Context, subreddit: str = 'python', sort: str = "hot") -> None:
        """
        Fetch reddit posts by using this command.

        Gets a post from r/python by default.
        Usage:
        --> .reddit [subreddit_name] [hot/top/new]
        """
        pages = []
        sort_list = ["hot", "new", "top", "rising"]
        if sort.lower() not in sort_list:
            await ctx.send(f"Invalid sorting: {sort}\nUsing default sorting: `Hot`")
            sort = "hot"

        data = await self.fetch(f'https://www.reddit.com/r/{subreddit}/{sort}/.json')

        try:
            posts = data["data"]["children"]
        except KeyError:
            return await ctx.send('Subreddit not found!')
        if not posts:
            return await ctx.send('No posts available!')

        if posts[1]["data"]["over_18"] is True:
            return await ctx.send("You cannot access this Subreddit.")

        upvote_emoji = self.bot.get_emoji(565557799040319508)
        comment_emoji = self.bot.get_emoji(565576076483624960)
        user_emoji = "🎅"

        # embed_titles = discord.Embed(colour=0xf9f586)
        embed_titles = ""

        random_posts = []
        while True:
            if len(random_posts) == 5:
                break
            rand_post = random.choice(posts)
            if rand_post not in random_posts:
                random_posts.append(rand_post)

        # -----------------------------------------------------------
        # This code below is bound of change when the emojis are added.

        upvote_emoji = self.bot.get_emoji(674608910656733185)
        comment_emoji = self.bot.get_emoji(674608751784755200)
        user_emoji = self.bot.get_emoji(674608692418707467)
        text_emoji = self.bot.get_emoji(674608836312825877)
        video_emoji = self.bot.get_emoji(674608791450550272)
        image_emoji = self.bot.get_emoji(674594916655169536)
        reddit_emoji = self.bot.get_emoji(674087978628284417)

        # ------------------------------------------------------------

        for i, post in enumerate(random_posts, start=1):
            post_title = post["data"]["title"][0:50]
            post_url = post['data']['url']
            if post_title == "":
                post_title = "No Title."
            elif post_title == post_url:
                post_title = "Title is itself a link."

            # ------------------------------------------------------------------
            # Embed building.

            embed_titles += f"**{i}.[{post_title}]({post_url})**\n"
            image_url = " "
            post_stats = f"{text_emoji}"  # Set default content type to text.

            if post["data"]["is_video"] is True or "youtube" in post_url.split("."):
                # This means the content type in the post is a video.
                post_stats = f"{video_emoji} "

            elif post_url.endswith("jpg") or post_url.endswith("png") or post_url.endswith("gif"):
                # This means the content type in the post is an image.
                post_stats = f"{image_emoji} "
                image_url = post_url

            votes = f'{upvote_emoji}{post["data"]["ups"]}'
            comments = f'{comment_emoji}\u2002{ post["data"]["num_comments"]}'
            post_stats += (
                f"\u2002{votes}\u2003"
                f"{comments}"
                f'\u2003{user_emoji}\u2002{post["data"]["author"]}\n'
            )
            embed_titles += f"{post_stats}\n"
            page_text = f"**[{post_title}]({post_url})**\n{post_stats}\n{post['data']['selftext'][0:200]}"

            embed = discord.Embed()
            page_tuple = (page_text, image_url)
            pages.append(page_tuple)

            # ------------------------------------------------------------------

        pages.insert(0, (embed_titles, " "))
        embed.set_author(name=f"r/{posts[0]['data']['subreddit']} - {sort}", icon_url=reddit_emoji.url)
        await ImagePaginator.paginate(pages, ctx, embed)


def setup(bot: commands.Bot) -> None:
    """Load the Cog."""
    bot.add_cog(Reddit(bot))
    log.debug('Loaded')
