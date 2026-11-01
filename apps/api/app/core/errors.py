from typing import Any

from fastapi import Request, Response
from fastapi.responses import JSONResponse


def _default_title_for_status(status_code: int) -> str:
    titles = {
        400: "Bad Request",
        401: "Unauthorized",
        403: "Forbidden",
        404: "Not Found",
        409: "Conflict",
        422: "Unprocessable Entity",
        429: "Too Many Requests",
        500: "Internal Server Error",
    }
    return titles.get(status_code, "Error")


class AppException(Exception):
    """Base application exception following RFC 7807 problem details."""

    def __init__(
        self,
        status_code: int,
        code: str,
        detail: str,
        title: str | None = None,
        headers: dict[str, str] | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        self.status_code = status_code
        self.code = code
        self.detail = detail
        self.title = title or _default_title_for_status(status_code)
        self.headers = headers
        self.extra = extra or {}
        super().__init__(detail)


def unauthorized(
    code: str = "UNAUTHORIZED",
    detail: str = "Authentication required",
    headers: dict[str, str] | None = None,
) -> AppException:
    auth_headers = {"WWW-Authenticate": "Bearer"}
    if headers:
        auth_headers.update(headers)
    return AppException(
        status_code=401,
        code=code,
        detail=detail,
        title="Unauthorized",
        headers=auth_headers,
    )


def forbidden(code: str = "FORBIDDEN", detail: str = "Access forbidden") -> AppException:
    return AppException(status_code=403, code=code, detail=detail, title="Forbidden")


def not_found(code: str = "NOT_FOUND", detail: str = "Resource not found") -> AppException:
    return AppException(status_code=404, code=code, detail=detail, title="Not Found")


def bad_request(code: str = "BAD_REQUEST", detail: str = "Invalid request") -> AppException:
    return AppException(status_code=400, code=code, detail=detail, title="Bad Request")


def too_many_requests(
    code: str = "RATE_LIMIT_EXCEEDED",
    detail: str = "Rate limit exceeded. Please wait before retrying.",
) -> AppException:
    return AppException(status_code=429, code=code, detail=detail, title="Too Many Requests")



async def app_exception_handler(request: Request, exc: Exception) -> Response:
    if isinstance(exc, AppException):
        content: dict[str, Any] = {
            "type": "about:blank",
            "title": exc.title,
            "status": exc.status_code,
            "detail": exc.detail,
            "code": exc.code,
        }
        if exc.extra:
            content.update(exc.extra)
        return JSONResponse(
            status_code=exc.status_code,
            content=content,
            headers=exc.headers,
        )

    return JSONResponse(
        status_code=500,
        content={
            "type": "about:blank",
            "title": "Internal Server Error",
            "status": 500,
            "detail": "An unexpected error occurred",
            "code": "INTERNAL_SERVER_ERROR",
        },
    )
