from discord.ext import commands
from discord.commands import SlashCommandGroup
from  lib.DatabaseManager import Database
from discord.ext.commands import has_permissions, CheckFailure

class QuickResponse(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    QuickResponseSlashGroup = SlashCommandGroup("quickresponse", "Configure Quick Responses")
    MessageQuickResponseSlashGroup = QuickResponseSlashGroup.create_subgroup("message", "Configure message quick responses")
    PhraseQuickResponseSlashGroup = QuickResponseSlashGroup.create_subgroup("phrase", "Configure message quick responses")
    
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
        if guild.id not in self.db.read(): # if the server isnt already in the database
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
        if ctx.content in self.db.read()[str(ctx.guild.id)]["MessageResponses"]:
            # send the response from the guild's responses
            await ctx.channel.send(self.db.read()[str(ctx.guild.id)]["MessageResponses"][ctx.content])

        # phrase responses
        for trigger in self.db.read()[str(ctx.guild.id)]["PhraseResponses"]:
            if trigger != "":
                if trigger in ctx.content:
                    # send the response from the guild's responses
                    await ctx.channel.send(self.db.read()[str(ctx.guild.id)]["PhraseResponses"][trigger])
         
    @has_permissions(manage_guild=True)
    @PhraseQuickResponseSlashGroup.command(description="Add/set a phrase response")
    async def add(self, ctx, phrase: str, response: str):
        self.db.db[str(ctx.guild.id)]["PhraseResponses"].update({phrase: response})
        self.db.save()
        await ctx.respond("Done!")
        
    @add.error
    async def add_error(self, ctx, error):
        if isinstance(error, CheckFailure):
            await ctx.respond("`manage server` permissions are required to run this command.")
            
    # I know this is the second function called add, it works though...
    @has_permissions(manage_guild=True)
    @MessageQuickResponseSlashGroup.command(description="Add/set a message response")
    async def add(self, ctx, message: str, response: str):
        self.db.db[str(ctx.guild.id)]["MessageResponses"].update({message: response})
        self.db.save()
        await ctx.respond("Done!")

    @add.error
    async def add_error(self, ctx, error):
        if isinstance(error, CheckFailure):
            await ctx.respond("`manage server` permissions are required to run this command.")
    
    @has_permissions(manage_guild=True)
    @MessageQuickResponseSlashGroup.command(description="Remove a message response")
    async def remove(self, ctx, message: str):
        self.db.db[str(ctx.guild.id)]["MessageResponses"].pop(message)
        self.db.save()
        await ctx.respond("Done!")
    
    @remove.error
    async def remove_error(self, ctx, error):
        if isinstance(error, CheckFailure):
            await ctx.respond("`manage server` permissions are required to run this command.")

    @has_permissions(manage_guild=True)
    @PhraseQuickResponseSlashGroup.command(description="Remove a phrase response")
    async def remove(self, ctx, phrase: str):
        self.db.db[str(ctx.guild.id)]["PhraseResponses"].pop(phrase)
        self.db.save()
        await ctx.respond("Done!")
    
    @remove.error
    async def remove_error(self, ctx, error):
        if isinstance(error, CheckFailure):
            await ctx.respond("`manage server` permissions are required to run this command.")

def setup(bot):
    bot.add_cog(QuickResponse(bot))
