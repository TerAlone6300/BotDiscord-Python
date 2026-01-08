import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional

# Bật / tắt debug log
DEBUG_MODE: bool = False


class Listening(commands.Cog):
    """Hiển thị bài hát Spotify mà người dùng đang nghe."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # cache: guild_id -> { user_id: spotify_info }
        self._presence_cache: dict[int, dict[int, dict]] = {}

    # ====== Cache helper ======
    def _cache_spotify(
        self, guild_id: int, user_id: int, spotify_activity: Optional[discord.Spotify]
    ):
        """Lưu trạng thái Spotify vào cache."""
        self._presence_cache.setdefault(guild_id, {})
        if spotify_activity is None:
            self._presence_cache[guild_id].pop(user_id, None)
            return

        self._presence_cache[guild_id][user_id] = {
            "title": spotify_activity.title,
            "artists": spotify_activity.artists,
            "album": spotify_activity.album,
            "cover": spotify_activity.album_cover_url,
            "start": spotify_activity.start,
            "end": spotify_activity.end,
        }

    # ====== Presence tracking ======
    @commands.Cog.listener()
    async def on_presence_update(
        self, before: discord.Member, after: discord.Member
    ) -> None:
        """Cập nhật cache khi người dùng thay đổi hoạt động."""
        guild = after.guild
        if not guild:
            return
        gid, uid = guild.id, after.id

        spotify = next(
            (a for a in after.activities if isinstance(a, discord.Spotify)), None
        )
        self._cache_spotify(gid, uid, spotify)

        if DEBUG_MODE:
            if spotify:
                print(
                    f"[Presence] {after} -> {spotify.title} - {', '.join(spotify.artists)} ({guild.name})"
                )
            else:
                print(f"[Presence] {after} không còn Spotify activity.")

    # ====== /listening command ======
    @app_commands.command(
        name="listening", description="Xem người dùng đang nghe bài hát nào trên Spotify."
    )
    @app_commands.describe(user="Người bạn muốn xem (mặc định là bạn)")
    async def listening(
        self, interaction: discord.Interaction, user: Optional[discord.Member] = None
    ):
        """Slash command chính: /listening"""
        user = user or interaction.user
        guild = interaction.guild

        # Ép chunk để cập nhật presence mới nhất
        try:
            if guild:
                await guild.chunk(cache=True)
                if DEBUG_MODE:
                    print(f"[Chunk] {guild.name} ({len(guild.members)} members loaded)")
        except Exception as e:
            if DEBUG_MODE:
                print(f"[Chunk][WARN] {e}")

        # Tìm Spotify activity trực tiếp
        spotify_activity = next(
            (a for a in user.activities if isinstance(a, discord.Spotify)), None
        )

        # Nếu không có, thử lấy từ cache
        if not spotify_activity:
            cached = self._presence_cache.get(guild.id if guild else None, {}).get(
                user.id
            )
            if cached:
                return await self._send_embed(
                    interaction, user, cached, cached_mode=True
                )

            # không tìm thấy -> thông báo
            await interaction.response.send_message(
                f"🎧 Không thấy {user.display_name} đang nghe nhạc trên Spotify.",
                ephemeral=True,
            )
            return

        # Có spotify activity trực tiếp
        await self._send_embed(interaction, user, spotify_activity)

    # ====== Embed builder ======
    async def _send_embed(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        data,
        cached_mode: bool = False,
    ):
        """Tạo và gửi embed Spotify (từ object hoặc cache dict)."""
        if isinstance(data, discord.Spotify):
            title = data.title
            artists = data.artists
            album = data.album
            cover = data.album_cover_url
            start = data.start
            end = data.end
        else:
            title = data.get("title")
            artists = data.get("artists", [])
            album = data.get("album")
            cover = data.get("cover")
            start = data.get("start")
            end = data.get("end")

        embed = discord.Embed(
            title=f"🎶 {user.display_name} đang lắng nghe"
            + ("" if cached_mode else ""),
            description=f"**{title}**\nTừ album **{album}**\nBởi {', '.join(artists)}",
            color=discord.Color.green(),
        )

        if cover:
            embed.set_thumbnail(url=cover)

        # Thanh tiến trình bài hát
        if start and end:
            try:
                elapsed = (discord.utils.utcnow() - start).total_seconds()
                duration = (end - start).total_seconds()
                if duration > 0:
                    progress = max(0, min(20, int((elapsed / duration) * 20)))
                    bar = "▬" * progress + "🔘" + "▬" * (20 - progress)
                    embed.add_field(name="Đang phát", value=f"`{bar}`", inline=False)
            except Exception as e:
                if DEBUG_MODE:
                    print(f"[Progress][WARN] {e}")

        # 💡 Dòng này giúp hiển thị thời gian auto như MasterSMP
        embed.timestamp = discord.utils.utcnow()
        embed.set_footer(
            text="Dữ liệu từ hoạt động Spotify trên Discord"
            + ("" if cached_mode else "")
        )

        await interaction.response.send_message(embed=embed)


# ====== Setup Cog ======
async def setup(bot: commands.Bot):
    existing = bot.tree.get_command("listening")
    if existing:
        try:
            bot.tree.remove_command(
                "listening", type=discord.AppCommandType.chat_input
            )
        except Exception:
            pass
    await bot.add_cog(Listening(bot))