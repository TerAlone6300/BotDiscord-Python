import discord
from discord.ext import commands, tasks
from discord import app_commands
import os, json, datetime

SAVE_PATH = "saves"

# === Helpers ===
def ensure_cache_dir(gid: int):
    path = os.path.join(SAVE_PATH, str(gid), "cache")
    os.makedirs(path, exist_ok=True)
    return path

def message_path(gid: int):
    return os.path.join(ensure_cache_dir(gid), "message.json")

def user_toggle_path(gid: int, uid: int):
    return os.path.join(ensure_cache_dir(gid), f"{uid}.json")

def load_user_toggle(gid: int, uid: int):
    path = user_toggle_path(gid, uid)
    if not os.path.exists(path):
        return {"enabled": True}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_user_toggle(gid: int, uid: int, data: dict):
    path = user_toggle_path(gid, uid)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def save_message(gid: int, data: dict):
    path = message_path(gid)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def load_message(gid: int):
    path = message_path(gid)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def is_expired(data: dict):
    if "time" not in data:
        return True
    try:
        t = datetime.datetime.fromisoformat(data["time"])
        return (datetime.datetime.utcnow() - t).days >= 7
    except:
        return True

# === Cog ===
class Snipe(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.clean_old.start()

    # Lưu tin bị xoá
    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return
        toggle = load_user_toggle(message.guild.id, message.author.id)
        if not toggle.get("enabled", True):
            return
        data = {
            "type": "delete",
            "author": str(message.author),
            "author_id": message.author.id,
            "content": message.content,
            "channel": message.channel.id,
            "time": datetime.datetime.utcnow().isoformat()
        }
        save_message(message.guild.id, data)

    # Lưu tin bị sửa
    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if before.author.bot or not before.guild:
            return
        if before.content == after.content:
            return
        toggle = load_user_toggle(before.guild.id, before.author.id)
        if not toggle.get("enabled", True):
            return
        data = {
            "type": "edit",
            "author": str(before.author),
            "author_id": before.author.id,
            "before": before.content,
            "after": after.content,
            "channel": before.channel.id,
            "time": datetime.datetime.utcnow().isoformat()
        }
        save_message(before.guild.id, data)

    # Slash group
    snipe = app_commands.Group(name="snipe", description="Xem hoặc quản lý snipe")

    @snipe.command(name="view", description="Xem tin nhắn bị xoá/chỉnh sửa gần nhất")
    async def snipe_view(self, interaction: discord.Interaction):
        data = load_message(interaction.guild.id)
        if not data or is_expired(data):
            return await interaction.response.send_message("⚠️ Không có tin nhắn được lưu hoặc đã quá 7 ngày.", ephemeral=True)

        ch = interaction.guild.get_channel(data["channel"])
        t = datetime.datetime.fromisoformat(data["time"]).strftime("%H:%M:%S - %d/%m/%Y")
        embed = discord.Embed(color=discord.Color.blurple())

        if data["type"] == "delete":
            embed.title = "🕵️ Tin nhắn bị xoá"
            embed.add_field(name="Tác giả", value=data["author"], inline=False)
            embed.add_field(name="Nội dung", value=data["content"] or "*Không có nội dung*", inline=False)
        else:
            embed.title = "✏️ Tin nhắn bị chỉnh sửa"
            embed.add_field(name="Tác giả", value=data["author"], inline=False)
            embed.add_field(name="Trước khi sửa", value=data.get("before") or "*Không có nội dung*", inline=False)
            embed.add_field(name="Sau khi sửa", value=data.get("after") or "*Không có nội dung*", inline=False)

        embed.set_footer(text=f"Kênh: #{ch} • {t}")
        await interaction.response.send_message(embed=embed)

    @snipe.command(name="toggle", description="Bật/tắt việc bot lưu tin nhắn của bạn (yêu cầu quyền quản lý)")
    async def snipe_toggle(self, interaction: discord.Interaction):
        member = interaction.user
        if not (member.guild_permissions.manage_messages or member.guild_permissions.manage_channels):
            return await interaction.response.send_message(
                "⛔ Bạn cần quyền **Quản lý tin nhắn** hoặc **Quản lý phòng** để dùng lệnh này.",
                ephemeral=True
            )
        gid, uid = interaction.guild.id, member.id
        toggle = load_user_toggle(gid, uid)
        toggle["enabled"] = not toggle.get("enabled", True)
        save_user_toggle(gid, uid, toggle)
        status = "✅ Đã bật — bot sẽ lưu tin nhắn của bạn." if toggle["enabled"] else "🚫 Đã tắt — bot sẽ bỏ qua tin nhắn của bạn."
        await interaction.response.send_message(status, ephemeral=True)

    # Cleaning old messages (>7 days)
    @tasks.loop(hours=12)
    async def clean_old(self):
        for gdir in os.listdir(SAVE_PATH):
            cache = os.path.join(SAVE_PATH, gdir, "cache", "message.json")
            if os.path.exists(cache):
                try:
                    with open(cache, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if is_expired(data):
                        os.remove(cache)
                        print(f"[SnipeCleaner] Removed expired snipe for guild {gdir}")
                except Exception as e:
                    print(f"[SnipeCleaner] Error checking {gdir}: {e}")

    @clean_old.before_loop
    async def before_clean(self):
        await self.bot.wait_until_ready()

# === setup ===
async def setup(bot):
    # remove any existing slash command named "snipe" to avoid duplicates
    existing = bot.tree.get_command("snipe")
    if existing is not None:
        try:
            bot.tree.remove_command("snipe", type=discord.AppCommandType.chat_input)
        except Exception:
            pass

    cog = Snipe(bot)
    await bot.add_cog(cog)
    # DO NOT call bot.tree.add_command(cog.snipe) here — adding the cog registers the group