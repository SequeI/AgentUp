"""AgentUp - A2A-compliant AI agent framework."""

# Core exports
from .api.app import app, create_app, main
from .config import load_config
from .core import AgentExecutor, FunctionDispatcher, FunctionExecutor
from .services import get_services, initialize_services
from .state import ConversationManager, get_context_manager

__version__ = "0.1.0"

__all__ = [
    # Main app
    "app",
    "create_app",
    "main",
    # Core
    "AgentExecutor",
    "FunctionDispatcher",
    "FunctionExecutor",
    # Config
    "load_config",
    # Services
    "get_services",
    "initialize_services",
    # State
    "ConversationManager",
    "get_context_manager",
]
