import json
import logging
import os
import random

import aiohttp
import discord
import requests
from discord.ext import commands

from bot.constants import Colours, ERROR_REPLIES

log = logging.getLogger(__name__)
api_key = os.environ['NASA_API']


async def fetch(session: aiohttp.ClientSession, url: str) -> str:
    """Helps to get JSON from an API."""
    async with session.get(url) as response:
        return await response.text()


class Space(commands.Cog):
    """A cog to get some amazing looking space pictures using NASA API."""

    def __init__(self, client: commands.bot):
        self.client = client

    @commands.command(description='Astronomy Picture of the Day')
    async def apod(self, ctx: commands.context) -> None:
        """Get a cool looking picture from NASA along it's description. That changes every day."""
        async with aiohttp.ClientSession() as session:
            log.info(f'{ctx.author} used apod command.')
            url = f'https://api.nasa.gov/planetary/apod?api_key={api_key}'
            response = requests.get(url)
            headers = response.headers

            if int(headers['X-RateLimit-Remaining']) <= 1:
                embed = discord.Embed(
                    title=random.choice(ERROR_REPLIES),
                    description='API request limit reached for now. Maybe you can try again after some time ?',
                    color=Colours.soft_red
                )
                await ctx.send(embed=embed)
                return
            html = await fetch(session, url)
            data = json.loads(html)
            embed = discord.Embed(
                title=data['title'],
                description=data['explanation'],
                color=Colours.blue
            )
            embed.set_image(url=data['hdurl'])
            embed.set_footer(text=data['date'])
            await ctx.send(embed=embed)

    @commands.command(description='Random Space Picture.')
    async def nasa(self, ctx: commands.context) -> None:
        """Get a random fact about NASA along with picture."""
        log.info(f'{ctx.author} used nasa command.')

        async with aiohttp.ClientSession() as session:
            html = await fetch(session, 'https://images-api.nasa.gov/search?media_type=image')
            data = json.loads(html)
            random_no = random.randint(1, len(data['collection']['items']))
            embed = discord.Embed(
                title=data['collection']['items'][random_no]['data'][0]['title'],
                description=data['collection']['items'][random_no]['data'][0]['description'],
                color=Colours.blue
            )
            embed.set_image(url=data['collection']['items'][random_no]['links'][0]['href'])
            embed.set_footer(text=data['collection']['items'][random_no]['data'][0]['date_created'])
            await ctx.send(embed=embed)

    @commands.command(description='Random Earth Picture.')
    async def earth(self, ctx: commands.context) -> None:
        """Get a random picture of Earth using NASA's API."""
        log.info(f'{ctx.author} used earth command.')
        async with aiohttp.ClientSession() as session:
            html = await fetch(session, 'https://epic.gsfc.nasa.gov/api/natural/all')
            data = json.loads(html)
            random_no = random.randint(0, len(data))
            date = data[random_no]['date']
            html = await fetch(session, f'https://epic.gsfc.nasa.gov/api/natural/date/{date}')
            data = json.loads(html)
            random_no = random.randint(1, 10)
            caption = data[random_no]['caption']
            image = data[random_no]['image']
            date = data[random_no]['date']
            url_date = date[:-9]
            url_date = url_date.replace('-', '/')
            embed = discord.Embed(
                title=caption,
                color=Colours.blue
            )
            embed.set_image(url=f'https://epic.gsfc.nasa.gov/archive/natural/{url_date}/jpg/{image}.jpg')
            embed.set_footer(text=date)
            await ctx.send(embed=embed)

    @commands.command(description="Get Random Pics from Mars's rovers. Using NASA's API.")
    async def mars(self, ctx: commands.context) -> None:
        """Get a random picture from Mars using NASA's API."""
        log.info(f'{ctx.author} used mars command.')
        async with aiohttp.ClientSession() as session:
            url = f'https://api.nasa.gov/mars-photos/api/v1/rovers/Curiosity/photos?sol=1000&api_key={api_key}'
            response = requests.get(url)  # Only Curiosity have Curious pictures.
            headers = response.headers

            if int(headers['X-RateLimit-Remaining']) <= 1:
                embed = discord.Embed(
                    title=random.choice(ERROR_REPLIES),
                    description='API request limit reached for now. Maybe you can try again after some time ?',
                    color=Colours.soft_red
                )
                await ctx.send(embed=embed)
                return

            html = await fetch(session, url)
            data = json.loads(html)
            random_no = random.randint(0, len(data['photos']))
            embed = discord.Embed(
                title=data['photos'][random_no]['rover']['name'],
                description=f"Camera- {data['photos'][random_no]['camera']['full_name']}",
                color=Colours.blue
            )
            embed.set_image(url=data['photos'][random_no]['img_src'])
            embed.set_footer(text=data['photos'][random_no]['earth_date'])
            await ctx.send(embed=embed)


def setup(client: commands.bot) -> None:
    """Load the Space cog."""
    client.add_cog(Space(client))
    log.info('Space Cog Loaded')
