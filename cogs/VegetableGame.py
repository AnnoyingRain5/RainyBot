from discord.ext import commands, tasks
import discord
from discord.commands import SlashCommandGroup
from lib.DatabaseManager import Database
from random import randint
from asyncinit import asyncinit


class Vector2(dict):
    def __init__(self, inX: int, inY: int):
        dict.__init__(self, fname={"x": inX, "y": inY})
        self.x = inX
        self.y = inY


def DictToVector2(indict: dict):
    return Vector2(indict["x"], indict["y"])


class Player():
    def __init__(self, user: discord.User, db: Database, newPlayer: bool = False, emoji: str = ""):
        self._db = db
        # if this is a new player, we need to do some extra setup
        if newPlayer:
            if emoji == None:  # if there is no emoji for this new player
                raise ValueError("emoji is required for new players")
            # keep generating positions until a free space is found
            while True:
                posx = randint(0, self._db.read()["GameSize"]["x"])
                posy = randint(0, self._db.read()["GameSize"]["y"])
                if len(self._db.read()["Players"]) > 1:
                    for player in self._db.read()["Players"]:
                        if posx != player["Position"]["x"] and posy != player["Position"]["y"]:
                            break
                else:
                    break

            self._db.db["Players"][user.id] = {
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
            self._db.save()
            self._db.reload()  # another weird case where this is needed...
            print("init player")
        # init private variables
        dbPlayer = db.read()["Players"][str(user.id)]
        self._tokens = int(dbPlayer["Balance"])
        self._health = int(dbPlayer['Health'])
        self._alive = bool(dbPlayer["Alive"])
        self._emoji = str(dbPlayer["Emoji"])
        self._position = DictToVector2(dbPlayer["Position"])
        self.dbPlayerID = user.id

    def kill(self, message: str = "Died"):
        self._alive = False
        self._db.db["Players"][str(self.dbPlayerID)]["Alive"] = False
        self._health = 0
        self._db.save()

    def _tokens_get(self): return self._tokens

    def _tokens_set(self, tokens: int):
        self._tokens += tokens
        self._db.db["Players"][str(self.dbPlayerID)]["Tokens"] = self._tokens
        self._db.save()

    def _health_get(self): return self._health

    def _health_set(self, health: int, reason: str = ""):
        if health == 0:
            self.kill(reason)
        else:
            self._health = health
            self._db.db["Players"][str(
                self.dbPlayerID)]["Health"] = self._health
            self._db.save()

    def _alive_get(self): return self._alive

    def _alive_set(self, alive: bool):
        if alive == False:
            self.kill()
        else:
            self._alive = alive
            self._db.db["Players"][str(self.dbPlayerID)]["Alive"] = self._alive
            self._db.save()

    def _emoji_get(self): return self._emoji

    def _emoji_set(self, emoji: str):
        # TODO check to see if an emoji is valid
        self._emoji = emoji
        self._db.db["Players"][str(self.dbPlayerID)]["Emoji"] = self._emoji
        self._db.save()

    def _position_get(self): return self._position

    def _position_set(self, newpos: Vector2):
        self._position = newpos
        self._db.db["Players"][str(self.dbPlayerID)
                               ]["Position"] = self._position
        self._db.save()

    tokens = property(_tokens_get, _tokens_set)
    health = property(_health_get, _health_set)
    alive = property(_alive_get, _alive_set)
    emoji = property(_emoji_get, _emoji_set)
    position = property(_position_get, _position_set)


@asyncinit
class GameManager():
    async def __init__(self, db: Database, bot: discord.Bot):
        self._db = db
        self._bot = bot
        self._players = []
        if len(self._db.db) >= 1:  # ensure there is a game before starting
            dbsize = self._db.db["GameSize"]
            self._size = Vector2(dbsize["x"], dbsize["y"])
            self._active = bool(self._db.db["GameActive"])
            self._AnnounceChannel = self._bot.get_channel(
                self._db.db["AnnouncementsChannelID"])
            for playerID in self._db.db["Players"]:
                player = await bot.fetch_user(playerID)
                if player != None:
                    self._players.append(Player(player, db))

        else:  # if there is no game, set all values to None or False
            self._size = None
            self._active = False
            self._AnnounceChannel = None

    def SetupGame(self, size: Vector2, AnnouncementsChannel: discord.TextChannel):
        self._db.db = {
            "Players": {},
            "GameActive": False,
            "GameSize": {
                "x": size.x,
                "y": size.y
            },
            "AnnouncementsChannelID": AnnouncementsChannel.id
        }
        self._db.save()
        dbsize = self._db.db["GameSize"]
        self._size = Vector2(dbsize["x"], dbsize["y"])
        self._active = bool(self._db.db["GameActive"])
        self._AnnounceChannel = self._bot.get_channel(
            self._db.db["AnnouncementsChannelID"])

    def get_size(self): return self._size

    def set_size(self, size: Vector2):
        if size.x <= 2 or size.y <= 2:
            raise ValueError("Both size axes must be at least 2")
        self._size = size
        self._db.db["Size"] = self._size
        self._db.save()

    def get_active(self): return self._active

    def set_active(self, active: bool):
        self._active = active
        self._db.db["GameActive"] = False
        self._db.save()

    def get_AnnounceChannel(self): return self._AnnounceChannel

    def set_AnnounceChannel(self, channel: discord.TextChannel):
        self._AnnounceChannel = channel
        self._db.db["AnnouncementChannelID"] = channel.id
        self._db.save()

    def get_players(self): return self._players

    def set_players(self, player: Player):  # ensure only players are added
        if type(player) == Player:
            self._players.append(player)
        else:
            raise AttributeError("A Player object is required")

    size = property(get_size, set_size)
    active = property(get_active, set_active)
    AnnounceChannel = property(get_AnnounceChannel, set_AnnounceChannel)
    players = property(get_players, set_players)

    async def announce(self, announcement: str):
        if self._AnnounceChannel != None:
            await self._AnnounceChannel.send(announcement)


def proximityCheck(pos1: Vector2, pos2: Vector2, MaxDistance: int):
    print(pos1.x - pos2.x)
    print(pos2.x - pos1.x)
    print(pos1.y - pos2.y)
    print(pos2.y - pos1.y)
    if pos1.x - pos2.x <= MaxDistance and pos1.x - pos2.x >= 0 or pos2.x - pos1.x <= MaxDistance and pos2.x - pos1.x >= 0:
        if pos1.y - pos2.y <= MaxDistance and pos1.y - pos2.y >= 0 or pos2.y - pos1.y <= MaxDistance and pos2.y - pos1.y >= 0:
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
        self.game = await GameManager(self.db, self.bot)
        self.add_tokens.start()

    @VegetableGameSlashGroup.command(description="View the current game board")
    async def viewboard(self, ctx, showownrange: bool, showallranges: bool):
        grid = []
        for y in range(self.game.size.y):
            grid.append([])
            for x in range(self.game.size.x):
                for player in self.game.players:
                    if player.position.x == x and player.position.y == y:
                        grid[y].append(f"{player.emoji} ")
                        break
                else:
                    grid[y].append("   ")
        # We have a grid (2d list), time for formatting
        fgrid = ""
        for y in grid:
            fgrid += "-" * len(y) * 5
            fgrid += "\n"
            fgrid += str(y)
            fgrid += "\n"
        fgrid += "-" * len(grid[0]) * 5
        fgrid += "\n"
        fgrid = fgrid.replace(",", "|")
        fgrid = fgrid.replace("'", "")
        fgrid = fgrid.replace("[", "|")
        fgrid = fgrid.replace("]", "|")

        await ctx.respond(f"```py\n{fgrid}```")

    @VegetableGameSlashGroup.command(description="Attack another player!")
    async def attack(self, ctx, target: discord.User):
        targetPlayer = Player(target, self.db)
        ownPlayer = Player(ctx.author, self.db)
        ownPos = ownPlayer.position
        targetPos = targetPlayer.position
        if ownPlayer.tokens > 0:
            if targetPlayer.alive:
                if proximityCheck(ownPos, targetPos, 5) == True:
                    targetPlayer.health -= 1
                    await ctx.respond(f"{target.mention} was just attacked! They now have {targetPlayer.health} health!")
                else:
                    await ctx.respond("They are too far away!")
            else:
                await ctx.respond("You cannot kill the dead.")
        else:
            await ctx.respond("You need an action token to do that!")

    @VegetableGameSlashGroup.command(description="Move somewhere else!")
    async def move(self, ctx, new_x: int, new_y: int):
        ownPlayer = Player(ctx.author, self.db)
        if self.db.db["Players"][str(ctx.author.id)]["Balance"] > 0:
            if proximityCheck(ownPlayer.position, Vector2(new_x, new_y), 2) == True:
                ownPlayer.position = Vector2(new_x, new_y)
                await ctx.respond(f"You have moved to x = {new_x}, y = {new_y}")
            else:
                await ctx.respond("You can't mode that far away in one go!")
        else:
            await ctx.respond("You need an action token to do that!")

    @VegetableGameSlashGroup.command(description="Vote for a player to recieve a bonus veggie! (only usable by dead players)")
    async def vote(self, ctx, player: discord.Member):
        await ctx.respond("Not yet implemented!")

    @VegetableGameSlashGroup.command(description="Prepare the game! (owner only)")
    async def preparegame(self, ctx, areyousure: bool, sizex: int, sizey: int, announcements_channel: discord.TextChannel):
        if areyousure == False:
            await ctx.respond("Please be sure before running this command, it wipes the database!")
        else:
            # user is sure
            self.game.SetupGame(Vector2(sizex, sizey), announcements_channel)
        await ctx.respond("The slate has been wiped clean, and a game is ready to start!")

    @VegetableGameSlashGroup.command(description="Start a game! (owner only)")
    async def startgame(self, ctx):
        self.game.active = True
        await ctx.respond("Started the game")
        await self.game.announce("The game has started! Have fun!")

    @VegetableGameSlashGroup.command(description="joingame")
    async def joingame(self, ctx, emoji: str):
        self.game.players.append(Player(ctx.author,
                                        self.db, newPlayer=True, emoji=emoji))
        await ctx.respond("You have joined the game!")
        await self.game.announce(f"{ctx.author.mention} Just joined the game!")

    # TODO change this to 24 hours when out of testing
    @tasks.loop(hours=0.5)
    async def add_tokens(self):
        await self.game.announce(
            "It's that time again! Everyone (who is still alive) just got an action token!")
        for player in self.game.players:
            print(f"added token to {player}")
            if player.alive:
                player.tokens += 1
        self.db.save()


def setup(bot):
    bot.add_cog(VegetableGame(bot))
