import discord
from discord.ext import commands
from discord import app_commands
import os, json

SAVE_PATH = "saves"

def ensure_guild_dir(gid: int):
    path = os.path.join(SAVE_PATH, str(gid))
    os.makedirs(path, exist_ok=True)
    return path

def load_json(gid: int, filename: str):
    path = os.path.join(ensure_guild_dir(gid), filename)
    if not os.path.exists(path):
        return {}
    return json.load(open(path, "r", encoding="utf-8"))

def save_json(gid: int, filename: str, data: dict):
    path = os.path.join(ensure_guild_dir(gid), filename)
    json.dump(data, open(path, "w", encoding="utf-8"), indent=4, ensure_ascii=False)

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        cfg = load_json(member.guild.id, "config.json")
        ch_id = cfg.get("welcome_channel")
        if ch_id:
            ch = member.guild.get_channel(ch_id)
            if ch:
                await ch.send(f"🎉 Chào mừng {member.mention} đến với **{member.guild.name}**!")

    welcome_group = app_commands.Group(name="welcome", description="Cài đặt chào mừng")

    @welcome_group.command(name="setup", description="Cài đặt kênh chào mừng")
    async def welcome_setup(self, interaction: discord.Interaction, channel: discord.TextChannel):
        cfg = load_json(interaction.guild.id, "config.json")
        cfg["welcome_channel"] = channel.id
        save_json(interaction.guild.id, "config.json", cfg)
        await interaction.response.send_message(f"✅ Welcome channel: {channel.mention}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Welcome(bot))