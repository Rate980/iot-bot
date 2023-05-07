from discord.ext import commands


class IotBot(commands.Bot):
    async def setup_hook(self):
        await self.load_extension("cogs.common")
        await self.load_extension("cogs.yomiage")
        await self.tree.sync()
