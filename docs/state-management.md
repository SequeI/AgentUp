# State Management

AgentUp provides comprehensive state management capabilities that enable your agents to maintain persistent conversation memory, user preferences, and long-running task data across sessions and restarts.

## Overview

State management in AgentUp allows agents to:

- **Remember conversations** across sessions and restarts
- **Learn user preferences** and adapt responses over time
- **Track long-running tasks** with pause/resume functionality
- **Share state** across multiple agent instances (with Redis)
- **Maintain context** for complex multi-turn interactions

## Storage Backends

AgentUp supports three storage backends, each optimized for different use cases:

### Memory Storage
- **Type**: `memory`
- **Persistence**: No (data lost on restart)
- **Performance**: Fastest
- **Use case**: Development and testing
- **Scalability**: Single instance only

### File Storage
- **Type**: `file`
- **Persistence**: Yes (JSON files on disk)
- **Performance**: Good for small to medium workloads
- **Use case**: Single-instance production deployments
- **Scalability**: Limited (file locking issues under high concurrency)

### Redis Storage
- **Type**: `redis`
- **Persistence**: Yes (in Redis database)
- **Performance**: Excellent for high concurrency
- **Use case**: Production deployments, distributed systems
- **Scalability**: Excellent (supports multiple agent instances)
- **Features**: TTL expiration, atomic operations, distributed access

## Configuration

Three different backends are supported for state management:
- **Redis**: For distributed, persistent state storage
- **File**: For local, file-based state storage  
- **Memory**: For in-memory state storage (not persistent)

In time more will be added, but these are the most common use cases. If something is of particular importance to you (PostgreSQL etc.), please open an issue on GitHub. AgentUp is built to be extensible, so adding new backends should be straightforward using the `StateStorage` interface.

### Redis Backend Configuration

**IMPORTANT**: Redis state management requires explicit configuration in the `state` section, even if Redis is configured in `services`.

Add Redis configuration to your `agent_config.yaml`:

```yaml
# External services configuration
services:
  redis:
    type: cache
    config:
      url: "redis://localhost:6379"

# State management - IMPORTANT: Explicit Redis configuration required
state:
  backend: redis
  ttl: 3600  # 1 hour expiration
  url: "redis://localhost:6379"          # REQUIRED: Explicit Redis URL
  key_prefix: "agentup:state:"           # REQUIRED: Key prefix for namespacing
```

**Why Explicit Configuration is Required:**
1. **Service vs State separation**: The `services.redis` is for caching, `state.redis` is for conversation persistence
2. **Different use cases**: Cache and state may use different Redis instances or configurations
3. **Namespace isolation**: State uses key prefixes to avoid conflicts with cache data

#### Production Redis Configuration

```yaml
services:
  redis:
    type: cache
    config:
      url: "${REDIS_CACHE_URL:redis://redis-cache:6379}"
      db: 1                    # Use different DB for cache
      max_connections: 20
      retry_on_timeout: true
      socket_keepalive: true

state:
  backend: redis
  url: "${REDIS_STATE_URL:redis://redis-state:6379}"
  key_prefix: "${STATE_KEY_PREFIX:agentup:state:}"
  ttl: 7200  # 2 hours
```

#### Multi-Redis Setup

Using different Redis instances for cache and state:

```yaml
services:
  # High-performance Redis for caching
  redis:
    type: cache
    config:
      url: "redis://fast-redis:6379"
      db: 0
      max_connections: 30

  # Persistent Redis for state
  redis_state:
    type: database
    config:
      url: "redis://persistent-redis:6379"
      db: 0

state:
  backend: redis
  url: "redis://persistent-redis:6379"
  key_prefix: "agentup:state:"
  ttl: 86400                  # 24 hours
```

### File Storage Configuration

Useful for local development, single-instance deployments, IoT devices, and systems with a limited footprint. JSON is used for the state files.

```yaml
state:
  backend: file
  storage_dir: "./agent_state"  # Optional, defaults to "./conversation_states"
```

### Memory Storage Configuration

