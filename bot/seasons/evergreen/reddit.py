import asyncio
import logging
import random
import discord

from collections import deque

from discord.ext import commands
from discord.ext import buttons
from discord.ext.commands.cooldowns import BucketType

log = logging.getLogger(__name__)


class Paginator(buttons.Paginator):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class Reddit(commands.Cog):
	"""Fetches reddit posts."""
	def __init__(self, bot):
		self.bot = bot
		self.img_cache = deque(maxlen=10)
	# 	self.cache_clear_task = bot.loop.create_task(self.clear_cache())

	# async def clear_cache(self):
	# 	self.img_cache.clear()
	# 	await asyncio.sleep(43200)  # clear cache every 12 hours

	async def fetch(self, session, url):
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
	async def get_reddit(self, ctx, subreddit='python', sort="hot"):
		"""
		Fetch reddit posts by using this command.
		Gets a post from r/dndmemes by default.
		"""
		pages=[]
		sort_list = ["hot", "new", "top", "rising"]
		if sort.lower() not in sort_list:
			await ctx.send(f"Invalid sorting: {sort}\nUsing default sorting: `Hot`")
			sort = "hot"

		session = self.bot.http_session
		data = await self.fetch(session, f'https://www.reddit.com/r/{subreddit}/{sort}/.json')

		try:
			posts = data["data"]["children"]
		except KeyError:
			return await ctx.send('Subreddit not found!')
		if not posts:
			return await ctx.send('No posts available!')

		if posts[1]["data"]["over_18"] == True:
			return await ctx.send("You cannot access this Subreddit.")

		upvote_emoji = self.bot.get_emoji(565557799040319508)
		comment_emoji = self.bot.get_emoji(565576076483624960)
		user_emoji = "🎅"

		embed_titles = discord.Embed(colour=0xf9f586)
		embed_titles.title = f"Posts from {posts[0]['data']['subreddit']} Subreddit\n"
		embed_titles.description = ""

		random_posts = []
		while True:
			if len(random_posts) == 5:
				break
			rand_post = random.choice(posts)
			if rand_post not in random_posts:
				random_posts.append(rand_post)


		for i, post in enumerate(random_posts, start=1):
			post_title = post["data"]["title"][0:50]
			post_url = post['data']['url']
			if post_title == "":
				post_title = "No Title."
			elif post_title == post_url:
				post_title = "Title is itself a link."

			embed_titles.description += f"**{i}.**[{post_title}]({post_url})\n"
			post_stats = (
				f'{upvote_emoji}{post["data"]["ups"]}  '
				f'{comment_emoji}{post["data"]["num_comments"]}  '
				f'{user_emoji}{post["data"]["author"]}\n\n'
						  )

			embed_titles.description += post_stats
			new_embed = discord.Embed()
			new_embed.title = post_title + "\n"
			new_embed.description = post_stats + "\n\n"
			new_embed.description = post['data']['selftext'][0:100]

			if post["data"]["media_embed"] != {}:
				content = post["data"]["media_embed"]["content"]
				i1 = content.index("src")
				i2 = content.index("frameborder")
				print(content)
				print(i1, i2)
				imageURL = content[i1+4:i2]
				print(imageURL)
				# new_embed.set_image(url=imageURL)

			new_embed.url = post_url
			pages.append(new_embed)

		pages.append(embed_titles)
		pages.reverse()
		embed = Paginator(embed=True, timeout=200, use_defaults=True,
                              extra_pages=pages)

		await embed.start(ctx)


def setup(bot):
	bot.add_cog(Reddit(bot))
	log.debug('Loaded')
