import os
import discord
from discord import app_commands
from discord.ext import commands
from openai import AsyncOpenAI

# Inicializa o cliente OpenRouter
client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

async def generate_text(prompt: str, model: str = "google/gemini-2.0-flash-001") -> str:
    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "user", "content": prompt}
        ],
    )
    return response.choices[0].message.content


class OpenRouter(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="gpt", description="Gera um texto com base no prompt usando OpenRouter.")
    @app_commands.describe(
        prompt="O que você quer perguntar?",
        model="Modelo a usar (opcional)"
    )
    async def ai_command(
        self,
        interact: discord.Interaction,
        prompt: str,
        model: str = "google/gemini-2.0-flash-001"
    ):
        await interact.response.defer()
        try:
            generated_text = await generate_text(prompt, model)

            if len(generated_text) > 2000:
                generated_text = generated_text[:1997] + "..."

            await interact.followup.send(generated_text)
        except Exception as e:
            await interact.followup.send(f"Erro ao gerar texto: {e}")


async def setup(bot):
    await bot.add_cog(OpenRouter(bot))