Even simpler, for development and testing purposes, or when you don't need persistence.

```yaml
state:
  backend: memory
  # No additional configuration needed
```

## Using State Management in Skills

### The @stateful Decorator

To use state management in your skills, import and apply the `@stateful` decorator:

```python
from src.agent.context import stateful
from a2a.types import Task

@stateful(storage='redis', url='redis://localhost:6379', key_prefix='agentup:state:', ttl=3600)
async def my_stateful_skill(task: Task, context, context_id):
    """A skill that uses state management."""
    
    # Get conversation history
    history = await context.get_history(context_id, limit=10)
    
    # Store user preferences
    await context.set_variable(context_id, 'user_preference', 'dark_mode')
    
    # Get stored preferences
    preference = await context.get_variable(context_id, 'user_preference', 'default')
    
    # Add to conversation history
    await context.add_to_history(context_id, 'user', task.input)
    await context.add_to_history(context_id, 'assistant', response)
    
    return response
```

### Decorator Parameters

The `@stateful` decorator accepts the following parameters:

- **`storage`**: Backend type (`'memory'`, `'file'`, `'redis'`)
- **`url`**: Redis URL (Redis only)
- **`key_prefix`**: Key prefix for namespacing (Redis only)
- **`ttl`**: Time-to-live in seconds (Redis only)
- **`storage_dir`**: Directory path (File only)

**Note**: You can override the configuration in the decorator if you need to use a different Redis instance or key prefix for specific handlers. However, an agent configuration is still required, even if you override the configuration in the decorator.

```python
# For Redis backend
@stateful(storage='redis', url='redis://localhost:6379', key_prefix='agentup:state:', ttl=3600)

# For file backend  
@stateful(storage='file', storage_dir='./conversation_states')

# For memory backend
@stateful(storage='memory')
```

### Injected Parameters

When using `@stateful`, your handler function receives additional parameters:

- **`context`**: ConversationContext instance for state operations
- **`context_id`**: Unique identifier for the conversation context

## State Operations

### Working with Variables

Store and retrieve arbitrary data:

```python
# Set a variable
await context.set_variable(context_id, 'user_name', 'Alice')
await context.set_variable(context_id, 'preferences', {'theme': 'dark', 'language': 'en'})

# Get a variable with default
name = await context.get_variable(context_id, 'user_name', 'Anonymous')
prefs = await context.get_variable(context_id, 'preferences', {})
```

### Conversation History

Manage conversation history:

```python
# Add messages to history
await context.add_to_history(context_id, 'user', 'Hello!')
await context.add_to_history(context_id, 'assistant', 'Hi there!')

# Get conversation history
history = await context.get_history(context_id, limit=10)  # Last 10 messages
full_history = await context.get_history(context_id)       # All messages

# History format
for message in history:
    role = message['role']        # 'user' or 'assistant'
    content = message['content']  # Message content
    timestamp = message['timestamp']  # ISO timestamp
```

### Metadata Management

Store metadata about conversations:

```python
# Set metadata
await context.set_metadata(context_id, 'user_id', 'user_123')
await context.set_metadata(context_id, 'session_start', datetime.utcnow().isoformat())

# Get metadata
user_id = await context.get_metadata(context_id, 'user_id')
start_time = await context.get_metadata(context_id, 'session_start')
```

### Context Management

```python
# Get or create context
state = await context.get_or_create(context_id, user_id='user_123')

# Clear a context (delete all data)
await context.clear_context(context_id)

# Cleanup old contexts (useful for maintenance)
cleaned_count = await context.cleanup_old_contexts(max_age_hours=24)
```

## Creating Stateful Skills

### Using AgentUp CLI

When creating skills with the CLI, enable state management:

```bash
agentup skill create

# Interactive prompts:
# ? Skill name: Conversation Memory Assistant
# ? Enable state management? Yes
# ? Storage backend: redis
```

This generates a handler with the `@stateful` decorator already configured.

### Manual Implementation

Create a stateful AI assistant:

