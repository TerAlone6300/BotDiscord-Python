import discord
from discord import app_commands
from discord.ext import commands
import aiohttp

class MinecraftInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Lấy UUID từ player name
    async def get_uuid(self, player: str):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.mojang.com/users/profiles/minecraft/{player}") as r:
                if r.status == 200:
                    data = await r.json()
                    return data.get("id")
                return None

    # Lệnh /skin
    @app_commands.command(name="skin", description="Hiển thị skin 3D của người chơi Minecraft")
    async def skin(self, interaction: discord.Interaction, player: str):
        uuid = await self.get_uuid(player)
        if not uuid:
            await interaction.response.send_message(f"❌ Không tìm thấy người chơi `{player}`.", ephemeral=True)
            return

        url = f"https://mc-heads.net/body/{uuid}.png"
        embed = discord.Embed(title=f"Skin của {player}", color=0x00ff00)
        embed.set_image(url=url)
        await interaction.response.send_message(embed=embed)

    # Lệnh /cape
    @app_commands.command(name="cape", description="Xem cape của người chơi Minecraft (nếu có)")
    async def cape(self, interaction: discord.Interaction, player: str):
        uuid = await self.get_uuid(player)
        if not uuid:
            await interaction.response.send_message(f"❌ Không tìm thấy người chơi `{player}`.", ephemeral=True)
            return

        mojang_cape = f"https://crafatar.com/capes/{uuid}"
        optifine_cape = f"https://optifine.net/capes/{player}"

        async with aiohttp.ClientSession() as session:
            async with session.get(mojang_cape) as mojang_res:
                if mojang_res.status == 200:
                    embed = discord.Embed(title=f"Cape Mojang của {player}", color=0x00ffff)
                    embed.set_image(url=mojang_cape)
                    await interaction.response.send_message(embed=embed)
                    return

            async with session.get(optifine_cape) as optifine_res:
                if optifine_res.status == 200:
                    embed = discord.Embed(title=f"Cape OptiFine của {player}", color=0x00ffff)
                    embed.set_image(url=optifine_cape)
                    await interaction.response.send_message(embed=embed)
                    return

        await interaction.response.send_message(f"❌ `{player}` không có cape Mojang hoặc OptiFine.", ephemeral=True)

    # Lệnh /tier
    @app_commands.command(name="tier", description="Lấy Minecraft tier của người chơi từ MCTiers và VanillaTierlist")
    async def tier(self, interaction: discord.Interaction, player: str):
        await interaction.response.defer(thinking=True)

        async with aiohttp.ClientSession() as session:
            tier_data = {}
            source_used = None

            # --- 1️⃣ Thử MCTiers.com ---
            try:
                async with session.get(f"https://mctiers.com/api/tiers/{player}") as r:
                    if r.status == 200:
                        data = await r.json()
                        # Một số API của MCTiers bọc trong "player"
                        if "tier" in data or "player" in data:
                            d = data.get("player", data)
                            tier_data = {
                                "tier": d.get("tier"),
                                "score": d.get("score"),
                                "source": "mctiers.com"
                            }
                            source_used = "mctiers.com"
            except Exception as e:
                print(f"MCTiers error: {e}")

            # --- 2️⃣ Nếu không có, thử VanillaTierlist ---
            if not tier_data:
                try:
                    async with session.get(f"https://vanillatierlist.com/api/player/{player}") as r:
                        if r.status == 200:
                            data = await r.json()

                            # Một số player có data trong "player" hoặc "data"
                            stats = data.get("stats") or data.get("player") or data.get("data")
                            if stats:
                                tier_data = {
                                    "tier": stats.get("tierName") or stats.get("tier"),
                                    "score": stats.get("score") or stats.get("points"),
                                    "elo": stats.get("elo") or stats.get("rankElo"),
                                    "rank_icon": stats.get("rankIcon") or stats.get("icon"),
                                    "source": "vanillatierlist.com"
                                }
                                source_used = "vanillatierlist.com"
                except Exception as e:
                    print(f"VanillaTierlist error: {e}")

            # --- 3️⃣ Nếu vẫn rỗng, thử API phụ từ VanillaTierlist leaderboard ---
            if not tier_data:
                try:
                    async with session.get("https://vanillatierlist.com/api/leaderboard") as r:
                        if r.status == 200:
                            data = await r.json()
                            leaderboard = data.get("players", [])
                            for p in leaderboard:
                                if p.get("name", "").lower() == player.lower():
                                    tier_data = {
                                        "tier": p.get("tierName"),
                                        "score": p.get("score"),
                                        "elo": p.get("elo"),
                                        "rank_icon": p.get("rankIcon"),
                                        "source": "vanillatierlist.com (leaderboard)"
                                    }
                                    source_used = "vanillatierlist.com (leaderboard)"
                                    break
                except Exception as e:
                    print(f"Leaderboard error: {e}")

            # --- 4️⃣ Hiển thị kết quả ---
            if tier_data:
                embed = discord.Embed(
                    title=f"Tier của {player}",
                    color=0xffcc00
                )
                embed.add_field(name="Tier", value=tier_data.get("tier", "Không rõ"), inline=True)

                if tier_data.get("score"):
                    embed.add_field(name="Score", value=str(tier_data["score"]), inline=True)
                if tier_data.get("elo"):
                    embed.add_field(name="ELO", value=str(tier_data["elo"]), inline=True)

                if tier_data.get("rank_icon"):
                    embed.set_thumbnail(url=tier_data["rank_icon"])

                embed.set_footer(text=f"Nguồn: {source_used}")
                await interaction.followup.send(embed=embed)
            else:
                await interaction.followup.send(
                    f"❌ Không tìm thấy thông tin tier của `{player}` trên MCTiers hoặc VanillaTierlist.\n"
                    f"(Có thể API đang bị bảo vệ hoặc rate-limit)",
                    ephemeral=True
                )

async def setup(bot):
    await bot.add_cog(MinecraftInfo(bot))