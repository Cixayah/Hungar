import discord
from discord import app_commands
from discord.ext import commands

class Messages(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()
        
    @commands.Cog.listener()
    async def on_message(self, msg:discord.Message):
        if msg.author ==self.bot.user:
          await msg.add_reaction('👾')
          
    @app_commands.command(description='Responde com: Opa, [seu nome] bão?')
    async def eai(self, interact: discord.Interaction ):
        # Responde a uma interação com uma mensagem efêmera
        await interact.response.send_message(f'Opa {interact.user.name}, bão? Testando 2803')     #, ephemeral=True após àspas para mensagem privada
async def setup(bot):
    await bot.add_cog(Messages(bot))
