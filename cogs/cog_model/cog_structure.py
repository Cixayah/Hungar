# Apenas uma estrutura para o modelo cog

import discord
from discord import app_commands
from discord.ext import commands

class Messages(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()
#    @app_commands.command()  #precisa estar dentro da classe 
async def setup(bot):
    await bot.add_cog()