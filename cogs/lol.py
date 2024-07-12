import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
import os, requests

load_dotenv()


class Lol(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()
        self.api_key = os.getenv("RIOT_API_KEY")  # API Key da Riot Games

    # Build
    @app_commands.command(description="Envia o link da build do campeão fornecido")
    @app_commands.describe(champion="Nome do campeão")
    async def build(self, interact: discord.Interaction, champion: str):
        champion_formatted = champion.capitalize()  # Primeira letra maiúscula
        build_link = f"https://leagueofgraphs.com/champions/builds/{champion}/master"
        await interact.response.send_message(
            f"Aqui está o link da build para **{champion_formatted}**:\n{build_link}"
        )

    # Counters
    @app_commands.command(description="Envia o link dos counters do campeão fornecido")
    @app_commands.describe(champion="Nome do campeão")
    async def counters(self, interact: discord.Interaction, champion: str):
        champion_formatted = champion.capitalize()  # Primeira letra maiúscula
        counters_link = f"https://leagueofgraphs.com/champions/counters/{champion}"
        await interact.response.send_message(
            f"Aqui está o link dos counters para **{champion_formatted}**:\n{counters_link}"
        )

    # Futuras novas funções abaixo


async def setup(bot):
    await bot.add_cog(Lol(bot))
