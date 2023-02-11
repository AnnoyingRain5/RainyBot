from discord.ext import commands, tasks
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
            if y % 2 == 0:  # if it is an even line
                if x == 0:
                    output += "+---+"
                else:
                    output += "---+"
            # line is not even, show content instead
            elif inputlist[int(y/2)][x] != "":  # cell has content
                output += f"|{inputlist[int(y/2)][x]} "
            else:  # cell does not have content
                output += "|    "
            if x == length - 1:
                if y % 2 != 0:  # if it is an odd line
                    output += "|"
        output += "\n"
    return output


def proximityCheck(pos1: dict, pos2: dict, MaxDistance: int):
    pos1x = int(pos1["x"])
    pox1y = int(pos1["y"])
    pos2x = int(pos2["x"])
    pox2y = int(pos2["y"])
    if pos1x - pos2x <= MaxDistance and pos1x - pos2x > 0 or pos2x - pos1x <= MaxDistance and pos2x - pos1x > 0:
        if pox1y - pox2y <= MaxDistance and pox1y - pox2y > 0 or pox2y - pox1y <= MaxDistance and pox2y - pox1y > 0:
            return True
    # otherwise
    return False


class VegetableGame(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    VegetableGameSlashGroup = SlashCommandGroup(
        "veg", "Interact with the Vegetable game!")

    def cog_unload(self):
        self.add_tokens.cancel()

    @commands.Cog.listener()
    async def on_ready(self):
        self.db = Database("VegetableGame")
        self.add_tokens.start()

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
        targetPlayer = self.db.read()["Players"][str(target.id)]
        ownPlayer = self.db.read()["Players"][str(ctx.author.id)]
        ownPos = ownPlayer["Position"]
        targetPos = targetPlayer["Position"]
        if ownPlayer["Balance"] > 0:
            if targetPlayer["Alive"] == True:
                if proximityCheck(ownPos, targetPos, 5) == True:
                    health = self.db.db["Players"][str(
                        target.id)]["Health"] - 1
                    self.db.db["Players"][str(target.id)]["Health"] = health
                    self.db.db["Players"][str(ctx.author.id)]["Balance"] -= 1
                    if health == 0:
                        self.db.db["Players"][str(target.id)]["Alive"] = False
                    self.db.save()
                    await ctx.respond(f"{target.mention} was just attacked! They now have {health} health!")
                else:
                    await ctx.respond("They are too far away!")
            else:
                await ctx.respond("You cannot kill the dead.")
        else:
            await ctx.respond("You need an action token to do that!")

    @VegetableGameSlashGroup.command(description="Move somewhere else!")
    async def move(self, ctx, new_x: int, new_y: int):
        ownPos = self.db.read()["Players"][str(ctx.author.id)]["Position"]
        if self.db.db["Players"][str(ctx.author.id)]["Balance"] > 0:
            if proximityCheck(ownPos, {"x": new_x, "y": new_y}, 2) == True:
                self.db.db["Players"][str(ctx.author.id)]["Position"] = {
                    "x": new_x, "y": new_y}
                self.db.save()
                await ctx.respond(f"You have moved to x = {new_x}, y = {new_y}")
            else:
                await ctx.respond("You can't mode that far away in one go!")
        else:
            await ctx.respond("You need an action token to do that!")

    @VegetableGameSlashGroup.command(description="Vote for a player to recieve a bonus veggie! (only usable by dead players)")
    async def vote(self, ctx, player: discord.Member):
        await ctx.respond("Not yet implemented!")

    @VegetableGameSlashGroup.command(description="Prepare the game! (owner only)")
    async def preparegame(self, ctx, areyousure: bool, sizex: int, sizey: int, announcements_channel: discord.abc.GuildChannel):
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
                },
                "Announcements_channel_ID": announcements_channel.id
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
            if len(self.db.read()["Players"]) > 1:
                for player in self.db.read()["Players"]:
                    if posx != player["Position"]["x"] and posy != player["Position"]["y"]:
                        break
            else:
                break

        self.db.db["Players"][ctx.author.id] = {
            "Position":
                {
                    "x": posx,
                    "y": posy
                },
                "Alive": True,
                "Balance": 0,
                "Emoji": emoji,
                "Health": 3
        }
        self.db.save()
        await ctx.respond("You have joined the game!")

    @tasks.loop(seconds=20)  # TODO change this to 24 hours when out of testing
    async def add_tokens(self):
        channel = self.bot.get_channel(self.db.db["Announcements_Channel_ID"])
        channel.send(
            "It's that time again! Everyone (who is still alive) just got an action token!")
        for player in self.db.db["Players"]:
            print(f"added token to {player}")
            if self.db.db["Players"][player]["Alive"] == True:
                self.db.db["Players"][player]["Balance"] += 1
        self.db.save()


def setup(bot):
    bot.add_cog(VegetableGame(bot))
