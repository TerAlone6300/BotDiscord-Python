import discord
from discord.ext import commands
from discord import app_commands
import asyncio

class Remind(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="remind", description="Đặt nhắc nhở (vd: 10s, 5m, 2h)")
    async def remind(self, interaction: discord.Interaction, time: str, content: str):
        units = {"s": 1, "m": 60, "h": 3600}
        try:
            seconds = int(time[:-1]) * units[time[-1]]
        except:
            await interaction.response.send_message("⚠️ Sai định dạng! (vd: 10s, 5m, 2h)", ephemeral=True)
            return

        await interaction.response.send_message(f"✅ Nhắc sau {time}", ephemeral=True)

        async def job():
            await asyncio.sleep(seconds)
            await interaction.followup.send(f"⏰ {interaction.user.mention} Nhắc: **{content}**")

        asyncio.create_task(job())

async def setup(bot):
    await bot.add_cog(Remind(bot))