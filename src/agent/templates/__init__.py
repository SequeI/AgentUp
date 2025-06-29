"""Template system for agent."""

from typing import Any, Dict, List

import questionary


def get_template_choices() -> List[questionary.Choice]:
    """Get available project templates."""
    return [
        questionary.Choice(
            "Minimal - Barebone agent (no AI, no external dependencies)",
            value="minimal",
            shortcut_key="m"
        ),
        questionary.Choice(
            "Standard - AI-powered agent with MCP (recommended)",
            value="standard",
            shortcut_key="s"
        ),
        questionary.Choice(
            "Full - Enterprise agent with all features",
            value="full",
            shortcut_key="f"
        ),
        questionary.Choice(
            "Demo - Example agent showcasing capabilities",
            value="demo",
            shortcut_key="d"
        ),
    ]


def get_feature_choices() -> List[questionary.Choice]:
    """Get available features for custom template."""
    return [
        questionary.Choice("Middleware System", value="middleware", checked=True),
        questionary.Choice("Multi-modal Processing", value="multimodal"),
        questionary.Choice("External Services (LLM, Database, Cache)", value="services"),
        questionary.Choice("State Management", value="state"),
        questionary.Choice("Authentication", value="auth", checked=True),
        questionary.Choice("Monitoring & Observability", value="monitoring"),
        questionary.Choice("Testing Framework", value="testing", checked=True),
        questionary.Choice("Deployment Tools", value="deployment"),
    ]


def get_template_features(template: str = None) -> Dict[str, Dict[str, Any]]:
    """Get features included in each template."""
    return {
        "minimal": {
            "features": [],
            "description": "Barebone agent with text processing only - no AI, no external dependencies"
        },
        "standard": {
            "features": ["middleware", "services", "auth", "testing", "mcp"],
            "description": "AI-powered agent with MCP integration - recommended for most users"
        },
        "full": {
            "features": ["middleware", "multimodal", "services", "state", "auth",
                        "monitoring", "testing", "deployment", "mcp"],
            "description": "Enterprise-ready agent with all features including multiple MCP servers"
        },
        "demo": {
            "features": ["middleware", "services", "auth", "testing", "mcp"],
            "description": "Example agent showcasing various capabilities with pre-built skills"
        }
    }
