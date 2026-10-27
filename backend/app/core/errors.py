"""Stable public errors with no request values, exception text, or secrets."""
from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import IntegrityError, OperationalError
from app.domain.responses import ErrorResponse


class ApiError(HTTPException):
    def __init__(self, status_code: int, code: str, detail: str):
        super().__init__(status_code, detail)
        self.code = code


def error_response(request: Request, status: int, code: str, detail: str, issues=None):
    request_id = getattr(request.state, "request_id", "unassigned")
    body = ErrorResponse(code=code, detail=detail, request_id=request_id, issues=issues or [])
    return JSONResponse(body.model_dump(mode="json"), status_code=status,
                        headers={"X-Request-ID": request_id, "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"})


def install_handlers(app):
    @app.exception_handler(StarletteHTTPException)
    async def http_error(request, exc):
        codes = {400: "BAD_REQUEST", 401: "AUTHENTICATION_REQUIRED", 403: "ACCESS_DENIED", 404: "NOT_FOUND", 405: "METHOD_NOT_ALLOWED", 409: "STATE_CONFLICT", 422: "VALIDATION_ERROR", 429: "LIMIT_EXCEEDED", 503: "SERVICE_UNAVAILABLE"}
        return error_response(request, exc.status_code, getattr(exc, "code", codes.get(exc.status_code, "REQUEST_FAILED")), str(exc.detail))

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, exc):
        # Pydantic's default errors can contain the rejected password/input itself.
        issues = [{"location": list(e["loc"]), "code": e["type"]} for e in exc.errors()]
        return error_response(request, 422, "VALIDATION_ERROR", "Please check the form values.", issues)

    @app.exception_handler(ResponseValidationError)
    async def response_error(request, exc):
        return error_response(request, 500, "RESPONSE_CONTRACT_ERROR", "The server could not produce a valid response.")

    @app.exception_handler(IntegrityError)
    async def integrity_error(request, exc):
        return error_response(request, 409, "CONCURRENT_CHANGE", "The record changed concurrently. Refresh and try again.")

    @app.exception_handler(OperationalError)
    async def database_error(request, exc):
        return error_response(request, 503, "DATABASE_UNAVAILABLE", "The database is temporarily unavailable. Try again.")

    @app.exception_handler(Exception)
    async def unexpected_error(request, exc):
        return error_response(request, 500, "INTERNAL_ERROR", "The server could not complete this request.")
