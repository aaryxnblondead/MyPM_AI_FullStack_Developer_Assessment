from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.db_init import init_db
from app.routers.candidates import router as candidates_router
from app.routers.evaluations import router as evaluations_router
from app.routers.health import router as health_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


app = FastAPI(title="MyPM Fit Check API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(candidates_router)
app.include_router(evaluations_router)


@app.exception_handler(RequestValidationError)
async def validation_handler(_req: Request, exc: RequestValidationError) -> JSONResponse:
    safe = [{"loc": e.get("loc"), "msg": e.get("msg"), "type": e.get("type")} for e in exc.errors()]
    return JSONResponse(status_code=422, content={"detail": "Invalid input.", "errors": safe})


@app.exception_handler(HTTPException)
async def http_handler(_req: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(Exception)
async def unhandled_handler(_req: Request, _exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=500, content={"detail": "Something went wrong. Try again."})


@app.get("/", include_in_schema=False)
def root() -> dict[str, str]:
    return {"status": "ok"}
