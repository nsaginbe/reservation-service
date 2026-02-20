import fastapi

from api import controllers, schemas

router = fastapi.APIRouter()


@router.get(
    "/free-rooms",
    response_model=schemas.BnovoResponse,
)
def bnovo_free_spaces(
    date_from: str = fastapi.Query(..., description="Start date in dd.mm.yyyy"),
    date_to: str = fastapi.Query(..., description="End date in dd.mm.yyyy"),
    house_category: str = fastapi.Query(..., description="House category to filter"),
):
    return controllers.bnovo_free_spaces(
        date_from=date_from,
        date_to=date_to,
        house_category=house_category,
    )
