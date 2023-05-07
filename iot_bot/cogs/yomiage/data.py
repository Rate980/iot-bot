import json
from pathlib import Path
from typing import TypeVar

import aiofiles
from attr import dataclass

filename = Path(__file__).resolve().parent / "data.json"


class Data:
    def __init__(self):
        if not filename.exists():
            filename.write_text("{}")

        with open(filename, "r") as f:
            self.data: dict[str, int] = json.load(f)

    def save(self):
        with open(filename, "w") as f:
            json.dump(
                self.data,
                f,
                ensure_ascii=False,
            )

    T = TypeVar("T")

    def get(self, key: str, default: T = None) -> int | T:
        return self.data.get(key, default)  # type: ignore

    def set(self, key: str, value: int):
        self.data[key] = value
        self.save()
