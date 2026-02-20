import datetime

import pydantic


class FreeSpace(pydantic.BaseModel):
    date_from: str
    date_to: str
    nights: int

    model_config = pydantic.ConfigDict(populate_by_name=True, extra="forbid")


class RoomFreeSpaces(pydantic.BaseModel):
    room: str
    free: list[FreeSpace]

    model_config = pydantic.ConfigDict(extra="forbid")


class Meta(pydantic.BaseModel):
    execution_started: datetime.datetime
    execution_finished: datetime.datetime
    duration_seconds: float

    model_config = pydantic.ConfigDict(extra="forbid")


class BnovoResponse(pydantic.BaseModel):
    date_from: str
    date_to: str
    house_category: str
    rooms: list[RoomFreeSpaces]
    meta: Meta

    model_config = pydantic.ConfigDict(extra="forbid")
