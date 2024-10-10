import discord
from discord import app_commands
from discord.ext import commands
import asyncio


class DeleteMessagesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()

    @app_commands.command(
        name="cleanup",
        description="Exclui um número específico de mensagens do canal (máximo 100)",
    )
    @app_commands.describe(amount="Número de mensagens a serem excluídas (máximo 100)")
    async def delete_messages(self, interact: discord.Interaction, amount: int):
        # Limita o número de mensagens a 100
        if amount > 100:
            await interact.response.send_message(
                "O número máximo de mensagens que podem ser excluídas é 100.",
                ephemeral=True,
            )
            return

        # Verifica se o usuário é o permitido
        if interact.user.id != 270943487300599808:
            await interact.response.send_message(
                "Você não tem permissão para usar este comando.", ephemeral=True
            )
            return

        await interact.response.send_message(
            "Iniciando a exclusão de mensagens...", ephemeral=True
        )

        channel = interact.channel
        messages_deleted = 0

        async for message in channel.history(limit=amount):
            await message.delete()
            messages_deleted += 1
            await asyncio.sleep(2)  # Espera 2 segundos entre as exclusões

        await interact.followup.send(
            f"{messages_deleted} mensagens foram excluídas com sucesso.", ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(DeleteMessagesCog(bot))
