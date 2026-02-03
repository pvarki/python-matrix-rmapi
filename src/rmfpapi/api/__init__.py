"""Api endpoints"""

from fastapi.routing import APIRouter

from .usercrud import router as usercrud_router
from .clientinfo import router as clientinfo_router
from .admininfo import router as admininfo_router
from .healthcheck import router as healthcheck_router
from .description import router as description_router
from .instructions import router as instructions_router

from .description import router_v2 as description_router_v2
from .userinfo import router as userinfo_router


all_routers = APIRouter()
all_routers.include_router(usercrud_router, prefix="/users", tags=["users"])
all_routers.include_router(clientinfo_router, prefix="/clients", tags=["clients"])
all_routers.include_router(admininfo_router, prefix="/admins", tags=["admins"])
all_routers.include_router(healthcheck_router, prefix="/healthcheck", tags=["healthcheck"])
all_routers.include_router(description_router, prefix="/description", tags=["description"])
all_routers.include_router(instructions_router, prefix="/instructions", tags=["instructions"])

all_routers_v2 = APIRouter()
all_routers_v2.include_router(description_router_v2, prefix="/description", tags=["description"])
all_routers_v2.include_router(userinfo_router, prefix="/clients", tags=["clients"])
