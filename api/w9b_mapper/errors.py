"""Vendored from Module 9 Week B. DO NOT MODIFY."""


class UnsupportedQueryError(ValueError):
    """Raised by the W9B mapper when no supported pattern matches.

    The path operation converts this to HTTP 422 with structured detail.
    """
