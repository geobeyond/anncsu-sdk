"""Response validation against OpenAPI specifications."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import httpx


@dataclass
class ValidationConfig:
    """Configuration for response validation."""

    enabled: bool = False
    """Whether response validation is enabled"""

    openapi_spec_path: Optional[Path] = None
    """Path to the OpenAPI specification file"""

    strict: bool = True
    """Whether to raise exceptions on validation errors or just log warnings"""


class ResponseValidator:
    """
    Validates HTTP responses against OpenAPI specifications.

    This validator uses openapi-pydantic to parse OpenAPI specs and validate
    that API responses match the expected schema.

    Note: This validator requires openapi-pydantic and pyyaml to be installed.
    These are included in the dev dependencies but not in the main SDK.
    """

    def __init__(self, spec_path: Path):
        """
        Initialize the response validator.

        Args:
            spec_path: Path to the OpenAPI specification YAML file

        Raises:
            ImportError: If openapi-pydantic or pyyaml are not installed
            FileNotFoundError: If the spec file doesn't exist
        """
        try:
            import yaml  # noqa: F401
            from openapi_pydantic import OpenAPI  # noqa: F401
        except ImportError as e:
            raise ImportError(
                "Response validation requires openapi-pydantic and pyyaml. "
                "These are included in dev dependencies. "
                "Install with: uv sync --dev"
            ) from e

        if not spec_path.exists():
            raise FileNotFoundError(f"OpenAPI spec not found: {spec_path}")

        self.spec_path = spec_path
        self._load_spec()

    def _load_spec(self) -> None:
        """Load and parse the OpenAPI specification."""
        import yaml

        with open(self.spec_path) as f:
            spec_dict = yaml.safe_load(f)

        # Detect OpenAPI version and use appropriate parser
        openapi_version = spec_dict.get("openapi", "")

        try:
            if openapi_version.startswith("3.0"):
                from openapi_pydantic.v3.v3_0 import OpenAPI

                self.spec = OpenAPI.model_validate(spec_dict)
            elif openapi_version.startswith("3.1"):
                from openapi_pydantic.v3.v3_1 import OpenAPI

                self.spec = OpenAPI.model_validate(spec_dict)
            else:
                raise ValueError(
                    f"Unsupported OpenAPI version: {openapi_version}. "
                    f"Supported versions: 3.0.x, 3.1.x"
                )
        except Exception as e:
            raise ValueError(f"Invalid OpenAPI specification: {e}") from e

    def validate_response(
        self,
        response: httpx.Response,
        operation_id: str,
    ) -> tuple[bool, list[str]]:
        """
        Validate an HTTP response against the OpenAPI spec.

        Args:
            response: The HTTP response to validate
            operation_id: The OpenAPI operation ID (e.g., "esisteOdonimoGetQueryParam")

        Returns:
            Tuple of (is_valid, errors) where errors is a list of validation error messages
        """
        errors = []

        # Find the operation in the spec
        operation = self._find_operation(operation_id)
        if not operation:
            errors.append(f"Operation '{operation_id}' not found in OpenAPI spec")
            return False, errors

        # Get expected response schema for this status code
        status_code = str(response.status_code)
        if not operation.responses:
            errors.append(f"No responses defined for operation '{operation_id}'")
            return False, errors

        response_spec = operation.responses.get(status_code)
        if not response_spec:
            # Try default response
            response_spec = operation.responses.get("default")
            if not response_spec:
                errors.append(
                    f"No response schema defined for status code {status_code} "
                    f"in operation '{operation_id}'"
                )
                return False, errors

        # Validate response content type
        content_type = response.headers.get("content-type", "").split(";")[0].strip()

        if not response_spec.content:
            # Response should have no content
            if response.content:
                errors.append(
                    f"Response should have no content but got: {len(response.content)} bytes"
                )
                return False, errors
            return True, []

        # Check if content type is expected
        if content_type not in response_spec.content:
            expected_types = list(response_spec.content.keys())
            errors.append(
                f"Unexpected content type '{content_type}'. "
                f"Expected one of: {expected_types}"
            )
            return False, errors

        # Validate response body against schema
        try:
            response_data = response.json()
        except Exception as e:
            errors.append(f"Failed to parse response JSON: {e}")
            return False, errors

        # Get the schema for this content type
        media_type = response_spec.content[content_type]
        if not media_type.media_type_schema:
            # No schema defined, consider valid
            return True, []

        # Validate against schema
        # Note: openapi-pydantic parses the schema but doesn't validate data against it
        # For full validation, we'd need jsonschema or similar
        # For now, we do basic structure validation
        validation_errors = self._validate_against_schema(
            response_data, media_type.media_type_schema
        )

        if validation_errors:
            errors.extend(validation_errors)
            return False, errors

        return True, []

    def _find_operation(self, operation_id: str):
        """Find an operation in the spec by operation ID."""
        if not self.spec.paths:
            return None

        for path_item in self.spec.paths.values():
            for operation in [
                path_item.get,
                path_item.post,
                path_item.put,
                path_item.delete,
                path_item.patch,
            ]:
                if operation and operation.operationId == operation_id:
                    return operation

        return None

    def _validate_against_schema(self, data: Any, schema: Any) -> list[str]:
        """
        Basic validation of data against OpenAPI schema.

        This is a simplified validation. For production use, consider
        integrating jsonschema for complete validation.
        """
        errors = []

        # This is a placeholder for more comprehensive validation
        # In a full implementation, you'd use jsonschema here
        # For now, we just check basic type matching

        if not isinstance(data, dict):
            if hasattr(schema, "type") and schema.type != type(data).__name__:
                errors.append(
                    f"Type mismatch: expected {schema.type}, got {type(data).__name__}"
                )

        return errors
