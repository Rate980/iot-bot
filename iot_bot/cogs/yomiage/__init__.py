import asyncio
import io
import os
import random
import shlex
import subprocess
from typing import IO, Any, Iterable, Optional, cast

import discord
from discord.ext import commands
from discord.oggparse import OggStream

from iot_bot.cogs.yomiage.data import Data

from .board import Board
from .voivo import Voivo


class AsyncFFmpegOpusAudio(discord.AudioSource):
    def __init__(
        self,
        source: str | bytearray | bytes | memoryview,
        *,
        bitrate: int = 128,
        codec: Optional[str] = None,
        executable: str = "ffmpeg",
        pipe: bool = False,
        stderr: Optional[int | IO[Any]] = None,
        before_options: str | Iterable[str] = (),
        options: str | Iterable[str] = (),
        ffmpeg_loglevel: str = "warning",
    ) -> None:
        self.pipe = pipe
        self.source = source
        if codec != "opus" and codec != "copy":
            codec = "libopus"

        if pipe and isinstance(source, str):
            raise TypeError("a bytes-like object is required, not 'str'")

        if not pipe and not isinstance(source, str):
            raise TypeError("a string is required, not '%s'" % type(source).__name__)

        input_file = cast(str, source if pipe else "-")

        cmd = [executable]
        if isinstance(before_options, str):
            cmd.extend(shlex.split(before_options))
        else:
            cmd.extend(before_options)

        cmd.append("-i")
        cmd.append(input_file)
        cmd.extend(
            (
                "-map_metadata",
                "-1",
                "-f",
                "opus",
                "-c:a",
                codec,
                "-ar",
                "48000",
                "-ac",
                "2",
                "-b:a",
                f"{bitrate}k",
                "-loglevel",
                ffmpeg_loglevel,
            )
        )
        if isinstance(options, str):
            cmd.extend(shlex.split(options))
        else:
            cmd.extend(options)

        cmd.append("pipe:1")
        self.__runner = asyncio.create_task(
            asyncio.subprocess.create_subprocess_exec(
                *cmd, stdin=subprocess.PIPE, stderr=stderr, stdout=subprocess.PIPE
            )
        )
        self.__runed = False
        self.__audio = None

    @property
    def runed(self) -> bool:
        return self.__runed

    async def run(self):
        pro = await self.__runner
        if self.pipe:
            pro.stdin.write(self.source)  # type: ignore

        await pro.wait()
        self.__audio = OggStream(io.BytesIO(await pro.stdout.read())).init_packets()  # type: ignore
        self.__runed = True

    def read(self):
        if not self.__runed:
            raise RuntimeError("not runed")
        return self.__audio.read()  # type: ignore


class Yomiage(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.voivo = Voivo()
        self.voice_client: discord.VoiceClient | None = None
        self.data = Data()

    @commands.Cog.listener()
    async def on_ready(self):
        return
        if (channel := self.bot.get_channel(540816542191845386)) is None:
            channel = await self.bot.fetch_channel(540816542191845386)

        if not isinstance(channel, discord.VoiceChannel):
            return

        self.voice = await channel.connect()

    async def cog_unload(self):
        await self.voivo.close()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        if self.voice_client is None:
            return

        q = await self.voivo.get_audio_query(text=message.content, speaker=3)
        uid = str(message.author.id)
        spkr = self.data.get(uid, 3)
        audio = await self.voivo.synthesis(audio_query=q, speaker=spkr)
        file_name = f"{random.randint(0, 100000)}.wav"
        with open(file_name, "wb") as f:
            f.write(audio)
        with open("err.txt", "w") as f:
            source = discord.FFmpegPCMAudio(file_name, stderr=f)
            # source = discord.FFmpegPCMAudio(io.BytesIO(audio), pipe=True, stderr=f)
            # source = discord.FFmpegOpusAudio(
            #     io.BytesIO(audio), pipe=True, stderr=f, before_options=""
            # )
            # source = AsyncFFmpegOpusAudio(audio, pipe=True, stderr=f)
            # await source.run()

        self.voice_client.play(source, after=lambda _: os.remove(file_name))

    @commands.guild_only()
    @commands.hybrid_command()
    async def start(self, ctx: commands.Context):
        if ctx.author.voice is None:  # type: ignore
            await ctx.send("vc入いれ")
            return

        if self.voice_client is not None:
            return

        self.voice_client = await ctx.author.voice.channel.connect()  # type: ignore

    @commands.hybrid_command()
    async def change(self, ctx: commands.Context):
        # view = Board(await self.voivo.speakers())
        view = Board(await self.voivo.speakers(), self.data.get(str(ctx.author.id), 3))
        # view = Board(
        #     [
        #         Speaker(
        #             name=chr(x + 65),
        #             speaker_uuid="a",
        #             styles=[Style(name="のまる", id=x)],
        #         )
        #         for x in range(40)
        #     ]
        # )
        await ctx.send(view=view, ephemeral=True)
        await view.wait()
        if not view.canceled:
            if (id := view.speaker_id) is None:
                return
            print(view.speaker_id)
            self.data.set(str(ctx.author.id), id)


async def setup(bot: commands.Bot):
    await bot.add_cog(Yomiage(bot))


if __name__ == "__main__":
    from pathlib import Path

    # import discord

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
    bot.run(token, root_logger=True)
