import discord
from discord.ext import commands
from discord import app_commands
import os, json
from collections import defaultdict

SAVE_PATH = "saves"


def ensure_guild_dir(gid: int) -> str:
    path = os.path.join(SAVE_PATH, str(gid))
    os.makedirs(path, exist_ok=True)
    return path


def load_json(gid: int, filename: str) -> dict:
    path = os.path.join(ensure_guild_dir(gid), filename)
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(gid: int, filename: str, data: dict):
    with open(os.path.join(ensure_guild_dir(gid), filename), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


class TempVoice(commands.Cog):
    """Temporary voice channel system (discord.py 4.x compliant)."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.user_channels: dict[int, dict[int, int]] = defaultdict(dict)

    # ===== Voice listener =====
    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState
    ):
        if not member.guild:
            return

        guild = member.guild
        gid = guild.id
        cfg = load_json(gid, "config.json")
        create_id = cfg.get("tempvoice_channel")

        # ---- JOIN create channel ----
        if after.channel and after.channel.id == create_id and before.channel != after.channel:
            perms = guild.me.guild_permissions
            if not (perms.manage_channels and perms.move_members):
                return

            category = after.channel.category
            name = f"🔊 Phòng của {member.display_name}"

            try:
                new_channel = await guild.create_voice_channel(
                    name=name,
                    category=category,
                    reason="TempVoice create"
                )
            except discord.Forbidden:
                return

            self.user_channels[gid][new_channel.id] = member.id

            try:
                await member.move_to(new_channel)
            except discord.Forbidden:
                pass

            return

        # ---- LEAVE temp channel ----
        if before.channel:
            ch_id = before.channel.id
            if ch_id in self.user_channels.get(gid, {}):
                if len(before.channel.members) == 0:
                    try:
                        await before.channel.delete(reason="TempVoice empty")
                    except discord.Forbidden:
                        pass
                    self.user_channels[gid].pop(ch_id, None)

    # ===== Slash group =====
    tempvoice = app_commands.Group(
        name="tempvoice",
        description="Quản lý voice tạm thời"
    )

    @tempvoice.command(name="setup", description="Chọn kênh voice làm Create a Voice")
    @app_commands.describe(channel="Kênh voice dùng để tạo phòng tạm")
    async def setup(
        self,
        interaction: discord.Interaction,
        channel: discord.VoiceChannel
    ):
        if not interaction.guild:
            return await interaction.response.send_message(
                "❌ Lệnh này chỉ dùng trong server.",
                ephemeral=True
            )

        perms = interaction.user.guild_permissions
        if not perms.manage_channels:
            return await interaction.response.send_message(
                "⛔ Cần quyền **Quản lý kênh**.",
                ephemeral=True
            )

        cfg = load_json(interaction.guild.id, "config.json")
        cfg["tempvoice_channel"] = channel.id
        save_json(interaction.guild.id, "config.json", cfg)

        await interaction.response.send_message(
            f"✅ `{channel.name}` đã được đặt làm Create a Voice.",
            ephemeral=True
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(TempVoice(bot))