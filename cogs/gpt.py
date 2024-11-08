import discord
from discord import app_commands
from discord.ext import commands
from langchain_openai import ChatOpenAI  # Updated import path
from langchain.prompts import PromptTemplate

class GPTCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.chat_model = ChatOpenAI(temperature=0.7)
        self.prompt = PromptTemplate(
            input_variables=["query"],
            template="Here is a response to your query: {query}",
        )
        super().__init__()

    @app_commands.command(name="gpt", description="Chat with the GPT-3 language model")
    async def gpt(self, interaction: discord.Interaction, *, query: str):
        async with interaction.channel.typing():
            formatted_prompt = self.prompt.format(query=query)
            response = self.chat_model(formatted_prompt)
            await interaction.response.send_message(response)

async def setup(bot):
    await bot.add_cog(GPTCog(bot))
