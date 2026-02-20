import contextlib

import fastapi
import starlette.middleware.cors

from api.v1 import routers
from common import conf as core_conf


@contextlib.asynccontextmanager
async def lifespan(app: fastapi.FastAPI):
    yield


app = fastapi.FastAPI(lifespan=lifespan)
app.add_middleware(
    starlette.middleware.cors.CORSMiddleware,
    allow_origins=core_conf.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routers.api_router)
