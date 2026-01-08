import discord
from discord.ext import commands
from datetime import timedelta

class Moderator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ===== TIMEOUT =====
    @commands.hybrid_command(name="timeout", description="Timeout một thành viên")
    async def timeout(self, ctx, member: discord.Member, duration: int, *, reason: str | None = None):

        perms = ctx.author.guild_permissions
        if not perms.manage_members:
            return await ctx.reply(
                "❌ Bạn cần quyền **Manage Members**.",
                ephemeral=bool(ctx.interaction)
            )

        if member == ctx.author:
            return await ctx.reply("❌ Không thể timeout chính mình.", ephemeral=bool(ctx.interaction))

        if member.top_role >= ctx.author.top_role:
            return await ctx.reply("❌ Role của bạn không đủ cao.", ephemeral=bool(ctx.interaction))

        until = discord.utils.utcnow() + timedelta(seconds=duration)
        await member.timeout(until, reason=reason)

        await ctx.reply(
            f"🔇 {member.mention} bị timeout **{duration}s**",
            ephemeral=bool(ctx.interaction)
        )

    # ===== KICK =====
    @commands.hybrid_command(name="kick")
    async def kick(self, ctx, member: discord.Member, *, reason: str | None = None):

        if not ctx.author.guild_permissions.kick_members:
            return await ctx.reply("❌ Cần quyền **Kick Members**.", ephemeral=bool(ctx.interaction))

        if member.top_role >= ctx.author.top_role:
            return await ctx.reply("❌ Role không đủ cao.", ephemeral=bool(ctx.interaction))

        await member.kick(reason=reason)
        await ctx.reply(f"👢 {member} đã bị kick.", ephemeral=bool(ctx.interaction))

    # ===== BAN =====
    @commands.hybrid_command(name="ban")
    async def ban(self, ctx, member: discord.Member, *, reason: str | None = None):

        if not ctx.author.guild_permissions.ban_members:
            return await ctx.reply("❌ Cần quyền **Ban Members**.", ephemeral=bool(ctx.interaction))

        if member.top_role >= ctx.author.top_role:
            return await ctx.reply("❌ Role không đủ cao.", ephemeral=bool(ctx.interaction))

        await member.ban(reason=reason, delete_message_days=1)
        await ctx.reply(f"🔨 {member} đã bị ban.", ephemeral=bool(ctx.interaction))

async def setup(bot):
    await bot.add_cog(Moderator(bot))