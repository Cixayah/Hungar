import discord
from discord import app_commands
from discord.ext import commands
import os
import requests
from dotenv import load_dotenv
import asyncio

load_dotenv()


class Lol(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()
        self.api_key = os.getenv("RIOT_API_KEY")

    async def get_puuid(self, name: str, tag: str):
        """Helper function to get PUUID from Riot ID"""
        headers = {"X-Riot-Token": self.api_key}
        account_url = f"https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{name}/{tag}"
        
        try:
            account_response = requests.get(account_url, headers=headers, timeout=10)
            if account_response.status_code == 200:
                return account_response.json().get("puuid")
            elif account_response.status_code == 404:
                return None
            else:
                print(f"Error getting PUUID: {account_response.status_code}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"Request exception: {e}")
            return None

    # /elo command
    @app_commands.command(name="elo", description="Mostra o elo do jogador (Ex: Cix + WTLE)")
    @app_commands.describe(name="Nome do jogador", tag="Hashtag do jogador (sem o #)")
    async def elo(self, interaction: discord.Interaction, name: str, tag: str):
        await interaction.response.defer()
        headers = {"X-Riot-Token": self.api_key}

        # Step 1: get PUUID
        puuid = await self.get_puuid(name, tag)
        if not puuid:
            await interaction.followup.send("❌ Riot ID não encontrado. Verifique se o nome e tag estão corretos.")
            return

        try:
            # Step 2: get summoner info
            summoner_url = f"https://br1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuid}"
            summoner_response = requests.get(summoner_url, headers=headers, timeout=10)
            
            if summoner_response.status_code != 200:
                await interaction.followup.send("⚠️ Erro ao buscar informações do invocador. Tente novamente.")
                return
                
            summoner = summoner_response.json()
            summoner_id = summoner.get("id")
            summoner_name = summoner.get("name", f"{name}#{tag}")
            summoner_level = summoner.get("summonerLevel", "N/A")

            # Step 3: get rank info
            rank_url = f"https://br1.api.riotgames.com/lol/league/v4/entries/by-summoner/{summoner_id}"
            rank_response = requests.get(rank_url, headers=headers, timeout=10)
            
            if rank_response.status_code != 200:
                await interaction.followup.send("⚠️ Erro ao buscar dados de elo. Tente novamente.")
                return
                
            rank_data = rank_response.json()
            
            # Create embed for better formatting
            embed = discord.Embed(
                title=f"🎮 {summoner_name}",
                color=0x0099ff,
                description=f"**Nível:** {summoner_level}"
            )
            
            if not rank_data:
                embed.add_field(
                    name="📊 Rank Competitivo", 
                    value="Ainda não possui rank competitivo", 
                    inline=False
                )
            else:
                # Process ranked queues
                for entry in rank_data:
                    queue_type = entry.get("queueType", "")
                    
                    if queue_type == "RANKED_SOLO_5x5":
                        queue_name = "🏆 Solo/Duo"
                    elif queue_type == "RANKED_FLEX_SR":
                        queue_name = "🤝 Flex 5v5"
                    else:
                        queue_name = f"🎯 {queue_type}"
                    
                    tier = entry.get("tier", "").capitalize()
                    division = entry.get("rank", "")
                    lp = entry.get("leaguePoints", 0)
                    wins = entry.get("wins", 0)
                    losses = entry.get("losses", 0)
                    
                    total_games = wins + losses
                    winrate = round((wins / total_games) * 100) if total_games > 0 else 0
                    
                    rank_info = f"**{tier} {division}** - {lp} LP\n"
                    rank_info += f"**W/L:** {wins}W/{losses}L ({winrate}% WR)"
                    
                    embed.add_field(
                        name=queue_name,
                        value=rank_info,
                        inline=True
                    )

            await interaction.followup.send(embed=embed)
            
        except requests.exceptions.RequestException as e:
            await interaction.followup.send("⚠️ Erro de conexão com a API da Riot. Tente novamente.")
            print(f"Request error in /elo: {e}")
        except Exception as e:
            await interaction.followup.send("⚠️ Erro inesperado. Tente novamente.")
            print(f"Unexpected error in /elo: {e}")

    # /stats command
    @app_commands.command(name="stats", description="Mostra últimas 5 partidas com KDA e modo.")
    @app_commands.describe(name="Nome do jogador", tag="Hashtag do jogador (sem o #)")
    async def stats(self, interaction: discord.Interaction, name: str, tag: str):
        await interaction.response.defer()
        headers = {"X-Riot-Token": self.api_key}

        # Get PUUID
        puuid = await self.get_puuid(name, tag)
        if not puuid:
            await interaction.followup.send("❌ Riot ID não encontrado. Verifique se o nome e tag estão corretos.")
            return

        try:
            # Get last 5 match IDs
            matches_url = f"https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start=0&count=5"
            matches_response = requests.get(matches_url, headers=headers, timeout=10)
            
            if matches_response.status_code != 200:
                await interaction.followup.send("⚠️ Erro ao buscar histórico de partidas.")
                return
                
            match_ids = matches_response.json()
            
            if not match_ids:
                await interaction.followup.send("📊 Nenhuma partida recente encontrada.")
                return

            # Enhanced mode mapping
            queue_map = {
                # Ranked queues
                420: "Solo/Duo",
                440: "Flex 5v5",
                470: "Flex 3v3",
                
                # Normal queues
                400: "Normal Draft",
                430: "Normal Blind",
                
                # Special modes
                450: "ARAM",
                900: "URF",
                1020: "One For All",
                1300: "Nexus Blitz",
                1400: "Ultimate Spellbook",
                1700: "Arena",
                
                # Featured modes
                76: "URF",
                318: "ARURF",
                325: "All Random",
                
                # Others
                0: "Custom",
                2000: "Tutorial"
            }

            embed = discord.Embed(
                title=f"📊 Últimas partidas de {name}#{tag}",
                color=0x00ff00
            )

            kda_list = []
            matches_processed = 0

            for match_id in match_ids:
                if matches_processed >= 5:  # Limit to 5 matches
                    break
                    
                match_url = f"https://americas.api.riotgames.com/lol/match/v5/matches/{match_id}"
                match_response = requests.get(match_url, headers=headers, timeout=10)
                
                if match_response.status_code != 200:
                    continue
                    
                match_data = match_response.json()
                info = match_data.get("info", {})
                participants = info.get("participants", [])
                queue_id = info.get("queueId", 0)
                game_duration = info.get("gameDuration", 0)
                
                # Get readable queue name
                queue_name = queue_map.get(queue_id, f"Queue {queue_id}")
                
                # Convert game duration to minutes
                duration_minutes = game_duration // 60 if game_duration > 0 else 0

                for player in participants:
                    if player.get("puuid") == puuid:
                        champion = player.get("championName", "Unknown")
                        kills = player.get("kills", 0)
                        deaths = player.get("deaths", 0)
                        assists = player.get("assists", 0)
                        win = player.get("win", False)
                        
                        # Calculate KDA
                        kda_value = (kills + assists) / deaths if deaths > 0 else (kills + assists)
                        kda_list.append(kda_value)

                        # Format match info
                        emoji = "✅" if win else "❌"
                        result_text = "Vitória" if win else "Derrota"
                        
                        match_info = f"{emoji} **{champion}**\n"
                        match_info += f"**KDA:** {kills}/{deaths}/{assists} ({kda_value:.2f})\n"
                        match_info += f"**Resultado:** {result_text}\n"
                        match_info += f"**Modo:** {queue_name}\n"
                        match_info += f"**Duração:** {duration_minutes}min"
                        
                        embed.add_field(
                            name=f"Partida {matches_processed + 1}",
                            value=match_info,
                            inline=True
                        )
                        
                        matches_processed += 1
                        break

            # Calculate average KDA
            if kda_list:
                average_kda = sum(kda_list) / len(kda_list)
                embed.add_field(
                    name="📈 Estatísticas",
                    value=f"**Média KDA:** {average_kda:.2f}\n**Partidas analisadas:** {len(kda_list)}",
                    inline=False
                )
            else:
                embed.description = "Nenhuma partida válida encontrada."

            await interaction.followup.send(embed=embed)
            
        except requests.exceptions.RequestException as e:
            await interaction.followup.send("⚠️ Erro de conexão com a API da Riot. Tente novamente.")
            print(f"Request error in /stats: {e}")
        except Exception as e:
            await interaction.followup.send("⚠️ Erro inesperado. Tente novamente.")
            print(f"Unexpected error in /stats: {e}")


async def setup(bot):
    await bot.add_cog(Lol(bot))