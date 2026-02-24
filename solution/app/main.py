import uuid
import sys
import asyncio
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException

from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from redis import asyncio as aioredis

from app.api.health import router as health_router

from app.api.auth.routers.register import router as auth_router
from app.api.auth.routers.login import router as login_router

from app.api.flags.routers.create_flag import router as create_flag_router
from app.api.flags.routers.list_flags import router as list_flags_router
from app.api.flags.routers.get_flag_by_id import router as get_flag_by_id_router

from app.api.users.routers.update_user import router as update_user_router
from app.api.users.routers.get_me import router as get_me_router
from app.api.users.routers.update_me import router as update_me_router
from app.api.users.routers.delete_user import router as delete_user_router
from app.api.users.routers.list_users import router as list_users_router
from app.api.users.routers.update_password import router as update_password_router
from app.api.users.routers.threshold import router as threshold_router
from app.api.users.routers.approvers import router as approvers_router

from app.api.decide.routers.decide_flags import router as decide_flags_router

from app.api.experiments.routers.create_exp import router as create_exp_router
from app.api.experiments.routers.delete_exp import router as delete_exp_router
from app.api.experiments.routers.get_exp import router as get_exp_router
from app.api.experiments.routers.status_exp import router as status_exp_router
from app.api.experiments.routers.update_exp import router as update_exp_router

from app.api.analytics.router.tracking import router as tracking_router
from app.api.analytics.router.reports import router as reports_router

from app.api.guardrails.routers.create import router as create_guardrale_router
from app.api.guardrails.routers.delete import router as delete_guardrale_router
from app.api.guardrails.routers.get import router as get_guardrale_router
from app.api.guardrails.routers.list import router as list_guardrale_router
from app.api.guardrails.routers.update import router as update_guardrale_router

from app.utils.error_handlers import validation_exception_handler, http_exception_handler
from app.database.init import init_db


if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await init_db()
    except Exception as e:
        print(f"Database initialization error: {e}")
    
    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = os.getenv("REDIS_PORT", "6379")
    redis_url = f"redis://{redis_host}:{redis_port}"
    
    redis = None
    try:
        redis = aioredis.from_url(redis_url, encoding="utf8", decode_responses=True)
        FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")
        print(f"Redis initialized successfully at {redis_url}!")
    except Exception as e:
        print(f"Redis initialization error: {e}")

    yield

    if redis:
        await redis.close()


app = FastAPI(lifespan=lifespan)


@app.middleware("http")
async def add_trace_id(request, call_next):
    trace_id = request.headers.get("X-Trace-Id") or str(uuid.uuid4())
    request.state.traceId = trace_id
    
    response = await call_next(request)
    response.headers["X-Trace-Id"] = trace_id
    return response


app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)

app.include_router(health_router, prefix="/api")

app.include_router(auth_router, prefix="/api")
app.include_router(login_router, prefix="/api")

app.include_router(create_flag_router, prefix="/api/flags")
app.include_router(list_flags_router, prefix="/api/flags")
app.include_router(get_flag_by_id_router, prefix="/api/flags")

app.include_router(update_user_router, prefix="/api/user")
app.include_router(update_me_router, prefix="/api/user")
app.include_router(list_users_router, prefix="/api/user")
app.include_router(get_me_router, prefix="/api/user")
app.include_router(delete_user_router, prefix="/api/user")
app.include_router(update_password_router, prefix="/api/user")
app.include_router(threshold_router, prefix="/api/user")
app.include_router(approvers_router, prefix="/api/user")

app.include_router(decide_flags_router, prefix="/api")

app.include_router(create_exp_router, prefix="/api/experiment")
app.include_router(get_exp_router, prefix="/api/experiment")
app.include_router(delete_exp_router, prefix="/api/experiment")
app.include_router(status_exp_router, prefix="/api/experiment")
app.include_router(update_exp_router, prefix="/api/experiment")

app.include_router(tracking_router, prefix="/api")
app.include_router(reports_router, prefix="/api")

app.include_router(create_guardrale_router, prefix="/api")
app.include_router(delete_guardrale_router, prefix="/api")
app.include_router(get_guardrale_router, prefix="/api")
app.include_router(list_guardrale_router, prefix="/api")
app.include_router(update_guardrale_router, prefix="/api")