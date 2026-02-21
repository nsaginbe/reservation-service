import fastapi

from api.v1.endpoints import parser

api_router = fastapi.APIRouter(prefix="/api/v1")

api_router.include_router(parser.router, tags=["parsers"])
