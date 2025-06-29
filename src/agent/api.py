from datetime import datetime
from typing import Any, Dict, AsyncGenerator, Union

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse

from .config import load_config
from .models import (
    AgentCapabilities,
    AgentCard,
    AgentExtension,
    AgentSkill,
    APIKeySecurityScheme,
    HTTPAuthSecurityScheme,
    JSONRPCError,
)
from .security import protected
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.request_handlers.jsonrpc_handler import JSONRPCHandler
from a2a.types import (
    SendMessageRequest,
    SendStreamingMessageRequest,
    GetTaskRequest,
    CancelTaskRequest,
    TaskResubscriptionRequest,
    SetTaskPushNotificationConfigRequest,
    GetTaskPushNotificationConfigRequest,
    JSONRPCErrorResponse,
    InternalError,
)

# Create router
router = APIRouter()

# Load configuration
config = load_config()

# Task storage (in production, use persistent storage)
task_storage: Dict[str, Dict[str, Any]] = {}

# Request handler instance management
_request_handler: DefaultRequestHandler | None = None


def set_request_handler_instance(handler: DefaultRequestHandler):
    """Set the global request handler instance."""
    global _request_handler
    _request_handler = handler


def get_request_handler() -> DefaultRequestHandler:
    """Get the global request handler instance."""
    if _request_handler is None:
        raise RuntimeError("Request handler not initialized")
    return _request_handler

def create_agent_card() -> AgentCard:
    """Create agent card with current configuration."""

    config = load_config()
    agent_info = config.get("agent", {})
    skills = config.get("skills", [])

    # Convert skills to A2A Skill format
    agent_skills = []
    for skill in skills:
        agent_skill = AgentSkill(
            id=skill.get("skill_id"),
            name=skill.get("name"),
            description=skill.get("description"),
            inputModes=[skill.get("input_mode", "text")],
            outputModes=[skill.get("output_mode", "text")],
            tags=skill.get("tags", ["general"])
        )
        agent_skills.append(agent_skill)

    # Create capabilities object with extensions
    extensions = []

    # Add MCP extension if enabled
    mcp_config = config.get("mcp", {})
    if mcp_config.get("enabled") and mcp_config.get("server", {}).get("enabled"):
        mcp_extension = AgentExtension(
            uri="https://modelcontextprotocol.io/mcp/1.0",
            description="Agent supports MCP for tool sharing and collaboration",
            params={
                "endpoint": "/mcp",
                "transport": "http",
                "authentication": "api_key",
            },
            required=False
        )
        extensions.append(mcp_extension)

    capabilities = AgentCapabilities(
        streaming=True,
        pushNotifications=True,  # Enabled since we have InMemoryPushNotifier configured
        stateTransitionHistory=True,
        extensions=extensions if extensions else None
    )

    # Create security schemes based on configuration
    security_config = config.get("security", {})
    security_schemes = {}
    security_requirements = []

    if security_config.get("enabled", False):
        auth_type = security_config.get("type", "api_key")

        if auth_type == "api_key":
            # API Key authentication
            api_key_scheme = APIKeySecurityScheme.model_validate({
            "name": "X-API-Key",
            "description": "API key for authentication",
            "in": "header",  # <- use the JSON alias
            "type": "apiKey"
        })
            security_schemes["X-API-Key"] = api_key_scheme.model_dump(by_alias=True)
            security_requirements.append({"X-API-Key": []})

        elif auth_type == "bearer":
            # Bearer Token authentication
            bearer_scheme = HTTPAuthSecurityScheme(
                scheme="bearer",
                description="Bearer token for authentication",
                type="http"
            )
            security_schemes["BearerAuth"] = bearer_scheme.model_dump(by_alias=True)
            security_requirements.append({"BearerAuth": []})

        elif auth_type == "oauth2":
            # OAuth2 Bearer Token authentication
            oauth2_config = security_config.get("oauth2", {})
            required_scopes = oauth2_config.get("required_scopes", [])

            oauth2_scheme = HTTPAuthSecurityScheme(
                scheme="bearer",
                description="OAuth2 Bearer token for authentication",
                type="http",
                bearerFormat="JWT"  # Indicate JWT format for OAuth2
            )
            security_schemes["OAuth2"] = oauth2_scheme.model_dump(by_alias=True)
            security_requirements.append({"OAuth2": required_scopes})

    # Create the official AgentCard
    agent_card = AgentCard(
        name=agent_info.get("name", config.get("project_name", "Agent")),
        description=agent_info.get("description", config.get("description", "AI Agent")),
        version=agent_info.get("version", "0.1.0"),
        url="http://localhost:8000",
        capabilities=capabilities,
        skills=agent_skills,
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
        securitySchemes=security_schemes if security_schemes else None,
        security=security_requirements if security_requirements else None
    )

    return agent_card


