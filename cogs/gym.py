import discord
from discord import app_commands
from discord.ext import commands


class GymCalculatorCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()

    @app_commands.command(
        name="gym",
        description="Calcula o IMC, TMB e o gasto calórico diário com base no nível de atividade.",
    )
    @app_commands.describe(
        peso="Seu peso em kg",
        altura="Sua altura em cm",  # Altura em cm
        idade="Sua idade",
        sexo="M para masculino, F para feminino",
        nivel_atividade="Nível de atividade: nenhum, leve, moderado ou intenso",
    )
    async def gym(
        self,
        interact: discord.Interaction,
        peso: float,
        altura: float,
        idade: int,
        sexo: str,
        nivel_atividade: str,
    ):
        # Verifica se o sexo é válido
        if sexo.lower() not in ["m", "f"]:
            await interact.response.send_message(
                "Sexo inválido. Use 'M' para masculino ou 'F' para feminino.",
                ephemeral=True,
            )
            return

        # Verifica se o nível de atividade é válido
        if nivel_atividade.lower() not in ["nenhum", "leve", "moderado", "intenso"]:
            await interact.response.send_message(
                "Nível de atividade inválido. Escolha entre: nenhum, leve, moderado ou intenso.",
                ephemeral=True,
            )
            return

        # Converte altura de cm para metros
        altura_metros = altura * 0.01  # Converte centímetros para metros

        # Calcula o IMC
        imc = self.calcular_imc(peso, altura_metros)

        # Calcula a TMB
        tmb = self.calcular_tmb(peso, altura_metros, idade, sexo)

        # Calcula o gasto calórico diário com base no nível de atividade
        gasto_calorico = self.calcular_gasto_calorico(tmb, nivel_atividade)

        # Classifica o IMC
        classificacao_imc = self.classificar_imc(imc)

        if tmb != -1:
            await interact.response.send_message(
                f"Seu IMC é: {imc:.2f} ({classificacao_imc})\n"
                f"Sua TMB é: {tmb:.2f} calorias/dia\n"
                f"Gasto calórico diário com nível de atividade {nivel_atividade}: {gasto_calorico:.2f} calorias/dia.",
                ephemeral=True,
            )
        else:
            await interact.response.send_message(
                "Não foi possível calcular a TMB devido a um erro no cálculo.",
                ephemeral=True,
            )

    # Função para calcular o IMC
    def calcular_imc(self, peso: float, altura: float) -> float:
        return peso / (altura * altura)

    # Função para calcular a TMB
    def calcular_tmb(self, peso: float, altura: float, idade: int, sexo: str) -> float:
        if sexo.lower() == "m":
            # Fórmula para homens
            return (
                88.36 + (13.4 * peso) + (4.8 * altura * 100) - (5.7 * idade)
            )  # altura convertida para cm
        elif sexo.lower() == "f":
            # Fórmula para mulheres
            return (
                447.6 + (9.2 * peso) + (3.1 * altura * 100) - (4.3 * idade)
            )  # altura convertida para cm
        else:
            return -1  # Retorna -1 para indicar sexo inválido

    # Função para calcular o gasto calórico com base no nível de atividade
    def calcular_gasto_calorico(self, tmb: float, nivel_atividade: str) -> float:
        fator_atividade = {
            "nenhum": 1.2,
            "leve": 1.375,
            "moderado": 1.55,
            "intenso": 1.725,
        }
        return tmb * fator_atividade[nivel_atividade.lower()]

    # Função para classificar o IMC
    def classificar_imc(self, imc: float) -> str:
        if imc < 18.5:
            return "Abaixo do peso"
        elif 18.5 <= imc < 24.9:
            return "Peso normal"
        elif 25 <= imc < 29.9:
            return "Sobrepeso"
        elif 30 <= imc < 34.9:
            return "Obesidade Grau 1"
        elif 35 <= imc < 39.9:
            return "Obesidade Grau 2"
        else:
            return "Obesidade Grau 3"


# Setup do bot
async def setup(bot):
    await bot.add_cog(GymCalculatorCog(bot))
