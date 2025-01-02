import asyncio
import random
import textwrap
from collections import namedtuple
from datetime import UTC, datetime, timedelta

from aiohttp import BasicAuth, ClientError
from discord import Colour, Embed, TextChannel
from discord.ext.commands import Cog, Context, group, has_any_role
from discord.ext.tasks import loop
from discord.utils import escape_markdown, sleep_until
from pydis_core.utils.logging import get_logger

from bot.bot import Bot
from bot.constants import Channels, ERROR_REPLIES, Emojis, Reddit as RedditConfig, STAFF_ROLES
from bot.utils.converters import Subreddit
from bot.utils.messages import sub_clyde
from bot.utils.pagination import ImagePaginator, LinePaginator

log = get_logger(__name__)

AccessToken = namedtuple("AccessToken", ["token", "expires_at"])
HEADERS = {"User-Agent": "python3:python-discord/bot:1.0.0 (by /u/PythonDiscord)"}
URL = "https://www.reddit.com"
OAUTH_URL = "https://oauth.reddit.com"
MAX_RETRIES = 3


class Reddit(Cog):
    """Track subreddit posts and show detailed statistics about them."""

    def __init__(self, bot: Bot):
        self.bot = bot

        self.webhook = None
        self.access_token = None
        self.client_auth = BasicAuth(RedditConfig.client_id.get_secret_value(), RedditConfig.secret.get_secret_value())

        self.auto_poster_loop.start()

    async def cog_unload(self) -> None:
        """Stop the loop task and revoke the access token when the cog is unloaded."""
        self.auto_poster_loop.cancel()
        if self.access_token and self.access_token.expires_at > datetime.now(tz=UTC):
            await self.revoke_access_token()

    async def cog_load(self) -> None:
        """Sets the reddit webhook when the cog is loaded."""
        self.webhook = await self.bot.fetch_webhook(RedditConfig.webhook)

    @property
    def channel(self) -> TextChannel:
        """Get the #reddit channel object from the bot's cache."""
        return self.bot.get_channel(Channels.reddit)

    def build_pagination_pages(self, posts: list[dict], paginate: bool) -> list[tuple] | str:
        """Build embed pages required for Paginator."""
        pages = []
        first_page = ""
        for post in posts:
            post_page = ""
            image_url = ""

            data = post["data"]

            title = textwrap.shorten(data["title"], width=50, placeholder="...")

            # Normal brackets interfere with Markdown.
            title = escape_markdown(title).replace("[", "⦋").replace("]", "⦌")
            link = URL + data["permalink"]

            first_page += f"**[{title.replace('*', '')}]({link})**\n"

            text = data["selftext"]
            if text:
                text = escape_markdown(text).replace("[", "⦋").replace("]", "⦌")
                first_page += textwrap.shorten(text, width=100, placeholder="...") + "\n"

            ups = data["ups"]
            comments = data["num_comments"]
            author = data["author"]

            content_type = Emojis.reddit_post_text
            if data["is_video"] or {"youtube", "youtu.be"}.issubset(set(data["url"].split("."))):
                # This means the content type in the post is a video.
                content_type = f"{Emojis.reddit_post_video}"

            elif data["url"].endswith(("jpg", "png", "gif")):
                # This means the content type in the post is an image.
                content_type = f"{Emojis.reddit_post_photo}"
                image_url = data["url"]

            first_page += (
                f"{content_type}\u2003{Emojis.reddit_upvote}{ups}\u2003{Emojis.reddit_comments}"
                f"\u2002{comments}\u2003{Emojis.reddit_users}{author}\n\n"
            )

            if paginate:
                post_page += f"**[{title}]({link})**\n\n"
                if text:
                    post_page += textwrap.shorten(text, width=252, placeholder="...") + "\n\n"
                post_page += (
                    f"{content_type}\u2003{Emojis.reddit_upvote}{ups}\u2003{Emojis.reddit_comments}\u2002"
                    f"{comments}\u2003{Emojis.reddit_users}{author}"
                )

                pages.append((post_page, image_url))

        if not paginate:
            # Return the first summery page if pagination is not required
            return first_page

        pages.insert(0, (first_page, ""))  # Using image paginator, hence settings image url to empty string
        return pages

    async def get_access_token(self) -> None:
        """
        Get a Reddit API OAuth2 access token and assign it to self.access_token.

        A token is valid for 1 hour. There will be MAX_RETRIES to get a token, after which the cog
        will be unloaded and a ClientError raised if retrieval was still unsuccessful.
        """
        for i in range(1, MAX_RETRIES + 1):
            response = await self.bot.http_session.post(
                url=f"{URL}/api/v1/access_token",
                headers=HEADERS,
                auth=self.client_auth,
                data={
                    "grant_type": "client_credentials",
                    "duration": "temporary"
                }
            )

            if response.status == 200 and response.content_type == "application/json":
                content = await response.json()
                expiration = int(content["expires_in"]) - 60  # Subtract 1 minute for leeway.
                self.access_token = AccessToken(
                    token=content["access_token"],
                    expires_at=datetime.now(tz=UTC) + timedelta(seconds=expiration)
                )

                log.debug(f"New token acquired; expires on UTC {self.access_token.expires_at}")
                return
            log.debug(
                f"Failed to get an access token: status {response.status} & content type {response.content_type}; "
                f"retrying ({i}/{MAX_RETRIES})"
            )

            await asyncio.sleep(3)

        self.bot.remove_cog(self.qualified_name)
        raise ClientError("Authentication with the Reddit API failed. Unloading the cog.")

    async def revoke_access_token(self) -> None:
        """
        Revoke the OAuth2 access token for the Reddit API.

        For security reasons, it's good practice to revoke the token when it's no longer being used.
        """
        response = await self.bot.http_session.post(
            url=f"{URL}/api/v1/revoke_token",
            headers=HEADERS,
            auth=self.client_auth,
            data={
                "token": self.access_token.token,
                "token_type_hint": "access_token"
            }
        )

        if response.status in [200, 204] and response.content_type == "application/json":
            self.access_token = None
        else:
            log.warning(f"Unable to revoke access token: status {response.status}.")

    async def fetch_posts(self, route: str, *, amount: int = 25, params: dict | None = None) -> list[dict]:
        """A helper method to fetch a certain amount of Reddit posts at a given route."""
        # Reddit's JSON responses only provide 25 posts at most.
        if not 25 >= amount > 0:
            raise ValueError("Invalid amount of subreddit posts requested.")

        # Renew the token if necessary.
        if not self.access_token or self.access_token.expires_at < datetime.now(tz=UTC):
            await self.get_access_token()

        url = f"{OAUTH_URL}/{route}"
        for _ in range(MAX_RETRIES):
            response = await self.bot.http_session.get(
                url=url,
                headers=HEADERS | {"Authorization": f"bearer {self.access_token.token}"},
                params=params
            )
            if response.status == 200 and response.content_type == "application/json":
                # Got appropriate response - process and return.
                content = await response.json()
                posts = content["data"]["children"]

                filtered_posts = [post for post in posts if not post["data"]["over_18"]]

                return filtered_posts[:amount]

            await asyncio.sleep(3)

        log.debug(f"Invalid response from: {url} - status code {response.status}, mimetype {response.content_type}")
        return []  # Failed to get appropriate response within allowed number of retries.

    async def get_top_posts(
            self, subreddit: Subreddit, time: str = "all", amount: int = 5, paginate: bool = False
    ) -> Embed | list[tuple]:
        """
        Get the top amount of posts for a given subreddit within a specified timeframe.

        A time of "all" will get posts from all time, "day" will get top daily posts and "week" will get the top
        weekly posts.

        The amount should be between 0 and 25 as Reddit's JSON requests only provide 25 posts at most.
        """
        embed = Embed()

        posts = await self.fetch_posts(
            route=f"{subreddit}/top",
            amount=amount,
            params={"t": time}
        )
        if not posts:
            embed.title = random.choice(ERROR_REPLIES)
            embed.colour = Colour.red()
            embed.description = (
                "Sorry! We couldn't find any SFW posts from that subreddit. "
                "If this problem persists, please let us know."
            )

            return embed

        if paginate:
            return self.build_pagination_pages(posts, paginate=True)

        # Use only starting summary page for #reddit channel posts.
        embed.description = self.build_pagination_pages(posts, paginate=False)
        embed.colour = Colour.og_blurple()
        return embed

    @loop()
    async def auto_poster_loop(self) -> None:
        """Post the top 5 posts daily, and the top 5 posts weekly."""
        # once d.py get support for `time` parameter in loop decorator,
        # this can be removed and the loop can use the `time=datetime.time.min` parameter
        now = datetime.now(tz=UTC)
        tomorrow = now + timedelta(days=1)
        midnight_tomorrow = tomorrow.replace(hour=0, minute=0, second=0)

        await sleep_until(midnight_tomorrow)

        if not self.webhook:
            await self.bot.fetch_webhook(RedditConfig.webhook)

        if datetime.now(tz=UTC).weekday() == 0:
            await self.top_weekly_posts()
            # if it's a monday send the top weekly posts

        for subreddit in RedditConfig.subreddits:
            top_posts = await self.get_top_posts(subreddit=subreddit, time="day")
            username = sub_clyde(f"{subreddit} Top Daily Posts")
            message = await self.webhook.send(username=username, embed=top_posts, wait=True)

            if message.channel.is_news():
                await message.publish()

    async def top_weekly_posts(self) -> None:
        """Post a summary of the top posts."""
        for subreddit in RedditConfig.subreddits:
            # Send and pin the new weekly posts.
            top_posts = await self.get_top_posts(subreddit=subreddit, time="week")
            username = sub_clyde(f"{subreddit} Top Weekly Posts")
            message = await self.webhook.send(wait=True, username=username, embed=top_posts)

            if subreddit.lower() == "r/python":
                if not self.channel:
                    log.warning("Failed to get #reddit channel to remove pins in the weekly loop.")
                    return

                # Remove the oldest pins so that only 12 remain at most.
                pins = await self.channel.pins()

                while len(pins) >= 12:
                    await pins[-1].unpin()
                    del pins[-1]

                await message.pin()

                if message.channel.is_news():
                    await message.publish()

    @group(name="reddit", invoke_without_command=True)
    async def reddit_group(self, ctx: Context) -> None:
        """View the top posts from various subreddits."""
        await self.bot.invoke_help_command(ctx)

    @reddit_group.command(name="top")
    async def top_command(self, ctx: Context, subreddit: Subreddit = "r/Python") -> None:
        """Send the top posts of all time from a given subreddit."""
        async with ctx.typing():
            pages = await self.get_top_posts(subreddit=subreddit, time="all", paginate=True)

        if isinstance(pages, Embed):
            # If get_top_posts hits an error, then an error embed is returned, not actual posts.
            await ctx.send(embed=pages)
            return

        await ctx.send(f"Here are the top {subreddit} posts of all time!")
        embed = Embed(
            color=Colour.og_blurple()
        )

        await ImagePaginator.paginate(pages, ctx, embed)

    @reddit_group.command(name="daily")
    async def daily_command(self, ctx: Context, subreddit: Subreddit = "r/Python") -> None:
        """Send the top posts of today from a given subreddit."""
        async with ctx.typing():
            pages = await self.get_top_posts(subreddit=subreddit, time="day", paginate=True)

        await ctx.send(f"Here are today's top {subreddit} posts!")
        embed = Embed(
            color=Colour.og_blurple()
        )

        await ImagePaginator.paginate(pages, ctx, embed)

    @reddit_group.command(name="weekly")
    async def weekly_command(self, ctx: Context, subreddit: Subreddit = "r/Python") -> None:
        """Send the top posts of this week from a given subreddit."""
        async with ctx.typing():
            pages = await self.get_top_posts(subreddit=subreddit, time="week", paginate=True)

        await ctx.send(f"Here are this week's top {subreddit} posts!")
        embed = Embed(
            color=Colour.og_blurple()
        )

        await ImagePaginator.paginate(pages, ctx, embed)

    @has_any_role(*STAFF_ROLES)
    @reddit_group.command(name="subreddits", aliases=("subs",))
    async def subreddits_command(self, ctx: Context) -> None:
        """Send a paginated embed of all the subreddits we're relaying."""
        embed = Embed()
        embed.title = "Relayed subreddits."
        embed.colour = Colour.og_blurple()

        await LinePaginator.paginate(
            RedditConfig.subreddits,
            ctx, embed,
            footer_text="Use the reddit commands along with these to view their posts.",
            empty=False,
            max_lines=15
        )


async def setup(bot: Bot) -> None:
    """Load the Reddit cog."""
    if not RedditConfig.secret or not RedditConfig.client_id:
        log.warning("Credentials not provided, cog not loaded.")
        return
    await bot.add_cog(Reddit(bot))
