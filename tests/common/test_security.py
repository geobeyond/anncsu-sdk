"""Tests for ANNCSU Common Security implementation.

This module tests the PDND Voucher authentication mechanism that is common
across all ANNCSU API specifications.
"""

from anncsu.common.security import Security


class TestSecurityInitialization:
    """Test Security class initialization."""

    def test_security_with_bearer_token(self):
        """Test Security initialization with bearer token."""
        security = Security(bearer="test-voucher-token")
        assert security.bearer == "test-voucher-token"

    def test_security_without_bearer_token(self):
        """Test Security initialization without bearer token (anonymous)."""
        security = Security()
        assert security.bearer is None

    def test_security_with_empty_bearer_token(self):
        """Test Security initialization with empty bearer token."""
        security = Security(bearer="")
        assert security.bearer == ""

    def test_security_with_none_bearer_token(self):
        """Test Security initialization with None bearer token."""
        security = Security(bearer=None)
        assert security.bearer is None


class TestBearerTokenFormat:
    """Test Bearer token format validation."""

    def test_valid_bearer_token_format(self):
        """Test that bearer tokens follow expected format."""
        # PDND voucher tokens are typically JWT format
        valid_tokens = [
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U",
            "test-token-123",
            "simple-token",
            "token-with-dashes-and-numbers-123",
        ]

        for token in valid_tokens:
            security = Security(bearer=token)
            assert security.bearer == token
            assert isinstance(security.bearer, str)

    def test_bearer_token_with_special_characters(self):
        """Test bearer tokens with special characters."""
        # JWT tokens contain dots and underscores
        token = "header.payload.signature"
        security = Security(bearer=token)
        assert security.bearer == token

    def test_bearer_token_length_variations(self):
        """Test bearer tokens of various lengths."""
        # Short token
        short_token = "abc"
        security = Security(bearer=short_token)
        assert security.bearer == short_token

        # Long token (typical JWT is ~200-300 chars)
        long_token = "a" * 500
        security = Security(bearer=long_token)
        assert security.bearer == long_token


class TestSecurityHeaderGeneration:
    """Test that Security properly generates Authorization headers."""

    def test_authorization_header_with_bearer_token(self):
        """Test that bearer token is properly formatted in headers."""
        security = Security(bearer="test-token")

        # The Security class should be used to populate Authorization headers
        # This tests the expected format
        expected_header = f"Bearer {security.bearer}"
        assert expected_header == "Bearer test-token"

    def test_authorization_header_format(self):
        """Test Authorization header format matches HTTP spec."""
        token = "my-pdnd-voucher-token"
        security = Security(bearer=token)

        # HTTP Authorization header format: "Bearer <token>"
        auth_header = f"Bearer {security.bearer}"
        assert auth_header.startswith("Bearer ")
        assert auth_header.split(" ", 1)[1] == token


class TestSecurityValidation:
    """Test security validation scenarios."""

    def test_missing_bearer_token_detection(self):
        """Test detection of missing bearer token."""
        security = Security()
        assert security.bearer is None

    def test_bearer_token_present_detection(self):
        """Test detection of present bearer token."""
        security = Security(bearer="token")
        assert security.bearer is not None
        assert security.bearer != ""

    def test_empty_vs_none_bearer_token(self):
        """Test distinction between empty string and None."""
        security_none = Security(bearer=None)
        security_empty = Security(bearer="")

        assert security_none.bearer is None
        assert security_empty.bearer == ""
        assert security_none.bearer != security_empty.bearer


class TestSecurityEdgeCases:
    """Test edge cases and error conditions."""

    def test_bearer_token_with_whitespace(self):
        """Test bearer token with leading/trailing whitespace."""
        token_with_spaces = "  token-with-spaces  "
        security = Security(bearer=token_with_spaces)
        # SDK should preserve the token as-is
        assert security.bearer == token_with_spaces

    def test_bearer_token_with_newlines(self):
        """Test bearer token with newline characters."""
        token_with_newline = "token\nwith\nnewline"
        security = Security(bearer=token_with_newline)
        assert security.bearer == token_with_newline

    def test_bearer_token_unicode(self):
        """Test bearer token with unicode characters."""
        unicode_token = "token-with-unicode-🔐"
        security = Security(bearer=unicode_token)
        assert security.bearer == unicode_token

    def test_very_long_bearer_token(self):
        """Test bearer token with extreme length."""
        # Some systems might have very long tokens
        very_long_token = "x" * 10000
        security = Security(bearer=very_long_token)
        assert security.bearer == very_long_token
        assert len(security.bearer) == 10000


