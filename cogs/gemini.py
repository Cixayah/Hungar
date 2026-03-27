import os
import discord
from discord import app_commands
from discord.ext import commands
from google import genai  # Use the new SDK structure

# Initialize the client outside the function (more efficient)
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def generate_text(prompt):
    # New syntax for generating content
    response = client.models.generate_content(
        model='gemini-2.0-flash', 
        contents=prompt
    )
    return response.text

class Gemini(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Removed super().__init__() as commands.Cog doesn't require it 
        # unless you have specific overrides.

    @app_commands.command(name="gemini", description="Gera um texto com base no prompt usando Gemini.")
    async def gemini_command(self, interact: discord.Interaction, prompt: str):
        await interact.response.defer() 
        try:
            # Running this in a thread is usually better for blocking IO, 
            # but for simple bots, this works:
            generated_text = generate_text(prompt)
            
            if len(generated_text) > 2000:
                generated_text = generated_text[:1997] + "..."
            
            await interact.followup.send(generated_text)
        except Exception as e:
            await interact.followup.send(f"Erro ao gerar texto: {e}")

async def setup(bot):
    await bot.add_cog(Gemini(bot))