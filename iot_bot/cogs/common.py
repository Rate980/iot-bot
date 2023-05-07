import discord
from discord.ext import commands


class Modal(discord.ui.Modal):
    users = discord.ui.Select(
        options=[
            discord.SelectOption(label="a", default=True),
            discord.SelectOption(label="b"),
        ]
    )

    def __init__(self):
        super().__init__(
            title="好きな食べ物は何ですか？",
        )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(self.users, ephemeral=True)


class Common(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command()
    async def ping(self, ctx):
        await ctx.interaction.response.send_modal(Modal())


async def setup(bot: commands.Bot):
    await bot.add_cog(Common(bot))


if __name__ == "__main__":
    import os
    from pathlib import Path

    import discord

    file = Path(__file__).resolve()
    prefix = file.parent

    token = os.environ["DIS_TEST_TOKEN"]

    intents = discord.Intents.all()

    class MyBot(commands.Bot):
        async def on_ready(self):
            print("ready")

        async def setup_hook(self):
            await self.load_extension(file.stem)
            await self.tree.sync()

    bot = MyBot("t!", intents=intents)
    bot.run(token)
