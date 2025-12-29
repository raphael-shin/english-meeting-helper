from __future__ import annotations

import time
from typing import Callable

from pydantic import BaseModel, ConfigDict


def to_camel(value: str) -> str:
    parts = value.split("_")
    return parts[0] + "".join(word.capitalize() for word in parts[1:])


def epoch_ms() -> int:
    return int(time.time() * 1000)


class CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="forbid")


CamelCaseAlias = Callable[[str], str]
