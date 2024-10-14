import discord
from discord import app_commands
from discord.ext import commands
import yt_dlp
import asyncio  # Importando asyncio

FFMPEG_OPTIONS = {'options': '-vn'}
YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist': True}

class MusicBot(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.queue = []

    @app_commands.command(name="play", description="Reproduz uma música do YouTube.")
    async def play(self, interaction: discord.Interaction, search: str):
        # Verifica se o usuário está em um canal de voz
        voice_channel = interaction.user.voice.channel if interaction.user.voice else None
        if not voice_channel:
            await interaction.response.send_message("Você precisa estar em um canal de voz!", ephemeral=True)
            return

        # Conecta ao canal de voz, se necessário
        if not interaction.guild.voice_client:
            try:
                await voice_channel.connect()
                await asyncio.sleep(5)  # Aguarda um momento para garantir a conexão
                await interaction.followup.send("Conectado ao canal de voz!")  # Log de conexão
            except Exception as e:
                await interaction.response.send_message(f"Ocorreu um erro ao tentar conectar ao canal de voz: {e}")
                return

        await interaction.response.defer()  # Defer para ganhar tempo na resposta
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(f"ytsearch:{search}", download=False)
            if 'entries' in info:
                info = info['entries'][0]
            url = info['url']
            title = info['title']
            self.queue.append((url, title))
            await interaction.followup.send(f'Adicionado à fila: **{title}**')

        # Verifica novamente se o bot está conectado
        if interaction.guild.voice_client.is_connected() and not interaction.guild.voice_client.is_playing():
            await self.play_next(interaction)

    async def play_next(self, interaction: discord.Interaction):
        # Verifica se o bot está conectado ao canal de voz
        if interaction.guild.voice_client and interaction.guild.voice_client.is_connected():
            if self.queue:
                url, title = self.queue.pop(0)
                source = discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS)
                interaction.guild.voice_client.play(
                    source, after=lambda _: self.bot.loop.create_task(self.play_next(interaction))
                )
                await interaction.followup.send(f'Tocando agora: **{title}**')
            else:
                await interaction.followup.send("A fila está vazia!")
        else:
            await interaction.followup.send("O bot não está conectado ao canal de voz.")

    @app_commands.command(name="skip", description="Pula para a próxima música.")
    async def skip(self, interaction: discord.Interaction):
        if interaction.guild.voice_client and interaction.guild.voice_client.is_playing():
            interaction.guild.voice_client.stop()
            await interaction.response.send_message("Música pulada ⏭")
        else:
            await interaction.response.send_message("Não há música tocando no momento.")

    @app_commands.command(name="leave", description="Remove o bot do canal de voz.")
    async def leave(self, interaction: discord.Interaction):
        if interaction.guild.voice_client:
            await interaction.guild.voice_client.disconnect()
            await interaction.response.send_message("Saí do canal de voz! 👋")
        else:
            await interaction.response.send_message("O bot não está em um canal de voz.")

async def setup(bot: commands.Bot):
    await bot.add_cog(MusicBot(bot))
