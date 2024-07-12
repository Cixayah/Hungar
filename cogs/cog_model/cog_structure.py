# Apenas uma estrutura para o modelo cog

import discord
from discord import app_commands
from discord.ext import commands


class class_name(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()

    @app_commands.command()  # precisa estar dentro da classe
    async def command_name(self, interact: discord.Interaction):
        await interact.response.send_message(
            f"This is just {interact.user.name} a exemple"
        )  # , ephemeral=True após àspas para mensagem privada


async def setup(bot):
    await bot.add_cog()
