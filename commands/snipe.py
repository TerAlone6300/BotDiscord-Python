import discord
from discord.ext import commands, tasks
from discord import app_commands
import os, json, datetime

SAVE_PATH = "saves"


# ===== Helpers =====
def ensure_cache_dir(gid: int) -> str:
    path = os.path.join(SAVE_PATH, str(gid), "cache")
    os.makedirs(path, exist_ok=True)
    return path


def message_path(gid: int) -> str:
    return os.path.join(ensure_cache_dir(gid), "message.json")


def user_toggle_path(gid: int, uid: int) -> str:
    return os.path.join(ensure_cache_dir(gid), f"{uid}.json")


def load_user_toggle(gid: int, uid: int) -> dict:
    path = user_toggle_path(gid, uid)
    if not os.path.exists(path):
        return {"enabled": True}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_user_toggle(gid: int, uid: int, data: dict):
    with open(user_toggle_path(gid, uid), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def save_message(gid: int, data: dict):
    with open(message_path(gid), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def load_message(gid: int):
    path = message_path(gid)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def is_expired(data: dict) -> bool:
    try:
        t = datetime.datetime.fromisoformat(data["time"])
        return (datetime.datetime.utcnow() - t).days >= 7
    except Exception:
        return True


# ===== Cog =====
class Snipe(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        self.clean_old.start()

    async def cog_unload(self):
        self.clean_old.cancel()

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if not message.guild or message.author.bot:
            return

        toggle = load_user_toggle(message.guild.id, message.author.id)
        if not toggle.get("enabled", True):
            return

        save_message(message.guild.id, {
            "type": "delete",
            "author": str(message.author),
            "author_id": message.author.id,
            "content": message.content,
            "channel": message.channel.id,
            "time": datetime.datetime.utcnow().isoformat()
        })

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if not before.guild or before.author.bot:
            return
        if before.content == after.content:
            return

        toggle = load_user_toggle(before.guild.id, before.author.id)
        if not toggle.get("enabled", True):
            return

        save_message(before.guild.id, {
            "type": "edit",
            "author": str(before.author),
            "author_id": before.author.id,
            "before": before.content,
            "after": after.content,
            "channel": before.channel.id,
            "time": datetime.datetime.utcnow().isoformat()
        })

    snipe = app_commands.Group(
        name="snipe",
        description="Xem hoặc quản lý tin nhắn đã xoá/chỉnh sửa"
    )

    @snipe.command(name="view")
    async def snipe_view(self, interaction: discord.Interaction):
        if not interaction.guild:
            return await interaction.response.send_message(
                "❌ Lệnh này chỉ dùng trong server.",
                ephemeral=True
            )

        data = load_message(interaction.guild.id)
        if not data or is_expired(data):
            return await interaction.response.send_message(
                "⚠️ Không có dữ liệu snipe hợp lệ.",
                ephemeral=True
            )

        channel = interaction.guild.get_channel(data["channel"])
        ts = datetime.datetime.fromisoformat(data["time"]).strftime("%d/%m/%Y %H:%M")

        embed = discord.Embed(color=discord.Color.blurple())
        embed.title = "🕵️ Tin nhắn bị xoá" if data["type"] == "delete" else "✏️ Tin nhắn bị chỉnh sửa"

        embed.add_field(name="Tác giả", value=data["author"], inline=False)

        if data["type"] == "delete":
            embed.add_field(
                name="Nội dung",
                value=data["content"] or "*Không có nội dung*",
                inline=False
            )
        else:
            embed.add_field(name="Trước", value=data["before"] or "*Trống*", inline=False)
            embed.add_field(name="Sau", value=data["after"] or "*Trống*", inline=False)

        embed.set_footer(text=f"Kênh: #{channel} • {ts}")
        await interaction.response.send_message(embed=embed)

    @snipe.command(name="toggle")
    async def snipe_toggle(self, interaction: discord.Interaction):
        if not interaction.guild:
            return await interaction.response.send_message(
                "❌ Không dùng trong DM.",
                ephemeral=True
            )

        perms = interaction.user.guild_permissions
        if not (perms.manage_messages or perms.manage_channels):
            return await interaction.response.send_message(
                "⛔ Cần quyền quản lý.",
                ephemeral=True
            )

        gid, uid = interaction.guild.id, interaction.user.id
        toggle = load_user_toggle(gid, uid)
        toggle["enabled"] = not toggle.get("enabled", True)
        save_user_toggle(gid, uid, toggle)

        await interaction.response.send_message(
            "✅ Đã bật snipe." if toggle["enabled"] else "🚫 Đã tắt snipe.",
            ephemeral=True
        )

    @tasks.loop(hours=12)
    async def clean_old(self):
        if not os.path.exists(SAVE_PATH):
            return

        for gdir in os.listdir(SAVE_PATH):
            if not gdir.isdigit():
                continue
            path = os.path.join(SAVE_PATH, gdir, "cache", "message.json")
            if not os.path.exists(path):
                continue
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if is_expired(data):
                    os.remove(path)
            except Exception:
                pass

    @clean_old.before_loop
    async def before_clean(self):
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot):
    await bot.add_cog(Snipe(bot))