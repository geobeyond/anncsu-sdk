"""Test imports for anncsu.common package.

This test suite verifies that all modules in the anncsu.common package
can be imported successfully after the refactoring that extracted shared
primitives from anncsu.pa.
"""

import pytest


class TestCommonPackageImports:
    """Test that the anncsu.common package structure is correct."""

    def test_import_common_package(self):
        """Test that anncsu.common package can be imported."""
        import anncsu.common

        assert anncsu.common is not None

    def test_common_package_has_path(self):
        """Test that anncsu.common has a __path__ attribute."""
        import anncsu.common

        assert hasattr(anncsu.common, "__path__")


class TestCommonTypesImports:
    """Test imports from anncsu.common.types module."""

    def test_import_types_module(self):
        """Test that anncsu.common.types can be imported."""
        import anncsu.common.types

        assert anncsu.common.types is not None

    def test_import_basemodel(self):
        """Test that BaseModel can be imported."""
        from anncsu.common.types import BaseModel

        assert BaseModel is not None

    def test_import_nullable(self):
        """Test that Nullable can be imported."""
        from anncsu.common.types import Nullable

        assert Nullable is not None

    def test_import_optional_nullable(self):
        """Test that OptionalNullable can be imported."""
        from anncsu.common.types import OptionalNullable

        assert OptionalNullable is not None

    def test_import_unset(self):
        """Test that UNSET can be imported."""
        from anncsu.common.types import UNSET

        assert UNSET is not None

    def test_import_unset_sentinel(self):
        """Test that UNSET_SENTINEL can be imported."""
        from anncsu.common.types import UNSET_SENTINEL

        assert UNSET_SENTINEL is not None

    def test_import_unrecognized_types(self):
        """Test that UnrecognizedInt and UnrecognizedStr can be imported."""
        from anncsu.common.types import UnrecognizedInt, UnrecognizedStr

        assert UnrecognizedInt is not None
        assert UnrecognizedStr is not None


class TestCommonUtilsImports:
    """Test imports from anncsu.common.utils module."""

    def test_import_utils_module(self):
        """Test that anncsu.common.utils can be imported."""
        import anncsu.common.utils

        assert anncsu.common.utils is not None

    def test_import_retry_config(self):
        """Test that RetryConfig can be imported."""
        from anncsu.common.utils import RetryConfig

        assert RetryConfig is not None

    def test_import_backoff_strategy(self):
        """Test that BackoffStrategy can be imported."""
        from anncsu.common.utils import BackoffStrategy

        assert BackoffStrategy is not None

    def test_import_serialized_request_body(self):
        """Test that SerializedRequestBody can be imported."""
        from anncsu.common.utils import SerializedRequestBody

        assert SerializedRequestBody is not None

    def test_import_field_metadata(self):
        """Test that FieldMetadata can be imported."""
        from anncsu.common.utils import FieldMetadata

        assert FieldMetadata is not None

    def test_import_query_param_metadata(self):
        """Test that QueryParamMetadata can be imported."""
        from anncsu.common.utils import QueryParamMetadata

        assert QueryParamMetadata is not None

    def test_import_path_param_metadata(self):
        """Test that PathParamMetadata can be imported."""
        from anncsu.common.utils import PathParamMetadata

        assert PathParamMetadata is not None

    def test_import_header_metadata(self):
        """Test that HeaderMetadata can be imported."""
        from anncsu.common.utils import HeaderMetadata

        assert HeaderMetadata is not None


class TestCommonErrorsImports:
    """Test imports from anncsu.common.errors module."""

    def test_import_errors_module(self):
        """Test that anncsu.common.errors can be imported."""
        import anncsu.common.errors

        assert anncsu.common.errors is not None

    def test_import_anncsu_base_error(self):
        """Test that AnncsuBaseError can be imported."""
        from anncsu.common.errors import AnncsuBaseError

        assert AnncsuBaseError is not None
        assert issubclass(AnncsuBaseError, Exception)

    def test_import_api_error(self):
        """Test that APIError can be imported."""
        from anncsu.common.errors import APIError

        assert APIError is not None

    def test_import_no_response_error(self):
        """Test that NoResponseError can be imported."""
        from anncsu.common.errors import NoResponseError

        assert NoResponseError is not None
        assert issubclass(NoResponseError, Exception)

    def test_import_response_validation_error(self):
        """Test that ResponseValidationError can be imported."""
        from anncsu.common.errors import ResponseValidationError

        assert ResponseValidationError is not None

    def test_api_error_inherits_from_base(self):
        """Test that APIError inherits from AnncsuBaseError."""
        from anncsu.common.errors import AnncsuBaseError, APIError

        assert issubclass(APIError, AnncsuBaseError)

    def test_response_validation_error_inherits_from_base(self):
        """Test that ResponseValidationError inherits from AnncsuBaseError."""
        from anncsu.common.errors import (
            AnncsuBaseError,
            ResponseValidationError,
        )

        assert issubclass(ResponseValidationError, AnncsuBaseError)


