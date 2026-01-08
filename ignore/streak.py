import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import pytz, json, os

DATA_FILE = "streak_data.json"
TZ = pytz.timezone("Asia/Ho_Chi_Minh")

# ====== HÀM QUẢN LÝ DỮ LIỆU ======
def load_data():
    if not os.path.exists(DATA_FILE):
        print("⚠️ File dữ liệu chưa tồn tại, tạo mới...")
        return {"groups": {}, "users": {}}

    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            # Đảm bảo cấu trúc đầy đủ
            data.setdefault("groups", {})
            data.setdefault("users", {})
            return data
    except json.JSONDecodeError:
        print("⚠️ File JSON bị lỗi, khởi tạo lại.")
        return {"groups": {}, "users": {}}


def save_data(data):
    # Đảm bảo có key chính
    data.setdefault("groups", {})
    data.setdefault("users", {})
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)


# ====== COG CHÍNH ======
class StreakSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = load_data()
        print("✅ StreakSystem đã được load. Dữ liệu hiện có:",
              len(self.data["groups"]), "server,", len(self.data["users"]), "cặp user.")

    def today(self):
        return datetime.now(TZ).strftime("%Y-%m-%d")

    # ========== SERVER STREAK ==========
    @app_commands.command(name="streak-start", description="Bật hoặc tắt chế độ streak cho server này")
    @app_commands.describe(toggle="Bật (true) hoặc tắt (false)")
    async def streak_start(self, interaction: discord.Interaction, toggle: bool):
        guild_id = str(interaction.guild.id)
        self.data.setdefault("groups", {})

        guild_data = self.data["groups"].get(
            guild_id, {"enabled": False, "count": 0, "days": {}}
        )
        guild_data["enabled"] = toggle
        self.data["groups"][guild_id] = guild_data
        save_data(self.data)

        state = "✅ Đã bật" if toggle else "⛔ Đã tắt"
        await interaction.response.send_message(f"{state} chế độ **streak tự động** cho server này!")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        guild_id = str(message.guild.id)
        today = self.today()

        self.data.setdefault("groups", {})
        guild_data = self.data["groups"].get(
            guild_id, {"enabled": False, "count": 0, "days": {}}
        )

        if not guild_data.get("enabled", False):
            return  # server chưa bật streak → bỏ qua

        guild_data.setdefault("days", {})
        today_data = guild_data["days"].get(today, {"users": [], "complete": False})

        if today_data["complete"]:
            return

        user_id = str(message.author.id)
        if user_id not in today_data["users"]:
            today_data["users"].append(user_id)

        if len(today_data["users"]) >= 3 and not today_data["complete"]:
            guild_data["count"] += 1
            today_data["complete"] = True
            await message.channel.send(
                f"🔥 Server **{message.guild.name}** đã hoàn thành streak hôm nay!\n"
                f"Tổng streak hiện tại: `{guild_data['count']}` ngày!"
            )

        guild_data["days"][today] = today_data
        self.data["groups"][guild_id] = guild_data
        save_data(self.data)

    # ========== CÁ NHÂN STREAK ==========
    @app_commands.command(
    name="streak-daily",
    description="Giữ streak cá nhân với người khác (User Install)"
    )
    @app_commands.allowed_installs(guilds=True, users=True)  # 🔹 Cho phép cả Guild & User Install
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)  # 🔹 Bật cho DM

    @app_commands.describe(partner="Tag người bạn muốn giữ chuỗi cùng")
    async def streak_daily(self, interaction: discord.Interaction, partner: discord.User):
        self.data.setdefault("users", {})

        user_id = str(interaction.user.id)
        partner_id = str(partner.id)
        pair_key = "_".join(sorted([user_id, partner_id]))
        today = self.today()

        pair = self.data["users"].get(pair_key, {"count": 0, "days": {}})
        pair.setdefault("days", {})
        today_data = pair["days"].get(today, {"users": [], "complete": False})

        if today_data["complete"]:
            return await interaction.response.send_message(
                f"🔥 Hai bạn đã hoàn thành streak hôm nay! Tổng streak: `{pair['count']}`", ephemeral=True
            )

        if user_id not in today_data["users"]:
            today_data["users"].append(user_id)

        if len(today_data["users"]) == 2:
            pair["count"] += 1
            today_data["complete"] = True
            msg = f"✅ Cả hai đã check-in đủ! Streak hiện tại: `{pair['count']}` 🔥"
        else:
            msg = f"🕒 Đợi {partner.mention} check-in nữa để hoàn thành hôm nay!"

        pair["days"][today] = today_data
        self.data["users"][pair_key] = pair
        save_data(self.data)

        await interaction.response.send_message(msg)


# ====== SETUP COG ======
async def setup(bot: commands.Bot):
    await bot.add_cog(StreakSystem(bot))