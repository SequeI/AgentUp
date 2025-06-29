"""Handler modules for agent."""

import logging
import importlib
from pathlib import Path

logger = logging.getLogger(__name__)

# Import core handler functions
from .handlers import (  # noqa: E402
    get_handler,
    register_handler,
    get_all_handlers,
    list_skills,
    handle_status,
    handle_capabilities,
    handle_echo
)

# Import multimodal handlers
from .handlers_multimodal import (  # noqa: E402
    handle_analyze_image,
    handle_process_document,
    handle_transform_image,
    handle_multimodal_chat
)
# Export all public functions and handlers
__all__ = [
    # Core handler functions
    'get_handler',
    'register_handler',
    'get_all_handlers',
    'list_skills',

    # Core handlers
    'handle_status',
    'handle_capabilities',
    'handle_echo',

    # Multimodal handlers
    'handle_analyze_image',
    'handle_process_document',
    'handle_transform_image',
    'handle_multimodal_chat',
]

# Auto-discovery of individual handler files
def discover_user_handlers():
    """Auto-discover and import all *_handler.py files to trigger @register_handler decorators."""
    handlers_dir = Path(__file__).parent

    # Find all handler files matching the pattern
    handler_files = list(handlers_dir.glob("*_handler.py"))

    for handler_file in handler_files:
        # Skip special handler files
        if handler_file.name in ["handlers.py", "handlers_multimodal.py"]:
            continue

        try:
            # Import the module to trigger @register_handler decorators
            module_name = f".{handler_file.stem}"
            importlib.import_module(module_name, package=__name__)
            logger.debug(f"Imported handler module: {handler_file.name}")

        except ImportError as e:
            logger.warning(f"Failed to import {handler_file.name}: {e}")
        except Exception as e:
            logger.error(f"Error loading handler from {handler_file.name}: {e}")

# Run discovery on module import
discover_user_handlers()
