from typing import Optional

from pydantic import BaseModel, Field


class ParseRoomOffer(BaseModel):
    meal: Optional[str] = Field(default=None, description="Meal plan")
    price: int = Field(..., description="Price in KZT")


class ParseRoom(BaseModel):
    name: str = Field(..., description="Room name")
    offers: list[ParseRoomOffer] = Field(default_factory=list)


class ParseData(BaseModel):
    dfrom: str
    dto: str
    adults: int
    children: str
    rooms: list[ParseRoom] = Field(default_factory=list)


class ParseResponse(BaseModel):
    status: str
    data: Optional[ParseData] = None
