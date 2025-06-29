import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ConversationState:
    """State for a conversation context."""
    context_id: str
    user_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]
    variables: Dict[str, Any]
    history: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'context_id': self.context_id,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'metadata': self.metadata,
            'variables': self.variables,
            'history': self.history
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationState':
        """Create from dictionary."""
        return cls(
            context_id=data['context_id'],
            user_id=data.get('user_id'),
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at']),
            metadata=data.get('metadata', {}),
            variables=data.get('variables', {}),
            history=data.get('history', [])
        )


class StateStorage:
    """Interface for state storage backends."""

    async def get(self, context_id: str) -> Optional[ConversationState]:
        """Get conversation state."""
        raise NotImplementedError

    async def set(self, state: ConversationState) -> None:
        """Save conversation state."""
        raise NotImplementedError

    async def delete(self, context_id: str) -> None:
        """Delete conversation state."""
        raise NotImplementedError

    async def list_contexts(self, user_id: Optional[str] = None) -> List[str]:
        """List context IDs, optionally filtered by user."""
        raise NotImplementedError


class InMemoryStorage(StateStorage):
    """In-memory state storage (not persistent)."""

    def __init__(self):
        self._states: Dict[str, ConversationState] = {}
        self._lock = asyncio.Lock()

    async def get(self, context_id: str) -> Optional[ConversationState]:
        """Get conversation state."""
        async with self._lock:
            return self._states.get(context_id)

    async def set(self, state: ConversationState) -> None:
        """Save conversation state."""
        async with self._lock:
            self._states[state.context_id] = state

    async def delete(self, context_id: str) -> None:
        """Delete conversation state."""
        async with self._lock:
            self._states.pop(context_id, None)

    async def list_contexts(self, user_id: Optional[str] = None) -> List[str]:
        """List context IDs, optionally filtered by user."""
        async with self._lock:
            if user_id:
                return [
                    ctx_id for ctx_id, state in self._states.items()
                    if state.user_id == user_id\
                ]
            return list(self._states.keys())


class FileStorage(StateStorage):
    """File-based state storage."""

    def __init__(self, storage_dir: str = "./conversation_states"):
        self.storage_dir = storage_dir
        import os
        os.makedirs(storage_dir, exist_ok=True)
        self._lock = asyncio.Lock()

    def _get_file_path(self, context_id: str) -> str:
        """Get file path for context."""
        return f"{self.storage_dir}/{context_id}.json"

    async def get(self, context_id: str) -> Optional[ConversationState]:
        """Get conversation state."""
        async with self._lock:
            file_path = self._get_file_path(context_id)
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                return ConversationState.from_dict(data)
            except FileNotFoundError:
                return None
            except Exception as e:
                logger.error(f"Error loading state {context_id}: {e}")
                return None

    async def set(self, state: ConversationState) -> None:
        """Save conversation state."""
        async with self._lock:
            file_path = self._get_file_path(state.context_id)
            try:
                with open(file_path, 'w') as f:
                    json.dump(state.to_dict(), f)
            except Exception as e:
                logger.error(f"Error saving state {state.context_id}: {e}")

    async def delete(self, context_id: str) -> None:
        """Delete conversation state."""
        async with self._lock:
            file_path = self._get_file_path(context_id)
            try:
                import os
                os.remove(file_path)
            except FileNotFoundError:
                pass
            except Exception as e:
                logger.error(f"Error deleting state {context_id}: {e}")

    async def list_contexts(self, user_id: Optional[str] = None) -> List[str]:
        """List context IDs, optionally filtered by user."""
        async with self._lock:
            import os
            contexts = []
            try:
                for filename in os.listdir(self.storage_dir):
                    if filename.endswith('.json'):
                        context_id = filename[:-5]  # Remove .json
                        if user_id:
                            # Load state to check user_id
                            state = await self.get(context_id)
                            if state and state.user_id == user_id:
                                contexts.append(context_id)
                        else:
                            contexts.append(context_id)
            except Exception as e:
                logger.error(f"Error listing contexts: {e}")
            return contexts


