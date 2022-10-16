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
        message = f"An error occured in {ctx.guild.name} ({ctx.guild.id}) in {ctx.channel.name} ({ctx.channel.mention}) by {ctx.author.name} ({ctx.author.mention})\nError: `{error}`\n The traceback will be supplied in the next message."
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
    message = f"The following error occoured in `{event}`:\nargs: ```py\n{args}```\nkwargs:```py\n{kwargs}```\n\nError type: `{sys.exc_info()[0]}`\nError value: `{sys.exc_info()[1]}`\nThe traceback will be supplied in the next message."
    await info.owner.send(message)
    await info.owner.send(f"```py\n{tb}```")


bot.run(os.getenv('TOKEN'))
