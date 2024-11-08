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

# Configurações do FFmpeg ajustadas
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn -bufsize 64k',
    'executable': '/usr/bin/ffmpeg'  # Caminho do FFmpeg no WSL
}

# Configurações do yt_dlp otimizadas
YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'socket_timeout': 120,
    'extractor_retries': 3,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
    'rm-cache-dir': True,
    'ffmpeg_location': '/usr/bin/ffmpeg'  # Adicionado o caminho do FFmpeg para o yt-dlp
}

# Configurações Spotify
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')

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
        guild_id = self.interaction.guild_id
        start = self.page * 10
        end = start + 10
        tracks = self.bot.get_cog('MusicBot').get_queue(guild_id)[start:end]
        total_pages = (len(self.bot.get_cog('MusicBot').get_queue(guild_id)) - 1) // 10 + 1

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
        guild_id = self.interaction.guild_id
        if (self.page + 1) * 10 < len(self.bot.get_cog('MusicBot').get_queue(guild_id)):
            self.page += 1
            await self.update_message()

class MusicBot(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.queues = {}
        self._current_players = {}
        self.last_interaction = None

    def get_queue(self, guild_id):
        if guild_id not in self.queues:
            self.queues[guild_id] = []
        return self.queues[guild_id]

    def add_to_queue(self, guild_id, track_info):
        self.get_queue(guild_id).extend(track_info)

    async def play_next(self, interaction: discord.Interaction):
        guild_id = interaction.guild_id
        if not interaction.guild.voice_client or not interaction.guild.voice_client.is_connected():
            return

        queue = self.get_queue(guild_id)
        if queue:
            try:
                track_info = queue.pop(0)
                url = track_info if track_info.startswith('http') else f"ytsearch:{track_info}"
                
                retries = 3
                while retries > 0:
                    try:
                        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                            info = ydl.extract_info(url, download=False)
                            if 'entries' in info:
                                info = info['entries'][0]
                            url = info['url']
                            title = info['title']

                            # Criar fonte de áudio com opções otimizadas
                            source = discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS)
                            source = discord.PCMVolumeTransformer(source, volume=1.0)

                            def after_playing(error):
                                if error:
                                    print(f"Erro durante a reprodução: {error}")
                                asyncio.run_coroutine_threadsafe(
                                    self.play_next(interaction),
                                    self.bot.loop
                                )

                            interaction.guild.voice_client.play(source, after=after_playing)
                            await interaction.channel.send(f'Tocando agora: **{title}**')
                            break

                    except Exception as e:
                        print(f"Tentativa {4-retries} falhou: {str(e)}")
                        retries -= 1
                        if retries == 0:
                            await interaction.channel.send("Não foi possível reproduzir esta música após várias tentativas.")
                            await self.play_next(interaction)
                        await asyncio.sleep(1)

            except Exception as e:
                print(f"Erro ao reproduzir música: {e}")
                await interaction.channel.send("Ocorreu um erro ao reproduzir esta música. Pulando para a próxima...")
                await self.play_next(interaction)
        else:
            await interaction.channel.send("A fila está vazia!")

    @app_commands.command(name="play", description="Reproduz uma música do YouTube ou Spotify.")
    async def play(self, interaction: discord.Interaction, search: str):
        await interaction.response.defer()
        self.last_interaction = interaction

        if not interaction.user.voice:
            await interaction.followup.send("Você precisa estar em um canal de voz!", ephemeral=True)
            return

        voice_channel = interaction.user.voice.channel
        guild_id = interaction.guild_id
        
        try:
            track_info = self.get_track_info(search)
            if track_info is None:
                await interaction.followup.send("Não consegui buscar essa música ou playlist.", ephemeral=True)
                return

            self.add_to_queue(guild_id, track_info)
            await interaction.followup.send(f'Adicionadas à fila: **{len(track_info)}** músicas.')

            if guild_id not in self._current_players or not interaction.guild.voice_client.is_playing():
                if guild_id not in self._current_players:
                    await voice_channel.connect()
                    await asyncio.sleep(1)
                self._current_players[guild_id] = True
                await self.play_next(interaction)

        except Exception as e:
            await interaction.followup.send(f"Ocorreu um erro: {str(e)}")
            print(f"Erro detalhado: {e}")

    @app_commands.command(name="shuffle", description="Embaralha a fila de músicas.")
    async def shuffle(self, interaction: discord.Interaction):
        guild_id = interaction.guild_id
        queue = self.get_queue(guild_id)
        random.shuffle(queue)
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
            interaction.guild.voice_client.stop()
            guild_id = interaction.guild_id
            self.get_queue(guild_id).clear()
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
        await view.update_message()

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
                        if track:
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
                return [url]
        except Exception as e:
            print(f"Erro ao buscar música: {e}")
            return None

async def setup(bot: commands.Bot):
    await bot.add_cog(MusicBot(bot))