```python
from src.agent.context import stateful
from src.agent.handlers import register_handler
from a2a.types import Task
from datetime import datetime

@register_handler("memory_assistant")
@stateful(storage='redis', url='redis://localhost:6379', key_prefix='agentup:state:', ttl=3600)
async def memory_assistant(task: Task, context, context_id):
    """AI assistant with conversation memory."""
    
    # Extract user message
    user_message = extract_user_message(task)
    
    # Get conversation history and user data
    history = await context.get_history(context_id, limit=5)
    interaction_count = await context.get_variable(context_id, 'interaction_count', 0)
    user_preferences = await context.get_variable(context_id, 'preferences', {})
    
    # Update interaction count
    await context.set_variable(context_id, 'interaction_count', interaction_count + 1)
    
    # Add current message to history
    await context.add_to_history(context_id, 'user', user_message)
    
    # Generate context-aware response
    if 'remember' in user_message.lower() and len(history) > 0:
        recent_topics = [msg['content'] for msg in history[-3:] if msg['role'] == 'user']
        response = f"I remember our conversation! Recently you asked about: {', '.join(recent_topics)}"
    else:
        response = f"Hello! This is our interaction #{interaction_count + 1}. How can I help you?"
    
    # Store response in history
    await context.add_to_history(context_id, 'assistant', response)
    
    # Update metadata
    await context.set_metadata(context_id, 'last_interaction', datetime.utcnow().isoformat())
    
    return response

def extract_user_message(task):
    """Extract text message from A2A task."""
    if hasattr(task, 'message') and task.message and hasattr(task.message, 'parts'):
        for part in task.message.parts:
            if hasattr(part, 'text'):
                return part.text
    return "No message content"
```

## Common Patterns

### User Preference Learning

```python
@stateful(storage='redis')
async def learning_assistant(task: Task, context, context_id):
    user_message = extract_user_message(task)
    
    # Get existing preferences
    preferences = await context.get_variable(context_id, 'preferences', {})
    
    # Learn from user input
    if 'python' in user_message.lower():
        preferences['interests'] = preferences.get('interests', [])
        if 'programming' not in preferences['interests']:
            preferences['interests'].append('programming')
    
    # Store updated preferences
    await context.set_variable(context_id, 'preferences', preferences)
    
    # Use preferences in response
    if 'programming' in preferences.get('interests', []):
        response = "I see you're interested in programming! Let me help with that."
    else:
        response = "How can I assist you today?"
    
    return response
```

### Long-Running Task Management

```python
@stateful(storage='redis')
async def task_manager(task: Task, context, context_id):
    user_message = extract_user_message(task)
    
    # Get current task state
    current_task = await context.get_variable(context_id, 'current_task', None)
    
    if user_message.lower().startswith('start task'):
        # Initialize new task
        task_data = {
            'id': str(uuid.uuid4()),
            'steps': ['Step 1', 'Step 2', 'Step 3'],
            'current_step': 0,
            'status': 'in_progress',
            'started_at': datetime.utcnow().isoformat()
        }
        await context.set_variable(context_id, 'current_task', task_data)
        return f"Started new task: {task_data['id']}"
    
    elif current_task and user_message.lower() == 'next step':
        # Advance task
        current_task['current_step'] += 1
        if current_task['current_step'] >= len(current_task['steps']):
            current_task['status'] = 'completed'
            response = "Task completed!"
        else:
            response = f"Advanced to step {current_task['current_step'] + 1}"
        
        await context.set_variable(context_id, 'current_task', current_task)
        return response
    
    else:
        return "Say 'start task' to begin or 'next step' to continue."
```

## Best Practices

### Performance

1. **Limit History Size**: Use the `limit` parameter when retrieving history
2. **Use TTL**: Set appropriate TTL values for Redis to prevent unbounded growth
3. **Batch Operations**: Group multiple state operations when possible
4. **Choose Right Backend**: Use Redis for production, file for development

### Data Management

1. **Namespace Keys**: Use meaningful context IDs to avoid collisions
2. **Clean Up**: Implement cleanup routines for old conversations
3. **Handle Errors**: Always handle state operation failures gracefully
4. **Validate Data**: Validate data before storing to prevent corruption

