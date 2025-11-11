"""Security configuration for ANNCSU APIs.

This module provides the Security class that handles authentication
across all ANNCSU API specifications using PDND Voucher tokens.
"""

from dataclasses import dataclass


@dataclass
class Security:
    """Security configuration for ANNCSU API authentication.

    All ANNCSU APIs use PDND (Piattaforma Digitale Nazionale Dati) voucher-based
    authentication with HTTP Bearer tokens.

    Attributes:
        bearer: PDND voucher token for Bearer authentication.
                This token is included in the Authorization header as "Bearer <token>".

    Example:
        >>> security = Security(bearer="your-pdnd-voucher-token")
        >>> # Token will be used in Authorization: Bearer your-pdnd-voucher-token
    """

    bearer: str | None = None
