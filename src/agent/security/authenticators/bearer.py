"""Bearer Token authenticator implementation."""

from typing import Set
from fastapi import Request

from ..base import BaseAuthenticator, AuthenticationResult
from ..exceptions import (
    SecurityConfigurationException,
    MissingCredentialsException,
    InvalidCredentialsException
)
from ..utils import (
    secure_compare,
    validate_bearer_token_format,
    extract_bearer_token,
    log_security_event,
    get_request_info
)


class BearerTokenAuthenticator(BaseAuthenticator):
    """Bearer Token based authentication."""

    def _validate_config(self) -> None:
        """Validate Bearer token authenticator configuration."""
        # Check for bearer token in config
        bearer_config = self.config.get('bearer', {})
        bearer_token = bearer_config.get('bearer_token') or self.config.get('bearer_token')

        if not bearer_token:
            raise SecurityConfigurationException("Bearer token is required for bearer authentication")

        # Handle environment variable placeholders
        if isinstance(bearer_token, str) and bearer_token.startswith('${') and bearer_token.endswith('}'):
            self.bearer_token = bearer_token
            return

        if not isinstance(bearer_token, str):
            raise SecurityConfigurationException("Bearer token must be a string")

        if not validate_bearer_token_format(bearer_token):
            raise SecurityConfigurationException("Invalid bearer token format")

        self.bearer_token = bearer_token

        # Additional JWT-specific configuration
        self.jwt_secret = bearer_config.get('jwt_secret')
        self.jwt_algorithm = bearer_config.get('algorithm', 'HS256')
        self.jwt_issuer = bearer_config.get('issuer')
        self.jwt_audience = bearer_config.get('audience')

    async def authenticate(self, request: Request) -> AuthenticationResult:
        """Authenticate request using Bearer token.

        Args:
            request: FastAPI request object

        Returns:
            AuthenticationResult: Authentication result

        Raises:
            MissingCredentialsException: If Bearer token is missing
            InvalidCredentialsException: If Bearer token is invalid
        """
        request_info = get_request_info(request)

        # Extract Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            log_security_event(
                'authentication',
                request_info,
                False,
                "Missing Authorization header"
            )
            raise MissingCredentialsException("Unauthorized")

        # Extract Bearer token
        token = extract_bearer_token(auth_header)
        if not token:
            log_security_event(
                'authentication',
                request_info,
                False,
                "Invalid Authorization header format"
            )
            raise InvalidCredentialsException("Unauthorized")

        # Validate token format
        if not validate_bearer_token_format(token):
            log_security_event(
                'authentication',
                request_info,
                False,
                "Invalid bearer token format"
            )
            raise InvalidCredentialsException("Unauthorized")

        # Compare with configured token using secure comparison
        configured_token = self.bearer_token

        # Handle environment variable placeholders
        if configured_token.startswith('${') and configured_token.endswith('}'):
            # Extract default value if provided
            if ':' in configured_token:
                default_value = configured_token.split(':', 1)[1][:-1]  # Remove closing }
                if secure_compare(token, default_value):
                    log_security_event('authentication', request_info, True, "Bearer token authenticated")
                    return AuthenticationResult(
                        success=True,
                        user_id=f"bearer_user_{hash(token) % 10000}",
                        credentials=token
                    )
            log_security_event(
                'authentication',
                request_info,
                False,
                "Bearer token environment variable not resolved"
            )
            raise InvalidCredentialsException("Unauthorized")

        if secure_compare(token, configured_token):
            log_security_event('authentication', request_info, True, "Bearer token authenticated")
            return AuthenticationResult(
                success=True,
                user_id=f"bearer_user_{hash(token) % 10000}",
                credentials=token
            )

        log_security_event(
            'authentication',
            request_info,
            False,
            "Bearer token does not match configured token"
        )
        raise InvalidCredentialsException("Unauthorized")

    def get_auth_type(self) -> str:
        """Get authentication type identifier."""
        return 'bearer'

    def get_required_headers(self) -> Set[str]:
        """Get required headers for Bearer authentication."""
        return {'Authorization'}

    def supports_scopes(self) -> bool:
        """Bearer tokens can support scopes (especially JWT)."""
        return True  # Could be extended to parse JWT scopes

    def _validate_jwt_token(self, token: str) -> AuthenticationResult:
        """Validate JWT token (future implementation).

        Args:
            token: The JWT token to validate

        Returns:
            AuthenticationResult: Authentication result with user info and scopes
        """
        # TODO: Implement proper JWT validation using PyJWT
        # This would include:
        # - Signature verification
        # - Expiration checking
        # - Issuer/audience validation
        # - Scope extraction
        pass