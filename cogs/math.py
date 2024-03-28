import discord
from discord import app_commands
from discord.ext import commands


class Math(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()

    @app_commands.command(description="Some dois números")
    async def somar(self, interact: discord.Interaction, n1: float, n2: float):
        if not isinstance(n1, float) or not isinstance(n2, float):
            await interact.response.send_message("Por favor, insira apenas números válidos.")
            return

        await interact.response.send_message(
            f"O resultado da soma entre {n1} + {n2} é igual a {n1 + n2}"
        )

    @app_commands.command(description="Subtraia dois números")
    async def subtrair(self, interact: discord.Interaction, n1: float, n2: float):
        if not isinstance(n1, float) or not isinstance(n2, float):
            await interact.response.send_message("Por favor, insira apenas números válidos.")
            return

        await interact.response.send_message(
            f"O resultado da subtração entre {n1} - {n2} é igual a {n1 - n2}"
        )

    @app_commands.command(description="Multiplique dois números")
    async def multiplicar(self, interact: discord.Interaction, n1: float, n2: float):
        if not isinstance(n1, float) or not isinstance(n2, float):
            await interact.response.send_message("Por favor, insira apenas números válidos.")
            return

        await interact.response.send_message(
            f"O resultado da multiplicação entre {n1} x {n2} é igual a {n1 * n2}"
        )

    @app_commands.command(description="Divida dois números")
    async def dividir(self, interact: discord.Interaction, n1: float, n2: float):
        if not isinstance(n1, float) or not isinstance(n2, float):
            await interact.response.send_message("Por favor, insira apenas números válidos.")
            return

        if n2 == 0:
            await interact.response.send_message("Não é possível dividir por zero.")
            return

        await interact.response.send_message(
            f"O resultado da divisão entre {n1} ÷ {n2} é igual a {n1 / n2}"
        )

    @app_commands.command(description="Calcule uma porcentagem de um valor")
    async def porcentagem(self, interact: discord.Interaction, percent: float, value: float):
        if not isinstance(percent, float) or not isinstance(value, float):
            await interact.response.send_message("Por favor, insira apenas números válidos.")
            return

        if percent < 0 or percent > 100:
            await interact.response.send_message("A porcentagem deve estar entre 0 e 100.")
            return

        result = (percent / 100) * value
        await interact.response.send_message(f"{percent}% de {value} é igual a {result}")


async def setup(bot):
    await bot.add_cog(Math(bot))
