import discord
from discord.ext import commands
from discord import app_commands

class RoleButton(discord.ui.Button):
    def __init__(self, role: discord.Role):
        super().__init__(label=role.name, style=discord.ButtonStyle.primary)
        self.role = role

    async def callback(self, interaction: discord.Interaction):
        if self.role in interaction.user.roles:
            await interaction.user.remove_roles(self.role)
            await interaction.response.send_message(f"❌ Gỡ role `{self.role.name}`", ephemeral=True)
        else:
            await interaction.user.add_roles(self.role)
            await interaction.response.send_message(f"✅ Thêm role `{self.role.name}`", ephemeral=True)

class RolePanel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="rolepanel", description="Tạo bảng chọn role bằng nút")
    async def rolepanel(self, interaction: discord.Interaction, role: discord.Role):
        view = discord.ui.View()
        view.add_item(RoleButton(role))
        await interaction.response.send_message(f"🎭 Bấm để nhận/gỡ role `{role.name}`", view=view)

async def setup(bot):
    await bot.add_cog(RolePanel(bot))