from pprint import pprint
from typing import TypedDict

import aiohttp

VOIVO_URL = "http://localhost:50021"


class Style(TypedDict):
    name: str
    id: int


class Speaker(TypedDict):
    name: str
    speaker_uuid: str
    styles: list[Style]


class Voivo:
    def __init__(self) -> None:
        self.session = aiohttp.ClientSession()
        self._speakers: list[Speaker] | None = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def close(self):
        await self.session.close()

    async def get_audio_query(self, text: str, speaker: int) -> dict:
        params = {"text": text, "speaker": speaker}
        async with self.session.post(f"{VOIVO_URL}/audio_query", params=params) as resp:
            if resp.status != 200:
                print(resp.status)
                print(await resp.text())
            return await resp.json()

    async def synthesis(self, audio_query: dict, speaker: int):
        params = {"speaker": speaker}
        async with self.session.post(
            f"{VOIVO_URL}/synthesis",
            params=params,
            json=audio_query,
            headers={("Content-Type", "application/json")},
        ) as resp:
            if resp.status != 200:
                print(resp.status)
                print(await resp.text())
            return await resp.read()

    async def speakers(self) -> list[Speaker]:
        if self._speakers is None:
            async with self.session.get(f"{VOIVO_URL}/speakers") as resp:
                if resp.status != 200:
                    print(resp.status)
                    print(await resp.text())
                self._speakers = await resp.json()

        return self._speakers  # type: ignore


if __name__ == "__main__":
    import asyncio

    async def main():
        async with Voivo() as voivo:
            # q = await voivo.get_audio_query(text="こんにちは", speaker=3)
            # # print(q)
            # # with open("query.json", "r") as f:
            # #     audio = await voivo.synthesis(audio_query=json.load(f), speaker=3)
            # audio = await voivo.synthesis(audio_query=q, speaker=3)
            # with open("test.wav", "wb") as f:
            #     f.write(audio)
            pprint(await voivo.speakers())

    asyncio.run(main())
