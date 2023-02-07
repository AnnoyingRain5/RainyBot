from discord.ext import commands
import discord
from discord.commands import SlashCommandGroup
from lib.DatabaseManager import Database


class VegetableGame(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    VegetableGameSlashGroup = SlashCommandGroup(
        "veg", "Interact with the Vegetable game!")

    @commands.Cog.listener()
    async def on_ready(self):
        self.db = Database("VegetableGame")

    @VegetableGameSlashGroup.command(description="View the current game board")
    async def viewboard(self, ctx, showownrange: bool, showallranges: bool):
        await ctx.respond("Not yet implemented!")
    
    @VegetableGameSlashGroup.command(description="Attack another player!")
    async def attack(self, ctx, player: discord.Member):
        await ctx.respond("Not yet implemented!")
    
    @VegetableGameSlashGroup.command(description="Move somewhere else!")
    async def move(self, ctx, x=int, y=int):
        await ctx.respond("Not yet implemented!")
    
    @VegetableGameSlashGroup.command(description="Vote for a player to recieve a bonus veggie! (only usable by dead players)")
    async def vote(self, ctx, player: discord.Member):
        await ctx.respond("Not yet implemented!")
        
def setup(bot):
    bot.add_cog(VegetableGame(bot))
