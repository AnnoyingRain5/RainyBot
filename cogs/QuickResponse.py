from discord.ext import commands
from discord.commands import SlashCommandGroup
from lib.DatabaseManager import Database
from discord.ext.commands import has_permissions, CheckFailure
from discord.channel import DMChannel
from discord.commands.context import ApplicationContext as SlashContext
from discord.errors import Forbidden


class QuickResponse(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    QuickResponseSlashGroup = SlashCommandGroup(
        "quickresponse", "Configure Quick Responses")
    MessageQuickResponseSlashGroup = QuickResponseSlashGroup.create_subgroup(
        "message", "Configure message quick responses")
    PhraseQuickResponseSlashGroup = QuickResponseSlashGroup.create_subgroup(
        "phrase", "Configure message quick responses")

    @commands.Cog.listener()
    async def on_ready(self):
        self.db = Database("QuickResponses")
        for guild in self.bot.guilds:
            # if the server does not have any QuickResponses
            if str(guild.id) not in self.db.read():
                # generate empty template
                self.db.update(
                    {
                        guild.id: {
                            # use empty values as its impossible to send an empty message
                            "PhraseResponses": {"": ""},
                            "MessageResponses": {"": ""}
                        }
                    }
                )

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        if guild.id not in self.db.read():  # if the server isnt already in the database
            # generate empty template
            self.db.update(
                {
                    guild.id: {
                        # use empty values as its impossible to send an empty message
                        "PhraseResponses": {"": ""},
                        "MessageResponses": {"": ""}
                    }
                }
            )

    @commands.Cog.listener()
    async def on_message(self, ctx):
        # message responses
        if ctx.author == self.bot.user:  # ignore all messages by this bot
            return
        if isinstance(ctx.channel, DMChannel):  # ignore all messages in DMs
            return
        if ctx.webhook_id != None:
            return
        # message responses
        for trigger in self.db.read()[str(ctx.guild.id)]["MessageResponses"]:
            if trigger != "":
                if trigger.lower() == ctx.content.lower():
                    # send the response from the guild's responses
                    try:
                        await ctx.channel.send(self.db.read()[str(ctx.guild.id)]["MessageResponses"][trigger])
                    except Forbidden:
                        pass

        # phrase responses
        for trigger in self.db.read()[str(ctx.guild.id)]["PhraseResponses"]:
            if trigger != "":
                if trigger in ctx.content:
                    # send the response from the guild's responses
                    try:
                        await ctx.channel.send(self.db.read()[str(ctx.guild.id)]["PhraseResponses"][trigger])
                    except Forbidden:
                        pass

    @has_permissions(manage_guild=True)
    @PhraseQuickResponseSlashGroup.command(description="Add/set a phrase response", name="add")
    async def add_phrase(self, ctx: SlashContext, phrase: str, response: str):
        if ctx.guild == None:
            await ctx.respond(f"This command must be run in a guild.")
            return
        self.db.db[str(ctx.guild.id)]["PhraseResponses"].update(
            {phrase: response})
        self.db.save()
        await ctx.respond("Done!")

    @add_phrase.error
    async def add_phrase_error(self, ctx: SlashContext, error):
        if isinstance(error, CheckFailure):
            await ctx.respond("`manage server` permissions are required to run this command.")

    # I know this is the second function called add, it works though...
    @has_permissions(manage_guild=True)
    @MessageQuickResponseSlashGroup.command(description="Add/set a message response", name="add")
    async def add_msg(self, ctx: SlashContext, message: str, response: str):
        if ctx.guild == None:
            await ctx.respond(f"This command must be run in a guild.")
            return
        self.db.db[str(ctx.guild.id)]["MessageResponses"].update(
            {message: response})
        self.db.save()
        await ctx.respond("Done!")

    @add_msg.error
    async def add_msg_error(self, ctx: SlashContext, error):
        if isinstance(error, CheckFailure):
            await ctx.respond("`manage server` permissions are required to run this command.")

    @has_permissions(manage_guild=True)
    @MessageQuickResponseSlashGroup.command(description="Remove a message response", name="remove")
    async def remove_msg(self, ctx: SlashContext, trigger: str):
        if ctx.guild == None:
            await ctx.respond(f"This command must be run in a guild.")
            return
        try:
            self.db.db[str(ctx.guild.id)]["MessageResponses"].pop(trigger)
            self.db.save()
        except KeyError:
            await ctx.respond(f"Error: There isn't a message response with the trigger: `{trigger}`")
            return
        await ctx.respond("Done!")

    @remove_msg.error
    async def remove_msg_error(self, ctx: SlashContext, error):
        if isinstance(error, CheckFailure):
            await ctx.respond("`manage server` permissions are required to run this command.")

    @has_permissions(manage_guild=True)
    @PhraseQuickResponseSlashGroup.command(description="Remove a phrase response", name="remove")
    async def remove_phrase(self, ctx: SlashContext, trigger: str):
        if ctx.guild == None:
            await ctx.respond(f"This command must be run in a guild.")
            return
        try:
            self.db.db[str(ctx.guild.id)]["PhraseResponses"].pop(trigger)
            self.db.save()
        except KeyError:
            await ctx.respond(f"Error: There isn't a phrase response with the trigger: `{trigger}`")
            return
        await ctx.respond("Done!")

    @remove_phrase.error
    async def remove_phrase_error(self, ctx: SlashContext, error):
        if isinstance(error, CheckFailure):
            await ctx.respond("`manage server` permissions are required to run this command.")


def setup(bot):
    bot.add_cog(QuickResponse(bot))
