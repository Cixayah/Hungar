import discord
from discord import app_commands
from discord.ext import commands


class Math(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()

    @app_commands.command(description='Some dois números')
    async def somar(self, interact: discord.Interaction, n1: float, n2: float):
        await interact.response.send_message(
            f"O resultado da soma entre {n1} + {n2} é igual a {n1+n2}"
        )

    @app_commands.command(description='Subtraia dois números')
    async def subtrair(self, interact: discord.Interaction, n1: float, n2: float):
        await interact.response.send_message(
            f"O resultado da subtração entre {n1} - {n2} é igual a {n1 - n2}"
        )

    @app_commands.command(description='Multiplique dois números')
    async def multiplicar(self, interact: discord.Interaction, n1: float, n2: float):
        await interact.response.send_message(
            f"O resultado da multiplicação entre {n1} x {n2} é igual a {n1 * n2}"
        )

    @app_commands.command(description='Divida dois números')
    async def dividir(self, interact: discord.Interaction, n1: float, n2: float):
        if n2 != 0:
            await interact.response.send_message(
                f"O resultado da divisão entre {n1} ÷ {n2} é igual a {n1 / n2}"
            )
        else:
            await interact.response.send_message("Não é possível dividir por zero.")

    @app_commands.command(description='Calcule uma porcentagem de um valor')
    async def porcentagem(self, interact: discord.Interaction, percent: float, value: float):
        result = (percent / 100) * value
        await interact.response.send_message(
            f"{percent}% de {value} é igual a {result}"
        )

async def setup(bot):
    await bot.add_cog(Math(bot))
