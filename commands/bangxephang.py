import discord
from discord.ext import commands, tasks
from discord import app_commands
import os, json, datetime
from typing import Literal, Optional
from zoneinfo import ZoneInfo

SAVE_BASE = "saves"
TZ_VN = ZoneInfo("Asia/Ho_Chi_Minh")
DAILY_FILE = "msg_log_daily.json"
WEEKLY_FILE = "msg_log_weekly.json"


def ensure_cache_dir(gid: int) -> str:
    path = os.path.join(SAVE_BASE, str(gid), "cache")
    os.makedirs(path, exist_ok=True)
    return path


def load_json(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_json(path: str, data: dict):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def add_message(gid: int, uid: int):
    cache = ensure_cache_dir(gid)
    for file in (DAILY_FILE, WEEKLY_FILE):
        path = os.path.join(cache, file)
        data = load_json(path)
        uid = str(uid)
        data[uid] = data.get(uid, 0) + 1
        save_json(path, data)


class BangXepHang(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        self.daily_reset.start()
        self.weekly_reset.start()

    async def cog_unload(self):
        self.daily_reset.cancel()
        self.weekly_reset.cancel()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return
        add_message(message.guild.id, message.author.id)
        await self.bot.process_commands(message)

    @tasks.loop(time=datetime.time(hour=0, minute=0, tzinfo=TZ_VN))
    async def daily_reset(self):
        for g in self.bot.guilds:
            save_json(os.path.join(ensure_cache_dir(g.id), DAILY_FILE), {})

    @tasks.loop(time=datetime.time(hour=23, minute=59, tzinfo=TZ_VN))
    async def weekly_reset(self):
        if datetime.datetime.now(TZ_VN).weekday() == 6:
            for g in self.bot.guilds:
                save_json(os.path.join(ensure_cache_dir(g.id), WEEKLY_FILE), {})

    def get_leaderboard(self, gid: int, period: str):
        file = DAILY_FILE if period == "24h" else WEEKLY_FILE
        data = load_json(os.path.join(ensure_cache_dir(gid), file))
        return sorted(
            [(int(uid), cnt) for uid, cnt in data.items()],
            key=lambda x: x[1],
            reverse=True
        )

    @app_commands.command(name="bangxephang", description="Xem BXH tin nhắn")
    @app_commands.describe(period="24h hoặc 1w")
    async def bangxephang(
        self,
        interaction: discord.Interaction,
        period: Optional[Literal["24h", "1w"]] = "24h"
    ):
        if not interaction.guild:
            return await interaction.response.send_message(
                "❌ Lệnh này chỉ dùng trong server.",
                ephemeral=True
            )

        entries = self.get_leaderboard(interaction.guild.id, period)
        desc = "\n".join(
            f"#{i+1} <@{uid}> — `{cnt}`"
            for i, (uid, cnt) in enumerate(entries[:10])
        ) or "Chưa có dữ liệu."

        embed = discord.Embed(
            title="📊 Bảng xếp hạng tin nhắn",
            description=desc,
            color=discord.Color.blurple(),
            timestamp=datetime.datetime.now(TZ_VN)
        )

        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(BangXepHang(bot))