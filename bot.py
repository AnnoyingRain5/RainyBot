import discord
import os
from dotenv import load_dotenv
from discord.ext.commands import CheckFailure
import sys
import traceback
from io import StringIO

load_dotenv()  # load env vars from file

# set up intents
intents = discord.Intents.default()
intents += discord.Intents.message_content

bot = discord.Bot(intents=intents)


@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    await bot.change_presence(activity=discord.Game(name="with Rains' emotions!"))


@bot.slash_command(description="Load cog")
async def load(ctx, cog: str):
    if await bot.is_owner(ctx.author):
        try:
            bot.load_extension(f'cogs.{cog}')
            await ctx.respond(f"Loaded cog `{cog}`!")
        except:
            await ctx.respond(f"Failed to load cog `{cog}`...")
    else:
        await ctx.respond(f"You are not <@!{bot.owner_id}>, nice try though.")


@bot.slash_command(description="Rnload cog")
async def unload(ctx, cog: str):
    if await bot.is_owner(ctx.author):
        try:
            bot.unload_extension(f'cogs.{cog}')
            await ctx.respond(f"Unloaded cog `{cog}`!")
        except:
            await ctx.respond(f"Failed to unload cog `{cog}`...")
    else:
        await ctx.respond(f"You are not <@!{bot.owner_id}>, nice try though.")


@bot.slash_command(description="Reload cog")
async def reload(ctx, cog: str):
    if await bot.is_owner(ctx.author):
        try:
            bot.unload_extension(f'cogs.{cog}')
            bot.load_extension(f'cogs.{cog}')
            await ctx.respond(f"Reloaded cog `{cog}`!")
        except:
            await ctx.respond(f"Failed to unload cog `{cog}`...")
    else:
        await ctx.respond(f"You are not <@!{bot.owner_id}>, nice try though.")


@bot.slash_command(description="List the cogs that are currently loaded")
async def listcogs(ctx):
    if await bot.is_owner(ctx.author):
        response = ""
        for item in bot.extensions.keys():
            response += item + ", "
        await ctx.respond(response)
    else:
        await ctx.respond(f"You are not <@!{bot.owner_id}>, nice try though.")


@bot.slash_command(description="Ping the bot!")
async def ping(ctx):
    await ctx.respond(f"Pong! Bot latency is: `{round(bot.latency*1000)}ms`")


@bot.slash_command(description="Get the link to the bot's source code!")
async def github(ctx):
    await ctx.respond("https://github.com/AnnoyingRain5/RainyBot")


@bot.slash_command(description="Learn more about the bot!")
async def info(ctx):
    info = await bot.application_info()
    version = os.popen("git describe --tags --abbrev=0").read().strip("\n")
    latest = os.popen(
        "git ls-remote --refs --tags | tail --lines=1 | cut --delimiter='/' --fields=3").read().strip("\n")

    embed = discord.Embed(
        title="Bot Info", description=f"Hi!\n I'm {info.name}, ")
    if info.id == 1018460858625572924:  # if the bot is the official bot
        embed.description += ""
    else:  # if this is either a self hosted bot or a fork
        if info.name == "RainyBot":  # if the name is the same as the official version, assume it's a self-hosted instance
            embed.description += "I appear to be a self hosted version of the official bot, which is great!\n"
        else:  # if the name is different, assume it's a fork
            embed.description += f"or at least that's what {info.owner.name} called me.\n I'm actually RainyBot, a bot made by AnnoyingRains.\n "
            embed.description += f"I'm either a fork or a self hosted version of the official bot, which is fine by me, it's who I am afterall!\n"
    embed.description += "\nTo learn more about what I can do, check my commands by hitting / and clicking on my profile picture in the command picker, "
    embed.description += "or by checking out my github! (/github)"

    footer = f"I appear to be running on version {version}, "
    if version == latest:
        footer += "which is the latest version!\n"
    else:  # if the bot is an old version, let the user know
        footer += f"which is outdated, the latest version is {latest}. Could you ask {info.owner.name} to update me?\n"

    embed.set_footer(text=footer)

    await ctx.respond(embed=embed)

# load all cogs
for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        # remove file extension and load cog
        bot.load_extension(f'cogs.{filename[:-3]}')


# Global command error handler
@bot.event
async def on_application_command_error(ctx, error):
    # Check failures should be handled by the individual cogs, not here.
    if not isinstance(error, CheckFailure):
        await ctx.send(f"An error occured and has been automatically reported to the developer. Error: `{error}`")
        info = await bot.application_info()
        sio = StringIO()
        # traceback requires a file-like object, so we use StringIO to get the traceback as a string
        traceback.print_exception(error, file=sio, limit=4)
        tb = sio.getvalue()  # get the string from the StringIO object
        message = f"An error occured in {ctx.guild.name} ({ctx.guild.id}) in {ctx.channel.name} ({ctx.channel.mention}) by {ctx.author.name} ({ctx.author.mention})\n"
        message += f"Error: `{error}`\n The traceback will be supplied in the next message."
        await info.owner.send(message)
        await info.owner.send(f"```py\n{tb}```")


# Global non-command error handler
@bot.event
async def on_error(event, *args, **kwargs):
    info = await bot.application_info()
    sio = StringIO()
    # traceback requires a file-like object, so we use StringIO to get the traceback as a string
    traceback.print_exc(file=sio, limit=4)
    tb = sio.getvalue()  # get the string from the StringIO object
    message = f"The following error occoured in `{event}`:\nargs: ```py\n{args}```\nkwargs:```py\n{kwargs}```\n\n"
    message += f"Error type: `{sys.exc_info()[0]}`\nError value: `{sys.exc_info()[1]}`\nThe traceback will be supplied in the next message."
    await info.owner.send(message)
    await info.owner.send(f"```py\n{tb}```")


bot.run(os.getenv('TOKEN'))
