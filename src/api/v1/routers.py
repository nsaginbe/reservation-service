import fastapi

from api.v1.endpoints import parsers

api_router = fastapi.APIRouter(prefix="/api/v1")

api_router.include_router(parsers.router, tags=["parsers"])
