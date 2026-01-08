import discord
from discord.ext import commands
from discord import app_commands
import os
import json

class Warn(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.data_dir = "saves"
        self.cache_subdir = "cache"
        self.filename = "warn.json"

        # Lưu cache trong RAM (tạm thời)
        self.warn_log_channels = {}

    # =============================
    #      HÀM HỖ TRỢ LƯU / ĐỌC
    # =============================
    def get_guild_path(self, guild_id: int) -> str:
        """Trả về đường dẫn thư mục guild"""
        return os.path.join(self.data_dir, str(guild_id), self.cache_subdir)

    def get_json_path(self, guild_id: int) -> str:
        """Trả về đường dẫn file warn.json"""
        return os.path.join(self.get_guild_path(guild_id), self.filename)

    def load_guild_data(self, guild_id: int):
        """Đọc dữ liệu warn-log channel cho guild"""
        path = self.get_json_path(guild_id)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.warn_log_channels[guild_id] = data.get("log_channel_id")
        else:
            self.warn_log_channels[guild_id] = None

    def save_guild_data(self, guild_id: int):
        """Lưu dữ liệu warn-log channel cho guild"""
        guild_path = self.get_guild_path(guild_id)
        os.makedirs(guild_path, exist_ok=True)
        data = {
            "log_channel_id": self.warn_log_channels.get(guild_id)
        }
        with open(self.get_json_path(guild_id), "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    # =============================
    #          SLASH COMMANDS
    # =============================

    # /warn <@user> [reason]
    @app_commands.command(name="warn", description="Cảnh cáo người dùng")
    @app_commands.describe(user="Người cần cảnh cáo", reason="Lý do (tùy chọn)")
    async def warn_user(self, interaction: discord.Interaction, user: discord.Member, reason: str = "Không có lý do cụ thể"):
        await interaction.response.defer(ephemeral=True)
        guild_id = interaction.guild_id

        # Đảm bảo dữ liệu guild được load
        if guild_id not in self.warn_log_channels:
            self.load_guild_data(guild_id)

        log_channel_id = self.warn_log_channels.get(guild_id)

        embed = discord.Embed(
            title="⚠️ CẢNH CÁO NGƯỜI DÙNG",
            color=discord.Color.orange()
        )
        embed.add_field(name="👤 Người bị cảnh cáo", value=user.mention, inline=True)
        embed.add_field(name="👮 Người cảnh cáo", value=interaction.user.mention, inline=True)
        embed.add_field(name="📄 Lý do", value=reason, inline=False)

        await interaction.followup.send(f"✅ Đã cảnh cáo {user.mention} vì: **{reason}**", ephemeral=True)

        if log_channel_id:
            channel = interaction.guild.get_channel(log_channel_id)
            if channel:
                await channel.send(embed=embed)
            else:
                await interaction.followup.send("⚠️ Kênh log không còn tồn tại. Dùng `/warn-log channel <kênh>` để đặt lại.", ephemeral=True)
        else:
            await interaction.followup.send("⚠️ Chưa có kênh log cảnh cáo. Dùng `/warn-log channel <kênh>` để đặt.", ephemeral=True)

    # /warn-log channel <channel>
    warn_log_group = app_commands.Group(name="warn-log", description="Cấu hình log cảnh cáo")

    @warn_log_group.command(name="channel", description="Đặt kênh log cảnh cáo")
    @app_commands.describe(channel="Chọn kênh log cảnh cáo")
    async def set_warn_log_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        guild_id = interaction.guild_id

        # Cập nhật và lưu
        self.warn_log_channels[guild_id] = channel.id
        self.save_guild_data(guild_id)

        await interaction.response.send_message(
            f"✅ Đã đặt kênh log cảnh cáo là {channel.mention}",
            ephemeral=True
        )

async def setup(bot: commands.Bot):
    await bot.add_cog(Warn(bot))