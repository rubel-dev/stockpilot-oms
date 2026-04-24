from typing import Any


class AppError(Exception):
    def __init__(
        self,
        *,
        code: str,
        message: str,
        status_code: int,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}


class AuthenticationError(AppError):
    def __init__(self, message: str = "Authentication required.") -> None:
        super().__init__(
            code="AUTHENTICATION_REQUIRED",
            message=message,
            status_code=401,
        )


class PermissionDeniedError(AppError):
    def __init__(self, message: str = "You do not have access to this resource.") -> None:
        super().__init__(
            code="PERMISSION_DENIED",
            message=message,
            status_code=403,
        )


class NotFoundError(AppError):
    def __init__(self, message: str = "Resource not found.") -> None:
        super().__init__(code="NOT_FOUND", message=message, status_code=404)


class ConflictError(AppError):
    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(code="CONFLICT", message=message, status_code=409, details=details)


class ValidationAppError(AppError):
    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            code="VALIDATION_ERROR",
            message=message,
            status_code=422,
            details=details,
        )


class InsufficientStockError(AppError):
    def __init__(self, message: str = "Not enough available stock for this operation.") -> None:
        super().__init__(
            code="INSUFFICIENT_STOCK",
            message=message,
            status_code=409,
        )


class InvalidOrderTransitionError(AppError):
    def __init__(self, message: str = "Invalid order status transition.") -> None:
        super().__init__(
            code="INVALID_ORDER_TRANSITION",
            message=message,
            status_code=409,
        )
