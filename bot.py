import discord
import os
from dotenv import load_dotenv
from discord.commands import SlashCommandGroup

load_dotenv() # load env vars from file

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

# load all cogs
for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        bot.load_extension(f'cogs.{filename[:-3]}') # remove file extension and load cog

bot.run(os.getenv('TOKEN'))