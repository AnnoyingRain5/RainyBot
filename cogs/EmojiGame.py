from discord.ext import commands, tasks
import discord
from discord.commands import SlashCommandGroup
from discord.commands.context import ApplicationContext as Context
from lib.DatabaseManager import Database
from random import randint
from asyncinit import asyncinit
from datetime import time


MAX_GIFT_DISTANCE = 6
MAX_ATTACK_DISTANCE = 4
MAX_MOVE_DISTANCE = 3


class Vector2(dict):
    def __init__(self, inX: int, inY: int):
        dict.__init__(self, fname={"x": inX, "y": inY})
        self.x = inX
        self.y = inY


def DictToVector2(indict: dict):
    return Vector2(indict["x"], indict["y"])


class Player():
    def __init__(self, user: discord.User | discord.Member, db: Database, newPlayer: bool = False, emoji: str = ""):
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
                    "Health": 3,
                    "Vote": ""
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
        self._vote = str(dbPlayer["Vote"])
        self._position = DictToVector2(dbPlayer["Position"])
        self.dbPlayerID = user.id

    def reload(self):
        dbPlayer = self._db.read()["Players"][str(self.dbPlayerID)]
        self._tokens = int(dbPlayer["Balance"])
        self._health = int(dbPlayer['Health'])
        self._alive = bool(dbPlayer["Alive"])
        self._emoji = str(dbPlayer["Emoji"])
        self._position = DictToVector2(dbPlayer["Position"])

    def kill(self, message: str = "Died"):
        self._alive = False
        self._db.db["Players"][str(self.dbPlayerID)]["Alive"] = False
        self._health = 0
        self._db.db["Players"][str(
            self.dbPlayerID)]["Health"] = self._health
        self._db.save()

    def _tokens_get(self):
        self.reload()
        return self._tokens

    def _tokens_set(self, tokens: int):
        self._tokens = tokens
        self._db.db["Players"][str(self.dbPlayerID)]["Balance"] = self._tokens
        self._db.save()

    def _health_get(self):
        self.reload()
        return self._health

    def _health_set(self, health: int, reason: str = ""):
        if health == 0:
            self.kill(reason)
        else:
            self._health = health
            self._db.db["Players"][str(
                self.dbPlayerID)]["Health"] = self._health
            self._db.save()

    def _alive_get(self):
        self.reload()
        return self._alive

    def _alive_set(self, alive: bool):
        if alive == False:
            self.kill()
        else:
            self._alive = alive
            self._db.db["Players"][str(self.dbPlayerID)]["Alive"] = self._alive
            self._db.save()

    def _emoji_get(self):
        self.reload()
        return self._emoji

    def _emoji_set(self, emoji: str):
        # TODO check to see if an emoji is valid
        self._emoji = emoji
        self._db.db["Players"][str(self.dbPlayerID)]["Emoji"] = self._emoji
        self._db.save()

    def _position_get(self):
        self.reload()
        return self._position

    def _position_set(self, newpos: Vector2):
        self._position = newpos
        self._db.db["Players"][str(self.dbPlayerID)
                               ]["Position"] = self._position
        self._db.save()

    def _vote_get(self):
        self.reload()
        return self._vote

    def _vote_set(self, vote: discord.Member):
        self._vote = vote.id
        self._db.db["Players"][str(self.dbPlayerID)]["Vote"] = self._vote
        self._db.save()

    tokens = property(_tokens_get, _tokens_set)
    health = property(_health_get, _health_set)
    alive = property(_alive_get, _alive_set)
    emoji = property(_emoji_get, _emoji_set)
    position = property(_position_get, _position_set)
    vote = property(_vote_get, _vote_set)


@asyncinit
class GameManager():
    async def __init__(self, db: Database, bot: discord.Bot, AddTokensTask):
        self._db = db
        self._bot = bot
        self._players = []
        self._AddTokensTask = AddTokensTask
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
            if self._active:
                self._AddTokensTask.start()

        else:  # if there is no game, set all values to None or False
            self._size = None
            self._active = False
            self._AnnounceChannel = None

    def SetupGame(self, size: Vector2, AnnouncementsChannel: discord.TextChannel):
        if size.x <= 2 or size.y <= 2:
            raise ValueError("Both size axes must be at least 2")
        if size.x >= 14 or size.y >= 14:
            raise ValueError(
                "Due to discord limitations; the maximum size is 13")
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
        if size.x >= 14 or size.y >= 14:
            raise ValueError(
                "Due to discord limitations; the maximum size is 13")
        self._size = size
        self._db.db["Size"] = self._size
        self._db.save()

    def get_active(self): return self._active

    def set_active(self, active: bool):
        self._active = active
        self._db.db["GameActive"] = self._active
        self._db.save()
        if self._active == True:
            self._AddTokensTask.start()
        else:
            self._AddTokensTask.stop()

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
    if pos1.x - pos2.x <= MaxDistance and pos1.x - pos2.x >= 0 or pos2.x - pos1.x <= MaxDistance and pos2.x - pos1.x >= 0:
        if pos1.y - pos2.y <= MaxDistance and pos1.y - pos2.y >= 0 or pos2.y - pos1.y <= MaxDistance and pos2.y - pos1.y >= 0:
            return True
    # otherwise
    return False


