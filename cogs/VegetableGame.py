from discord.ext import commands
import discord
from discord.commands import SlashCommandGroup
from lib.DatabaseManager import Database
from random import randint

def List2DToTable(inputlist):
    output = ""
    height = len(inputlist)
    length = len(inputlist[0])
    print(height, length)
    for y in range(height * 2 + 1):
        for x in range(length):
            if y % 2 == 0: # if it is an even line
                if x == 0:
                    output += "+---+"
                else:
                    output += "---+"
            # line is not even, show content instead
            elif inputlist[int(y/2)][x] != "": # cell has content
                    output += f"|{inputlist[int(y/2)][x]} "
            else: # cell does not have content
                output += "|    "
            if x == length - 1:
                if y % 2 != 0: # if it is an odd line
                    output += "|"
        output += "\n"
    return output

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
        grid = []
        for y in range(self.db.read()["GameSize"]["y"]):
            grid.append([])
            for x in range(self.db.read()["GameSize"]["x"]):
                for player in self.db.read()["Players"]:
                    if player["Position"]["x"] == x and player["Position"]["y"] == y:
                        grid[y].append(player["emoji"])
                grid[y].append("")
        ctx.respond(List2DToTable(grid))
                
    @VegetableGameSlashGroup.command(description="Attack another player!")
    async def attack(self, ctx, player: discord.Member):
        await ctx.respond("Not yet implemented!")
    
    @VegetableGameSlashGroup.command(description="Move somewhere else!")
    async def move(self, ctx, x=int, y=int):
        await ctx.respond("Not yet implemented!")
    
    @VegetableGameSlashGroup.command(description="Vote for a player to recieve a bonus veggie! (only usable by dead players)")
    async def vote(self, ctx, player: discord.Member):
        await ctx.respond("Not yet implemented!")
        
    @VegetableGameSlashGroup.command(description="Prepare the game! (owner only)")
    async def preparegame(self, ctx, areyousure: bool, sizex: int, sizey: int):
        if areyousure == False:
            await ctx.respond("Please be sure before running this command, it wipes the database!")
        else:
            # user is sure
            self.db.db = {
                "Players": {},
                "GameActive": False,
                "GameSize": {
                    "x": sizex,
                    "y": sizey
                }
            }
            self.db.save()
        await ctx.respond("The slate has been wiped clean, and a game is ready to start!")
        
    @VegetableGameSlashGroup.command(description="Start a game! (owner only)")
    async def startgame(self, ctx):
        self.db.update({"GameActive": True})
        self.db.save()
        await ctx.respond("The game has now started, have fun! (or don't)")
        
    @VegetableGameSlashGroup.command(description="joingame")
    async def joingame(self, ctx, emoji: str):
        x = randint(0, self.db.read()["GameSize"]["x"])
        y = randint(0, self.db.read()["GameSize"]["y"])
        self.db.db["Players"][ctx.author.id] = {
            "Position":
                {
                    "x": x,
                    "y": y
                },
                "Alive": True,
                "Balance": 0,
                "emoji": emoji
            }
        self.db.save()
        await ctx.respond("You have joined the game!")
            
def setup(bot):
    bot.add_cog(VegetableGame(bot))
