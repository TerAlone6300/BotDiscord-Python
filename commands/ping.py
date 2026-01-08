import discord
from discord.ext import commands
from discord import app_commands

class Ping(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # tag bot để ping
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        if self.bot.user in message.mentions:
            latency = round(self.bot.latency * 1000)
            await message.channel.send(f"🏓 Pong! Bot phản hồi trong khoảng {latency}ms")

    # slash /ping
    @app_commands.command(name="ping", description="Xem độ trễ bot")
    async def ping(self, interaction: discord.Interaction):
        latency = round(self.bot.latency * 1000)
        await interaction.response.send_message(f"🏓 Pong! Bot phản hồi trong khoảng {latency}ms")

async def setup(bot):
    await bot.add_cog(Ping(bot))