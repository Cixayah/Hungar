import discord
from discord import app_commands
from discord.ext import commands


class Messages(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()

    @commands.Cog.listener()
    async def on_message(self, msg):
        # Verifica se a mensagem foi enviada pelo bot
        if msg.author == self.bot.user:
            try:
                await msg.add_reaction("👾")
            except discord.NotFound:
                pass
            except Exception as e:
                print(f"Erro ao adicionar reação: {e}")

    @app_commands.command(description="Responde com: Opa, [seu nome] bão?")
    async def eai(self, interact: discord.Interaction):
        # Responde a uma interação com uma mensagem efêmera
        await interact.response.send_message(
            f"Opa {interact.user.name}, bão?"
        )  # , ephemeral=True após àspas para mensagem privada

    @app_commands.command(description="Envia o link da playlist do Spotify")
    async def aminho(self, interact: discord.Interaction):
        # Responde a uma interação com o link da playlist do Spotify
        await interact.response.send_message(
            f"Aqui está o link da nossa playlist:\n```https://open.spotify.com/playlist/723PwpAlSlPF6hq7uoEZtT?si=6252377f5eb14ae8```"
        )


async def setup(bot):
    await bot.add_cog(Messages(bot))