class ConversationContext:
    """Manage conversation context and state."""

    def __init__(self, storage: Optional[StateStorage] = None):
        self.storage = storage or InMemoryStorage()

    async def get_or_create(self, context_id: str, user_id: Optional[str] = None) -> ConversationState:
        """Get existing context or create new one."""
        state = await self.storage.get(context_id)

        if not state:
            state = ConversationState(
                context_id=context_id,
                user_id=user_id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                metadata={},
                variables={},
                history=[]
            )
            await self.storage.set(state)

        return state

    async def update_state(self, context_id: str, **kwargs) -> None:
        """Update conversation state."""
        state = await self.get_or_create(context_id)

        # Update fields
        for key, value in kwargs.items():
            if hasattr(state, key):
                setattr(state, key, value)

        state.updated_at = datetime.utcnow()
        await self.storage.set(state)

    async def add_to_history(self, context_id: str, role: str, content: str,
                           metadata: Optional[Dict[str, Any]] = None) -> None:
        """Add message to conversation history."""
        state = await self.get_or_create(context_id)

        message = {
            'role': role,
            'content': content,
            'timestamp': datetime.utcnow().isoformat(),
            'metadata': metadata or {}
        }

        state.history.append(message)

        # Limit history size to prevent unbounded growth
        if len(state.history) > 100:
            state.history = state.history[-100:]

        state.updated_at = datetime.utcnow()
        await self.storage.set(state)

    async def get_history(self, context_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get conversation history."""
        state = await self.storage.get(context_id)
        if not state:
            return []

        history = state.history
        if limit:
            history = history[-limit:]

        return history

    async def set_variable(self, context_id: str, key: str, value: Any) -> None:
        """Set a context variable."""
        state = await self.get_or_create(context_id)
        state.variables[key] = value
        state.updated_at = datetime.utcnow()
        await self.storage.set(state)

    async def get_variable(self, context_id: str, key: str, default: Any = None) -> Any:
        """Get a context variable."""
        state = await self.storage.get(context_id)
        if not state:
            return default
        return state.variables.get(key, default)

    async def set_metadata(self, context_id: str, key: str, value: Any) -> None:
        """Set context metadata."""
        state = await self.get_or_create(context_id)
        state.metadata[key] = value
        state.updated_at = datetime.utcnow()
        await self.storage.set(state)

    async def get_metadata(self, context_id: str, key: str, default: Any = None) -> Any:
        """Get context metadata."""
        state = await self.storage.get(context_id)
        if not state:
            return default
        return state.metadata.get(key, default)

    async def clear_context(self, context_id: str) -> None:
        """Clear a conversation context."""
        await self.storage.delete(context_id)

    async def cleanup_old_contexts(self, max_age_hours: int = 24) -> int:
        """Clean up contexts older than max_age_hours."""
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        cleaned = 0

        for context_id in await self.storage.list_contexts():
            state = await self.storage.get(context_id)
            if state and state.updated_at < cutoff_time:
                await self.storage.delete(context_id)
                cleaned += 1

        return cleaned


# Global context manager
_context_manager: Optional[ConversationContext] = None


def get_context_manager(storage_type: str = 'memory', **kwargs) -> ConversationContext:
    """Get or create global context manager."""
    global _context_manager

    if _context_manager is None:
        if storage_type == 'memory':
            storage = InMemoryStorage()
        elif storage_type == 'file':
            storage = FileStorage(**kwargs)
        else:
            raise ValueError(f"Unknown storage type: {storage_type}")

        _context_manager = ConversationContext(storage)

    return _context_manager


# Decorator for handlers that need state management
def stateful(storage: str = 'memory', **storage_kwargs):
    """Decorator to add state management to handlers."""
    def decorator(func):
        async def wrapper(task, *args, **kwargs):
            # Get context manager
            context = get_context_manager(storage, **storage_kwargs)

            # Extract context ID from task
            context_id = getattr(task, 'context_id', None) or task.id

            # Add context to kwargs
            kwargs['context'] = context
            kwargs['context_id'] = context_id

            # Call original function
            return await func(task, *args, **kwargs)

        return wrapper
    return decorator


# Export classes and functions
__all__ = [
    'ConversationState', 'StateStorage', 'InMemoryStorage', 'FileStorage',
    'ConversationContext', 'get_context_manager', 'stateful'
]