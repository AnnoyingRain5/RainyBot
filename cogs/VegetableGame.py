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

def proximityCheck(pos1: dict, pos2: dict, MaxDistance: int):
    if pos1["x"] - pos2["x"] <= MaxDistance or pos2["x"] - pos1["x"] <= MaxDistance:
        if pos1["y"] - pos2["y"] <= MaxDistance or pos2["y"] - pos1["y"] <= MaxDistance:
            return True
    # otherwise
    return False

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
    async def attack(self, ctx, target: discord.Member):
        targetPlayer = self.db.read()["Players"][target.id]
        ownPlayer = self.db.read()["Players"][ctx.author.id]
        ownPos = ownPlayer["Position"]
        targetPos = targetPlayer["Position"]
        if ownPlayer["Balance"] > 0:
            if targetPlayer["Alive"] == True:
                if proximityCheck(ownPos, targetPos, 5) == True:
                    health = self.db.db["Players"][target.id]["Health"] - 1
                    self.db.db["Players"][target.id]["Health"] = health
                    self.db.db["Players"][ctx.author.id]["Balance"] -= 1
                    self.db.save()
                    await ctx.respond(f"{target.mention} was just attacked! They now have {health} health!")
                else:
                    await ctx.respond("They are too far away!")
            else:
                await ctx.respond("You cannot kill the dead.")
        else:
            await ctx.respond("You need an action token to do that!")
    
    @VegetableGameSlashGroup.command(description="Move somewhere else!")
    async def move(self, ctx, newX=int, newY=int):
        ownPos = self.db.read()["Players"][ctx.author.id]["Position"]
        if self.db.db["Players"][ctx.author.id]["Balance"] > 0:
            if proximityCheck(ownPos, {"x": newX, "y": newY}, 2):
                self.db.db["Players"][ctx.author.id]["Position"] = {"x": newX, "y": newY}
            else:
                await ctx.respond("You can't mode that far away in one go!")
        else:
            await ctx.respond("You need an action token to do that!")
    
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
        # keep generating positions until you find a free space
        while True:
            posx = randint(0, self.db.read()["GameSize"]["x"])
            posy = randint(0, self.db.read()["GameSize"]["y"])
            for player in self.db.read()["Players"]:
                if posx != player["Position"]["x"] and posy != player["Position"]["y"]:
                    break

        self.db.db["Players"][ctx.author.id] = {
            "Position":
                {
                    "x": x,
                    "y": y
                },
                "Alive": True,
                "Balance": 0,
                "Emoji": emoji,
                "Health": 3
            }
        self.db.save()
        await ctx.respond("You have joined the game!")
            
def setup(bot):
    bot.add_cog(VegetableGame(bot))
