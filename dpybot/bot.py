import os

import discord
from discord.ext import commands

from dpybot import log
from dpybot.core_commands import Core
from dpybot.context import Context
from dpybot.config import Config


class DpyBot(commands.AutoShardedBot):
    def __init__(self) -> None:
        self._config = Config.get_conf(cog_name="Core", identifier=0)
        self._config.register_global(TOKEN="", prefixes=["k", "!"])
        self._config.register_guild(prefixes=["k", "!"])
        super().__init__(
            command_prefix=self._fetch_prefix,
            intents=discord.Intents.all(),
        )

    async def _fetch_prefix(self, bot: commands.Bot, message: discord.Message) -> str:
        if not self.is_ready():
            return ""
        if cog := self.get_cog("Core"):
            prefixes = await cog.get_prefixes(message.guild)

        else:
            prefixes = commands.when_mentioned_or("k", "!")(bot, message)

        return prefixes

    async def get_context(self, message: discord.Message, *, cls=Context) -> commands.Context:
        return await super().get_context(message, cls=cls)

    async def setup_hook(self) -> None:
        LOAD_ON_STARTUP = os.getenv("DPYBOT_LOAD_ON_STARTUP", "").split(",")
        await self.add_cog(Core(self))
        for pkg_name in LOAD_ON_STARTUP:
            await self.load_package(pkg_name)

    async def on_ready(self) -> None:
        log.info("I am ready!")

    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError) -> None:
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send_help(ctx.command)
        elif isinstance(error, commands.BadArgument):
            if error.args:
                await ctx.send(error.args[0])
            else:
                await ctx.send_help(ctx.command)
        else:
            log.error(type(error).__name__, exc_info=error)

    async def reload_package(self, name: str) -> None:
        try:
            await self.reload_extension(f"dpybot.cogs.{name}")
        except commands.ExtensionNotFound:
            await self.load_extension(f"dpybot.cogs.{name}")

    async def load_package(self, name: str) -> None:
        await self.load_extension(f"dpybot.cogs.{name}")

    async def unload_package(self, name: str) -> None:
        await self.unload_extension(f"dpybot.cogs.{name}")
