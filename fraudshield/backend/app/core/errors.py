"""Domain errors raised by services; main.py turns them into HTTP responses."""


class NotFound(LookupError):
    """The thing asked for does not exist."""


class Conflict(ValueError):
    """The request is valid but clashes with current state (e.g. a case for that domain is already open)."""

    def __init__(self, message: str, ref: str | None = None):
        super().__init__(message)
        self.ref = ref


class InvalidTransition(ValueError):
    """A case status change that the workflow does not allow."""


class RateLimited(Exception):
    """Too many requests from one client."""