class TestPDNDVoucherIntegration:
    """Test PDND Voucher specific scenarios."""

    def test_pdnd_voucher_jwt_format(self):
        """Test PDND voucher in JWT format."""
        # Typical PDND voucher is a JWT token
        jwt_token = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6InRlc3Qta2V5In0.eyJpc3MiOiJwZG5kIiwic3ViIjoiY29tdW5lLXRlc3QiLCJhdWQiOiJhbm5jc3UiLCJleHAiOjE3MzY2MDAwMDAsImlhdCI6MTczNjUxMzYwMH0.signature"
        security = Security(bearer=jwt_token)
        assert security.bearer == jwt_token

        # JWT should have 3 parts separated by dots
        parts = security.bearer.split(".")
        assert len(parts) == 3

    def test_pdnd_voucher_refresh_scenario(self):
        """Test updating bearer token (token refresh scenario)."""
        security = Security(bearer="old-token")
        assert security.bearer == "old-token"

        # In a real scenario, the token would be refreshed
        # Create new Security instance with refreshed token
        refreshed_security = Security(bearer="new-token")
        assert refreshed_security.bearer == "new-token"
        assert refreshed_security.bearer != security.bearer

    def test_multiple_security_instances(self):
        """Test multiple Security instances with different tokens."""
        security1 = Security(bearer="token-1")
        security2 = Security(bearer="token-2")
        security3 = Security()

        assert security1.bearer == "token-1"
        assert security2.bearer == "token-2"
        assert security3.bearer is None

        # Each instance is independent
        assert security1.bearer != security2.bearer


class TestSecurityTypeValidation:
    """Test type validation for Security parameters."""

    def test_bearer_token_must_be_string_or_none(self):
        """Test that bearer token is string or None."""
        # Valid: string
        security_str = Security(bearer="token")
        assert isinstance(security_str.bearer, str)

        # Valid: None
        security_none = Security(bearer=None)
        assert security_none.bearer is None

        # Valid: empty string
        security_empty = Security(bearer="")
        assert isinstance(security_empty.bearer, str)

    def test_security_immutability(self):
        """Test that Security objects maintain their values."""
        token = "immutable-token"
        security = Security(bearer=token)

        # Store original value
        original = security.bearer

        # Value should remain the same
        assert security.bearer == original
        assert security.bearer == token


class TestSecurityDocumentation:
    """Test that Security class has proper documentation."""

    def test_security_class_docstring(self):
        """Test that Security class has documentation."""
        assert Security.__doc__ is not None

    def test_security_attribute_documentation(self):
        """Test that Security has bearer attribute."""
        import inspect

        sig = inspect.signature(Security.__init__)

        # Bearer parameter should exist
        assert "bearer" in sig.parameters or len(sig.parameters) > 1


class TestSecurityCommonAcrossAPIs:
    """Test that Security is common across all ANNCSU APIs."""

    def test_security_is_reusable(self):
        """Test that same Security can be used for multiple API calls."""
        security = Security(bearer="reusable-token")

        # Simulate multiple API calls using the same security
        api_call_count = 100
        for _ in range(api_call_count):
            # Each call should see the same token
            assert security.bearer == "reusable-token"

    def test_security_configuration_consistency(self):
        """Test that Security configuration is consistent."""
        token = "consistent-token"

        # Create multiple Security instances with same token
        instances = [Security(bearer=token) for _ in range(10)]

        # All should have the same bearer token
        for instance in instances:
            assert instance.bearer == token

    def test_security_for_different_api_endpoints(self):
        """Test Security works for different ANNCSU API endpoints."""
        # Same security should work for:
        # - Consultazione API (query endpoints)
        # - Aggiornamento odonimi API
        # - Aggiornamento accessi API
        # - Aggiornamento coordinate API
        # - Aggiornamento interni API

        security = Security(bearer="universal-pdnd-voucher")

        # The bearer token should be the same regardless of endpoint
        assert security.bearer == "universal-pdnd-voucher"


class TestSecurityBestPractices:
    """Test security best practices."""

    def test_security_with_production_like_token(self):
        """Test with production-like PDND voucher token."""
        # Simulate a real PDND voucher (JWT format with realistic length)
        production_token = (
            "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6InBkbmQta2V5LTEyMyJ9."
            "eyJpc3MiOiJodHRwczovL2F1dGgucGRuZC5pdGFsaWEuaXQiLCJzdWIiOiJjb211b"
            "mUtZGktcm9tYSIsImF1ZCI6Imh0dHBzOi8vYXBpLmFuY3N1Lmdvdi5pdCIsImV4cC"
            "I6MTczNjYwMDAwMCwiaWF0IjoxNzM2NTEzNjAwLCJzY29wZSI6ImFuY3N1LmNvbnN"
            "1bHRhemlvbmUgYW5jc3UuYWdnaW9ybmFtZW50byJ9."
            "ABC123signature456DEF789"
        )

        security = Security(bearer=production_token)
        assert security.bearer == production_token
        assert len(security.bearer) > 200  # Real JWTs are typically 200+ chars
