"""Base authenticator class for the security module."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Set
from fastapi import Request

from ..base import AuthenticationResult, BaseAuthenticator
from ..exceptions import SecurityConfigurationException