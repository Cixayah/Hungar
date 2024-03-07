import discord
from discord import app_commands
from discord.ext import commands

class Messages(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()
        
    @commands.Cog.listener()
    async def on_message(self, msg:discord.Message):
          await msg.add_reaction('👾')
    
async def setup(bot):
    await bot.add_cog(Messages(bot))