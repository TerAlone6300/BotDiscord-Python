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

class Ticket(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    ticket_group = app_commands.Group(name="ticket", description="Hệ thống ticket")

    @ticket_group.command(name="setup", description="Cài đặt category chứa ticket")
    async def ticket_setup(self, interaction: discord.Interaction, category: discord.CategoryChannel):
        cfg = load_json(interaction.guild.id, "config.json")
        cfg["ticket_category"] = category.id
        save_json(interaction.guild.id, "config.json", cfg)
        await interaction.response.send_message(f"✅ Ticket category: `{category.name}`", ephemeral=True)

    @commands.command()
    async def ticket(self, ctx: commands.Context):
        button = discord.ui.Button(label="🎫 Tạo Ticket", style=discord.ButtonStyle.green)

        async def button_callback(interaction: discord.Interaction):
            guild = interaction.guild
            cfg = load_json(guild.id, "config.json")
            cat = guild.get_channel(cfg.get("ticket_category")) if cfg.get("ticket_category") else None
            if not cat:
                cat = await guild.create_category("Tickets")
                cfg["ticket_category"] = cat.id
                save_json(guild.id, "config.json", cfg)

            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                interaction.user: discord.PermissionOverwrite(read_messages=True)
            }
            channel = await guild.create_text_channel(
                name=f"ticket-{interaction.user.name}",
                overwrites=overwrites,
                category=cat
            )
            await channel.send(f"🎟️ Chào {interaction.user.mention}, nhân viên sẽ hỗ trợ bạn sớm nhất!")
            await interaction.response.send_message("Đã tạo ticket cho bạn!", ephemeral=True)

        button.callback = button_callback
        view = discord.ui.View()
        view.add_item(button)
        await ctx.send("Bấm nút để tạo ticket:", view=view)

async def setup(bot):
    cog = Ticket(bot)
    await bot.add_cog(cog)