"""
Create a client assertion JWT for PDND authentication.

This script generates a signed JWT client assertion required for PDND (Piattaforma Digitale Nazionale Dati)
authentication. The JWT is signed with an RSA private key and includes all required claims.

Usage:
    python create_client_assertion.py \
        --kid <key_id> \
        --alg RS256 \
        --typ JWT \
        --issuer <client_id> \
        --subject <client_id> \
        --audience <audience_url> \
        --purpose-id <purpose_id> \
        --key-path <path_to_private_key>

    Or using the modern CLI:

    python create_client_assertion.py create \
        --kid <key_id> \
        --issuer <client_id> \
        --subject <client_id> \
        --audience <audience_url> \
        --purpose-id <purpose_id> \
        --key-path <path_to_private_key>

Requirements:
    - Python 3.12+
    - authlib>=1.3.0
    - typer>=0.15.0
    - pydantic>=2.11.2
"""

import datetime
import os
import uuid
from pathlib import Path
from typing import Annotated

import typer
from authlib.jose import jwt
from pydantic import BaseModel, Field, field_validator
from rich.console import Console

# Initialize Typer app and Rich console
app = typer.Typer(
    help="Generate client assertion JWTs for PDND authentication",
    no_args_is_help=True,
)
console = Console()


class JWTConfig(BaseModel):
    """Configuration for JWT client assertion generation with validation."""

    kid: Annotated[
        str,
        Field(
            description="Key ID (kid) header parameter - identifies which key was used",
            min_length=1,
        ),
    ]
    alg: Annotated[
        str,
        Field(
            description="Algorithm for signing the JWT",
            pattern="^RS256$",
        ),
    ] = "RS256"
    typ: Annotated[
        str,
        Field(
            description="Token type",
            pattern="^JWT$",
        ),
    ] = "JWT"
    issuer: Annotated[
        str,
        Field(
            description="Issuer (iss) - typically your client_id from PDND",
            min_length=1,
        ),
    ]
    subject: Annotated[
        str,
        Field(
            description="Subject (sub) - typically your client_id from PDND",
            min_length=1,
        ),
    ]
    audience: Annotated[
        str,
        Field(
            description="Audience (aud) - the PDND token endpoint URL",
            pattern="^https://.*",
        ),
    ]
    purpose_id: Annotated[
        str,
        Field(
            description="Purpose ID for the PDND request",
            min_length=1,
        ),
    ]
    key_path: Annotated[
        Path,
        Field(description="Path to the RSA private key file (PEM format)"),
    ]
    validity_minutes: Annotated[
        int,
        Field(
            description="JWT validity period in minutes",
            gt=0,
            le=43200,  # Max 30 days
        ),
    ] = 43200

    @field_validator("key_path")
    @classmethod
    def validate_key_path(cls, v: Path) -> Path:
        """Validate that the key file exists and is readable."""
        if not v.exists():
            raise ValueError(f"Key file not found: {v}")
        if not v.is_file():
            raise ValueError(f"Key path is not a file: {v}")
        return v

    @field_validator("audience")
    @classmethod
    def validate_audience(cls, v: str) -> str:
        """Validate audience URL format."""
        if not v.startswith("https://"):
            raise ValueError("Audience must be an HTTPS URL")
        return v


def read_private_key(key_path: Path) -> bytes:
    """
    Read the RSA private key from a file.

    Args:
        key_path: Path to the private key file (PEM format)

    Returns:
        bytes: The private key content

    Raises:
        FileNotFoundError: If the key file doesn't exist
        PermissionError: If the key file is not readable
    """
    try:
        return key_path.read_bytes()
    except FileNotFoundError:
        console.print(f"[red]Error: Key file not found: {key_path}[/red]")
        raise typer.Exit(code=1) from None
    except PermissionError:
        console.print(
            f"[red]Error: Permission denied reading key file: {key_path}[/red]"
        )
        raise typer.Exit(code=1) from None


def generate_jwt(config: JWTConfig) -> str:
    """
    Generate a JWT client assertion with the given configuration.

    Args:
        config: JWT configuration validated by Pydantic

    Returns:
        str: The generated JWT token

    Raises:
        Exception: If JWT generation fails
    """
    # Generate timestamps
    issued = datetime.datetime.now(datetime.UTC)
    delta = datetime.timedelta(minutes=config.validity_minutes)
    expire_in = issued + delta
    jti = uuid.uuid4()

    # JWT header
    header = {
        "kid": config.kid,
        "alg": config.alg,
        "typ": config.typ,
    }

    # JWT payload
    payload = {
        "iss": config.issuer,
        "sub": config.subject,
        "aud": config.audience,
        "purposeId": config.purpose_id,
        "jti": str(jti),
        "iat": int(issued.timestamp()),
        "exp": int(expire_in.timestamp()),
    }

    # Load the private key
    rsa_key = read_private_key(config.key_path)

    try:
        # Encode the JWT using authlib
        client_assertion = jwt.encode(header, payload, rsa_key)

        # authlib returns bytes, decode to string
        if isinstance(client_assertion, bytes):
            client_assertion = client_assertion.decode("utf-8")

        return client_assertion
    except Exception as e:
        console.print(f"[red]Error generating JWT: {e}[/red]")
        raise typer.Exit(code=1) from None


