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
    'ffmpeg_location': '/usr/bin/ffmpeg'
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
        try:
            start = self.page * 10
            end = start + 10
            tracks = self.bot.get_cog('MusicBot').queue[start:end]
            total_pages = (len(self.bot.get_cog('MusicBot').queue) - 1) // 10 + 1

            queue_message = "\n".join([f"{i+1}. {track}" for i, track in enumerate(tracks, start=start)])
            content = f"**Fila de músicas:**\n{queue_message}\n\nPágina {self.page + 1}/{total_pages}"
            await self.interaction.edit_original_response(content=content, view=self)
        except Exception as e:
            print(f"Erro ao atualizar mensagem da fila: {e}")
            await self.interaction.edit_original_response(content="Erro ao atualizar a fila de músicas.", view=self)

    @discord.ui.button(label="Anterior", style=discord.ButtonStyle.primary)
    async def previous_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer()
        if self.page > 0:
            self.page -= 1
            await self.update_message()

    @discord.ui.button(label="Próxima", style=discord.ButtonStyle.primary)
    async def next_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer()
        if (self.page + 1) * 10 < len(self.bot.get_cog('MusicBot').queue):
            self.page += 1
            await self.update_message()

class MusicBot(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.queue = []
        self._current_player = None
        self.last_interaction = None
        self.is_playing = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 3

    async def cleanup(self):
        """Limpa o estado do bot"""
        self._current_player = None
        self.last_interaction = None
        self.queue.clear()
        self.is_playing = False
        self.reconnect_attempts = 0

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

    async def play_next(self, interaction: discord.Interaction):
        if not interaction.guild.voice_client or not interaction.guild.voice_client.is_connected():
            await self.cleanup()
            return

        if self.queue:
            try:
                self.is_playing = True
                track_info = self.queue.pop(0)
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

                            source = discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS)
                            source = discord.PCMVolumeTransformer(source, volume=1.0)

                            def after_playing(error):
                                if error:
                                    print(f"Erro durante a reprodução: {error}")
                                self.is_playing = False
                                asyncio.run_coroutine_threadsafe(
                                    self.play_next(interaction),
                                    self.bot.loop
                                )

                            if interaction.guild.voice_client:
                                interaction.guild.voice_client.play(source, after=after_playing)
                                await interaction.channel.send(f'Tocando agora: **{title}**')
                                break

                    except Exception as e:
                        print(f"Tentativa {4-retries} falhou: {str(e)}")
                        retries -= 1
                        if retries == 0:
                            await interaction.channel.send("Não foi possível reproduzir esta música após várias tentativas.")
                            self.is_playing = False
                            await self.play_next(interaction)
                        await asyncio.sleep(1)

            except Exception as e:
                print(f"Erro ao reproduzir música: {e}")
                await interaction.channel.send("Ocorreu um erro ao reproduzir esta música. Pulando para a próxima...")
                self.is_playing = False
                await self.play_next(interaction)
        else:
            self.is_playing = False
            await interaction.channel.send("A fila está vazia!")

    async def ensure_voice_connection(self, interaction: discord.Interaction):
        """Garante que o bot está conectado ao canal de voz"""
        if not interaction.guild.voice_client:
            if not interaction.user.voice:
                raise ValueError("Você precisa estar em um canal de voz!")
            
            try:
                await interaction.user.voice.channel.connect()
                self.reconnect_attempts = 0
                await asyncio.sleep(1)
            except Exception as e:
                print(f"Erro ao conectar ao canal de voz: {e}")
                self.reconnect_attempts += 1
                if self.reconnect_attempts < self.max_reconnect_attempts:
                    await asyncio.sleep(1)
                    return await self.ensure_voice_connection(interaction)
                else:
                    raise Exception("Não foi possível conectar ao canal de voz após várias tentativas.")

    @app_commands.command(name="play", description="Reproduz uma música do YouTube ou Spotify.")
    async def play(self, interaction: discord.Interaction, search: str):
        await interaction.response.defer()
        self.last_interaction = interaction

        try:
            await self.ensure_voice_connection(interaction)
            
            track_info = self.get_track_info(search)
            if track_info is None:
                await interaction.followup.send("Não consegui buscar essa música ou playlist.", ephemeral=True)
                return

            self.queue.extend(track_info)
            await interaction.followup.send(f'Adicionadas à fila: **{len(track_info)}** músicas.')

            if not self.is_playing:
                await self.play_next(interaction)

        except ValueError as ve:
            await interaction.followup.send(str(ve), ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"Ocorreu um erro: {str(e)}")
            print(f"Erro detalhado: {e}")

    @app_commands.command(name="shuffle", description="Embaralha a fila de músicas.")
    async def shuffle(self, interaction: discord.Interaction):
        if not self.queue:
            await interaction.response.send_message("A fila está vazia!")
            return
            
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
        try:
            if interaction.guild.voice_client:
                interaction.guild.voice_client.stop()
                await self.cleanup()
                await interaction.response.send_message("Música parada e fila limpa!")
            else:
                await interaction.response.send_message("O bot não está tocando música no momento.")
        except Exception as e:
            print(f"Erro ao parar música: {e}")
            await self.cleanup()
            await interaction.response.send_message("Houve um erro ao parar, mas o estado foi limpo.")

    @app_commands.command(name="leave", description="Remove o bot do canal de voz.")
    async def leave(self, interaction: discord.Interaction):
        try:
            if interaction.guild.voice_client:
                # Para qualquer música que esteja tocando
                interaction.guild.voice_client.stop()
                # Limpa o estado
                await self.cleanup()
                # Desconecta do canal
                await interaction.guild.voice_client.disconnect(force=True)
                await interaction.response.send_message("Saí do canal de voz!")
            else:
                await interaction.response.send_message("O bot não está em um canal de voz.")
        except Exception as e:
            print(f"Erro ao deixar o canal de voz: {e}")
            await self.cleanup()
            await interaction.response.send_message("Houve um erro ao sair, mas o estado foi limpo.")

    @app_commands.command(name="reconnect", description="Força a reconexão do bot")
    async def reconnect(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()
            
            if not interaction.user.voice:
                await interaction.followup.send("Você precisa estar em um canal de voz!", ephemeral=True)
                return
                
            voice_channel = interaction.user.voice.channel
            
            # Se já estiver conectado, desconecta primeiro
            if interaction.guild.voice_client:
                await interaction.guild.voice_client.disconnect(force=True)
            
            # Limpa o estado
            await self.cleanup()
            
            # Reconecta
            await voice_channel.connect()
            await interaction.followup.send("Reconectado com sucesso!")
            
        except Exception as e:
            print(f"Erro ao reconectar: {e}")
            await interaction.followup.send("Erro ao tentar reconectar. Por favor, tente novamente.")

    @app_commands.command(name="queue", description="Exibe a fila de músicas.")
    async def queue(self, interaction: discord.Interaction):
        if not self.queue:
            await interaction.response.send_message("A fila está vazia!", ephemeral=True)
            return
            
        view = QueueView(self.bot, interaction)
        await interaction.response.send_message(content="Aqui está a fila de músicas.", view=view, ephemeral=True)
        await view.update_message()

async def setup(bot: commands.Bot):
    await bot.add_cog(MusicBot(bot))