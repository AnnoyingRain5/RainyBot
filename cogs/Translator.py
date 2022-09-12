from discord import Webhook
import discord
import aiohttp
import googletrans
import json
from discord.commands import SlashCommandGroup
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True

translator = googletrans.Translator()
GuildToChannelGroupList = {}


class Translator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()
        with open('db/Translator.json', 'r') as f:
            self.database = json.loads(f.read())
            
    TranslatorSlashGroup = SlashCommandGroup("translator", "Configure the translator")
    TranslatorChannelSlashGroup = TranslatorSlashGroup.create_subgroup("channelgroup", "Configure Channel Groups")

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        if guild.id not in self.database: # if the server does not have any ChannelGroups
            # generate empty template
            self.database.update(
                {
                    guild.id: {
                        "ChannelGroups": {"0", {"": ""}},
                        "webhooks": {"": ""}
                    }
                }
            )
        with open('db/Translator.json', 'w') as f:
            f.write(json.dumps(self.database, indent=4))
        print(self.bot.guilds)
        
    @commands.Cog.listener()
    async def on_ready(self):
        with open('db/Translator.json', 'r') as f:
            self.database = json.loads(f.read())
        for guild in self.bot.guilds:
            # if the server does not have any ChannelGroups
            if str(guild.id) not in self.database:
                print(f"{guild.id} not in database")
                # generate empty template
                self.database.update(
                    {
                        guild.id: {
                            "ChannelGroups": {"0": {"": ""}},
                            "webhooks": {"": ""}
                        }
                    }
                )
                with open('db/Translator.json', 'w') as f:
                    f.write(json.dumps(self.database, indent=4))
                # I have no idea why this works...
                with open('db/Translator.json', 'r') as f:
                    self.database = json.loads(f.read())

    @commands.Cog.listener()
    async def on_message(self, ctx):
        if ctx.webhook_id == None: # if the message isnt from a webhook
            for ChannelGroupID in self.database[str(ctx.guild.id)]["ChannelGroups"]:
                ChannelGroup = self.database[str(ctx.guild.id)]["ChannelGroups"][ChannelGroupID]
                if str(ctx.channel.id) in ChannelGroup: # if the channel is in the channelGroup
                    for channel in ChannelGroup:
                        if channel != str(ctx.channel.id) and channel != "0": # dont send the message in its own channel, and dont send it to ID 0
                            webhook = Webhook.from_url(self.database[str(ctx.guild.id)]["webhooks"][str(channel)], session=self.session)
                            SourceLang = ChannelGroup[str(ctx.channel.id)] # language of the channel the original message was in
                            DestinationLang = ChannelGroup[str(channel)] # language of the current channel in the ChannelGroup
                            TranslatedText = translator.translate(ctx.content, DestinationLang, SourceLang).text
                            print(f"'{ctx.content}' in {SourceLang} is '{TranslatedText}' in {DestinationLang}")
                            await webhook.send(TranslatedText, username=ctx.author.name, avatar_url=ctx.author.avatar.url)

    @TranslatorChannelSlashGroup.command(description="Create a channel group")
    #adding a default value makes parameter optional
    async def create(self, ctx, channel1, channel1language, channel1webhook, channel2, channel2language, channel2webhook,
             channel3=0, channel3language='', channel3webhook='', channel4=0, channel4language='', channel4webhook='', channel5=0, channel5language='', channel5webhook=''):
                 
        ChannelGroup = {channel1: channel1language, channel2: channel2language, channel3: channel3language, channel4: channel4language, channel5: channel5language}
        WebhookTable = {channel1: channel1webhook, channel2: channel2webhook, channel3: channel3webhook, channel4: channel4webhook, channel5: channel5webhook}
        ChannelGroupID = str(int(list(self.database[str(ctx.guild.id)]["ChannelGroups"])[-1])+1)
        self.database[str(ctx.guild.id)]["ChannelGroups"].update({ChannelGroupID: ChannelGroup}) # ensure each channelgroup is seperate
        self.database[str(ctx.guild.id)]["webhooks"].update(WebhookTable)
        with open('db/Translator.json', 'w') as f:
            f.write(json.dumps(self.database, indent=4))
        await ctx.respond("Channel group created!")

    @TranslatorSlashGroup.command(description="Display the server config JSON")
    async def viewserverconfig(self, ctx):
        await ctx.respond(f"```json\n\n{json.dumps(self.database[str(ctx.guild.id)], indent=4)}\n```")
        
    @TranslatorChannelSlashGroup.command(description="Remove a channel group")
    async def remove(self, ctx, channelgroupid: int):
        if channelgroupid == 0:
            await ctx.respond("You cannot remove group ID 0! That group is reserved to ensure the bot doesn't crash...")
        else:
            self.database[str(ctx.guild.id)]["ChannelGroups"].pop(str(channelgroupid))
            with open('db/Translator.json', 'w') as f:
                f.write(json.dumps(self.database, indent=4))
                
def setup(bot):
    bot.add_cog(Translator(bot))
