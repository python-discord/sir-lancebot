import asyncio
import logging
import random
from unsplash.api import Api as uApi
from unsplash.auth import Auth as uAuth

import discord
from discord.ext import commands

from bot.constants import Tokens

log = logging.getLogger(__name__)

UnClient_id = Tokens.UNSPLASH_API

UnClient_secret = Tokens.UNSPLASH_SECRET

redirect_uri = "urn:ietf:wg:oauth:2.0:oob"

unsplash_auth = uAuth(client_id,

class EarthPhotos(commands.Cog):
    """This cog contains the command for earth photos."""
    
    def init(self, bot: commands.Bot):
        self.bot = bot
        self.current_channel = None
        
    @commands.command(aliases=["earth"])
    async def earth_photos(self, ctx: commands.Context):
        """
        Returns a random photo of earth, sourced from Unsplash.
        """
        
        
        
        
