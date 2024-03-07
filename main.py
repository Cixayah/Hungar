#Bibliotecas do Python
import discord
from discord.ext import commands
from discord import app_commands
#Permissões do Bot
perms = discord.Intents.default()
perms.members = True
perms.message_content = True
#Prefixo do bot (Não altere, deixa "/" por padrão do discord)
bot = commands.Bot(command_prefix="/", intents=perms)


@bot.tree.command(description="Responde com: Opa,[seu nome] bão?")
async def eai(interact:discord.Interaction):
    await interact.response.send_message(f'Opa {interact.user.name}, bão?', ephemeral=True)
    
#Eventos do bot
@bot.event
async def on_member_remove(member:discord.Member):
    channel = bot.get_channel(602254582118350868)
    await channel.send(f"{member.display_name} cornão saiu do server!")
     
@bot.event #Verificação se o bot ficou online.
async def on_ready():
    await bot.tree.sync()
    print("Gol do Yuri Alberto!")

bot.run(token)