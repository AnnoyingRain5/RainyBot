from discord import SlashCommandGroup
from discord.commands.context import ApplicationContext as SlashContext
from discord.ext import commands
from lib.DatabaseManager import Database
from discord.ext.commands import has_permissions, CheckFailure


class ColourRoles(commands.Cog):
    ColourSlashGroup = SlashCommandGroup("colour", "Set custom role colours")

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.db = Database("ColourRoles")
        for guild in self.bot.guilds:
            # if the server does not have any QuickResponses
            if str(guild.id) not in self.db.read():
                # disable by default
                self.db.update({guild.id: {"enabled": False}})

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        if guild.id not in self.db.read():  # if the server isnt already in the database
            # disable by default
            self.db.update({guild.id: {"enabled": False}})

    @ColourSlashGroup.command(description="Set your color!")
    async def set(self, ctx: SlashContext, color: str):
        if self.db.read()[str(ctx.guild.id)]["enabled"] != True:
            await ctx.respond(
                "Colour roles are disabled on this server.", ephemeral=True
            )
            return
        color = color.lstrip("#")
        try:
            intcolor = int(color, 16)
            if len(color) != 6:
                # I would like to apologise in advance for this, I have no idea
                # why I wrote it like that, I mean it works?
                raise Exception
            color = hex(intcolor)
        except Exception as e:
            colors = {
                "red": 0xFF0000,
                "green": 0x00FF00,
                "blue": 0x0000FF,
                "orange": 0xF47B4F,
                "pink": 0xFFC0CB,
                "purple": 0x800080,
            }

            if color in colors:
                intcolor = colors[color]
                color = str(hex(colors[color]))
            else:
                await ctx.respond(
                    "You need to give me either a hex code for a color or basic color name!\n"
                    + "Valid colors are as follows: red, green, blue, orange, pink and purple.",
                    ephemeral=True,
                )
                return
        if intcolor == 0:
            await ctx.respond(
                "You cannot set your color to pure black.", ephemeral=True
            )
            return

        for role in ctx.author.roles:
            if role.color.value != 0 and role.name.startswith("Colour: "):
                await ctx.author.remove_roles(role)
        roles = await ctx.guild.fetch_roles()
        for role in roles:
            if role.name == "Colour: " + color.lstrip("0x").upper():
                await ctx.author.add_roles(role)
                await ctx.respond("Sounds good to me! Role added!", ephemeral=True)
                break
        else:
            role = await ctx.guild.create_role(
                name="Colour: " + color.lstrip("0x").upper(), color=intcolor
            )
            await ctx.author.add_roles(role)
            await ctx.respond(
                "Sounds good to me! Role created and added!", ephemeral=True
            )

    @ColourSlashGroup.command(description="Remove all unused color roles")
    @has_permissions(administrator=True)
    async def remove_unused(self, ctx: SlashContext):
        for role in await ctx.guild.fetch_roles():
            if role.color.value != 0 and role.name.startswith("Colour: "):
                if len(role.members) == 0:
                    print("deleting role ", role.name)
                    await role.delete()
        await ctx.respond("done!", ephemeral=True)

    @remove_unused.error
    async def remove_unused_error(self, ctx: SlashContext, error):
        if isinstance(error, CheckFailure):
            await ctx.respond(
                "Admininstrator permissions are required to run this command."
            )

    @ColourSlashGroup.command(description="Enable Colour Roles")
    @has_permissions(administrator=True)
    async def enable(self, ctx: SlashContext):
        self.db.db[str(ctx.guild.id)] = {"enabled": True}
        self.db.save()
        await ctx.respond("Done!")

    @enable.error
    async def enable_error(self, ctx: SlashContext, error):
        if isinstance(error, CheckFailure):
            await ctx.respond(
                "Admininstrator permissions are required to run this command."
            )

    @ColourSlashGroup.command(description="Disable Colour Roles")
    @has_permissions(administrator=True)
    async def disable(self, ctx: SlashContext):
        self.db.db[str(ctx.guild.id)] = {"enabled": False}
        self.db.save()
        await ctx.respond("Done!")

    @disable.error
    async def disable_error(self, ctx: SlashContext, error):
        if isinstance(error, CheckFailure):
            await ctx.respond(
                "Admininstrator permissions are required to run this command."
            )


def setup(bot):
    bot.add_cog(ColourRoles(bot))