### Security

1. **User Isolation**: Ensure context IDs prevent cross-user data access
2. **Sensitive Data**: Be careful storing sensitive information in state
3. **Redis Security**: Use Redis AUTH and network security in production
4. **Data Encryption**: Consider encrypting sensitive state data

## Testing State Management

### Unit Testing

```python
import pytest
from src.agent.context import ConversationContext, InMemoryStorage

@pytest.mark.asyncio
async def test_conversation_memory():
    # Use in-memory storage for testing
    storage = InMemoryStorage()
    context = ConversationContext(storage)
    
    context_id = "test_context"
    
    # Test basic operations
    await context.set_variable(context_id, "test_key", "test_value")
    value = await context.get_variable(context_id, "test_key")
    assert value == "test_value"
    
    # Test conversation history
    await context.add_to_history(context_id, "user", "Hello")
    history = await context.get_history(context_id)
    assert len(history) == 1
    assert history[0]["content"] == "Hello"
```

### Integration Testing

Use the provided test scripts:

```bash
# Test memory storage
python test_memory_storage.py

# Test file storage  
python test_file_storage.py

# Test Redis storage (requires Redis server)
python test_redis_storage.py
```

## Environment-Specific Configurations

### Development Environment

```yaml
state:
  backend: file
  storage_dir: "./dev_conversations"
```

### Testing Environment

```yaml
state:
  backend: memory
  # Fast, isolated, no persistence needed
```

### Production Environment

```yaml
services:
  redis:
    type: cache
    config:
      url: "${REDIS_URL:redis://redis-server:6379}"

state:
  backend: redis
  url: "${REDIS_URL:redis://redis-server:6379}"
  key_prefix: "${REDIS_KEY_PREFIX:agentup:state:}"
  ttl: 7200  # 2 hours
```

## Configuration Issues and Solutions

### Issue 1: State Not Persisting

**Problem**: Default handlers don't use state management

**Solution**: Apply `@stateful` decorator to your handlers:

```python
# ❌ Default handler - no state management
async def ai_assistant(task: Task):
    return "I don't remember conversations"

# ✅ Stateful handler - persistent memory
@stateful(storage='redis', url='redis://localhost:6379', key_prefix='agentup:state:', ttl=3600)
async def ai_assistant(task: Task, context, context_id):
    history = await context.get_history(context_id)
    return f"I remember our {len(history)} previous interactions"
```

### Issue 2: Redis Connection Failed

**Problem**: Missing explicit Redis URL in state configuration

**Solution**: Add explicit Redis configuration:

```yaml
# ❌ INSUFFICIENT - Will not work
state:
  backend: redis
  ttl: 3600

# ✅ CORRECT - Required for state management
state:
  backend: redis
  ttl: 3600
  url: "redis://localhost:6379"          # This line is critical
  key_prefix: "agentup:state:"
```

### Issue 3: Import Error

**Problem**: Cannot import stateful decorator

**Solution**: Use correct import path:

```python
# ✅ Correct import
from src.agent.context import stateful

# ❌ Wrong - will fail
from agent.context import stateful
from .context import stateful
```

## Troubleshooting

### Common Issues

1. **Redis Connection Failed**
   - Ensure Redis server is running: `redis-server`
   - Check Redis URL in configuration
   - Install Redis client: `pip install redis`

2. **State Not Persisting**
   - Verify `@stateful` decorator is applied to handlers
   - Check that state configuration is in `agent_config.yaml`
   - Ensure backend is properly configured

3. **Memory Usage Growing**
   - Set appropriate TTL values
   - Implement cleanup routines
   - Monitor conversation history size

4. **Handler Not Using State**
   - Import: `from src.agent.context import stateful`
   - Apply decorator with correct parameters
   - Ensure handler signature includes `context` and `context_id`

### Configuration Validation

Use this script to validate your configuration:

