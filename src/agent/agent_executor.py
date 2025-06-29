import logging
from typing import List, Any

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import (
    DataPart,
    InvalidParamsError,
    Part,
    Task,
    TaskArtifactUpdateEvent,
    TaskState,
    TaskStatus,
    TextPart,
    UnsupportedOperationError,
)
from a2a.utils import (
    new_agent_text_message,
    new_task,
    new_artifact,
    new_data_artifact,
)
from a2a.utils.errors import ServerError
from .models import BaseAgent
from a2a.types import AgentCard
from .function_dispatcher import get_function_dispatcher


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class GenericAgentExecutor(AgentExecutor):
    """Enhanced A2A-compliant AgentExecutor with streaming and multi-modal support."""

    def __init__(self, agent: BaseAgent | AgentCard):
        self.agent = agent
        self.supports_streaming = getattr(agent, 'supports_streaming', False)

        # Handle both BaseAgent and AgentCard
        if isinstance(agent, AgentCard):
            self.agent_name = agent.name
        else:
            self.agent_name = agent.agent_name

        # Load config for new routing system
        from .config import load_config
        config = load_config()

        # Parse routing configuration (new format)
        routing_config = config.get('routing', {})
        self.default_routing_mode = routing_config.get('default_mode', 'ai')
        self.fallback_skill = routing_config.get('fallback_skill', 'echo')
        self.fallback_enabled = routing_config.get('fallback_enabled', True)

        # Parse skills with routing configuration
        self.skills = {}
        for skill_data in config.get('skills', []):
            if skill_data.get('enabled', True):
                skill_id = skill_data['skill_id']
                self.skills[skill_id] = {
                    'routing_mode': skill_data.get('routing_mode', self.default_routing_mode),
                    'keywords': skill_data.get('keywords', []),
                    'patterns': skill_data.get('patterns', []),
                    'name': skill_data.get('name', skill_id),
                    'description': skill_data.get('description', '')
                }


        # Initialize Function Dispatcher if any skill uses AI routing
        self.needs_ai = any(skill['routing_mode'] == 'ai' for skill in self.skills.values())
        if self.needs_ai:
            self.dispatcher = get_function_dispatcher()
        else:
            self.dispatcher = None

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        logger.info(f'Executing agent {self.agent_name}')
        error = self._validate_request(context)
        if error:
            raise ServerError(error=InvalidParamsError(data={"reason": error}))

        task = context.current_task

        if not task:
            task = new_task(context.message)
            await event_queue.enqueue_event(task)

        updater = TaskUpdater(event_queue, task.id, task.contextId)

        try:
            # Transition to working state
            await updater.update_status(
                TaskState.working,
                new_agent_text_message(
                    f"Processing request with for task {task.id} using {self.agent_name}.",
                    task.contextId,
                    task.id,
                ),
                final=False,
            )

            # Check if task requires specific input/clarification
            if await self._requires_input(task, context):
                await updater.update_status(
                    TaskState.input_required,
                    new_agent_text_message(
                        "I need more information to proceed. Please provide additional details.",
                        task.contextId,
                        task.id,
                    ),
                    final=False,
                )
                return

            # New routing system: determine skill and routing mode
            user_input = self._extract_user_message(task)
            target_skill, routing_mode = self._determine_skill_and_routing(user_input)

            logger.info(f"Processing task {task.id} with skill '{target_skill}' using {routing_mode} routing")

            # Process based on determined routing mode
            if routing_mode == 'ai' and self.dispatcher:
                if self.supports_streaming:
                    # Stream responses incrementally
                    await self._process_streaming(task, updater, event_queue)
                else:
                    # Process synchronously with AI
                    result = await self.dispatcher.process_task(task)
                    await self._create_response_artifact(result, task, updater)
            else:
                # Use direct routing (either skill specifies direct, or AI fallback)
                if routing_mode == 'ai' and not self.dispatcher and self.fallback_enabled:
                    logger.warning("AI routing requested but no dispatcher available, falling back to direct routing")

                result = await self._process_direct_routing(task, target_skill)
                await self._create_response_artifact(result, task, updater)

        except ValueError as e:
            # Handle unsupported operations gracefully (UnsupportedOperationError is a data model, not exception)
            if "unsupported" in str(e).lower():
                logger.warning(f"Unsupported operation requested: {e}")
                await updater.update_status(
                    TaskState.rejected,
                    new_agent_text_message(
                        f"This operation is not supported: {str(e)}",
                        task.contextId,
                        task.id,
                ),
                final=True,
            )
        except Exception as e:
            logger.error(f"Error processing task: {e}")
            await updater.update_status(
                TaskState.failed,
                new_agent_text_message(
                    f"I encountered an error processing your request: {str(e)}",
                    task.contextId,
                    task.id,
                ),
                final=True,
            )

    def _determine_skill_and_routing(self, user_input: str) -> tuple[str, str]:
        """Determine which skill and routing mode to use for the user input."""
        import re

        if not user_input:
            return self.fallback_skill, self.default_routing_mode

        # Check each skill's routing configuration
        for skill_id, skill_config in self.skills.items():
            routing_mode = skill_config['routing_mode']

            # For direct routing skills, check keywords and patterns
            if routing_mode == 'direct':
                keywords = skill_config.get('keywords', [])
                patterns = skill_config.get('patterns', [])

                # Check keywords
                for keyword in keywords:
                    if keyword.lower() in user_input.lower():
                        logger.debug(f"Matched keyword '{keyword}' for skill '{skill_id}'")
                        return skill_id, routing_mode

                # Check patterns
                for pattern in patterns:
                    try:
                        if re.search(pattern, user_input, re.IGNORECASE):
                            logger.debug(f"Matched pattern '{pattern}' for skill '{skill_id}'")
                            return skill_id, routing_mode
                    except re.error as e:
                        logger.warning(f"Invalid regex pattern '{pattern}' in skill '{skill_id}': {e}")

        # No direct routing match found, use fallback skill with default routing mode
        return self.fallback_skill, self.default_routing_mode


    async def _process_direct_routing(self, task: Task, target_skill: str = None) -> str:
        """Process task using direct handler routing (no AI)."""
        logger.info(f"Starting direct routing for task: {task}")

        # Use provided target skill or fall back to fallback skill
        skill_id = target_skill or self.fallback_skill
        logger.info(f"Routing to skill: {skill_id}")

        # Get handler for the skill
        from .handlers import get_handler
        handler = get_handler(skill_id)

        if not handler:
            return f"No handler found for skill: {skill_id}"

        # Call handler directly
        try:
            result = await handler(task)
            return result if isinstance(result, str) else str(result)
        except Exception as e:
            logger.error(f"Error in handler {skill_id}: {e}")
            return f"Error processing request: {str(e)}"

    def _extract_user_message(self, task: Task) -> str:
        """Extract user message from A2A task using A2A SDK structure."""
        try:
            if not (hasattr(task, 'history') and task.history):
                return ""

            # Get the latest user message from history
            for message in reversed(task.history):
                if message.role == 'user' and message.parts:
                    for part in message.parts:
                        # A2A SDK uses Part(root=TextPart(...)) structure
                        if hasattr(part, 'root') and hasattr(part.root, 'kind'):
                            if part.root.kind == 'text' and hasattr(part.root, 'text'):
                                return part.root.text
            return ""
        except Exception as e:
            logger.error(f"Error extracting user message: {e}")
            return ""

    async def _process_streaming(
        self,
        task: Task,
        updater: TaskUpdater,
        event_queue: EventQueue,
    ) -> None:
        """Process task with streaming support."""
        try:
            # Start streaming
            stream = await self.dispatcher.process_task_streaming(task)

            artifact_parts: List[Part] = []
            chunk_count = 0

            async for chunk in stream:
                chunk_count += 1

                if isinstance(chunk, str):
                    # Text chunk - A2A SDK structure
                    part = Part(root=TextPart(text=chunk))
                    artifact_parts.append(part)

                    # Send incremental update
                    artifact = new_artifact(
                        [part],
                        name=f"{self.agent_name}-stream-{chunk_count}",
                        description="Streaming response"
                    )

                    update_event = TaskArtifactUpdateEvent(
                        taskId=task.id,
                        contextId=task.contextId,
                        artifact=artifact,
                        append=True,
                        lastChunk=False,
                        kind="artifact-update",
                    )
                    await event_queue.enqueue_event(update_event)

                elif isinstance(chunk, dict):
                    # Data chunk - A2A SDK structure
                    part = Part(root=DataPart(data=chunk))
                    artifact_parts.append(part)

                    artifact = new_data_artifact(
                        chunk,
                        name=f"{self.agent_name}-data-{chunk_count}",
                    )

                    update_event = TaskArtifactUpdateEvent(
                        taskId=task.id,
                        contextId=task.contextId,
                        artifact=artifact,
                        append=True,
                        lastChunk=False,
                        kind="artifact-update",
                    )
                    await event_queue.enqueue_event(update_event)

            # Final update
            if artifact_parts:
                final_artifact = new_artifact(
                    artifact_parts,
                    name=f"{self.agent_name}-complete",
                    description="Complete response"
                )
                await updater.add_artifact(artifact_parts, name=final_artifact.name)

            await updater.complete()

        except Exception:
            raise

    async def _create_response_artifact(
        self,
        result: Any,
        task: Task,
        updater: TaskUpdater,
    ) -> None:
        """Create appropriate artifact based on result type."""
        if not result:
            # Empty response
            await updater.update_status(
                TaskState.completed,
                new_agent_text_message(
                    "Task completed successfully.",
                    task.contextId,
                    task.id,
                ),
                final=True,
            )
            return

        parts: List[Part] = []

        # Handle different result types
        if isinstance(result, str):
            # Text response
            parts.append(Part(root=TextPart(text=result)))
        elif isinstance(result, dict):
            # Structured data response
            # Add both human-readable text and machine-readable data
            if "summary" in result:
                parts.append(Part(root=TextPart(text=result["summary"])))
            parts.append(Part(root=DataPart(data=result)))
        elif isinstance(result, list):
            # List of items - convert to structured data
            parts.append(Part(root=DataPart(data={"items": result})))
        else:
            # Fallback to string representation
            parts.append(Part(root=TextPart(text=str(result))))

        # Create multi-modal artifact
        artifact = new_artifact(
            parts,
            name=f"{self.agent_name}-result",
            description=f"Response from {self.agent_name}"
        )

        await updater.add_artifact(parts, name=artifact.name)
        await updater.complete()

    async def _requires_input(self, task: Task, context: RequestContext) -> bool:
        """Check if task requires additional input from user."""
        # This could be enhanced with actual logic to detect incomplete requests
        # For now, return False to proceed with processing
        return False

    def _validate_request(self, context: RequestContext) -> bool:
        return False

    async def cancel(
        self, request: RequestContext, event_queue: EventQueue
    ) -> Task | None:
        """Cancel a running task if supported."""
        task = request.current_task

        if not task:
            raise ServerError(error=InvalidParamsError(data={"reason": "No task to cancel"}))

        # Check if task can be canceled
        if task.status.state in [TaskState.completed, TaskState.failed, TaskState.canceled, TaskState.rejected]:
            raise ServerError(
                error=UnsupportedOperationError(
                    data={"reason": f"Task in state '{task.status.state}' cannot be canceled"}
                )
            )

        # If dispatcher supports cancellation
        if hasattr(self.dispatcher, 'cancel_task'):
            try:
                await self.dispatcher.cancel_task(task.id)

                # Update task status
                updater = TaskUpdater(event_queue, task.id, task.contextId)
                await updater.update_status(
                    TaskState.canceled,
                    new_agent_text_message(
                        "Task has been canceled by user request.",
                        task.contextId,
                        task.id,
                    ),
                    final=True,
                )

                # Return updated task
                task.status = TaskStatus(state=TaskState.canceled)
                return task

            except Exception as e:
                logger.error(f"Error canceling task {task.id}: {e}")
                raise ServerError(
                    error=UnsupportedOperationError(
                        data={"reason": f"Failed to cancel task: {str(e)}"}
                    )
                )
        else:
            # Cancellation not supported by dispatcher
            raise ServerError(
                error=UnsupportedOperationError(
                    data={"reason": "Task cancellation is not supported by this agent"}
                )
            )