@router.get("/task/{task_id}/status")
@protected()
async def get_task_status(task_id: str, request: Request) -> JSONResponse:
    """Get task status and result."""

    if task_id not in task_storage:
        raise HTTPException(status_code=404, detail="Task not found")

    task_data = task_storage[task_id]

    response = {
        "id": task_id,
        "status": task_data['status'].value,
        "created_at": task_data['created_at'].isoformat(),
        "updated_at": task_data['updated_at'].isoformat()
    }

    if 'result' in task_data:
        response['result'] = task_data['result']

    if 'error' in task_data:
        response['error'] = task_data['error']

    return JSONResponse(status_code=200, content=response)

@router.get("/health")
async def health_check() -> JSONResponse:
    """Basic health check endpoint."""
    config = load_config()
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "agent": config.get('project_name', 'Agent'),
            "timestamp": datetime.now().isoformat()
        }
    )

@router.get("/services/health")
async def services_health() -> JSONResponse:
    """Check health of all services."""
    try:
        from .services import get_services
        services = get_services()
        health_results = await services.health_check_all()
    except ImportError:
        health_results = {"error": "Services module not available"}

    all_healthy = all(
        result.get('status') == 'healthy'
        for result in health_results.values()
    )

    return JSONResponse(
        status_code=200 if all_healthy else 503,
        content={
            "status": "healthy" if all_healthy else "degraded",
            "services": health_results,
            "timestamp": datetime.now().isoformat()
        }
    )

# A2A AgentCard
@router.get("/.well-known/agent.json", response_model=AgentCard)
async def get_agent_discovery() -> AgentCard:
    """A2A agent discovery endpoint."""
    return create_agent_card()

async def sse_generator(async_iterator: AsyncGenerator) -> AsyncGenerator[str, None]:
    """Convert async iterator to SSE format."""
    try:
        async for response in async_iterator:
            # Each response is a SendStreamingMessageResponse
            data = response.model_dump_json(by_alias=True)
            yield f"data: {data}\n\n"
    except Exception as e:
        # Send error event
        error_response = JSONRPCErrorResponse(
            id=None,
            error=InternalError(message=str(e))
        )
        yield f"data: {error_response.model_dump_json(by_alias=True)}\n\n"

