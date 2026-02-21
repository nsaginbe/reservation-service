from datetime import date, datetime
from typing import Any, Dict

from fastapi import HTTPException

from api import parser


def parse_date(value: str) -> date:
    return datetime.strptime(value, "%d.%m.%Y").date()


async def parse_rooms(dfrom: str, dto: str, adults: int, children: str) -> Dict[str, Any]:
    start_date: date = parse_date(dfrom)
    end_date: date = parse_date(dto)

    if end_date <= start_date:
        raise HTTPException(
            status_code=400,
            detail="dto must be later than dfrom",
        )

    data = await parser.fetch_rooms(
        dfrom=start_date,
        dto=end_date,
        adults=adults,
        children=children,
    )

    return {
        "status": "ok",
        "data": data,
    }
