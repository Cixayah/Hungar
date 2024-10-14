import discord
from discord import app_commands
from discord.ext import commands
import yt_dlp
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import asyncio
import os
from dotenv import load_dotenv  # Importa o dotenv para carregar as variáveis do .env

# Carrega as variáveis do .env
load_dotenv()

FFMPEG_OPTIONS = {'options': '-vn'}
YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist': True}

# Substitua pelos seus CLIENT_ID e CLIENT_SECRET
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')

# Autenticação no Spotify
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET
))

class MusicBot(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.queue = []

    def get_track_info(self, spotify_url):
        """Extrai nome e artista de um link do Spotify."""
        try:
            track = sp.track(spotify_url)
            name = track['name']
            artist = track['artists'][0]['name']
            return f"{name} {artist}"
        except Exception as e:
            print(f"Erro ao buscar música no Spotify: {e}")
            return None

    @app_commands.command(name="play", description="Reproduz uma música do YouTube ou Spotify.")
    async def play(self, interaction: discord.Interaction, search: str):
        await interaction.response.defer()  # Adiciona defer logo no início

        # Verifica se é um link do Spotify e busca a música correspondente
        if "open.spotify.com/track" in search:
            search = self.get_track_info(search)
            if not search:
                await interaction.followup.send("Não consegui buscar essa música no Spotify.", ephemeral=True)
                return

        # Verifica se o usuário está em um canal de voz
        voice_channel = interaction.user.voice.channel if interaction.user.voice else None
        if not voice_channel:
            await interaction.followup.send("Você precisa estar em um canal de voz!", ephemeral=True)
            return

        # Conecta ao canal de voz, se necessário
        if not interaction.guild.voice_client:
            try:
                await voice_channel.connect()
                await asyncio.sleep(1)
                await interaction.followup.send("Conectado ao canal de voz!")
            except Exception as e:
                await interaction.followup.send(f"Erro ao conectar ao canal de voz: {e}")
                return

        # Busca a música no YouTube
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(f"ytsearch:{search}", download=False)
            if 'entries' in info:
                info = info['entries'][0]
            url = info['url']
            title = info['title']
            self.queue.append((url, title))
            await interaction.followup.send(f'Adicionado à fila: **{title}**')

        # Toca a música se nada estiver tocando
        if not interaction.guild.voice_client.is_playing():
            await self.play_next(interaction)

    async def play_next(self, interaction: discord.Interaction):
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

    @app_commands.command(name="pause", description="Pausa a música atual.")
    async def pause(self, interaction: discord.Interaction):
        if interaction.guild.voice_client and interaction.guild.voice_client.is_playing():
            interaction.guild.voice_client.pause()
            await interaction.response.send_message("Música pausada ⏸️")
        else:
            await interaction.response.send_message("Não há música tocando no momento.")

    @app_commands.command(name="resume", description="Retoma a música pausada.")
    async def resume(self, interaction: discord.Interaction):
        if interaction.guild.voice_client and interaction.guild.voice_client.is_paused():
            interaction.guild.voice_client.resume()
            await interaction.response.send_message("Música retomada ▶️")
        else:
            await interaction.response.send_message("A música não está pausada.")

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
