"""Content-feature exception definitions."""


class AIMaticError(Exception):
    """Base exception for AI Matic application errors."""

    error_code: str = "aimatic_error"

    def __init__(self, message: str, *, error_code: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        if error_code:
            self.error_code = error_code


class ContentGenerationError(AIMaticError):
    """Raised when content generation fails at the business layer."""

    error_code = "content_generation_error"


class ValidationError(AIMaticError):
    """Raised when input validation fails at the service layer."""

    error_code = "validation_error"


class ProviderNotFoundError(AIMaticError):
    """Raised when a configured provider is not registered in the factory."""

    error_code = "provider_not_found"


class ProviderAPIError(AIMaticError):
    """Raised when an external provider API call fails."""

    error_code = "provider_api_error"
