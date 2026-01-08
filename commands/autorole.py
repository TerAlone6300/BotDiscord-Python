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

class AutoRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Khi có thành viên mới join thì add role nếu đã config
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        cfg = load_json(member.guild.id, "config.json")
        role_id = cfg.get("auto_role")
        if role_id:
            role = member.guild.get_role(role_id)
            if role:
                try:
                    await member.add_roles(role)
                except:
                    pass

    # Slash command group auto
    auto_group = app_commands.Group(name="auto", description="Cài đặt auto-role")

    @auto_group.command(name="role", description="Đặt role tự động khi thành viên mới vào")
    async def auto_role(self, interaction: discord.Interaction, role: discord.Role):
        cfg = load_json(interaction.guild.id, "config.json")
        cfg["auto_role"] = role.id
        save_json(interaction.guild.id, "config.json", cfg)
        await interaction.response.send_message(f"✅ Auto-role đã đặt: `{role.name}`", ephemeral=True)

async def setup(bot):
    await bot.add_cog(AutoRole(bot))