"""Custom exception classes for domain errors.

Services raise these exceptions. Routers catch them via the global
exception handler registered in main.py.
"""


class AppError(Exception):
    """Base application error.

    Attributes:
        message: Human-readable error message.
        code: Machine-readable error code.
        status_code: Suggested HTTP status code (used by the handler).
    """

    def __init__(
        self,
        message: str = "An unexpected error occurred",
        code: str = "INTERNAL_ERROR",
        status_code: int = 500,
    ) -> None:
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(AppError):
    """Resource not found."""

    def __init__(self, resource: str = "Resource", identifier: str = "") -> None:
        detail = f"{resource} not found" if not identifier else f"{resource} '{identifier}' not found"
        super().__init__(message=detail, code=f"{resource.upper()}_NOT_FOUND", status_code=404)


class DuplicateError(AppError):
    """Duplicate resource conflict."""

    def __init__(self, resource: str = "Resource", field: str = "") -> None:
        detail = f"{resource} already exists" if not field else f"{resource} with this {field} already exists"
        super().__init__(message=detail, code=f"DUPLICATE_{resource.upper()}", status_code=409)


class ValidationError(AppError):
    """Business logic validation failed."""

    def __init__(self, message: str = "Validation failed") -> None:
        super().__init__(message=message, code="VALIDATION_ERROR", status_code=400)


class AuthenticationError(AppError):
    """Authentication failed."""

    def __init__(self, message: str = "Invalid credentials") -> None:
        super().__init__(message=message, code="AUTHENTICATION_FAILED", status_code=401)


class AuthorizationError(AppError):
    """Insufficient permissions."""

    def __init__(self, message: str = "Not authorized") -> None:
        super().__init__(message=message, code="FORBIDDEN", status_code=403)