class EmojiGame(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    EmojiGameSlashGroup = SlashCommandGroup(
        "gm", "Interact with the Emoji game!")

    def cog_unload(self):
        self.add_tokens.cancel()

    @commands.Cog.listener()
    async def on_ready(self):
        self.db = Database("EmojiGame")
        self.game = await GameManager(self.db, self.bot, self.add_tokens)

    @EmojiGameSlashGroup.command(description="View the current game board")
    async def viewboard(self, ctx: Context, showownrange: bool, showallranges: bool):
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

    @EmojiGameSlashGroup.command(description="Attack another player!")
    async def attack(self, ctx: Context, target: discord.Member):
        if self.game.active != True:  # Only run if a game is active
            await ctx.respond("A game needs to be active to attack!")
            return
        targetPlayer = Player(target, self.db)
        ownPlayer = Player(ctx.author, self.db)
        ownPos = ownPlayer.position
        targetPos = targetPlayer.position
        if ownPlayer.tokens > 0:
            if targetPlayer.alive:
                if proximityCheck(ownPos, targetPos, MAX_ATTACK_DISTANCE) == True:
                    targetPlayer.health -= 1
                    if targetPlayer.alive == False:  # If we just killed them
                        await ctx.respond(f"You have just killed {ctx.author.mention}")
                        await self.game.announce(f"{target.mention} was slain by {ctx.author.mention}!")
                    else:
                        await ctx.respond(f"{target.mention} was just attacked! They now have {targetPlayer.health} health!")
                else:
                    await ctx.respond("They are too far away!")
            else:
                await ctx.respond("You cannot kill the dead.")
        else:
            await ctx.respond("You need an action token to do that!")

    @EmojiGameSlashGroup.command(description="Move somewhere else!")
    async def move(self, ctx: Context, new_x: int, new_y: int):
        if self.game.active != True:  # Only run if a game is active
            await ctx.respond("A game needs to be active to move!")
            return
        ownPlayer = Player(ctx.author, self.db)
        if self.db.db["Players"][str(ctx.author.id)]["Balance"] > 0:
            if proximityCheck(ownPlayer.position, Vector2(new_x, new_y), MAX_MOVE_DISTANCE) == True:
                ownPlayer.position = Vector2(new_x, new_y)
                await ctx.respond(f"You have moved to x = {new_x}, y = {new_y}")
            else:
                await ctx.respond("You can't mode that far away in one go!")
        else:
            await ctx.respond("You need an action token to do that!")

    @EmojiGameSlashGroup.command(description="Vote for a player to recieve a bonus Token! (only usable by dead players)")
    async def vote(self, ctx: Context, target: discord.Member):
        if self.game.active != True:  # Only run if a game is active
            await ctx.respond("A game needs to be active to vote!")
        Player(ctx.author, self.db).vote = target
        await ctx.respond(f"You have voted for {target.mention}")

    @EmojiGameSlashGroup.command(description="Prepare the game! (owner only)")
    async def preparegame(self, ctx: Context, areyousure: bool, sizex: int, sizey: int, announcements_channel: discord.TextChannel):
        if not await self.bot.is_owner(ctx.author):
            await ctx.respond(f"This command is only for <@!{self.bot.owner_id}>, sorry!")
        if areyousure == False:
            await ctx.respond("Please be sure before running this command, it wipes the database!")
        else:
            # user is sure
            try:
                self.game.SetupGame(Vector2(sizex, sizey),
                                    announcements_channel)
            except ValueError as e:
                await ctx.respond(f"Error: {e}")
            else:
                await ctx.respond("The slate has been wiped clean, and a game is ready to start!")
                await self.game.announce("The game is ready to start! Get ready!")

    @EmojiGameSlashGroup.command(description="Start a game! (owner only)")
    async def startgame(self, ctx):
        if not await self.bot.is_owner(ctx.author):
            await ctx.respond(f"This command is only for <@!{self.bot.owner_id}>, sorry!")
        await self.game.announce("The game has started! Have fun!")
        self.game.active = True
        await ctx.respond("Started the game")

    @EmojiGameSlashGroup.command(description="Pause the game! (owner only)")
    async def pausegame(self, ctx):
        if not await self.bot.is_owner(ctx.author):
            await ctx.respond(f"This command is only for <@!{self.bot.owner_id}>, sorry!")
        await self.game.announce("The game has been put on hold...")
        self.game.active = False
        await ctx.respond("Stopped the game")

    @EmojiGameSlashGroup.command(description="Join the game!")
    async def joingame(self, ctx: Context, emoji: str):
        self.game.players.append(Player(ctx.author,
                                        self.db, newPlayer=True, emoji=emoji))
        await ctx.respond("You have joined the game!")
        await self.game.announce(f"{ctx.author.mention} Just joined the game!")

    @EmojiGameSlashGroup.command(description="Get info on a particular player!")
    async def getinfo(self, ctx: Context, target: discord.Member):
        player = Player(target, self.db)
        if player.health != 0:
            fhealth = "❤️" * player.health
        else:
            # player has no health
            fhealth = "Zero"
        embed = discord.Embed(
            title=target.name,
            type="rich",
            fields=[
                discord.EmbedField(
                    inline=True,
                    name="Health",
                    value=fhealth
                ),
                discord.EmbedField(
                    inline=True,
                    name="Position",
                    value=f"**X:** {player.position.x} **Y:** {player.position.y}"
                ),
                discord.EmbedField(
                    inline=True,
                    name="Emoji",
                    value=player.emoji
                ),
                discord.EmbedField(
                    inline=True,
                    name="Balance",
                    value=player.tokens
                ),
                discord.EmbedField(
                    inline=True,
                    name="Alive",
                    value=player.alive
                )
            ]
        )
        await ctx.respond(embed=embed)

    @EmojiGameSlashGroup.command(description="Gift someone a token!")
    async def gifttoken(self, ctx: Context, target: discord.Member):
        if self.game.active != True:  # Only run if a game is active
            await ctx.respond("A game needs to be active to gift tokens!")
            return
        ownPlayer = Player(ctx.author, self.db)
        targetPlayer = Player(target, self.db)
        if proximityCheck(ownPlayer.position, targetPlayer.position, MAX_GIFT_DISTANCE):
            if ownPlayer.tokens >= 1:
                ownPlayer.tokens -= 1
                targetPlayer.tokens += 1
            else:
                await ctx.respond("You need a token to do that!")
                return
        else:
            await ctx.respond(f"{target.display_name} is too far away!")
            return
        await ctx.respond(f"You have gifted {target.display_name} a token!")
        await self.game.announce(f"{ctx.author.mention} just gifted {target.mention} a token!")

    @EmojiGameSlashGroup.command(description="What is Emoji Game")
    async def help(self, ctx: Context):
        concept = "Emoji Game is an (unoriginal) virtual board game that revolves around \"Action Tokens\".\n"
        concept += "To be able to move or attack other players, you need to spend an action token.\n"
        concept += "One action token is given to every player every 24 hours. You can spend it, "
        concept += "gift it to someone else, or just keep it for later!\n"
        concept += "But do note that there is a maximum range for each action, "
        concept += "so you cannot just attack someone from across the map.\n"
        concept += "Due to the nature of the game, it is highly recommended to create alliences with other players...\n"
        concept += "but can you ever trust them enough to do that?"

        rules = f"The maximum amount of tiles you can move in one go is: {MAX_MOVE_DISTANCE}\n"
        rules += f"The maximum distance you can attack from is: {MAX_ATTACK_DISTANCE}\n"
        rules += f"The maximum distance you can gift from is: {MAX_GIFT_DISTANCE}\n"
        rules += "Each player has 3 health, and there is no way to increase your health if you lose some.\n"
        rules += "Dead players can vote on who should recieve a bonus Action Token next distribution\n"
        rules += "You cannot join a game once it has started\n"
        rules += "You do not gain any bonus Action Tokens for killing someone who is holding some\n"
        rules += "Dead players cannot use any action tokens (ie do anything notable)\n"
        rules += "You recieve one Action Token every day at 12 PM UTC (<t:1676203200:t> in your local timezone)"

        embed = discord.Embed(
            title="Emoji Game Info",
            fields=[
                discord.EmbedField(
                    name="Concept:",
                    value=concept
                ),
                discord.EmbedField(
                    name="Rules:",
                    value=rules
                ),
            ]
        )
        await ctx.respond(embed=embed)

    @tasks.loop(time=time(12))
    async def add_tokens(self):
        await self.game.announce(
            "It's that time again! Everyone (who is still alive) just got an action token!")
        votes = {}
        for player in self.game.players:
            if player.alive:
                player.tokens += 1
            elif player.vote != "":
                if player.vote in votes:
                    votes[player.vote] += 1
                else:
                    votes[player.vote] = 1
        if votes != {}:
            winner = await self.bot.fetch_user(max(votes))
            Player(winner, self.db).tokens += 1


def setup(bot):
    bot.add_cog(EmojiGame(bot))
