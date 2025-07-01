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
        # Encode the name to handle special characters
        encoded_name = requests.utils.quote(name)
        encoded_tag = requests.utils.quote(tag)
        account_url = f"https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{encoded_name}/{encoded_tag}"
        
        try:
            account_response = requests.get(account_url, headers=headers, timeout=15)
            
            if account_response.status_code == 200:
                data = account_response.json()
                return data.get("puuid")
            elif account_response.status_code == 404:
                return None
            else:
                print(f"Error getting PUUID: {account_response.status_code} - {account_response.text}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"Request exception: {e}")
            return None

    # /elo command - VERSÃO CORRIGIDA COM ENDPOINT CORRETO
    @app_commands.command(name="elo", description="Mostra o elo do jogador (Ex: Cix + WTLE)")
    @app_commands.describe(name="Nome do jogador", tag="Hashtag do jogador (sem o #)")
    async def elo(self, interaction: discord.Interaction, name: str, tag: str):
        await interaction.response.defer()
        
        # Verificar se a API key existe
        if not self.api_key:
            await interaction.followup.send("❌ API key da Riot não configurada.")
            return
            
        headers = {"X-Riot-Token": self.api_key}

        try:
            # Step 1: get PUUID
            puuid = await self.get_puuid(name, tag)
            if not puuid:
                await interaction.followup.send(f"❌ Riot ID `{name}#{tag}` não encontrado. Verifique se o nome e tag estão corretos.")
                return

            # Step 2: get summoner info (para pegar o nome e level)
            summoner_url = f"https://br1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuid}"
            summoner_response = requests.get(summoner_url, headers=headers, timeout=15)
            
            if summoner_response.status_code == 404:
                await interaction.followup.send("❌ Jogador não encontrado no servidor brasileiro (BR1).")
                return
            elif summoner_response.status_code != 200:
                print(f"Summoner error: {summoner_response.text}")
                await interaction.followup.send(f"⚠️ Erro ao buscar informações do invocador (Status: {summoner_response.status_code}). Tente novamente.")
                return
                
            summoner = summoner_response.json()
            summoner_name = summoner.get("name", f"{name}#{tag}")
            summoner_level = summoner.get("summonerLevel", "N/A")

            # Step 3: get rank info usando PUUID diretamente
            rank_url = f"https://br1.api.riotgames.com/lol/league/v4/entries/by-puuid/{puuid}"
            rank_response = requests.get(rank_url, headers=headers, timeout=15)
            
            if rank_response.status_code != 200:
                print(f"Rank error: {rank_response.text}")
                await interaction.followup.send(f"⚠️ Erro ao buscar dados de elo (Status: {rank_response.status_code}). Tente novamente.")
                return
                
            rank_data = rank_response.json()
            
            # Determine embed color based on highest rank
            embed_color = 0x0099ff  # Default blue
            highest_tier = ""
            
            if rank_data:
                for entry in rank_data:
                    tier = entry.get("tier", "").upper()
                    if tier == "CHALLENGER":
                        embed_color = 0xF0E68C  # Gold for Challenger
                        highest_tier = "CHALLENGER"
                        break
                    elif tier == "GRANDMASTER":
                        embed_color = 0xFF6347  # Red for Grandmaster
                        highest_tier = "GRANDMASTER"
                    elif tier == "MASTER" and highest_tier != "GRANDMASTER":
                        embed_color = 0x9932CC  # Purple for Master
                        highest_tier = "MASTER"
                    elif tier in ["DIAMOND", "EMERALD"] and highest_tier not in ["MASTER", "GRANDMASTER"]:
                        embed_color = 0x00CED1  # Cyan for Diamond/Emerald
                        highest_tier = tier
            
            # Create embed with better formatting
            embed = discord.Embed(
                color=embed_color
            )
            
            # Title with emoji based on rank
            rank_emoji = "👑" if highest_tier == "CHALLENGER" else "💎" if highest_tier in ["GRANDMASTER", "MASTER"] else "🎮"
            embed.set_author(
                name=f"{rank_emoji} {summoner_name}",
                icon_url="https://cdn.discordapp.com/attachments/123456789/123456789/lol_icon.png"
            )
            
            embed.add_field(
                name="📊 Informações Gerais",
                value=f"**Nível:** {summoner_level}\n**Riot ID:** {name}#{tag}",
                inline=False
            )
            
            if not rank_data:
                embed.add_field(
                    name="🏅 Ranks Competitivos", 
                    value="```\n❌ Ainda não possui rank competitivo\n```", 
                    inline=False
                )
            else:
                # Process ranked queues with better formatting
                solo_info = ""
                flex_info = ""
                
                for entry in rank_data:
                    queue_type = entry.get("queueType", "")
                    tier = entry.get("tier", "").capitalize()
                    rank = entry.get("rank", "")
                    lp = entry.get("leaguePoints", 0)
                    wins = entry.get("wins", 0)
                    losses = entry.get("losses", 0)
                    
                    total_games = wins + losses
                    winrate = round((wins / total_games) * 100) if total_games > 0 else 0
                    
                    # Get tier emoji
                    tier_emojis = {
                        "CHALLENGER": "👑",
                        "GRANDMASTER": "🏆",
                        "MASTER": "🌟",
                        "DIAMOND": "💎",
                        "EMERALD": "🟢",
                        "PLATINUM": "⚪",
                        "GOLD": "🟡",
                        "SILVER": "⚪",  
                        "BRONZE": "🟤",   
                        "IRON": "⚫"         
                    }
                    
                    tier_emoji = tier_emojis.get(tier.upper(), "🎯")
                    
                    # Handle special tiers
                    if tier.upper() in ["MASTER", "GRANDMASTER", "CHALLENGER"]:
                        rank_display = f"{tier_emoji} **{tier}**"
                    else:
                        rank_display = f"{tier_emoji} **{tier} {rank}**"
                    
                    # Special badges
                    badges = []
                    if entry.get("hotStreak", False):
                        badges.append("🔥")
                    if entry.get("veteran", False):
                        badges.append("⭐")
                    if entry.get("freshBlood", False):
                        badges.append("🆕")
                    
                    badge_text = " " + "".join(badges) if badges else ""
                    
                    rank_text = f"{rank_display}{badge_text}\n"
                    rank_text += f"**LP:** {lp} | **W/L:** {wins}/{losses} ({winrate}%)"
                    
                    if queue_type == "RANKED_SOLO_5x5":
                        solo_info = rank_text
                    elif queue_type == "RANKED_FLEX_SR":
                        flex_info = rank_text
                
                # Add rank fields
                if solo_info:
                    embed.add_field(
                        name="🏆 Solo/Duo",
                        value=solo_info,
                        inline=True
                    )
                
                if flex_info:
                    embed.add_field(
                        name="🤝 Flex 5v5",
                        value=flex_info,
                        inline=True
                    )
                
                # Add empty field for spacing if both exist
                if solo_info and flex_info:
                    embed.add_field(name="\u200b", value="\u200b", inline=True)
            
            # Footer with timestamp
            embed.set_footer(
                text="Dados da Riot Games API",
                icon_url="https://cdn.discordapp.com/attachments/123456789/123456789/riot_icon.png"
            )
            embed.timestamp = discord.utils.utcnow()
            
            await interaction.followup.send(embed=embed)
            
        except requests.exceptions.Timeout:
            await interaction.followup.send("⏰ Timeout na conexão com a API da Riot. Tente novamente.")
        except requests.exceptions.RequestException as e:
            await interaction.followup.send("⚠️ Erro de conexão com a API da Riot. Tente novamente.")
            print(f"Request error in /elo: {e}")
        except KeyError as e:
            await interaction.followup.send("⚠️ Erro ao processar dados da API. Tente novamente.")
            print(f"KeyError in /elo: {e}")
        except Exception as e:
            await interaction.followup.send("⚠️ Erro inesperado. Tente novamente.")
            print(f"Unexpected error in /elo: {e}")

    # /stats command
    @app_commands.command(name="stats", description="Mostra últimas 5 partidas com KDA e modo.")
    @app_commands.describe(name="Nome do jogador", tag="Hashtag do jogador (sem o #)")
    async def stats(self, interaction: discord.Interaction, name: str, tag: str):
        await interaction.response.defer()
        
        if not self.api_key:
            await interaction.followup.send("❌ API key da Riot não configurada.")
            return
            
        headers = {"X-Riot-Token": self.api_key}

        # Get PUUID
        puuid = await self.get_puuid(name, tag)
        if not puuid:
            await interaction.followup.send("❌ Riot ID não encontrado. Verifique se o nome e tag estão corretos.")
            return

        try:
            # Get last 5 match IDs
            matches_url = f"https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start=0&count=5"
            matches_response = requests.get(matches_url, headers=headers, timeout=15)
            
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
                color=0x00ff99
            )
            embed.set_author(
                name=f"📊 Histórico de Partidas",
                icon_url="https://cdn.discordapp.com/attachments/123456789/123456789/match_icon.png"
            )

            kda_list = []
            matches_processed = 0

            for match_id in match_ids:
                if matches_processed >= 5:  # Limit to 5 matches
                    break
                    
                match_url = f"https://americas.api.riotgames.com/lol/match/v5/matches/{match_id}"
                match_response = requests.get(match_url, headers=headers, timeout=15)
                
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

                        # Get champion emoji (you can expand this)
                        champion_emojis = {
                            "Jinx": "🔫", "Yasuo": "⚔️", "Lux": "✨", "Zed": "🗡️",
                            "Ahri": "🦊", "Thresh": "⛓️", "Lee Sin": "👊", "Katarina": "🗡️",
                            "Vayne": "🏹", "Azir": "🏺", "Syndra": "🔮", "Jhin": "🎭"
                        }
                        champ_emoji = champion_emojis.get(champion, "⚔️")
                        
                        # Format match info with better layout
                        emoji = "🟢" if win else "🔴"
                        result_text = "VITÓRIA" if win else "DERROTA"
                        
                        match_info = f"{emoji} **{result_text}**\n"
                        match_info += f"{champ_emoji} **{champion}**\n"
                        match_info += f"📊 **{kills}/{deaths}/{assists}** (KDA: {kda_value:.1f})\n"
                        match_info += f"🎮 {queue_name}\n"
                        match_info += f"⏱️ {duration_minutes}min"
                        
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
            
        except requests.exceptions.Timeout:
            await interaction.followup.send("⏰ Timeout na conexão com a API da Riot. Tente novamente.")
        except requests.exceptions.RequestException as e:
            await interaction.followup.send("⚠️ Erro de conexão com a API da Riot. Tente novamente.")
            print(f"Request error in /stats: {e}")
        except Exception as e:
            await interaction.followup.send("⚠️ Erro inesperado. Tente novamente.")
            print(f"Unexpected error in /stats: {e}")


async def setup(bot):
    await bot.add_cog(Lol(bot))