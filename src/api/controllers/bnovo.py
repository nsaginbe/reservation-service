from datetime import datetime

import starlette.exceptions
import starlette.status

from api import bnovo, schemas
from common import conf


def bnovo_free_spaces(
    date_from: str,
    date_to: str,
    house_category: str,
) -> schemas.BnovoResponse:
    execution_started = datetime.now()

    try:
        start_date = bnovo.parse_date(date_from)
        end_date = bnovo.parse_date(date_to)
    except ValueError:
        raise starlette.exceptions.HTTPException(
            status_code=starlette.status.HTTP_400_BAD_REQUEST,
            detail="Dates must match dd.mm.yyyy",
        )

    if end_date < start_date:
        raise starlette.exceptions.HTTPException(
            status_code=starlette.status.HTTP_400_BAD_REQUEST,
            detail="date_to must be on or after date_from",
        )

    if not conf.BNOVO_EMAIL or not conf.BNOVO_PASSWORD:
        raise starlette.exceptions.HTTPException(
            status_code=starlette.status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="BNOVO_EMAIL or BNOVO_PASSWORD is not configured",
        )

    try:
        rooms = bnovo.fetch_rooms_data(
            email=conf.BNOVO_EMAIL,
            password=conf.BNOVO_PASSWORD,
            headless=conf.HEADLESS,
            house_category=house_category,
            timeout_ms=conf.TIMEOUT_MS,
            date_from=date_from,
        )
    except Exception as exc:  # pragma: no cover - network/browser interaction
        raise starlette.exceptions.HTTPException(
            status_code=starlette.status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to fetch Bnovo data: {exc}",
        ) from exc

    free_data = [
        schemas.RoomFreeSpaces(
            room=room.room_name,
            free=[
                schemas.FreeSpace(**space)
                for space in bnovo.compute_free_spaces(room.bookings, start_date, end_date)
            ],
        )
        for room in rooms
    ]

    execution_finished = datetime.now()

    return schemas.BnovoResponse(
        date_from=bnovo.format_date(start_date),
        date_to=bnovo.format_date(end_date),
        house_category=house_category,
        rooms=free_data,
        meta=schemas.Meta(
            execution_started=execution_started,
            execution_finished=execution_finished,
            duration_seconds=(execution_finished - execution_started).total_seconds(),
        ),
    )
