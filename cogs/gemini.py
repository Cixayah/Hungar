import os
import discord
from discord import app_commands
from discord.ext import commands
import google.generativeai as genai

# Configurando o Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def generate_text(prompt):
    model = genai.GenerativeModel('gemini-2.0-flash')
    response = model.generate_content(prompt)
    return response.text

class Gemini(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()

    @app_commands.command(name="gemini", description="Gera um texto com base no prompt usando Gemini.")
    async def gemini_command(self, interact: discord.Interaction, prompt: str):
        await interact.response.defer()  # evita timeout enquanto gera o texto
        try:
            generated_text = generate_text(prompt)
            if len(generated_text) > 2000:
                generated_text = generated_text[:1997] + "..."
            await interact.followup.send(generated_text)
        except Exception as e:
            await interact.followup.send(f"Erro ao gerar texto: {e}")

async def setup(bot):
    await bot.add_cog(Gemini(bot))
