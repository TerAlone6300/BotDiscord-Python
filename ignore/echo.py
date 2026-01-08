import discord
from discord import app_commands
from discord.ext import commands

OWNER_ID = 1076150512224833536  # thay ID của bạn

class Echo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="echo", description="Hiển thị danh sách quyền (chỉ mình tôi thấy)")
    @app_commands.default_permissions()  # ẩn command khỏi tất cả mọi người
    async def echo(self, interaction: discord.Interaction):
        if interaction.user.id != OWNER_ID:
            return await interaction.response.send_message(
                "❌ Bạn không thể dùng command này.", ephemeral=True
            )

        permissions = [
            "Administrator",
            "Ban Members",
            "Kick Members",
            "Manage Channels",
            "Manage Messages",
            "Manage Roles",
            "Mute Members",
            "Deafen Members",
            "Move Members",
            "Send Messages",
            "Add Reactions",
            "Use Application Commands"
        ]
        text = "**Danh sách quyền Discord:**\n" + "\n".join(f"- {p}" for p in permissions)
        await interaction.response.send_message(text, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Echo(bot))