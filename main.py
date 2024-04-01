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

async def load_cogs():
    # Carrega os módulos (cogs) do bot a partir do diretório 'cogs'
    for archive in os.listdir('cogs'):
        if archive.endswith('.py'):
            await bot.load_extension(f'cogs.{archive[:-3]}')
        
@bot.command()
async def syncro(ctx: commands.Context):
    # IDs dos membros autorizados a usar o comando
    allowed_ids = [270943487300599808, 223614228903231488, 476897909565292544]
    # cix, w7, lari

    # Verifica se o autor do comando está na lista de IDs autorizados
    if ctx.author.id in allowed_ids:
        sincs = await bot.tree.sync()
        # Responde com o número total de comandos registrados
        await ctx.reply(f'Total de comandos registrados: {len(sincs)}')
    else:
        # Responde se o autor não estiver autorizado
        await ctx.reply('Apenas a equipe pode usar este comando!')

# Eventos do bot
@bot.event
async def on_member_remove(member: discord.Member):
    # Envia uma mensagem quando um membro deixa o servidor, mencionando o perfil do membro
    channel = bot.get_channel(602254582118350868)
    mention = member.mention  # Obtém a menção do perfil do membro que saiu
    await channel.send(f"A pessoa corna {mention} saiu do server!")


@bot.event  # Verificação se o bot ficou online.
async def on_ready():
    # Carrega os módulos (cogs) quando o bot está pronto
    await load_cogs()
    print("BOT ON!")

# Inicia o bot com o token fornecido
bot.run(TOKEN)
