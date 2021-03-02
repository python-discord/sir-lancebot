import asyncio
import logging
import random
from unsplash.api import Api
from unsplash.auth import Auth

import discord
from discord.ext import commands

log = logging.getLogger(__name__)

class EarthPhotos(commands.Cog):
    """This cog contains the command for earth photos."""
    
    def init(self, bot: commands.Bot):
        self.bot = bot
        self.current_channel = None
        
    @commands.command(aliases=["earth"])
    async def earth_photos(self, ctx: commands.Context):
        """
        Returns a random photo of earth.
        """
        
        
        
        