@app.command()
def create(
    kid: Annotated[
        str,
        typer.Option(
            "--kid",
            help="Key ID (kid) header parameter - identifies which key was used",
            show_default=False,
            metavar="KEY_ID",
            rich_help_panel="Required JWT Header Parameters",
        ),
    ],
    issuer: Annotated[
        str,
        typer.Option(
            "--issuer",
            help="Issuer (iss) - typically your client_id from PDND. Example: 'a1b2c3d4-e5f6-7890-abcd-ef1234567890'",
            show_default=False,
            metavar="CLIENT_ID",
            rich_help_panel="Required JWT Claims",
        ),
    ],
    subject: Annotated[
        str,
        typer.Option(
            "--subject",
            help="Subject (sub) - typically your client_id from PDND. Example: 'a1b2c3d4-e5f6-7890-abcd-ef1234567890'",
            show_default=False,
            metavar="CLIENT_ID",
            rich_help_panel="Required JWT Claims",
        ),
    ],
    audience: Annotated[
        str,
        typer.Option(
            "--audience",
            help="Audience (aud) - the PDND token endpoint URL. Example: 'https://auth.interop.pagopa.it/token.oauth2'",
            show_default=False,
            metavar="URL",
            rich_help_panel="Required JWT Claims",
        ),
    ],
    purpose_id: Annotated[
        str,
        typer.Option(
            "--purpose-id",
            help="Purpose ID for the PDND request. Example: '12345678-90ab-cdef-1234-567890abcdef'",
            show_default=False,
            metavar="PURPOSE_ID",
            rich_help_panel="Required JWT Claims",
        ),
    ],
    key_path: Annotated[
        Path,
        typer.Option(
            "--key-path",
            help="Path to the RSA private key file (PEM format). Example: './private_key.pem'",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            show_default=False,
            metavar="PATH",
            rich_help_panel="Required JWT Signing",
        ),
    ],
    alg: Annotated[
        str,
        typer.Option(
            "--alg",
            help="Algorithm for signing the JWT (only RS256 supported)",
            metavar="ALGORITHM",
            rich_help_panel="Optional JWT Parameters",
        ),
    ] = "RS256",
    typ: Annotated[
        str,
        typer.Option(
            "--typ",
            help="Token type (should be JWT)",
            metavar="TYPE",
            rich_help_panel="Optional JWT Parameters",
        ),
    ] = "JWT",
    validity_minutes: Annotated[
        int,
        typer.Option(
            "--validity-minutes",
            help="JWT validity period in minutes. Examples: 1440 (24 hours), 10080 (7 days), 43200 (30 days max)",
            min=1,
            max=43200,
            metavar="MINUTES",
            rich_help_panel="Optional JWT Parameters",
        ),
    ] = 43200,
    clear_screen: Annotated[
        bool,
        typer.Option(
            "--clear/--no-clear",
            help="Clear the terminal screen before output",
            rich_help_panel="Display Options",
        ),
    ] = True,
) -> None:
    """
    Generate a client assertion JWT for PDND authentication.

    This command creates a signed JWT token that can be used for PDND
    (Piattaforma Digitale Nazionale Dati) authentication.

    Example:

        python create_client_assertion.py create \\
            --kid "my-key-id" \\
            --issuer "my-client-id" \\
            --subject "my-client-id" \\
            --audience "https://auth.interop.pagopa.it/token.oauth2" \\
            --purpose-id "my-purpose-id" \\
            --key-path ./private_key.pem
    """
    try:
        # Create and validate configuration
        config = JWTConfig(
            kid=kid,
            alg=alg,
            typ=typ,
            issuer=issuer,
            subject=subject,
            audience=audience,
            purpose_id=purpose_id,
            key_path=key_path,
            validity_minutes=validity_minutes,
        )

        # Generate JWT
        token = generate_jwt(config)

        # Clear screen if requested
        if clear_screen:
            os.system("clear")

        # Output the token
        console.print(token)

    except ValueError as e:
        console.print(f"[red]Validation error: {e}[/red]")
        raise typer.Exit(code=1) from None
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        raise typer.Exit(code=1) from None


if __name__ == "__main__":
    app()