class TestCommonHooksImports:
    """Test imports from anncsu.common.hooks module."""

    def test_import_hooks_module(self):
        """Test that anncsu.common.hooks can be imported."""
        import anncsu.common.hooks

        assert anncsu.common.hooks is not None

    def test_import_sdk_hooks(self):
        """Test that SDKHooks can be imported."""
        from anncsu.common.hooks import SDKHooks

        assert SDKHooks is not None

    def test_import_hook_contexts(self):
        """Test that hook context classes can be imported."""
        from anncsu.common.hooks import (
            AfterErrorContext,
            AfterSuccessContext,
            BeforeRequestContext,
        )

        assert BeforeRequestContext is not None
        assert AfterSuccessContext is not None
        assert AfterErrorContext is not None


class TestCommonInfrastructureImports:
    """Test imports of infrastructure components."""

    def test_import_http_client(self):
        """Test that HTTPClient can be imported."""
        from anncsu.common.httpclient import HttpClient

        assert HttpClient is not None

    def test_import_async_http_client(self):
        """Test that AsyncHttpClient can be imported."""
        from anncsu.common.httpclient import AsyncHttpClient

        assert AsyncHttpClient is not None

    def test_import_base_sdk(self):
        """Test that BaseSDK can be imported."""
        from anncsu.common.basesdk import BaseSDK

        assert BaseSDK is not None

    def test_import_sdk_configuration(self):
        """Test that SDKConfiguration can be imported."""
        from anncsu.common.sdkconfiguration import SDKConfiguration

        assert SDKConfiguration is not None


class TestCommonUtilityModules:
    """Test that individual utility modules can be imported."""

    def test_import_annotations(self):
        """Test that annotations module can be imported."""
        from anncsu.common.utils import annotations

        assert annotations is not None

    def test_import_datetimes(self):
        """Test that datetimes module can be imported."""
        from anncsu.common.utils import datetimes

        assert datetimes is not None

    def test_import_enums(self):
        """Test that enums module can be imported."""
        from anncsu.common.utils import enums

        assert enums is not None

    def test_import_eventstreaming(self):
        """Test that eventstreaming module can be imported."""
        from anncsu.common.utils import eventstreaming

        assert eventstreaming is not None

    def test_import_forms(self):
        """Test that forms module can be imported."""
        from anncsu.common.utils import forms

        assert forms is not None

    def test_import_headers(self):
        """Test that headers module can be imported."""
        from anncsu.common.utils import headers

        assert headers is not None

    def test_import_logger(self):
        """Test that logger module can be imported."""
        from anncsu.common.utils import logger

        assert logger is not None

    def test_import_metadata(self):
        """Test that metadata module can be imported."""
        from anncsu.common.utils import metadata

        assert metadata is not None

    def test_import_queryparams(self):
        """Test that queryparams module can be imported."""
        from anncsu.common.utils import queryparams

        assert queryparams is not None

    def test_import_requestbodies(self):
        """Test that requestbodies module can be imported."""
        from anncsu.common.utils import requestbodies

        assert requestbodies is not None

    def test_import_retries(self):
        """Test that retries module can be imported."""
        from anncsu.common.utils import retries

        assert retries is not None

    def test_import_security(self):
        """Test that security module can be imported."""
        from anncsu.common.utils import security

        assert security is not None

    def test_import_serializers(self):
        """Test that serializers module can be imported."""
        from anncsu.common.utils import serializers

        assert serializers is not None

    def test_import_unmarshal_json_response(self):
        """Test that unmarshal_json_response module can be imported."""
        from anncsu.common.utils import unmarshal_json_response

        assert unmarshal_json_response is not None

    def test_import_url(self):
        """Test that url module can be imported."""
        from anncsu.common.utils import url

        assert url is not None

    def test_import_values(self):
        """Test that values module can be imported."""
        from anncsu.common.utils import values

        assert values is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
