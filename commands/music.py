import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp
import asyncio
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
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(gid: int, filename: str, data: dict):
    path = os.path.join(ensure_guild_dir(gid), filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# yt-dlp + ffmpeg config
YDL_OPTIONS = {"format": "bestaudio", "noplaylist": True, "quiet": True}
FFMPEG_OPTIONS = {"options": "-vn"}

class MusicPanel(discord.ui.View):
    def __init__(self, music_cog, guild_id):
        super().__init__(timeout=None)
        self.music_cog = music_cog
        self.guild_id = guild_id

    @discord.ui.button(label="⏯ Pause/Resume", style=discord.ButtonStyle.primary)
    async def pause_resume(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = interaction.guild.voice_client
        if not vc:
            return await interaction.response.send_message("⚠️ Bot không trong voice.", ephemeral=True)
        if vc.is_playing():
            vc.pause()
            await interaction.response.send_message("⏸ Đã pause.", ephemeral=True)
        elif vc.is_paused():
            vc.resume()
            await interaction.response.send_message("▶️ Đã resume.", ephemeral=True)

    @discord.ui.button(label="⏭ Skip", style=discord.ButtonStyle.secondary)
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = interaction.guild.voice_client
        if not vc:
            return await interaction.response.send_message("⚠️ Bot không trong voice.", ephemeral=True)
        vc.stop()
        await interaction.response.send_message("⏭ Đã skip bài.", ephemeral=True)

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queue = {}   # {guild_id: [url, url]}
        self.panels = {}  # {guild_id: message_id}

    async def ensure_panel(self, interaction: discord.Interaction):
        cfg = load_json(interaction.guild.id, "config.json")
        panel_channel_id = cfg.get("voicepanel_channel")
        channel = interaction.channel if panel_channel_id is None else interaction.guild.get_channel(panel_channel_id)

        if not self.panels.get(interaction.guild.id):
            msg = await channel.send("🎶 **Music Panel**", view=MusicPanel(self, interaction.guild.id))
            self.panels[interaction.guild.id] = msg.id

    async def play_next(self, guild_id):
        if not self.queue.get(guild_id):
            return
        url = self.queue[guild_id].pop(0)
        guild = self.bot.get_guild(guild_id)
        vc = guild.voice_client
        if not vc:
            return

        def after_play(err):
            fut = asyncio.run_coroutine_threadsafe(self.play_next(guild_id), self.bot.loop)
            try:
                fut.result()
            except:
                pass

        vc.play(discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS), after=after_play)

    @app_commands.command(name="play", description="Phát nhạc từ YouTube/SoundCloud hoặc từ khóa tìm kiếm")
    async def play(self, interaction: discord.Interaction, query: str):
        if not interaction.user.voice or not interaction.user.voice.channel:
            return await interaction.response.send_message("⚠️ Bạn cần vào voice channel trước.", ephemeral=True)

        vc = interaction.guild.voice_client
        if not vc:
            vc = await interaction.user.voice.channel.connect()

        # lấy URL audio
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            if query.startswith("http"):
                info = ydl.extract_info(query, download=False)
            else:
                info = ydl.extract_info(f"ytsearch:{query}", download=False)["entries"][0]
            url = info["url"]
            title = info.get("title")

        self.queue.setdefault(interaction.guild.id, []).append(url)
        await interaction.response.send_message(f"🎶 Đã thêm **{title}** vào hàng chờ.")

        if not vc.is_playing() and not vc.is_paused():
            await self.ensure_panel(interaction)
            await self.play_next(interaction.guild.id)

    # group voicepanel
    voicepanel = app_commands.Group(name="voicepanel", description="Cài đặt Music Panel")

    @voicepanel.command(name="set", description="Chọn kênh text để hiển thị Music Panel")
    async def set_panel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        cfg = load_json(interaction.guild.id, "config.json")
        cfg["voicepanel_channel"] = channel.id
        save_json(interaction.guild.id, "config.json", cfg)
        await interaction.response.send_message(f"✅ Đã đặt kênh {channel.mention} làm Music Panel.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Music(bot))