@router.post("/", response_model=None)
@protected()
async def jsonrpc_endpoint(
    request: Request,
    handler: DefaultRequestHandler = Depends(get_request_handler),
) -> Union[JSONResponse, StreamingResponse]:
    """This is the main JSON-RPC 2.0 endpoint with SSE Streaming support."""
    try:
        # Parse JSON-RPC request
        body = await request.json()

        # Validate JSON-RPC structure
        if not isinstance(body, dict):
            return JSONResponse(
                status_code=200,
                content={
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32600,
                        "message": "Invalid Request"
                    },
                    "id": body.get("id") if isinstance(body, dict) else None
                }
            )

        if body.get("jsonrpc") != "2.0":
            return JSONResponse(
                status_code=200,
                content={
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32600,
                        "message": "Invalid Request"
                    },
                    "id": body.get("id")
                }
            )

        method = body.get("method")
        params = body.get("params", {})
        request_id = body.get("id")

        if not method:
            return JSONResponse(
                status_code=200,
                content={
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32600,
                        "message": "Invalid Request"
                    },
                    "id": request_id
                }
            )

        # Create JSONRPCHandler with the agent card, which is needed for capabilities,
        # security schemes, and other metadata for the agent.
        agent_card = create_agent_card()
        jsonrpc_handler = JSONRPCHandler(agent_card, handler)

        # Route to appropriate handler based on method
        if method == "message/send":
            # Non-streaming method
            rpc_request = SendMessageRequest(
                jsonrpc="2.0",
                id=request_id,
                method=method,
                params=params
            )
            response = await jsonrpc_handler.on_message_send(rpc_request)
            return JSONResponse(
                status_code=200,
                content=response.model_dump(by_alias=True)
            )

        elif method == "message/stream":
            # Streaming method - return SSE
            rpc_request = SendStreamingMessageRequest(
                jsonrpc="2.0",
                id=request_id,
                method=method,
                params=params
            )
            response_stream = jsonrpc_handler.on_message_send_stream(rpc_request)
            return StreamingResponse(
                sse_generator(response_stream),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                }
            )

        elif method == "tasks/get":
            # Non-streaming method
            rpc_request = GetTaskRequest(
                jsonrpc="2.0",
                id=request_id,
                method=method,
                params=params
            )
            response = await jsonrpc_handler.on_get_task(rpc_request)
            return JSONResponse(
                status_code=200,
                content=response.model_dump(by_alias=True)
            )

        elif method == "tasks/cancel":
            # Non-streaming method
            rpc_request = CancelTaskRequest(
                jsonrpc="2.0",
                id=request_id,
                method=method,
                params=params
            )
            response = await jsonrpc_handler.on_cancel_task(rpc_request)
            return JSONResponse(
                status_code=200,
                content=response.model_dump(by_alias=True)
            )

        elif method == "tasks/resubscribe":
            # Streaming method - return SSE
            rpc_request = TaskResubscriptionRequest(
                jsonrpc="2.0",
                id=request_id,
                method=method,
                params=params
            )
            response_stream = jsonrpc_handler.on_resubscribe_to_task(rpc_request)
            return StreamingResponse(
                sse_generator(response_stream),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                }
            )

        elif method == "tasks/pushNotificationConfig/set":
            # Non-streaming method
            rpc_request = SetTaskPushNotificationConfigRequest(
                jsonrpc="2.0",
                id=request_id,
                method=method,
                params=params
            )
            response = await jsonrpc_handler.set_push_notification(rpc_request)
            return JSONResponse(
                status_code=200,
                content=response.model_dump(by_alias=True)
            )

        elif method == "tasks/pushNotificationConfig/get":
            # Non-streaming method
            rpc_request = GetTaskPushNotificationConfigRequest(
                jsonrpc="2.0",
                id=request_id,
                method=method,
                params=params
            )
            response = await jsonrpc_handler.get_push_notification(rpc_request)
            return JSONResponse(
                status_code=200,
                content=response.model_dump(by_alias=True)
            )

        elif method == "tasks/pushNotificationConfig/list":
            # Non-streaming method - need to handle this separately as it's not in JSONRPCHandler
            # For now, return unsupported operation
            return JSONResponse(
                status_code=200,
                content={
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32601,
                        "message": "Method not found",
                        "data": "tasks/pushNotificationConfig/list is not yet implemented"
                    },
                    "id": request_id
                }
            )

        elif method == "tasks/pushNotificationConfig/delete":
            # Non-streaming method - need to handle this separately as it's not in JSONRPCHandler
            # For now, return unsupported operation
            return JSONResponse(
                status_code=200,
                content={
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32601,
                        "message": "Method not found",
                        "data": "tasks/pushNotificationConfig/delete is not yet implemented"
                    },
                    "id": request_id
                }
            )

        else:
            # Method not found
            return JSONResponse(
                status_code=200,
                content={
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32601,
                        "message": "Method not found",
                        "data": f"Unknown method: {method}"
                    },
                    "id": request_id
                }
            )

    except Exception as e:
        # Unexpected error
        return JSONResponse(
            status_code=200,
            content={
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": "Internal error",
                    "data": str(e)
                },
                "id": body.get("id") if 'body' in locals() else None
            }
        )

# Error handlers (to be registered with FastAPI app)
async def jsonrpc_error_handler(request: Request, exc: JSONRPCError):
    """Handle JSON-RPC errors."""
    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "data": exc.data
            }
        }
    )

# Export router and handlers
__all__ = ['router', 'jsonrpc_error_handler', 'set_request_handler_instance', 'get_request_handler']