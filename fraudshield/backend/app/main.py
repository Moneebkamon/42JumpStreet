from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.errors import Conflict, InvalidTransition, NotFound, RateLimited

app = FastAPI(title="FraudShield API", version="0.1.0")
app.include_router(api_router, prefix="/api/v1")


@app.exception_handler(NotFound)
async def _not_found(_: Request, exc: NotFound) -> JSONResponse:
    return JSONResponse({"detail": str(exc)}, status_code=404)


@app.exception_handler(Conflict)
async def _conflict(_: Request, exc: Conflict) -> JSONResponse:
    return JSONResponse({"detail": str(exc), "ref": exc.ref}, status_code=409)


@app.exception_handler(InvalidTransition)
async def _bad_transition(_: Request, exc: InvalidTransition) -> JSONResponse:
    return JSONResponse({"detail": str(exc)}, status_code=409)


@app.exception_handler(RateLimited)
async def _limited(_: Request, exc: RateLimited) -> JSONResponse:
    return JSONResponse({"detail": str(exc)}, status_code=429)


@app.exception_handler(ValueError)
async def _bad_value(_: Request, exc: ValueError) -> JSONResponse:
    return JSONResponse({"detail": str(exc)}, status_code=422)
