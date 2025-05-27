import discord
from discord import app_commands
from discord.ext import commands
import os
import requests
from dotenv import load_dotenv

load_dotenv()


class Lol(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()
        self.api_key = os.getenv("RIOT_API_KEY")

    # /elo command
    @app_commands.command(name="elo", description="Mostra o elo do jogador (Ex: Cix + WTLE)")
    @app_commands.describe(name="Nome do jogador", tag="Hashtag do jogador (sem o #)")
    async def elo(self, interaction: discord.Interaction, name: str, tag: str):
        await interaction.response.defer()
        headers = {"X-Riot-Token": self.api_key}

        # Step 1: get PUUID
        account_url = f"https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{name}/{tag}"
        account_response = requests.get(account_url, headers=headers)
        if account_response.status_code != 200:
            await interaction.followup.send("❌ Riot ID não encontrado.")
            return
        puuid = account_response.json().get("puuid")

        # Step 2: get summoner ID
        summoner_url = f"https://br1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuid}"
        summoner_response = requests.get(summoner_url, headers=headers)
        if summoner_response.status_code != 200:
            await interaction.followup.send("⚠️ Erro ao buscar informações do invocador.")
            return
        summoner = summoner_response.json()
        summoner_id = summoner.get("id")
        summoner_name = summoner.get("name", f"{name}#{tag}")

        # Step 3: get rank
        rank_url = f"https://br1.api.riotgames.com/lol/league/v4/entries/by-summoner/{summoner_id}"
        rank_response = requests.get(rank_url, headers=headers)
        if rank_response.status_code != 200:
            await interaction.followup.send("⚠️ Erro ao buscar dados de elo.")
            return
        rank_data = rank_response.json()
        if not rank_data:
            await interaction.followup.send(f"🎮 **{summoner_name}** ainda não tem rank competitivo.")
            return

        message = f"🎮 **{summoner_name}**\n"
        for entry in rank_data:
            queue_type = "Solo/Duo" if entry["queueType"] == "RANKED_SOLO_5x5" else "Flex"
            tier = entry["tier"].capitalize()
            division = entry["rank"]
            lp = entry["leaguePoints"]
            wins = entry["wins"]
            losses = entry["losses"]
            winrate = round((wins / (wins + losses)) * 100)
            message += (
                f"🏆 **{queue_type}**: {tier} {division} - {lp} LP "
                f"({wins}W/{losses}L - {winrate}% WR)\n"
            )

        await interaction.followup.send(message)


    # /stats command
    @app_commands.command(name="stats", description="Mostra últimas 5 partidas com KDA e modo.")
    @app_commands.describe(name="Nome do jogador", tag="Hashtag do jogador (sem o #)")
    async def stats(self, interaction: discord.Interaction, name: str, tag: str):
        await interaction.response.defer()
        headers = {"X-Riot-Token": self.api_key}

        # get PUUID
        account_url = f"https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{name}/{tag}"
        account_response = requests.get(account_url, headers=headers)
        if account_response.status_code != 200:
            await interaction.followup.send("❌ Riot ID não encontrado.")
            return
        puuid = account_response.json().get("puuid")

        # get last 5 match IDs
        matches_url = (
            f"https://americas.api.riotgames.com/lol/match/v5/matches/"
            f"by-puuid/{puuid}/ids?start=0&count=5"
        )
        matches_response = requests.get(matches_url, headers=headers)
        if matches_response.status_code != 200:
            await interaction.followup.send("⚠️ Erro ao buscar histórico de partidas.")
            return
        match_ids = matches_response.json()

        # mode mapping
        mode_map = {
            "CLASSIC": "Solo/Duo",
            "ARAM": "ARAM",
            "TUTORIAL": "Tutorial",
            "URF": "URF",
            "DOOMBOTSTEEMO": "Doom Bots",
            "ONEFORALL": "One For All",
            "ASCENSION": "Ascension",
            "FIRSTBLOOD": "First Blood",
            "KINGPORO": "King Poro",
            "PROJECT": "PROJECT",
            "GAMEMODEX": "Game Mode X",
            "NEXUSBLITZ": "Nexus Blitz",
            "ULTBOOK": "Ultimate Spellbook",
            "ARENA": "Arena",
        }

        message = f"📊 Últimas 5 partidas de **{name}#{tag}**:\n\n"
        kda_list = []

        for match_id in match_ids:
            match_url = f"https://americas.api.riotgames.com/lol/match/v5/matches/{match_id}"
            match_response = requests.get(match_url, headers=headers)
            if match_response.status_code != 200:
                continue
            match_data = match_response.json()
            info = match_data.get("info", {})
            participants = info.get("participants", [])
            game_mode = info.get("gameMode", "Desconhecido")
            readable_mode = mode_map.get(game_mode, game_mode)

            for player in participants:
                if player.get("puuid") == puuid:
                    champion = player.get("championName")
                    kills = player.get("kills")
                    deaths = player.get("deaths")
                    assists = player.get("assists")
                    win = player.get("win")

                    kda_value = (kills + assists) / deaths if deaths != 0 else (kills + assists)
                    kda_list.append(kda_value)

                    emoji = "✅" if win else "❌"
                    result_text = "Vitória" if win else "Derrota"
                    message += (
                        f"{emoji} {champion}: "
                        f"{kills}/{deaths}/{assists} "
                        f"(KDA {kda_value:.2f}) - {result_text} "
                        f"({readable_mode})\n"
                    )
                    break

        count = len(kda_list)
        if count == 0:
            await interaction.followup.send("Nenhuma partida recente encontrada.")
            return

        average_kda = sum(kda_list) / count
        message += f"\n📈 Média de KDA nas últimas {count} partidas: {average_kda:.2f}"

        await interaction.followup.send(message)

    # /duo command
    @app_commands.command(name="duo", description="Mostra com quem você mais joga em duo.")
    @app_commands.describe(name="Nome do jogador", tag="Hashtag do jogador (sem o #)")
    async def duo(self, interaction: discord.Interaction, name: str, tag: str):
        await interaction.response.defer()
        headers = {"X-Riot-Token": self.api_key}

        # get PUUID
        account_url = f"https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{name}/{tag}"
        account_response = requests.get(account_url, headers=headers)
        if account_response.status_code != 200:
            await interaction.followup.send("❌ Riot ID não encontrado.")
            return
        puuid = account_response.json().get("puuid")

        # get last 20 match IDs
        matches_url = (
            f"https://americas.api.riotgames.com/lol/match/v5/matches/"
            f"by-puuid/{puuid}/ids?start=0&count=20"
        )
        matches_response = requests.get(matches_url, headers=headers)
        if matches_response.status_code != 200:
            await interaction.followup.send("⚠️ Erro ao buscar histórico de partidas.")
            return
        match_ids = matches_response.json()

        duo_counter = {}
        for match_id in match_ids:
            match_url = f"https://americas.api.riotgames.com/lol/match/v5/matches/{match_id}"
            match_response = requests.get(match_url, headers=headers)
            if match_response.status_code != 200:
                continue
            match_data = match_response.json()
            participants = match_data.get("info", {}).get("participants", [])

            team_id = None
            for player in participants:
                if player.get("puuid") == puuid:
                    team_id = player.get("teamId")
                    break
            if team_id is None:
                continue

            for player in participants:
                if player.get("puuid") != puuid and player.get("teamId") == team_id:
                    partner = player.get("summonerName")
                    duo_counter[partner] = duo_counter.get(partner, 0) + 1

        if not duo_counter:
            await interaction.followup.send(f"🤝 {name}#{tag} não tem parceiros frequentes nas últimas partidas.")
            return

        best_partner = max(duo_counter, key=duo_counter.get)
        times_played = duo_counter[best_partner]
        await interaction.followup.send(
            f"🤝 {name}#{tag} jogou mais com **{best_partner}** nas últimas {len(match_ids)} partidas ({times_played} vezes)."
        )


async def setup(bot):
    await bot.add_cog(Lol(bot))
