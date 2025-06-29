"""Main entry point for the agent."""

import logging
import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager
import httpx

from .agent_executor import GenericAgentExecutor as AgentExecutorImpl
from .api import router, jsonrpc_error_handler, create_agent_card, set_request_handler_instance
from .config import load_config
from .models import JSONRPCError
from .security import create_security_manager

from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryPushNotifier, InMemoryTaskStore

# Optional imports; fall back to None if the module isn't present
try:
    from .services import initialize_services_from_config
except ImportError:
    initialize_services_from_config = None

try:
    from .function_dispatcher import register_ai_functions_from_handlers
except ImportError:
    register_ai_functions_from_handlers = None

try:
    from .mcp_support.mcp_integration import initialize_mcp_integration, shutdown_mcp_integration
except ImportError:
    initialize_mcp_integration = None
    shutdown_mcp_integration = None


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan manager for the FastAPI application."""
    # Load configuration and attach to app.state
    config = load_config()
    app.state.config = config

    agent_cfg = config.get("agent", {})
    name = agent_cfg.get("name", "Agent")
    version = agent_cfg.get("version", "0.1.0")
    logger.info(f"Starting {name} v{version}")

    # Initialize security manager
    try:
        security_manager = create_security_manager(config)
        app.state.security_manager = security_manager
        if security_manager.is_auth_enabled():
            logger.info(f"Security enabled with {security_manager.get_primary_auth_type()} authentication")
        else:
            logger.info("Security disabled - all endpoints will be public")
    except Exception as e:
        logger.error(f"Failed to initialize security manager: {e}")
        # Continue without security for now, but log the error
        app.state.security_manager = None

    # — Initialize services if available & enabled —
    svc_cfg = config.get("services", {})
    if initialize_services_from_config and svc_cfg.get("enabled", True):
        try:
            await initialize_services_from_config(config)
            logger.info("Services initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize services: {e}")

    # — Load registry skills if available —
    try:
        from .registry_skill_loader import load_all_registry_skills
        load_all_registry_skills()
        logger.info("Registry skills loaded successfully")
    except ImportError:
        logger.debug("Registry skill loader not available")
    except Exception as e:
        logger.error(f"Failed to load registry skills: {e}")

    # — Register AI functions if available & requested —
    routing_cfg = config.get("routing", {})
    default_mode = routing_cfg.get("default_mode", "ai")
    logger.info(f"Routing default mode set to: {default_mode}")
    
    # Register AI functions if any skills might use AI routing
    # Note: In mixed routing, skills can override the default mode
    skills = config.get("skills", [])
    needs_ai = any(skill.get("routing_mode", default_mode) == "ai" for skill in skills)
    
    if register_ai_functions_from_handlers and needs_ai and svc_cfg.get("ai_functions", True):
        try:
            register_ai_functions_from_handlers()
            logger.info("AI functions registered successfully")
        except Exception as e:
            logger.error(f"Failed to register AI functions: {e}")
    elif not needs_ai:
        logger.info("No AI routing skills found - skipping AI function registration")

    # — Initialize MCP integration if available & enabled —
    mcp_cfg = config.get("mcp", {})
    if initialize_mcp_integration and mcp_cfg.get("enabled", False):
        try:
            await initialize_mcp_integration(config)
            logger.info("MCP integration initialized successfully")

            # Add MCP HTTP endpoint if server is enabled
            if mcp_cfg.get("server", {}).get("enabled", False):
                try:
                    from .mcp_support.mcp_http_server import MCPHTTPServer, create_mcp_router

                    # Create MCP HTTP server
                    mcp_http_server = MCPHTTPServer(
                        agent_name=agent_cfg.get("name", "Agent"),
                        agent_version=agent_cfg.get("version", "0.1.0")
                    )
                    await mcp_http_server.initialize()

                    # Store in app state for later access
                    app.state.mcp_http_server = mcp_http_server

                    # Create and mount MCP router
                    mcp_router = create_mcp_router(mcp_http_server)
                    app.include_router(mcp_router)

                    logger.info("MCP HTTP endpoint added at /mcp")
                except Exception as e:
                    logger.error(f"Failed to add MCP HTTP endpoint: {e}")

        except Exception as e:
            logger.error(f"Failed to initialize MCP integration: {e}")

    yield

    # Shutdown hooks
    logger.info("Shutting down...")
    if shutdown_mcp_integration and mcp_cfg.get("enabled", False):
        try:
            await shutdown_mcp_integration()
            logger.info("MCP integration shut down successfully")
        except Exception as e:
            logger.error(f"Failed to shutdown MCP integration: {e}")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    agent_card = create_agent_card()

    # Create and register the request handler
    client = httpx.AsyncClient()
    request_handler = DefaultRequestHandler(
        agent_executor=AgentExecutorImpl(agent=create_agent_card()),
        task_store=InMemoryTaskStore(),
        push_notifier=InMemoryPushNotifier(client),
    )
    set_request_handler_instance(request_handler)

    # Create FastAPI app
    app = FastAPI(
        title=agent_card.name,
        description=agent_card.description,
        version=agent_card.version,
        lifespan=lifespan,
    )

    # Add default routes and exception handlers
    app.include_router(router)
    app.add_exception_handler(JSONRPCError, jsonrpc_error_handler)

    return app


app = create_app()


def main():
    """Main function to set up and run the agent."""
    logger.info("Starting server")
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()
