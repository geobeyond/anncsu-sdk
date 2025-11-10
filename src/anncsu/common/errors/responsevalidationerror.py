"""Response validation error class for ANNCSU SDKs."""

import httpx
from typing import Optional

from anncsu.common.errors.base import AnncsuBaseError


class ResponseValidationError(AnncsuBaseError):
    """Error raised when there is a type mismatch between the response data and the expected Pydantic model."""

    def __init__(
        self,
        message: str,
        raw_response: httpx.Response,
        cause: Exception,
        body: Optional[str] = None,
    ):
        message = f"{message}: {cause}"
        super().__init__(message, raw_response, body)

    @property
    def cause(self):
        """Normally the Pydantic ValidationError"""
        return self.__cause__
