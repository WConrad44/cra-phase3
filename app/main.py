from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .config import MAX_BODY_BYTES
from .database import Base, engine
from .routes import health, test_controls, tickets

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="CRA Vulnerability Ticketing Service",
    version="0.3.0",
    description="Phase 3 implementation of the pod's common CRA vulnerability-reporting API.",
)


@app.middleware("http")
async def body_size_limit(request: Request, call_next):
    length = request.headers.get("content-length")
    if length is not None:
        try:
            if int(length) > MAX_BODY_BYTES:
                return JSONResponse(
                    status_code=413,
                    content={"title": "Request body too large", "status": 413},
                )
        except ValueError:
            pass
    return await call_next(request)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        loc = [str(x) for x in error.get("loc", []) if x != "body"]
        errors.append({"field": ".".join(loc) or "body", "message": error.get("msg", "invalid")})
    return JSONResponse(
        status_code=400,
        content={"title": "Invalid request", "status": 400, "errors": errors},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    titles = {
        400: "Invalid request",
        401: "Unauthorized",
        404: "Not found",
        405: "Method not allowed",
        409: "State conflict",
        413: "Request body too large",
        422: "Rule violation",
    }
    return JSONResponse(
        status_code=exc.status_code,
        content={"title": titles.get(exc.status_code, "Request failed"), "status": exc.status_code, "detail": str(exc.detail)},
    )


app.include_router(health.router)
app.include_router(tickets.router)
app.include_router(test_controls.router)
