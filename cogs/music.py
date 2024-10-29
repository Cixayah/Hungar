import discord
from discord import app_commands
from discord.ext import commands
import yt_dlp
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import asyncio
import os
import random
from dotenv import load_dotenv
from discord.ui import View, Button

# Carrega as variáveis do .env
load_dotenv()

# Configurações do FFmpeg para reconexão
FFMPEG_OPTIONS = {
    'options': '-vn -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -http_persistent 1 -reconnect_at_eof 1 -fflags +genpts -use_wallclock_as_timestamps 1'
}

# Configurações do yt_dlp com aumento do timeout de conexão
YDL_OPTIONS = {
    'format': 'bestaudio',
    'noplaylist': True,
    'socket_timeout': 60,
    'rm-cache-dir': True
}

# Substitua pelos seus CLIENT_ID e CLIENT_SECRET
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')

# Autenticação no Spotify
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET
))

class QueueView(View):
    def __init__(self, bot, interaction):
        super().__init__(timeout=None)
        self.bot = bot
        self.interaction = interaction
        self.page = 0

    async def update_message(self):
        start = self.page * 10
        end = start + 10
        tracks = self.bot.get_cog('MusicBot').queue[start:end]
        total_pages = (len(self.bot.get_cog('MusicBot').queue) - 1) // 10 + 1

        queue_message = "\n".join([f"{i+1}. {track}" for i, track in enumerate(tracks, start=start)])
        content = f"**Fila de músicas:**\n{queue_message}\n\nPágina {self.page + 1}/{total_pages}"
        await self.interaction.edit_original_response(content=content, view=self)

    @discord.ui.button(label="Anterior", style=discord.ButtonStyle.primary)
    async def previous_button(self, interaction: discord.Interaction, button: Button):
        if self.page > 0:
            self.page -= 1
            await self.update_message()

    @discord.ui.button(label="Próxima", style=discord.ButtonStyle.primary)
    async def next_button(self, interaction: discord.Interaction, button: Button):
        if (self.page + 1) * 10 < len(self.bot.get_cog('MusicBot').queue):
            self.page += 1
            await self.update_message()

class MusicBot(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.queue = []

    @staticmethod
    def get_track_info(url):
        """Extrai nome e artista de um link do Spotify ou de uma playlist, ou usa o link do YouTube diretamente."""
        yt_dlp.YoutubeDL().cache.remove()
        try:
            if "playlist" in url:
                tracks = []
                offset = 0
                while True:
                    playlist = sp.playlist_tracks(url, limit=100, offset=offset)
                    if not playlist['items']:
                        break
                    for item in playlist['items']:
                        track = item['track']
                        name = track['name']
                        artist = track['artists'][0]['name']
                        tracks.append(f"{name} {artist}")
                    offset += 100
                return tracks
            elif "open.spotify.com" in url:
                track = sp.track(url)
                name = track['name']
                artist = track['artists'][0]['name']
                return [f"{name} {artist}"]
            else:
                # Se não for Spotify, assume que é um link do YouTube
                return [url]  # Retorna o URL do YouTube diretamente
        except Exception as e:
            print(f"Erro ao buscar música: {e}")
            return None

    @app_commands.command(name="play", description="Reproduz uma música do YouTube ou Spotify.")
    async def play(self, interaction: discord.Interaction, search: str):
        await interaction.response.defer()
        # Verifica se é um link do Spotify ou YouTube e busca a música ou playlist correspondente
        track_info = self.get_track_info(search)
        if track_info is None:
            await interaction.followup.send("Não consegui buscar essa música ou playlist.", ephemeral=True)
            return
        # Adiciona todas as músicas da playlist à fila
        self.queue.extend(track_info)
        # Mostra o número de músicas adicionadas
        await interaction.followup.send(f'Adicionadas à fila: **{len(track_info)}** músicas.')
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
                await interaction.followup.send(f"Erro ao conectar ao canal de voz: {e }")
                return
        # Toca a música se nada estiver tocando
        if not interaction.guild.voice_client.is_playing():
            await self.play_next(interaction)

    async def handle_error(self, error, interaction):
        if error:
            print(f"Erro durante a reprodução: {error}")
        await self.play_next(interaction)

    async def play_next(self, interaction: discord.Interaction):
        if interaction.guild.voice_client and interaction.guild.voice_client.is_connected():
            if self.queue:
                track_info = self.queue.pop(0)
                url = track_info if track_info.startswith('http') else f"ytsearch:{track_info}"
                with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                    info = ydl.extract_info(url, download=False)
                    if 'entries' in info:
                        info = info['entries'][0]
                    url = info['url']
                    title = info['title']
                    source = discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS)
                    interaction.guild.voice_client.play(
                        source, after=lambda _: self.bot.loop.create_task(self.play_next(interaction))
                    )
                    # Enviar mensagem de "tocando agora" usando um try-except para capturar erros
                    try:
                        await interaction.channel.send(f'Tocando agora: **{title}**')
                    except discord.HTTPException as e:
                        print(f"Erro ao enviar mensagem: {e}")
            else:
                await interaction.channel.send("A fila está vazia!")

    @app_commands.command(name="shuffle", description="Embaralha a fila de músicas.")
    async def shuffle(self, interaction: discord.Interaction):
        random.shuffle(self.queue)
        await interaction.response.send_message("A fila foi embaralhada!")

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

    @app_commands.command(name="stop", description="Para a música atual e limpa a fila.")
    async def stop(self, interaction: discord.Interaction):
        if interaction.guild.voice_client:
            interaction.guild.voice_client.stop()  # Para a música atual
            self.queue.clear()  # Limpa a fila
            await interaction.response.send_message("Música parada e fila limpa!")
        else:
            await interaction.response.send_message("O bot não está tocando música no momento.")

    @app_commands.command(name="leave", description="Remove o bot do canal de voz.")
    async def leave(self, interaction: discord.Interaction):
        if interaction.guild.voice_client:
            await interaction.guild.voice_client.disconnect()
            await interaction.response.send_message("Saí do canal de voz!")
        else:
            await interaction.response.send_message("O bot não está em um canal de voz.")

    @app_commands.command(name="queue", description="Exibe a fila de músicas.")
    async def queue(self, interaction: discord.Interaction):
        view = QueueView(self.bot, interaction)
        await interaction.response.send_message(content="Aqui está a fila de músicas.", view=view, ephemeral=True)
        await view.update_message()  # Atualiza a mensagem imediatamente após o envio

async def setup(bot: commands.Bot):
    await bot.add_cog(MusicBot(bot))
