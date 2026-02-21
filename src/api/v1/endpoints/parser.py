from fastapi import APIRouter, Query

from api.controllers import parser as parser_controller
from api.schemas.parser import ParseResponse

router = APIRouter()


@router.get("/parse-rooms", response_model=ParseResponse)
async def parse_rooms(
    dfrom: str = Query(..., description="Дата заезда (dd.mm.yyyy)"),
    dto: str = Query(..., description="Дата выезда (dd.mm.yyyy)"),
    adults: int = Query(..., ge=1, description="Количество взрослых"),
    children: str = Query(
        default="[]",
        description="Возраста всех детей: [], [5], [0,1,4]",
    ),
):
    return await parser_controller.parse_rooms(
        dfrom=dfrom,
        dto=dto,
        adults=adults,
        children=children,
    )
