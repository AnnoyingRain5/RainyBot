import discord
from discord.ext import commands
import json
from discord.commands import SlashCommandGroup
from  lib.DatabaseManager import Database

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
        if guild.id not in self.QuickResponses: # if the server isnt already in the database
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

    @PhraseQuickResponseSlashGroup.command(description="Add/set a phrase response")
    async def add(self, ctx, phrase: str, response: str):
        self.db.db[str(ctx.guild.id)]["PhraseResponses"].update({phrase: response})
        self.db.save()
        await ctx.respond("Done!")
        
    # I know this is the second function called add, it works though...
    @MessageQuickResponseSlashGroup.command(description="Add/set a message response")
    async def add(self, ctx, message: str, response: str):
        print(self.db.db)
        self.db.db[str(ctx.guild.id)]["MessageResponses"].update({message: response})
        self.db.save()
        await ctx.respond("Done!")

    @MessageQuickResponseSlashGroup.command(description="Remove a message response")
    async def remove(self, ctx, message: str):
        self.db.db[str(ctx.guild.id)]["MessageResponses"].pop(message)
        self.db.save()
        await ctx.respond("Done!")

    @PhraseQuickResponseSlashGroup.command(description="Remove a phrase response")
    async def remove(self, ctx, phrase: str):
        self.db.db[str(ctx.guild.id)]["PhraseResponses"].pop(phrase)
        self.db.save()
        await ctx.respond("Done!")

def setup(bot):
    bot.add_cog(QuickResponse(bot))
