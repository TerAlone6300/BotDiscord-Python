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

class AutoResponder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild or message.author.bot:
            return
        responses = load_json(message.guild.id, "responses.json")
        content = message.content.lower()
        for trigger, data in responses.items():
            mode = data.get("mode", "chứa")
            trg = trigger.lower()
            if (mode == "chínhxác" and content == trg) \
               or (mode == "chứa" and trg in content) \
               or (mode == "bắtdầu" and content.startswith(trg)) \
               or (mode == "kếtthúc" and content.endswith(trg)):
                await message.channel.send(data["response"])
                break

    # ======================= COMMANDS ==========================
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.checks.has_permissions(manage_messages=True)
    @app_commands.command(name="addresponse", description="Thêm AutoResponder (chỉ cho người có quyền Quản lý tin nhắn)")
    async def addresponse(self, interaction: discord.Interaction, trigger: str, response: str, mode: str = "chứa"):
        gid = interaction.guild.id
        responses = load_json(gid, "responses.json")
        if mode not in ["chínhxác","chứa","bắtdầu","kếtthúc"]:
            await interaction.response.send_message("⚠️ Mode không hợp lệ!", ephemeral=True)
            return
        responses[trigger] = {"response": response, "mode": mode}
        save_json(gid, "responses.json", responses)
        await interaction.response.send_message(f"✅ Đã thêm `{trigger}` (mode: {mode})", ephemeral=True)

    @app_commands.default_permissions(manage_messages=True)
    @app_commands.checks.has_permissions(manage_messages=True)
    @app_commands.command(name="delresponse", description="Xoá AutoResponder (chỉ cho người có quyền Quản lý tin nhắn)")
    async def delresponse(self, interaction: discord.Interaction, trigger: str):
        gid = interaction.guild.id
        responses = load_json(gid, "responses.json")
        if trigger in responses:
            del responses[trigger]
            save_json(gid, "responses.json", responses)
            await interaction.response.send_message(f"🗑️ Đã xoá `{trigger}`", ephemeral=True)
        else:
            await interaction.response.send_message("⚠️ Không tìm thấy!", ephemeral=True)

    @app_commands.default_permissions(manage_messages=True)
    @app_commands.checks.has_permissions(manage_messages=True)
    @app_commands.command(name="listresponses", description="Danh sách AutoResponder (chỉ cho người có quyền Quản lý tin nhắn)")
    async def listresponses(self, interaction: discord.Interaction):
        responses = load_json(interaction.guild.id, "responses.json")
        if not responses:
            await interaction.response.send_message("📭 Trống!", ephemeral=True)
        else:
            text = "\n".join([f"- `{k}` ({v['mode']}) → `{v['response']}`" for k,v in responses.items()])
            await interaction.response.send_message(f"📋 AutoResponder:\n{text}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(AutoResponder(bot))