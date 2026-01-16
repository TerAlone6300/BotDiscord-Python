import discord
from discord.ext import commands
from discord import app_commands

class Ping(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # Ping khi tag bot
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        if self.bot.user and self.bot.user in message.mentions:
            latency = round(self.bot.latency * 1000)
            await message.channel.send(
                f"🏓 Pong! Bot phản hồi trong khoảng `{latency}ms`"
            )

        # QUAN TRỌNG: để prefix command còn hoạt động
        await self.bot.process_commands(message)

    # Slash command /ping
    @app_commands.command(name="ping", description="Xem độ trễ bot")
    async def ping(self, interaction: discord.Interaction):
        latency = round(self.bot.latency * 1000)
        await interaction.response.send_message(
            f"🏓 Pong! Bot phản hồi trong khoảng `{latency}ms`"
        )

async def setup(bot: commands.Bot):
    await bot.add_cog(Ping(bot))