import discord
from discord.ext import commands, tasks
from discord import app_commands
import os, json, datetime, asyncio
from typing import Literal, Optional
from zoneinfo import ZoneInfo

# ====== Cấu hình chung ======
SAVE_BASE = "saves"
TZ_VN = ZoneInfo("Asia/Ho_Chi_Minh")
DAILY_FILE = "msg_log_daily.json"
WEEKLY_FILE = "msg_log_weekly.json"


# ====== Helper lưu & đọc ======
def ensure_cache_dir(gid: int):
    path = os.path.join(SAVE_BASE, str(gid), "cache")
    os.makedirs(path, exist_ok=True)
    return path


def load_json(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


def save_json(path: str, data: dict):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


# ====== Ghi log tin nhắn ======
def add_message(gid: int, uid: int):
    cache_dir = ensure_cache_dir(gid)
    daily_path = os.path.join(cache_dir, DAILY_FILE)
    weekly_path = os.path.join(cache_dir, WEEKLY_FILE)

    daily = load_json(daily_path)
    weekly = load_json(weekly_path)

    uid = str(uid)
    daily[uid] = daily.get(uid, 0) + 1
    weekly[uid] = weekly.get(uid, 0) + 1

    save_json(daily_path, daily)
    save_json(weekly_path, weekly)


# ====== Lớp chính ======
class BangXepHang(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.daily_reset.start()
        self.weekly_reset.start()

    # ====== Ghi tin nhắn ======
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return
        add_message(message.guild.id, message.author.id)

    # ====== Reset tự động ======
    @tasks.loop(minutes=1)
    async def daily_reset(self):
        now = datetime.datetime.now(TZ_VN)
        if now.hour == 0 and now.minute == 0:
            for guild in self.bot.guilds:
                cache_dir = ensure_cache_dir(guild.id)
                save_json(os.path.join(cache_dir, DAILY_FILE), {})
                print(f"🕛 Reset BXH ngày: {guild.name}")
            await asyncio.sleep(60)

    @tasks.loop(minutes=1)
    async def weekly_reset(self):
        now = datetime.datetime.now(TZ_VN)
        if now.weekday() == 6 and now.hour == 23 and now.minute == 59:
            for guild in self.bot.guilds:
                cache_dir = ensure_cache_dir(guild.id)
                save_json(os.path.join(cache_dir, WEEKLY_FILE), {})
                print(f"📅 Reset BXH tuần: {guild.name}")
            await asyncio.sleep(60)

    # ====== Leaderboard ======
    def get_leaderboard(self, gid: int, period: str):
        cache_dir = ensure_cache_dir(gid)
        path = os.path.join(cache_dir, DAILY_FILE if period == "24h" else WEEKLY_FILE)
        data = load_json(path)
        return [(int(uid), cnt) for uid, cnt in sorted(data.items(), key=lambda x: x[1], reverse=True)]

    def make_embed_page(self, interaction, entries, page, per_page, label):
        total = len(entries)
        pages = max(1, (total + per_page - 1) // per_page)
        start = page * per_page
        chunk = entries[start:start + per_page]

        embed = discord.Embed(
            title=f"📊 Bảng Xếp Hạng Tin Nhắn — {label}",
            description=f"Server: **{interaction.guild.name}**",
            color=discord.Color.blurple(),
            timestamp=datetime.datetime.now(TZ_VN)
        )

        if not chunk:
            embed.add_field(
                name="Không có dữ liệu",
                value="Chưa có ai gửi tin nhắn trong khoảng thời gian này.",
                inline=False
            )
        else:
            lines = []
            for i, (uid, cnt) in enumerate(chunk, start=start + 1):
                member = interaction.guild.get_member(uid)
                name = member.display_name if member else f"ID {uid}"
                lines.append(f"**#{i}** — {name} — `{cnt}` tin nhắn")

            embed.add_field(
                name=f"Trang {page + 1}/{pages}",
                value="\n".join(lines),
                inline=False
            )

        embed.set_footer(
            text=f"Yêu cầu bởi {interaction.user}",
            icon_url=interaction.user.display_avatar.url
        )
        return embed, pages

    # ====== View chuyển trang ======
    class PagerView(discord.ui.View):
        def __init__(self, cog, interaction, entries, per_page, label):
            super().__init__(timeout=180)
            self.cog = cog
            self.interaction = interaction
            self.entries = entries
            self.per_page = per_page
            self.label = label
            self.page = 0
            self.author_id = interaction.user.id

        async def interaction_check(self, interaction: discord.Interaction):
            if interaction.user.id != self.author_id:
                await interaction.response.send_message(
                    "⚠️ Chỉ người yêu cầu mới dùng được nút này.", ephemeral=True
                )
                return False
            return True

        async def update_message(self, interaction):
            embed, pages = self.cog.make_embed_page(
                self.interaction, self.entries, self.page, self.per_page, self.label
            )
            self.prev_button.disabled = self.page <= 0
            self.next_button.disabled = self.page >= pages - 1
            await interaction.edit_original_response(embed=embed, view=self)

        @discord.ui.button(label="⏮️ Trước", style=discord.ButtonStyle.secondary, disabled=True)
        async def prev_button(self, interaction: discord.Interaction, _):
            if self.page > 0:
                self.page -= 1
            await self.update_message(interaction)

        @discord.ui.button(label="⏭️ Tiếp", style=discord.ButtonStyle.secondary)
        async def next_button(self, interaction: discord.Interaction, _):
            pages = max(1, (len(self.entries) + self.per_page - 1) // self.per_page)
            if self.page < pages - 1:
                self.page += 1
            await self.update_message(interaction)

        async def on_timeout(self):
            for child in self.children:
                child.disabled = True
            try:
                await self.interaction.edit_original_response(view=self)
            except:
                pass

    # ====== Slash command ======
    @app_commands.command(
        name="bangxephang",
        description="Xem bảng xếp hạng tin nhắn (24h hoặc 1w)"
    )
    @app_commands.describe(period="24h (mặc định) hoặc 1w (tuần này)")
    async def bangxephang(
        self,
        interaction: discord.Interaction,
        period: Optional[Literal["24h", "1w"]] = None
    ):
        await interaction.response.defer(thinking=True)

        if period not in ("24h", "1w"):
            period = "24h"

        label = "24 giờ gần nhất" if period == "24h" else "Tuần này"
        entries = self.get_leaderboard(interaction.guild.id, period)

        embed, _ = self.make_embed_page(interaction, entries, 0, 10, label)
        view = BangXepHang.PagerView(self, interaction, entries, 10, label)

        await interaction.followup.send(embed=embed, view=view)


# ====== Setup ======
async def setup(bot):
    existing = bot.tree.get_command("bangxephang")
    if existing:
        bot.tree.remove_command(
            "bangxephang",
            type=discord.AppCommandType.chat_input
        )
        await bot.add_cog(BangXepHang(bot))
        view = BangXepHang.PagerView(self, interaction, entries, 10, label)
        await interaction.followup.send(embed=embed, view=view)


# ====== Setup ======
async def setup(bot):
    existing = bot.tree.get_command("bangxephang")
    if existing:
        bot.tree.remove_command("bangxephang", type=discord.AppCommandType.chat_input)
    await bot.add_cog(BangXepHang(bot))