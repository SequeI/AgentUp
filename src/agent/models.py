# Import typing for exception classes
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from abc import ABC

# Import official A2A types
from a2a.types import (
    AgentCard,
    AgentSkill,
    AgentCapabilities,
    AgentExtension,
    APIKeySecurityScheme,
    HTTPAuthSecurityScheme,
    SecurityScheme,
    Artifact,
    DataPart,
    JSONRPCMessage,
    Message,
    Role,
    SendMessageRequest,
    Task,
    TaskState,
    TaskStatus,
    TextPart,
    In,
    Part
)


class JSONRPCError(Exception):
    """JSON-RPC error with code."""
    def __init__(self, code: int, message: str, data: Any = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.data = data

class TaskNotFoundError(Exception):
    """Task not found error."""
    pass

class ContentTypeNotSupportedError(Exception):
    """Content type not supported error."""
    pass

class InvalidAgentResponseError(Exception):
    """Invalid agent response error."""
    pass

class RoutingConfig(BaseModel):
    """Global routing configuration."""
    default_mode: str = "ai"  # "ai" or "direct"
    fallback_skill: Optional[str] = None  # Fallback skill when no match
    fallback_enabled: bool = True  # Allow AI→Direct fallback

class SkillConfig(BaseModel):
    """Configuration for a skill - extends A2A with routing config."""
    skill_id: str
    name: str
    description: str
    input_mode: str = "text"
    output_mode: str = "text"
    routing_mode: Optional[str] = None  # "ai", "direct", or None (use default)
    keywords: Optional[List[str]] = None  # For direct routing
    patterns: Optional[List[str]] = None  # For direct routing
    config: Optional[Dict[str, Any]] = None
    middleware: Optional[List[Dict[str, Any]]] = None
    enabled: bool = True  # Allow disabling skills

class AgentConfig(BaseModel):
    """Configuration for the agent."""
    project_name: str = "MyAgent"
    description: str = "An AgentUp A2A-compliant AI agent"
    version: str = "1.0.0"
    dispatcher_path: Optional[str] = None  # e.g. "src.agent.function_dispatcher:get_function_dispatcher"
    # Services
    services_enabled: bool = True
    services_init_path: Optional[str] = None    # e.g. "src.agent.services:initialize_services_from_config"

    # MCP integration
    mcp_enabled: bool = False
    mcp_init_path: Optional[str] = None         # e.g. "src.agent.mcp.mcp_integration:initialize_mcp_integration"
    mcp_shutdown_path: Optional[str] = None

    skills: List[SkillConfig] = []
    security: Optional[Dict[str, Any]] = None
    services: Optional[Dict[str, Any]] = None


class ServiceConfig(BaseModel):
    type: str                        # e.g. "llm", "database", "mcp_client", etc.
    init_path: Optional[str] = None  # for custom loader overrides
    settings: Optional[Dict[str, Any]] = {}

class SkillResponse(BaseModel):
    """Response from a skill handler."""
    success: bool
    result: Optional[str] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class BaseAgent(BaseModel, ABC):
    """Base class for agents."""

    model_config = {
        'arbitrary_types_allowed': True,
        'extra': 'allow',
    }

    agent_name: str = Field(
        description='The name of the agent.',
    )

    description: str = Field(
        description="A brief description of the agent's purpose.",
    )

    content_types: list[str] = Field(description='Supported content types.')

# Re-export A2A types for convenience
__all__ = [
    # A2A types
    'AgentCard', 'Artifact', 'DataPart', 'JSONRPCMessage', 'AgentSkill', 'AgentCapabilities',
    'AgentExtension', 'APIKeySecurityScheme', 'In', 'SecurityScheme', 'HTTPAuthSecurityScheme',
    'Message', 'Role', 'SendMessageRequest', 'Task', 'TextPart', 'Part',
    'TaskState', 'TaskStatus',
    # Custom exceptions
    'JSONRPCError', 'TaskNotFoundError', 'ContentTypeNotSupportedError',
    'InvalidAgentResponseError',
    # Custom models
    'RoutingConfig', 'SkillConfig', 'AgentConfig', 'SkillResponse', 'BaseAgent'
]