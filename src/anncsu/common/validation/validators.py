"""Custom validators for ANNCSU-specific business rules."""

import base64
import re
from typing import Any


def base64_validator(v: Any) -> str:
    """
    Validate that a string is valid base64 encoded.

    Args:
        v: Value to validate

    Returns:
        The validated string

    Raises:
        ValueError: If the string is not valid base64
    """
    if not isinstance(v, str):
        raise ValueError("Value must be a string")

    try:
        # Validate base64 encoding
        base64.b64decode(v, validate=True)
        return v
    except Exception as e:
        raise ValueError(f"Invalid base64 encoding: {e}") from e


def belfiore_code_validator(v: Any) -> str:
    """
    Validate Italian Belfiore municipality code format.

    Format: One uppercase letter followed by 3 digits (e.g., H501 for Rome)

    Args:
        v: Value to validate

    Returns:
        The validated string

    Raises:
        ValueError: If the code doesn't match Belfiore format
    """
    if not isinstance(v, str):
        raise ValueError("Belfiore code must be a string")

    pattern = r"^[A-Z]\d{3}$"
    if not re.match(pattern, v):
        raise ValueError(
            f"Invalid Belfiore code format: '{v}'. "
            "Expected format: one uppercase letter followed by 3 digits (e.g., H501)"
        )

    return v