```python
import yaml

def validate_state_config():
    with open('agent_config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    state_cfg = config.get('state', {})
    if not state_cfg:
        print("❌ No state configuration found")
        return False
    
    backend = state_cfg.get('backend')
    print(f"✅ Backend: {backend}")
    
    if backend == 'redis':
        url = state_cfg.get('url')
        prefix = state_cfg.get('key_prefix')
        ttl = state_cfg.get('ttl')
        
        if not url:
            print("❌ Missing Redis URL")
            return False
        if not prefix:
            print("❌ Missing key prefix")
            return False
        
        print(f"✅ Redis URL: {url}")
        print(f"✅ Key prefix: {prefix}")
        print(f"✅ TTL: {ttl}")
    
    return True

if __name__ == "__main__":
    validate_state_config()
```

### Test State Operations

```python
import asyncio
from src.agent.context import get_context_manager

async def test_state():
    # Load your config
    import yaml
    with open('agent_config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    state_cfg = config['state']
    backend = state_cfg['backend']
    
    if backend == 'redis':
        context_manager = get_context_manager(
            'redis',
            url=state_cfg['url'],
            key_prefix=state_cfg['key_prefix'],
            ttl=state_cfg['ttl']
        )
    else:
        context_manager = get_context_manager(backend)
    
    # Test basic operations
    test_id = "config_test"
    await context_manager.set_variable(test_id, "test", "success")
    value = await context_manager.get_variable(test_id, "test")
    
    print(f"State test: {value}")
    await context_manager.clear_context(test_id)

if __name__ == "__main__":
    asyncio.run(test_state())
```

### Debugging

Enable debug logging to see state operations:

```python
import logging
logging.getLogger('src.agent.context').setLevel(logging.DEBUG)
```

Check Redis data directly:

```bash
redis-cli
> KEYS agentup:state:*
> GET agentup:state:your_context_id
```

## Migration Between Backends

### From Memory to File

```yaml
# Change configuration
state:
  backend: file  # Changed from memory
  storage_dir: "./conversation_states"

# Update handlers
@stateful(storage='file', storage_dir='./conversation_states')  # Updated decorator
```

### From File to Redis

```yaml
# Add Redis service
services:
  redis:
    type: cache
    config:
      url: "redis://localhost:6379"

# Update state configuration
state:
  backend: redis  # Changed from file
  url: "redis://localhost:6379"
  key_prefix: "agentup:state:"
  ttl: 3600

# Update handlers
@stateful(storage='redis', url='redis://localhost:6379', key_prefix='agentup:state:', ttl=3600)
```

### Upgrading from Previous Versions

If upgrading from AgentUp versions without state management:

1. **Add state configuration** to `agent_config.yaml`
2. **Update handlers** to use `@stateful` decorator
3. **Test with existing agent** to ensure compatibility

## Examples

See the complete examples in the repository:

- [`demo_conversation_memory_skill.py`](../demo_conversation_memory_skill.py) - Conversation memory demonstration
- [`demo_multi_session_task_skill.py`](../demo_multi_session_task_skill.py) - Multi-session task management
- [`test_*_storage.py`](../) - Comprehensive testing scripts

## Best Practices

### Configuration Management

1. **Use environment variables** for production URLs
2. **Set appropriate TTL** values (1-24 hours typically)
3. **Use meaningful key prefixes** for multi-tenant scenarios
4. **Keep development configs simple** (file or memory)

### Handler Design

1. **Apply `@stateful` selectively** - not all handlers need state
2. **Match decorator parameters** to configuration
3. **Handle state gracefully** - don't fail if state is unavailable
4. **Use meaningful context IDs** - typically user or session based

### Testing

1. **Test with all backends** during development
2. **Use memory backend** for unit tests
3. **Validate configuration** before deployment
4. **Monitor Redis** connections and memory usage

## Next Steps

1. **Choose your backend** based on deployment needs
2. **Configure agent_config.yaml** with explicit Redis settings
3. **Apply @stateful decorator** to handlers that need memory
4. **Test with provided scripts** to verify functionality
5. **Monitor and optimize** based on usage patterns