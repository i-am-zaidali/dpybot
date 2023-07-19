from discord.ext import commands
import discord


class Context(commands.Context):
    async def tick(self, *, value: bool = True, message: str = None) -> None:
        emoji = "\N{WHITE HEAVY CHECK MARK}" if value else "\N{CROSS MARK}"

        try:
            await self.message.add_reaction(emoji)

        except discord.HTTPException:
            if message is None:
                message = emoji
            await self.send(message)
