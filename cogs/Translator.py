from discord import Webhook
import aiohttp
import googletrans
import json
from discord.commands import SlashCommandGroup
from discord.ext import commands
from discord.ext.commands import has_permissions, CheckFailure
from lib.DatabaseManager import Database

translator = googletrans.Translator()
GuildToChannelGroupList = {}


class Translator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()
        self.db = Database("Translator")
            
    TranslatorSlashGroup = SlashCommandGroup("translator", "Configure the translator")
    TranslatorChannelSlashGroup = TranslatorSlashGroup.create_subgroup("channelgroup", "Configure Channel Groups")

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        if guild.id not in self.db.read(): # if the server does not have any ChannelGroups
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
        if ctx.webhook_id == None: # if the message isnt from a webhook
            for ChannelGroupID in self.db.read()[str(ctx.guild.id)]["ChannelGroups"]:
                ChannelGroup = self.db.read()[str(ctx.guild.id)]["ChannelGroups"][ChannelGroupID]
                if str(ctx.channel.id) in ChannelGroup: # if the channel is in the channelGroup
                    for channel in ChannelGroup:
                        if channel != str(ctx.channel.id) and channel != "0": # dont send the message in its own channel, and dont send it to ID 0
                            webhook = Webhook.from_url(self.db.read()[str(ctx.guild.id)]["webhooks"][str(channel)], session=self.session)
                            # Get the attachments
                            attachments = []
                            for attachment in ctx.attachments:
                                attachments.append(await attachment.to_file())
                            if ctx.content == "": # if the message is empty (only attachments)
                                await webhook.send(content="", username=ctx.author.name, avatar_url=ctx.author.avatar.url, files=attachments)
                            SourceLang = ChannelGroup[str(ctx.channel.id)] # language of the channel the original message was in
                            DestinationLang = ChannelGroup[str(channel)] # language of the current channel in the ChannelGroup
                            TranslatedText = translator.translate(ctx.content, DestinationLang, SourceLang).text
                            print(f"'{ctx.content}' in {SourceLang} is '{TranslatedText}' in {DestinationLang}")
                            await webhook.send(TranslatedText, username=ctx.author.name, avatar_url=ctx.author.avatar.url, files=attachments)
    @has_permissions(administrator=True)
    @TranslatorChannelSlashGroup.command(description="Create a channel group")
    #adding a default value makes parameter optional
    async def create(self, ctx, channel1, channel1language, channel1webhook, channel2, channel2language, channel2webhook,
             channel3=0, channel3language='', channel3webhook='', channel4=0, channel4language='', channel4webhook='', channel5=0, channel5language='', channel5webhook=''):
                 
        ChannelGroup = {channel1: channel1language, channel2: channel2language, channel3: channel3language, channel4: channel4language, channel5: channel5language}
        WebhookTable = {channel1: channel1webhook, channel2: channel2webhook, channel3: channel3webhook, channel4: channel4webhook, channel5: channel5webhook}
        ChannelGroupID = str(int(list(self.db.read()[str(ctx.guild.id)]["ChannelGroups"])[-1])+1)
        self.db.db[str(ctx.guild.id)]["ChannelGroups"].update({ChannelGroupID: ChannelGroup}) # ensure each channelgroup is seperate
        self.db.db[str(ctx.guild.id)]["webhooks"].update(WebhookTable)
        self.db.save()
        await ctx.respond("Channel group created!")

    @create.error
    async def create_error(self, ctx, error):
        if isinstance(error, CheckFailure):
            await ctx.respond("Admininstrator permissions are required to run this command.")
    
    @has_permissions(administrator=True)
    @TranslatorSlashGroup.command(description="Display the server config JSON")
    async def viewserverconfig(self, ctx):
        await ctx.respond(f"```json\n\n{json.dumps(self.db.read()[str(ctx.guild.id)], indent=4)}\n```")
    
    @viewserverconfig.error
    async def viewserverconfig_error(self, ctx, error):
        if isinstance(error, CheckFailure):
            await ctx.respond("Admininstrator permissions are required to run this command.")
            
    @TranslatorSlashGroup.command(description="Learn how to use the Translator feature")
    async def tutorial(self, ctx):
        await ctx.respond(f"Check out the tutorial here:\nhttps://github.com/AnnoyingRain5/RainyBot/wiki/Translator")
    
    @has_permissions(administrator=True)
    @TranslatorChannelSlashGroup.command(description="Remove a channel group")
    async def remove(self, ctx, channelgroupid: int):
        if channelgroupid == 0:
            await ctx.respond("You cannot remove group ID 0! That group is reserved to ensure the bot doesn't crash...")
        else:
            self.db.db[str(ctx.guild.id)]["ChannelGroups"].pop(str(channelgroupid))
            self.db.save()
            await ctx.respond("Done!")
            
    @remove.error
    async def remove_error(self, ctx, error):
        if isinstance(error, CheckFailure):
            await ctx.respond("Admininstrator permissions are required to run this command.")
            
def setup(bot):
    bot.add_cog(Translator(bot))
