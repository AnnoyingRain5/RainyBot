from discord import Webhook
from discord.channel import DMChannel
import aiohttp
import googletrans
import json
from discord.commands import SlashCommandGroup
from discord.ext import commands
from discord.ext.commands import has_permissions, CheckFailure
from lib.DatabaseManager import Database
from httpcore._exceptions import ReadTimeout
from discord.commands.context import ApplicationContext as SlashContext

translator = googletrans.Translator()
GuildToChannelGroupList = {}


class Translator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()
        self.db = Database("Translator")

    TranslatorSlashGroup = SlashCommandGroup(
        "translator", "Configure the translator")
    TranslatorChannelSlashGroup = TranslatorSlashGroup.create_subgroup(
        "channelgroup", "Configure Channel Groups")

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        if guild.id not in self.db.read():  # if the server does not have any ChannelGroups
            # generate empty template
            self.db.update(
                {
                    guild.id: {
                        "ChannelGroups": {"0": {"": ""}},
                        "webhooks": {"": ""}
                    }
                }
            )

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            # if the server does not have any ChannelGroups
            if str(guild.id) not in self.db.read():
                # generate empty template
                self.db.update(
                    {
                        guild.id: {
                            "ChannelGroups": {"0": {"": ""}},
                            "webhooks": {"": ""}
                        }
                    }
                )

    @commands.Cog.listener()
    async def on_message(self, ctx):
        if ctx.webhook_id == None and not isinstance(ctx.channel, DMChannel):
            # if the message isnt from a webhook or in a DM
            for ChannelGroupID in self.db.read()[str(ctx.guild.id)]["ChannelGroups"]:
                ChannelGroup = self.db.read()[str(
                    ctx.guild.id)]["ChannelGroups"][ChannelGroupID]
                if str(ctx.channel.id) in ChannelGroup:  # if the channel is in the channelGroup
                    for channel in ChannelGroup:
                        # dont send the message in its own channel, and dont send it to ID 0
                        if channel != str(ctx.channel.id) and channel != "0":
                            webhook = Webhook.from_url(self.db.read()[str(
                                ctx.guild.id)]["webhooks"][str(channel)], session=self.session)
                            # Get the attachments
                            attachments = []
                            for attachment in ctx.attachments:
                                attachments.append(await attachment.to_file())
                            # if the message is empty (only attachments)
                            if ctx.content == "":
                                await webhook.send(content="", username=ctx.author.name, avatar_url=ctx.author.avatar.url, files=attachments)
                            # language of the channel the original message was in
                            SourceLang = ChannelGroup[str(ctx.channel.id)]
                            # language of the current channel in the ChannelGroup
                            DestinationLang = ChannelGroup[str(channel)]
                            try:
                                TranslatedText = translator.translate(
                                    ctx.content, DestinationLang, SourceLang).text
                            except ReadTimeout:  # give it another shot if it times out
                                TranslatedText = translator.translate(
                                    ctx.content, DestinationLang, SourceLang).text
                            print(
                                f"'{ctx.content}' in {SourceLang} is '{TranslatedText}' in {DestinationLang}")
                            if ctx.author.avatar != None:  # if the user has a profile picture set
                                await webhook.send(TranslatedText, username=ctx.author.name, avatar_url=ctx.author.avatar.url, files=attachments)
                            else:
                                await webhook.send(TranslatedText, username=ctx.author.name, files=attachments)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if after.webhook_id == None:  # if the message isnt from a webhook
            for ChannelGroupID in self.db.read()[str(after.guild.id)]["ChannelGroups"]:
                ChannelGroup = self.db.read()[str(
                    after.guild.id)]["ChannelGroups"][ChannelGroupID]
                # if the channel is in the channelGroup
                if str(after.channel.id) in ChannelGroup:
                    for channel in ChannelGroup:
                        # dont send the message in its own channel, and dont send it to ID 0
                        if channel != str(after.channel.id) and channel != "0":
                            webhook = Webhook.from_url(self.db.read()[str(
                                after.guild.id)]["webhooks"][str(channel)], session=self.session)
                            # Get the attachments
                            attachments = []
                            for attachment in after.attachments:
                                attachments.append(await attachment.to_file())
                            # if the message is empty (only attachments)
                            if after.content == "":
                                print(
                                    "Error! a message was edited to be empty! This should not be possible!")
                            # language of the channel the original message was in
                            SourceLang = ChannelGroup[str(after.channel.id)]
                            # language of the current channel in the ChannelGroup
                            DestinationLang = ChannelGroup[str(channel)]
                            TranslatedText = translator.translate(
                                f"I edited a message!\nBefore: \"{before.content}\", \n After: \"{after.content}\"", DestinationLang, SourceLang).text
                            if after.author.avatar != None:  # if the user has a profile picture set
                                await webhook.send(TranslatedText, username=after.author.name, avatar_url=after.author.avatar.url, files=attachments)
                            else:
                                await webhook.send(TranslatedText, username=after.author.name, files=attachments)

    @has_permissions(administrator=True)
    @TranslatorChannelSlashGroup.command(description="Create a channel group")
    # adding a default value makes parameter optional
    async def create(self, ctx: SlashContext, channel1, channel1language, channel1webhook,
                     channel2, channel2language, channel2webhook, channel3=0, channel3language='', channel3webhook='',
                     channel4=0, channel4language='', channel4webhook='', channel5=0, channel5language='', channel5webhook=''):
        if ctx.guild == None:
            await ctx.respond(f"This command must be run in a guild.")
            return

        ChannelGroup = {channel1: channel1language, channel2: channel2language,
                        channel3: channel3language, channel4: channel4language, channel5: channel5language}
        WebhookTable = {channel1: channel1webhook, channel2: channel2webhook,
                        channel3: channel3webhook, channel4: channel4webhook, channel5: channel5webhook}
        ChannelGroupID = str(
            int(list(self.db.read()[str(ctx.guild.id)]["ChannelGroups"])[-1])+1)
        self.db.db[str(ctx.guild.id)]["ChannelGroups"].update(
            {ChannelGroupID: ChannelGroup})  # ensure each channelgroup is seperate
        self.db.db[str(ctx.guild.id)]["webhooks"].update(WebhookTable)
        self.db.save()
        await ctx.respond("Channel group created!")

    @create.error
    async def create_error(self, ctx: SlashContext, error):
        if isinstance(error, CheckFailure):
            await ctx.respond("Admininstrator permissions are required to run this command.")

    @has_permissions(administrator=True)
    @TranslatorChannelSlashGroup.command(description="Add a channel to a ChannelGroup")
    # adding a default value makes parameter optional
    async def addchannel(self, ctx: SlashContext, groupid, channel, language, webhook):
        if ctx.guild == None:
            await ctx.respond(f"This command must be run in a guild.")
            return
        if groupid == '0':
            await ctx.respond("Group ID cannot be 0")
            return
        self.db.db[str(ctx.guild.id)]["ChannelGroups"][groupid].update(
            {channel: language})
        self.db.db[str(ctx.guild.id)]["webhooks"].update({channel: webhook})
        self.db.save()
        await ctx.respond("Channel added to ChannelGroup!")

    @addchannel.error
    async def addchannel_error(self, ctx: SlashContext, error):
        if isinstance(error, CheckFailure):
            await ctx.respond("Admininstrator permissions are required to run this command.")

    @has_permissions(administrator=True)
    @TranslatorChannelSlashGroup.command(description="Remove a channel from a ChannelGroup")
    # adding a default value makes parameter optional
    async def removechannel(self, ctx: SlashContext, groupid, channel):
        if ctx.guild == None:
            await ctx.respond(f"This command must be run in a guild.")
            return
        if groupid == '0':
            await ctx.respond("Group ID cannot be 0")
            return
        if channel == '0':
            await ctx.respond("channel ID cannot be 0")
            return
        self.db.db[str(ctx.guild.id)]["ChannelGroups"][groupid].pop(channel)
        self.db.db[str(ctx.guild.id)]["webhooks"].pop(channel)
        self.db.save()
        await ctx.respond("Channel removed from ChannelGroup!")

    @addchannel.error
    async def removechannel_error(self, ctx: SlashContext, error):
        if isinstance(error, CheckFailure):
            await ctx.respond("Admininstrator permissions are required to run this command.")

    @has_permissions(administrator=True)
    @TranslatorSlashGroup.command(description="Display the server config JSON")
    async def viewserverconfig(self, ctx: SlashContext):
        if ctx.guild == None:
            await ctx.respond(f"This command must be run in a guild.")
            return
        await ctx.respond(f"```json\n\n{json.dumps(self.db.read()[str(ctx.guild.id)], indent=4)}\n```")

    @viewserverconfig.error
    async def viewserverconfig_error(self, ctx: SlashContext, error):
        if isinstance(error, CheckFailure):
            await ctx.respond("Admininstrator permissions are required to run this command.")

    @TranslatorSlashGroup.command(description="Learn how to use the Translator feature")
    async def tutorial(self, ctx: SlashContext):
        await ctx.respond(f"Check out the tutorial here:\nhttps://github.com/AnnoyingRain5/RainyBot/wiki/Translator")

    @has_permissions(administrator=True)
    @TranslatorChannelSlashGroup.command(description="Remove a channel group")
    async def remove(self, ctx: SlashContext, channelgroupid: int):
        if ctx.guild == None:
            await ctx.respond(f"This command must be run in a guild.")
            return
        if channelgroupid == 0:
            await ctx.respond("You cannot remove group ID 0! That group is reserved to ensure the bot doesn't crash...")
        else:
            self.db.db[str(ctx.guild.id)]["ChannelGroups"].pop(
                str(channelgroupid))
            self.db.save()
            await ctx.respond("Done!")

    @remove.error
    async def remove_error(self, ctx: SlashContext, error):
        if isinstance(error, CheckFailure):
            await ctx.respond("Admininstrator permissions are required to run this command.")


def setup(bot):
    bot.add_cog(Translator(bot))
