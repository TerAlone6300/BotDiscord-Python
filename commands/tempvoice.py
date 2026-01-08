import discord
from discord.ext import commands
from discord import app_commands
import os, json
from collections import defaultdict

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

class TempVoice(commands.Cog):
    """
    Temporary voice channels:
    - Admin sets a "create" voice channel with /tempvoice setup
    - When a user joins that channel, bot creates a private voice channel and moves them
    - When the created channel becomes empty, bot deletes it
    """
    def __init__(self, bot):
        self.bot = bot
        # mapping: guild_id -> { temp_channel_id: owner_id }
        self.user_channels = defaultdict(dict)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        # ignore if not in a guild (DMs)
        if member.guild is None:
            return

        gid = member.guild.id
        cfg = load_json(gid, "config.json")
        create_id = cfg.get("tempvoice_channel")

        # --- User joined the "create" channel: make a new voice channel and move them ---
        if after.channel and create_id and after.channel.id == create_id:
            # choose category same as the create channel (if any)
            category = after.channel.category
            # create a channel name (you can customize here)
            channel_name = f"🔊 Phòng của {member.display_name}"
            try:
                new_channel = await member.guild.create_voice_channel(name=channel_name, category=category)
            except Exception:
                # fallback: create without category
                new_channel = await member.guild.create_voice_channel(name=channel_name)

            # record owner
            self.user_channels[gid][new_channel.id] = member.id

            # try to move the user into new_channel
            try:
                await member.move_to(new_channel)
            except Exception:
                # if move fails, still keep the channel (admin can move manually)
                pass

            return  # done for join handling

        # --- User left a channel: if it's one of our temp channels and it's empty -> delete it ---
        # handle the case where before.channel exists and is tracked
        if before.channel:
            old_ch = before.channel
            old_id = old_ch.id
            if old_id in self.user_channels.get(gid, {}):
                # if channel empty -> delete and cleanup map
                try:
                    if len(old_ch.members) == 0:
                        try:
                            await old_ch.delete()
                        except Exception:
                            pass
                        # remove from map safely
                        try:
                            del self.user_channels[gid][old_id]
                        except KeyError:
                            pass
                except Exception:
                    # if reading members fails for some reason, attempt delete anyway
                    try:
                        await old_ch.delete()
                    except:
                        pass
                    try:
                        del self.user_channels[gid][old_id]
                    except:
                        pass

    # Slash group for tempvoice
    temp_group = app_commands.Group(name="tempvoice", description="Các lệnh tạm thời cho voice")

    @temp_group.command(name="setup", description="Chọn kênh voice làm 'Create a Voice'")
    @app_commands.describe(channel="Chọn kênh voice mà user join sẽ trigger tạo phòng")
    async def setup(self, interaction: discord.Interaction, channel: discord.VoiceChannel):
        if interaction.guild is None:
            await interaction.response.send_message("Lệnh chỉ dùng trong server.", ephemeral=True)
            return
        cfg = load_json(interaction.guild.id, "config.json")
        cfg["tempvoice_channel"] = channel.id
        save_json(interaction.guild.id, "config.json", cfg)
        await interaction.response.send_message(f"✅ Đã đặt kênh `{channel.name}` làm Create a Voice", ephemeral=True)

async def setup(bot):
    await bot.add_cog(TempVoice(bot))