# Bibliotecas do Python
import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
# Permissões do Bot
perms = discord.Intents.default()
perms.members = True
perms.message_content = True
# .env
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
# Prefixo do bot (Não altere, deixe "/" por padrão do discord)
bot = commands.Bot(command_prefix="/", intents=perms)

@bot.command()
async def syncro(ctx: commands.Context):
    # IDs dos membros autorizados a usar o comando
    allowed_ids = [270943487300599808, 223614228903231488, 476897909565292544]

    # Verifica se o autor do comando está na lista de IDs autorizados
    if ctx.author.id in allowed_ids:
        # Responde com o número total de comandos
        await ctx.reply(f'Total de comandos registrados: {len(bot.commands)}')
    else:
        # Responde se o autor não estiver autorizado
        await ctx.reply('Apenas a equipe pode usar este comando!')

@bot.command(description='Responde com: Opa, [seu nome] bão?')
async def eai(ctx: commands.Context):
    await ctx.send(f'Opa {ctx.author.name}, bão?')

@bot.command(description='Soma dois números')
async def somar(ctx: commands.Context, number_one: float, number_two: float):
    result = number_one + number_two
    await ctx.send(f'A soma entre {number_one} + {number_two} é igual a {result}.')

# Eventos do bot
@bot.event
async def on_member_remove(member: discord.Member):
    channel = bot.get_channel(602254582118350868)
    await channel.send(f"{member.display_name} cornão saiu do server!")

@bot.event  # Verificação se o bot ficou online.
async def on_ready():
    print("Gol do Yuri Alberto!")

bot.run(TOKEN)
