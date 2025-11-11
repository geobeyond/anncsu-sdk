"""
Example models demonstrating Phase 1 validation with Pydantic Field constraints.

These examples show how to enhance generated models with validation rules.
In practice, these constraints should be added to the actual generated models
in anncsu.pa.models or incorporated into the Speakeasy generation templates.
"""

from pydantic import Field, field_validator
from typing_extensions import Annotated

from anncsu.common.types import BaseModel
from anncsu.common.utils import FieldMetadata, QueryParamMetadata
from anncsu.common.validation.validators import (
    base64_validator,
    belfiore_code_validator,
)


class EsisteOdonimoGetQueryParamRequestValidated(BaseModel):
    """
    Enhanced version of EsisteOdonimoGetQueryParamRequest with validation.

    This demonstrates Phase 1 validation - adding Pydantic Field constraints
    and custom validators to ensure data quality at the input level.
    """

    codcom: Annotated[
        str,
        Field(
            min_length=4,
            max_length=4,
            pattern=r"^[A-Z]\d{3}$",
            description="Codice Belfiore del comune dell'odonimo",
            examples=["H501"],  # Rome
        ),
        FieldMetadata(query=QueryParamMetadata(style="form", explode=True)),
    ]
    r"""
    Codice Belfiore del comune dell'odonimo.

    Format: One uppercase letter followed by 3 digits (e.g., H501 for Rome).
    """

    denom: Annotated[
        str,
        Field(
            min_length=1,
            description="Denominazione esatta dell'odonimo - base64 encoded",
            examples=["VklBIFJPTUE="],  # "VIA ROMA" in base64
        ),
        FieldMetadata(query=QueryParamMetadata(style="form", explode=True)),
    ]
    r"""
    Denominazione esatta dell'odonimo - base64 encoded.

    Must be a valid base64 encoded string.
    """

    # Custom validators for business logic
    @field_validator("codcom")
    @classmethod
    def validate_belfiore_code(cls, v: str) -> str:
        """Validate Belfiore code format using custom validator."""
        return belfiore_code_validator(v)

    @field_validator("denom")
    @classmethod
    def validate_base64_encoding(cls, v: str) -> str:
        """Validate base64 encoding using custom validator."""
        return base64_validator(v)


# Example demonstrating strict mode configuration
class StrictValidatedModel(BaseModel):
    """
    Example model with strict validation enabled.

    Strict mode ensures:
    - No type coercion (e.g., "123" won't be converted to int 123)
    - Extra fields are forbidden
    - Assignment validation is enabled
    """

    model_config = {
        "strict": True,  # Strict type checking
        "extra": "forbid",  # No extra fields allowed
        "validate_assignment": True,  # Validate on attribute assignment
        "str_strip_whitespace": True,  # Clean string inputs
    }

    required_string: Annotated[
        str,
        Field(min_length=1, max_length=100, description="A required string field"),
    ]

    optional_int: Annotated[
        int | None,
        Field(ge=0, le=1000, description="An optional integer with range"),
    ] = None
