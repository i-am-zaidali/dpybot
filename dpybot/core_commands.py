# This file contains commands that are core to the bot.
# These are also moslty copied from redbot

from __future__ import annotations

import asyncio
import aiohttp
from typing import TYPE_CHECKING

import discord
from discord.ext import commands

from dpybot import log
import dpybot.chat_formatting as cf

if TYPE_CHECKING:
    from dpybot.bot import DpyBot


class Core(commands.Cog):
    def __init__(self, bot: DpyBot) -> None:
        self.bot = bot

    @commands.group(name="set")
    async def _set(self, ctx: commands.Context):
        """Commands for changing [botname]'s settings."""

    # -- Bot Metadata Commands -- ###

    @_set.group(name="bot", aliases=["metadata"])
    @commands.admin_or_permissions(manage_nicknames=True)
    async def _set_bot(self, ctx: commands.Context):
        """Commands for changing [botname]'s metadata."""

    @commands.is_owner()
    @_set_bot.command(name="description")
    async def _set_bot_description(self, ctx: commands.Context, *, description: str = ""):
        """
        Sets the bot's description.

        Use without a description to reset.
        This is shown in a few locations, including the help menu.

        The maximum description length is 250 characters to ensure it displays properly.

        The default is "Red V3".

        **Examples:**
        - `[p]set bot description` - Resets the description to the default setting.
        - `[p]set bot description MyBot: A Red V3 Bot`

        **Arguments:**
        - `[description]` - The description to use for this bot. Leave blank to reset to the default.
        """
        if not description:
            await ctx.bot._config.description.clear()
            ctx.bot.description = "Red V3"
            await ctx.send("Description reset.")
        elif len(description) > 250:  # While the limit is 256, we bold it adding characters.
            await ctx.send(
                (
                    "This description is too long to properly display. "
                    "Please try again with below 250 characters."
                )
            )
        else:
            await ctx.bot._config.description.set(description)
            ctx.bot.description = description
            await ctx.tick()

    @_set_bot.group(name="avatar", invoke_without_command=True)
    @commands.is_owner()
    async def _set_bot_avatar(self, ctx: commands.Context, url: str = None):
        """Sets [botname]'s avatar

        Supports either an attachment or an image URL.

        **Examples:**
        - `[p]set bot avatar` - With an image attachment, this will set the avatar.
        - `[p]set bot avatar` - Without an attachment, this will show the command help.
        - `[p]set bot avatar https://links.flaree.xyz/k95` - Sets the avatar to the provided url.

        **Arguments:**
        - `[url]` - An image url to be used as an avatar. Leave blank when uploading an attachment.
        """
        if len(ctx.message.attachments) > 0:  # Attachments take priority
            data = await ctx.message.attachments[0].read()
        elif url is not None:
            if url.startswith("<") and url.endswith(">"):
                url = url[1:-1]

            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(url) as r:
                        data = await r.read()
                except aiohttp.InvalidURL:
                    return await ctx.send("That URL is invalid.")
                except aiohttp.ClientError:
                    return await ctx.send("Something went wrong while trying to get the image.")
        else:
            await ctx.send_help()
            return

        try:
            async with ctx.typing():
                await ctx.bot.user.edit(avatar=data)
        except discord.HTTPException:
            await ctx.send(
                (
                    "Failed. Remember that you can edit my avatar "
                    "up to two times a hour. The URL or attachment "
                    "must be a valid image in either JPG or PNG format."
                )
            )
        except ValueError:
            await ctx.send("JPG / PNG format only.")
        else:
            await ctx.send("Done.")

    @_set_bot_avatar.command(name="remove", aliases=["clear"])
    @commands.is_owner()
    async def _set_bot_avatar_remove(self, ctx: commands.Context):
        """
        Removes [botname]'s avatar.

        **Example:**
        - `[p]set bot avatar remove`
        """
        async with ctx.typing():
            await ctx.bot.user.edit(avatar=None)
        await ctx.send("Avatar removed.")

    @_set_bot.command(name="username", aliases=["name"])
    @commands.is_owner()
    async def _set_bot_username(self, ctx: commands.Context, *, username: str):
        """Sets [botname]'s username.

        Maximum length for a username is 32 characters.

        Note: The username of a verified bot cannot be manually changed.
            Please contact Discord support to change it.

        **Example:**
        - `[p]set bot username BaguetteBot`

        **Arguments:**
        - `<username>` - The username to give the bot.
        """
        try:
            if self.bot.user.public_flags.verified_bot:
                await ctx.send(
                    (
                        "The username of a verified bot cannot be manually changed."
                        " Please contact Discord support to change it."
                    )
                )
                return
            if len(username) > 32:
                await ctx.send("Failed to change name. Must be 32 characters or fewer.")
                return
            async with ctx.typing():
                await asyncio.wait_for(self._name(name=username), timeout=30)
        except asyncio.TimeoutError:
            await ctx.send(
                (
                    "Changing the username timed out. "
                    "Remember that you can only do it up to 2 times an hour."
                    " Use nicknames if you need frequent changes: {command}"
                ).format(command=cf.inline(f"{ctx.clean_prefix}set bot nickname"))
            )
        except discord.HTTPException as e:
            if e.code == 50035:
                error_string = e.text.split("\n")[1]  # Remove the "Invalid Form body"
                await ctx.send(
                    (
                        "Failed to change the username. "
                        "Discord returned the following error:\n"
                        "{error_message}"
                    ).format(error_message=cf.inline(error_string))
                )
            else:
                log.error(
                    "Unexpected error occurred when trying to change the username.", exc_info=e
                )
                await ctx.send("Unexpected error occurred when trying to change the username.")
        else:
            await ctx.send("Done.")

    @_set_bot.command(name="nickname")
    @commands.admin_or_permissions(manage_nicknames=True)
    @commands.guild_only()
    async def _set_bot_nickname(self, ctx: commands.Context, *, nickname: str = None):
        """Sets [botname]'s nickname for the current server.

        Maximum length for a nickname is 32 characters.

        **Example:**
        - `[p]set bot nickname 🎃 SpookyBot 🎃`

        **Arguments:**
        - `[nickname]` - The nickname to give the bot. Leave blank to clear the current nickname.
        """
        try:
            if nickname and len(nickname) > 32:
                await ctx.send("Failed to change nickname. Must be 32 characters or fewer.")
                return
            await ctx.guild.me.edit(nick=nickname)
        except discord.Forbidden:
            await ctx.send("I lack the permissions to change my own nickname.")
        else:
            await ctx.send("Done.")

    @_set_bot.command(name="custominfo")
    @commands.is_owner()
    async def _set_bot_custominfo(self, ctx: commands.Context, *, text: str = None):
        """Customizes a section of `[p]info`.

        The maximum amount of allowed characters is 1024.
        Supports markdown, links and "mentions".

        Link example: `[My link](https://example.com)`

        **Examples:**
        - `[p]set bot custominfo >>> I can use **markdown** such as quotes, ||spoilers|| and multiple lines.`
        - `[p]set bot custominfo Join my [support server](discord.gg/discord)!`
        - `[p]set bot custominfo` - Removes custom info text.

        **Arguments:**
        - `[text]` - The custom info text.
        """
        if not text:
            await ctx.bot._config.custom_info.clear()
            await ctx.send("The custom text has been cleared.")
            return
        if len(text) <= 1024:
            await ctx.bot._config.custom_info.set(text)
            await ctx.send("The custom text has been set.")
            await ctx.invoke(self.info)
        else:
            await ctx.send("Text must be fewer than 1024 characters long.")

    # -- End Bot Metadata Commands -- ###
    # -- Bot Status Commands -- ###

    @_set.group(name="status")
    @commands.bot_in_a_guild()
    @commands.is_owner()
    async def _set_status(self, ctx: commands.Context):
        """Commands for setting [botname]'s status."""

    @_set_status.command(
        name="streaming", aliases=["stream", "twitch"], usage="[(<streamer> <stream_title>)]"
    )
    @commands.bot_in_a_guild()
    @commands.is_owner()
    async def _set_status_stream(self, ctx: commands.Context, streamer=None, *, stream_title=None):
        """Sets [botname]'s streaming status to a twitch stream.

        This will appear as `Streaming <stream_title>` or `LIVE ON TWITCH` depending on the context.
        It will also include a `Watch` button with a twitch.tv url for the provided streamer.

        Maximum length for a stream title is 128 characters.

        Leaving both streamer and stream_title empty will clear it.

        **Examples:**
        - `[p]set status stream` - Clears the activity status.
        - `[p]set status stream 26 Twentysix is streaming` - Sets the stream to `https://www.twitch.tv/26`.
        - `[p]set status stream https://twitch.tv/26 Twentysix is streaming` - Sets the URL manually.

        **Arguments:**
        - `<streamer>` - The twitch streamer to provide a link to. This can be their twitch name or the entire URL.
        - `<stream_title>` - The text to follow `Streaming` in the status."""
        status = ctx.bot.guilds[0].me.status if len(ctx.bot.guilds) > 0 else None

        if stream_title:
            stream_title = stream_title.strip()
            if "twitch.tv/" not in streamer:
                streamer = "https://www.twitch.tv/" + streamer
            if len(streamer) > 511:
                await ctx.send("The maximum length of the streamer url is 511 characters.")
                return
            if len(stream_title) > 128:
                await ctx.send("The maximum length of the stream title is 128 characters.")
                return
            activity = discord.Streaming(url=streamer, name=stream_title)
            await ctx.bot.change_presence(status=status, activity=activity)
        elif streamer is not None:
            await ctx.send_help()
            return
        else:
            await ctx.bot.change_presence(activity=None, status=status)
        await ctx.send("Done.")

    @_set_status.command(name="playing", aliases=["game"])
    @commands.bot_in_a_guild()
    @commands.is_owner()
    async def _set_status_game(self, ctx: commands.Context, *, game: str = None):
        """Sets [botname]'s playing status.

        This will appear as `Playing <game>` or `PLAYING A GAME: <game>` depending on the context.

        Maximum length for a playing status is 128 characters.

        **Examples:**
        - `[p]set status playing` - Clears the activity status.
        - `[p]set status playing the keyboard`

        **Arguments:**
        - `[game]` - The text to follow `Playing`. Leave blank to clear the current activity status.
        """

        if game:
            if len(game) > 128:
                await ctx.send("The maximum length of game descriptions is 128 characters.")
                return
            game = discord.Game(name=game)
        else:
            game = None
        status = ctx.bot.guilds[0].me.status if len(ctx.bot.guilds) > 0 else discord.Status.online
        await ctx.bot.change_presence(status=status, activity=game)
        if game:
            await ctx.send("Status set to `Playing {game.name}`.".format(game=game))
        else:
            await ctx.send("Game cleared.")

    @_set_status.command(name="listening")
    @commands.bot_in_a_guild()
    @commands.is_owner()
    async def _set_status_listening(self, ctx: commands.Context, *, listening: str = None):
        """Sets [botname]'s listening status.

        This will appear as `Listening to <listening>`.

        Maximum length for a listening status is 128 characters.

        **Examples:**
        - `[p]set status listening` - Clears the activity status.
        - `[p]set status listening jams`

        **Arguments:**
        - `[listening]` - The text to follow `Listening to`. Leave blank to clear the current activity status.
        """

        status = ctx.bot.guilds[0].me.status if len(ctx.bot.guilds) > 0 else discord.Status.online
        if listening:
            if len(listening) > 128:
                await ctx.send("The maximum length of listening descriptions is 128 characters.")
                return
            activity = discord.Activity(name=listening, type=discord.ActivityType.listening)
        else:
            activity = None
        await ctx.bot.change_presence(status=status, activity=activity)
        if activity:
            await ctx.send("Status set to `Listening to {listening}`.".format(listening=listening))
        else:
            await ctx.send("Listening cleared.")

    @_set_status.command(name="watching")
    @commands.bot_in_a_guild()
    @commands.is_owner()
    async def _set_status_watching(self, ctx: commands.Context, *, watching: str = None):
        """Sets [botname]'s watching status.

        This will appear as `Watching <watching>`.

        Maximum length for a watching status is 128 characters.

        **Examples:**
        - `[p]set status watching` - Clears the activity status.
        - `[p]set status watching [p]help`

        **Arguments:**
        - `[watching]` - The text to follow `Watching`. Leave blank to clear the current activity status.
        """

        status = ctx.bot.guilds[0].me.status if len(ctx.bot.guilds) > 0 else discord.Status.online
        if watching:
            if len(watching) > 128:
                await ctx.send("The maximum length of watching descriptions is 128 characters.")
                return
            activity = discord.Activity(name=watching, type=discord.ActivityType.watching)
        else:
            activity = None
        await ctx.bot.change_presence(status=status, activity=activity)
        if activity:
            await ctx.send("Status set to `Watching {watching}`.".format(watching=watching))
        else:
            await ctx.send("Watching cleared.")

    @_set_status.command(name="competing")
    @commands.bot_in_a_guild()
    @commands.is_owner()
    async def _set_status_competing(self, ctx: commands.Context, *, competing: str = None):
        """Sets [botname]'s competing status.

        This will appear as `Competing in <competing>`.

        Maximum length for a competing status is 128 characters.

        **Examples:**
        - `[p]set status competing` - Clears the activity status.
        - `[p]set status competing London 2012 Olympic Games`

        **Arguments:**
        - `[competing]` - The text to follow `Competing in`. Leave blank to clear the current activity status.
        """

        status = ctx.bot.guilds[0].me.status if len(ctx.bot.guilds) > 0 else discord.Status.online
        if competing:
            if len(competing) > 128:
                await ctx.send("The maximum length of competing descriptions is 128 characters.")
                return
            activity = discord.Activity(name=competing, type=discord.ActivityType.competing)
        else:
            activity = None
        await ctx.bot.change_presence(status=status, activity=activity)
        if activity:
            await ctx.send("Status set to `Competing in {competing}`.".format(competing=competing))
        else:
            await ctx.send("Competing cleared.")

    async def _set_my_status(self, ctx: commands.Context, status: discord.Status):
        game = ctx.bot.guilds[0].me.activity if len(ctx.bot.guilds) > 0 else None
        await ctx.bot.change_presence(status=status, activity=game)
        return await ctx.send("Status changed to {}.".format(status))

    @_set_status.command(name="online")
    @commands.bot_in_a_guild()
    @commands.is_owner()
    async def _set_status_online(self, ctx: commands.Context):
        """Set [botname]'s status to online."""
        await self._set_my_status(ctx, discord.Status.online)

    @_set_status.command(name="dnd", aliases=["donotdisturb", "busy"])
    @commands.bot_in_a_guild()
    @commands.is_owner()
    async def _set_status_dnd(self, ctx: commands.Context):
        """Set [botname]'s status to do not disturb."""
        await self._set_my_status(ctx, discord.Status.do_not_disturb)

    @_set_status.command(name="idle", aliases=["away", "afk"])
    @commands.bot_in_a_guild()
    @commands.is_owner()
    async def _set_status_idle(self, ctx: commands.Context):
        """Set [botname]'s status to idle."""
        await self._set_my_status(ctx, discord.Status.idle)

    @_set_status.command(name="invisible", aliases=["offline"])
    @commands.bot_in_a_guild()
    @commands.is_owner()
    async def _set_status_invisible(self, ctx: commands.Context):
        """Set [botname]'s status to invisible."""
        await self._set_my_status(ctx, discord.Status.invisible)

    @commands.is_owner()
    @commands.command()
    async def reload(self, ctx: commands.Context, pkg_name: str) -> None:
        try:
            await self.bot.reload_package(pkg_name)
        except commands.ExtensionNotLoaded:
            await ctx.send(f"Cog package with name `{pkg_name}` wasn't loaded.")
        except commands.ExtensionNotFound:
            await ctx.send(f"Can't find cog package with name `{pkg_name}.")
        except commands.NoEntryPointError:
            await ctx.send(f"Cog package with name `{pkg_name}` doesn't have `setup()` function.")
        except commands.ExtensionFailed as e:
            await ctx.send(
                f"Cog package with name `{pkg_name}` couldn't be reloaded."
                " See logs for more details."
            )
            log.error(
                "Cog package with name `%s` couldn't be reloaded.",
                pkg_name,
                exc_info=e.original,
            )
        else:
            await ctx.send(f"{pkg_name} reloaded.")

    @commands.is_owner()
    @commands.command()
    async def load(self, ctx: commands.Context, pkg_name: str) -> None:
        try:
            await self.bot.load_package(pkg_name)
        except commands.ExtensionAlreadyLoaded:
            await ctx.send(f"Cog package with name `{pkg_name}` is already loaded.")
        except commands.ExtensionNotFound:
            await ctx.send(f"Can't find cog package with name `{pkg_name}.")
        except commands.NoEntryPointError:
            await ctx.send(f"Cog package with name `{pkg_name}` doesn't have `setup()` function.")
        except commands.ExtensionFailed as e:
            await ctx.send(
                f"Cog package with name `{pkg_name}` couldn't be loaded."
                " See logs for more details."
            )
            log.error(
                "Cog package with name `%s` couldn't be loaded.",
                pkg_name,
                exc_info=e.original,
            )
        else:
            await ctx.send(f"{pkg_name} loaded.")

    @commands.is_owner()
    @commands.command()
    async def unload(self, ctx: commands.Context, pkg_name: str) -> None:
        try:
            await self.bot.unload_package(pkg_name)
        except commands.ExtensionNotLoaded:
            await ctx.send(f"Cog package with name `{pkg_name}` wasn't loaded.")
        else:
            await ctx.send(f"{pkg_name} unloaded.")

    @commands.command()
    async def ping(self, ctx: commands.Context) -> None:
        await ctx.send("Pong!")

    @commands.is_owner()
    @commands.command()
    async def shutdown(self, ctx: commands.Context) -> None:
        print("Shutting down...")
        await ctx.send("Shutting down...")
        await self.bot.close()
