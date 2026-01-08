import discord
from discord.ext import commands
import os
import asyncio
import aiohttp
import logging
import datetime
import sys
import traceback

# ===== LOG TO FILE + STDOUT =====
log_file = open("latest.log", "a", encoding="utf-8")

class Tee:
    def __init__(self, *files):
        self.files = files
    def write(self, data):
        for f in self.files:
            f.write(data)
            f.flush()
    def flush(self):
        for f in self.files:
            f.flush()

sys.stdout = Tee(sys.stdout, log_file)
sys.stderr = Tee(sys.stderr, log_file)

print("Bot started")

def log(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    msg = f"[{timestamp}] {message}"
    print(msg)
    with open("latest.log", "a", encoding="utf-8") as f:
        f.write(msg + "\n")

# ===== CONFIG =====
OWNER_ID = 0000000000000000000
BOTTOKEN = "YOUR_BOT_TOKEN_HERE"
OP_PASSWORD = "your_password_here"

# ===== LOGGING =====
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)

discord.utils.setup_logging(level=logging.INFO)
logging.getLogger("discord.http").setLevel(logging.CRITICAL)

# ===== INTENTS =====
intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.messages = True
intents.message_content = True
intents.presences = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ===== LOAD EXTENSIONS =====
async def load_extensions():
    for folder in ("commands", "extensions"):
        os.makedirs(folder, exist_ok=True)
        for file in os.listdir(folder):
            if file.endswith(".py"):
                module = f"{folder}.{file[:-3]}"
                try:
                    await bot.load_extension(module)
                    print(f"📦 Loaded: {module}")
                except Exception as e:
                    print(f"❌ Load error {module}: {e}")

# ===== SETUP HOOK (ĐÚNG CHUẨN) =====
@bot.setup_hook
async def setup_hook():
    await load_extensions()
    await bot.tree.sync()
    print("✅ Slash commands synced (GLOBAL)")

# ===== READY =====
@bot.event
async def on_ready():
    print(f"🤖 Logged in as {bot.user}")
    print(f"🔗 Connected to {len(bot.guilds)} guilds")

# ===== OP RELOAD SYSTEM =====
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    content = message.content.strip()
    if not content.startswith((f"<@{bot.user.id}>", f"<@!{bot.user.id}>")):
        await bot.process_commands(message)
        return

    args = content.split()
    if "--op" not in args or "--reload" not in args:
        return

    password = None
    if "--p" in args:
        i = args.index("--p")
        if i + 1 < len(args):
            password = args[i + 1]

    if not (password == OP_PASSWORD or message.author.id == OWNER_ID):
        return

    async def reload_folder(folder):
        for f in os.listdir(folder):
            if f.endswith(".py"):
                mod = f"{folder}.{f[:-3]}"
                try:
                    await bot.reload_extension(mod)
                    print(f"🔄 Reloaded {mod}")
                except commands.ExtensionNotLoaded:
                    await bot.load_extension(mod)
                    print(f"➕ Loaded {mod}")
                except Exception as e:
                    print(f"❌ Reload error {mod}: {e}")

    if "commands" in args or "both" in args:
        await reload_folder("commands")
    if "extensions" in args or "both" in args:
        await reload_folder("extensions")

    await message.add_reaction("✅")
    await bot.process_commands(message)

# ===== SLASH ERROR HANDLER =====
@bot.tree.error
async def on_app_command_error(interaction, error):
    traceback.print_exception(type(error), error, error.__traceback__)
    try:
        if interaction.response.is_done():
            await interaction.followup.send(f"⚠️ `{error}`", ephemeral=True)
        else:
            await interaction.response.send_message(f"⚠️ `{error}`", ephemeral=True)
    except discord.HTTPException:
        pass

# ===== RUN =====
async def main():
    async with bot:
        await bot.start(BOTTOKEN)

if __name__ == "__main__":
    asyncio.run(main())