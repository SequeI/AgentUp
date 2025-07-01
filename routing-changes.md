# Skill and Routing Refinement for AgentUp Architecture

This document outlines the new routing architecture for AgentUp, focusing on skills and their invocation methods. The goal is to simplify skill management while enhancing flexibility and AI integration.

AgentUp supports a **skills-based architecture** where skills are Python functions which are registered with decorators @register_handler("skill_name").

Skills can be invoked directly via keyword or pattern matching, or through AI routing where an LLM selects the appropriate skill based on natural language intent. Alongside Skills are also MCP servers, which are only selected by the LLM, again based on natural language intent.

1. **Direct routing** via keyword/pattern matching
2. **AI routing** via an LLM choosing among all available skills based on natural-language intent

Each skill is registered with a decorator:

```python
@register_handler("echo")
async def handle_echo(task: Task) -> str:
    …
```

If the skill is registered with the `@ai_function` decorator, it will be available for AI routing as well.

```python
@ai_function(
    description="Echo back user messages with optional modifications",
    parameters={
        "message": {"type": "string", "description": "Message to echo back"},
        "format": {"type": "string", "description": "Format style (uppercase, lowercase, title)"}
    }
)
@rate_limited(requests_per_minute=120)
@timed()
async def handle_echo(task: Task) -> str:
```

# Changes Overview

## New Skill Configuration

Skills are declared in `agent_config.yaml` the same as the current implementation.

Each entry must include:

* **skill\_id** (string) — unique, matches the decorator
* **name**, **description** — metadata for humans & the LLM
* **input\_mode**, **output\_mode** — e.g. `text` or `json`
* **keywords** (optional) — exact tokens for direct routing
* **patterns** (optional) — regexes for direct routing

The routing logic is now becomes based on implicit based on the presence of `keywords` or `patterns`. If neither is present, the skill is only available via AI routing. AI however, may select any skill based on its name, description, and input schema.

This means no more `routing_mode` field in each skill. Instead, the routing behavior is determined by the presence of `keywords` and `patterns`. If it has keywords or patterns, it can be directly routed to (when matched). If not, it is only available for AI routing.

Let's use the following example skills to illustrate this:

```yaml
skills:
  - skill_id: get_weather
    name: Weather Report Assistant
    description: Provides current weather information
    input_mode: text
    output_mode: text

  - skill_id: system_info
    name: System Information Assistant
    description: Reports CPU, memory, and disk usage
    input_mode: text
    output_mode: text
    keywords:
      - system
      - memory
      - cpu
      - disk
    patterns:
      - .*system.*info.*

  - skill_id: file_reader
    name: File Reader Assistant
    description: Reads contents of a file
    input_mode: text
    output_mode: text
```

Using the skills defined above, here are some example interactions:

1. **“What’s the weather like in London?”**
   No direct keywords / patterns matched → AI routing → LLM invokes `get_weather`.

2. **“I need system info and how much memory is available?”**
   Matches `system_info` keywords → direct call to `handle_system_info`.

3. **“How powerful is your machine?”**
   No keyword match → AI routing → LLM infers `system_info` → invokes handler.

So to summarize, the routing behavior is now implicit:

- Direct Routing

1. **Match** incoming text against each skill’s `keywords` and `patterns`.
2. If **exactly one** skill matches, invoke its handler immediately.
3. If **multiple** skills match, see section "Prioritization & Disambiguation" below.

- AI Routing

* If **no direct match** or the matched skill has no keywords/patterns, the message is sent to the LLM.
* The LLM knows all skills as tools, with name, description, and parameter schema.
* The LLM returns a structured function invocation; the agent executes that handler.


## Configuration Changes

* **Removed**: explicit `routing_mode` in each skill
* **Removed**: explicit `routing` top level key
* **New**: routing behavior is implicit based on presence of `keywords`/`patterns` or lack thereof
* **All** all skills remain available to the LLM, regardless of direct-routing eligibility

---

## AI Provider Configuration

AI providers are now configured under a single `ai_provider` section in `agent_config.yaml`. This allows for a more unified configuration approach, separating LLMs from the services section.

In `agent_config.yaml`:

```yaml
ai_provider:
    provider: openai
    api_key: ${OPENAI_API_KEY}
    model: gpt-4o-mini
    temperature: 0.7
    max_tokens: 1000
    top_p: 1.0
    base_url: https://api.openai.com/v1
```

```yaml
ai_provider:
    provider: ollama 
    model: llama3
    temperature: 0.7
    max_tokens: 1000
    top_p: 1.0
    base_url: http://localhost:11434/v1
```

```yaml
ai_provider:
    provider: antropic
    api_key: ${ANTHROPIC_API_KEY}
    model: claude-sonnet3.7
    temperature: 0.7
    max_tokens: 1000
    top_p: 1.0
    base_url: https://api.anthropic.com/v1
```

The `ai_provider` section replaces the previous `llm` configuration, allowing for a more streamlined approach to AI integration. The `services` section, which previously contained LLM configurations, now focuses on other external services only

mcp servers are still configured under `mcp:` so no changes are needed there.

## Configuration Changes Summary

* **Removed**: `llm` section in `services`
* **New**: `ai_provider` section for unified AI configuration
* **No changes** to `mcp` server configuration

## CLI Changes

### Remove AI Provider Selection During Agent Creation

During Agent Creation there is a services section that allows the user to select AI providers like OpenAI, Anthropic, and Ollama. This should **be removed** as the AI provider is now configured in the `agent_config.yaml` file under the `ai_provider` section.

```bash
$ agentup agent create --template minimal
Select features to include: (Use arrow keys to move, <space> to select, <a> to toggle, <i> to invert)
» ○ External Services (LLM, Database, Cache)

Selecting the "External Services" option gives you:

? Select external services: (Use arrow keys to move, <space> to select, <a> to toggle, <i> to invert)
 » ○ OpenAI <-- should be removed
   ○ Anthropic <-- should be removed
   ○ Ollama <-- should be removed
   ○ PostgreSQL
   ○ Redis
   ○ Custom API
```

### Add new AI Provider section during Agent Creation

Instead we should do this:

```bash
$ agentup agent create --template minimal
----------------------------------------
Create your AI agent:
----------------------------------------
? Agent name: myagemt
? Description: AI Agent myagemt Project.
? Would you like to customize the features? Yes
? Select features to include: (Use arrow keys to move, <space> to select, <a> to toggle, <i> to invert) 
   ○ Middleware System
   ○ Multi-modal Processing
   ○ External Services (Database, Cache)
   ○ State Management
   ○ AI Provider <-- new value
   ○ Authentication
   ○ Monitoring & Observability
   ○ Testing Framework
   ○ Deployment Tools

<user selects "AI Provider">
? Please select an AI Provider:
   ○ OpenAI
   ○ Anthropic
   ○ Ollama
   ○ <any extra providers added in the future>
```

For now we can let the user set their own model and keys etc in the `agent_config.yaml` file.

So selecting 'OpenAI' would then result in a llm_provider configuration value for OpenAI being in the agent_config.yaml file:

## New Change for Skill Creation - AI Routing Mode

When creating a new skill, the CLI should now prompt for the routing mode and allow the user to select between:
1. **Direct** - keyword/pattern matching
2. **AI** - intelligent routing using an LLM

```bash
$ agentup skill create
AgentUp - Interactive Skill Generator
Let's add a new skill to your agent.

? Skill name: ai_skill
? Skill ID: ai_skill
? Description: Handle ai_skill requests
? Input mode: text
? Output mode: text
? Routing mode: AI (intelligent routing using LLM)
? Configure advanced options? Yes
? Set skill priority? Yes
? Priority (lower number = higher priority, default: 100): 100
? Add tags for Skill categorization? Yes
? Tags (comma-separated, e.g.: assistant, file, utility): my ai skills
? Does this skill use external APIs? No
? Configure middleware? Yes
? Select middleware: done (3 selections)
? Requests per minute: 60
? Max retries: 3
? Enable state management? Yes
? Storage backend: file

AI Routing Mode
Using AI routing - no keywords or patterns needed.
✓ Updated agent_config.yaml
✓ Updated routing configuration
✓ Created handler file: src/agent/handlers/ai_skill_handler.py


Skill added successfully!

Skill ID: ai_skill

Next steps:
1. Implement the handler in src/agent/handlers/ai_skill_handler.py
```

## New Change for Skill Creation - Direct Routing Mode

When creating a new skill with direct routing, the CLI should prompt for keywords and patterns to match against user input. The routing mode should be set to "Direct (keyword/pattern matching)".
This allows the skill to be invoked directly based on specific keywords or regex patterns.

The direct routing mode should also keep the `@ai_function` decorator, as it is still useful for skills that may use AI in the future.

```bash
$ agentup skill create

AgentUp - Interactive Skill Generator
Let's add a new skill to your agent.

? Skill name: direct-skill
? Skill ID: direct_skill
? Description: Handle direct-skill requests
? Input mode: text
? Output mode: text
? Routing mode: Direct (keyword/pattern matching)
? Configure advanced options? Yes
? Set skill priority? Yes
? Priority (lower number = higher priority, default: 100): 100
? Does this skill use external APIs? Yes
? Service name (e.g., openai, weather_api): paypal
? Requires API key? Yes
? Environment variable name: PAYPAL_API_KEY
? Configure middleware? Yes
? Select middleware: [Rate limiting]
? Requests per minute: 60
? Enable state management? Yes
? Storage backend: file
? Configure routing rules for this skill? Yes

Routing Configuration
Configure how users will trigger this skill.
? Keywords (comma-separated):  Words that will trigger this skill direct skill, direct_skill, direct-skill
? Add regex patterns for advanced routing? Yes
? Regex pattern (or press Enter to finish):  e.g., '^(process|analyze).*' to match text starting with 'process' or 'analyze' *direct
? Add another pattern? No
✓ Updated agent_config.yaml
✓ Created handler file: src/agent/handlers/direct_skill_handler.py

Skill added successfully!

Skill ID: direct_skill

Next steps:
1. Implement the handler in src/agent/handlers/direct_skill_handler.py
```

src/agent/handlers/direct_skill_handler.py

```python
import os
import httpx
import logging
from typing import Dict, Any
from a2a.types import Task

from ..handlers import register_handler
from ..services import get_services
from ..messages import MessageProcessor, ConversationContext
from ..function_dispatcher import ai_function
from ..middleware import rate_limited
from ..context import stateful

logger = logging.getLogger(__name__)


@register_handler("direct_skill")
@ai_function(
    description="Handle direct-skill requests",
    parameters={
        "user_input": {"type": "string", "description": "The user's request or query"}
    }
)
@stateful(storage='')
@rate_limited(requests_per_minute=60)
async def handle_direct_skill(task: Task, context, context_id) -> str:
    """Handle direct-skill requests"""
# TODO: Get API configuration
    # api_key = os.getenv("PAYPAL_API_KEY")

# Extract user message using A2A-compliant message processing
    messages = MessageProcessor.extract_messages(task)
    latest_message = MessageProcessor.get_latest_user_message(messages)

    if not latest_message:
        return "Please provide input for direct-skill."

    content = latest_message.get("content", "") if isinstance(latest_message, dict) else getattr(latest_message, "content", "")

    # Update conversation context
    ConversationContext.increment_message_count(task.id)

# Get services for external API integration
    services = get_services()

    # TODO: Implement your API integration here
    # api_key = os.getenv("PAYPAL_API_KEY")
    # Example: api_data = await fetch_api_data(content)

# TODO: Implement your skill logic here
    # Process the user input: {content}

    return f"Processed request for direct-skill: {content}"
```

## Example Configurations


```yaml
# AgentUp Agent Configuration - Created from Minimal Template

#  Agent Information
agent:
  name: test
  description: AI Agent test Project.
  version: 0.1.0


# Core skills configuration
skills:
  - skill_id: echo
    name: Echo
    description: Echo back the input text
    tags: [echo, basic, simple]
    input_mode: text
    output_mode: text
    keywords: [echo, repeat, say]
    patterns: ['.echo']  # Catch-all for minimal template
    priority: 50
  - skill_id: ai_assistant
    name: AI Assistant
    description: AI-powered assistant for various tasks
    tags: [ai, assistant, helper]  # Tags for use within the @ai_function decorator
    # No keywords or patterns defined, only available via AI routing
    input_mode: text
    output_mode: text
    priority: 100
  - skill_id: weather_report
    name: Weather Report Assistant
    description: Provides current weather information
    input_mode: text
    output_mode: text
    keywords: [weather, forecast, temperature]
    patterns: ['.*weather.*', '.*forecast.*']  # Regex patterns for direct routing
    priority: 80
  - skill_id: system_info
    name: System Information Assistant
    description: Reports CPU, memory, and disk usage
    input_mode: text
    output_mode: text
    keywords: [system, memory, cpu, disk]
    patterns: ['.*system.*info.*']  # Regex patterns for direct routing
    priority: 70
  - skill_id: file_reader
    name: File Reader Assistant
    description: Reads contents of a file
    tags: [file, reader, utility]  # Tags for use within the @ai_function decorator
    # No keywords or patterns defined, only available via AI routing
    input_mode: text
    output_mode: text
    priority: 60

# Registry skills section # Security configuration (no changes required)
registry_skills: []

# Security configuration (no changes required)
security:
  enabled: true
  type: "api_key"
  api_key:
    header_name: "X-API-Key"
    location: "header"  # Options: header, query, cookie
    # The below is randomly generated, and not hardcoded, please change if relevant
    keys:
      - "upzhFLX3xhojq3MC5JiE0fXSYkcwazX_"

# AI configuration
ai_provider:
    provider: openai
    api_key: ${OPENAI_API_KEY}  # Set your OpenAI API key in
    model: gpt-4o-mini
    temperature: 0.7
    max_tokens: 1000
    top_p: 1.0
    base_url: https://api.openai.com/v1

# Services configuration (no changes required, just remove LLM specifics)
services:
  postgres:
    type: database
    config:
      connection_url: '${DATABASE_URL:postgresql://user:pass@localhost/db}'
  redis:
    type: cache
    config:
      url: '${REDIS_CACHE_URL:redis://localhost:6379}'
      db: 1
      max_connections: 20
      retry_on_timeout: true

# Middleware configuration (no changes required)
middleware:
  - name: logged
    params:
      log_level: 20  # INFO level
  - name: timed
    params: {}

# Push notifications configuration (no changes required)
push_notifications:
  enabled: true
  backend: memory             # Simple memory backend for minimal template
  validate_urls: false        # Disable validation for minimal setup

# State management configuration (no changes required)
state:
  backend: memory           # Simple memory state for minimal template
  ttl: 3600  # 1 hour
```

## Further Changes & Improvements

### Prioritization & Disambiguation

* **Priority scores** on skills to break ties when multiple direct matches occur.
* Or, prompt the user with a short disambiguation (“Did you mean X or Y?”).

### Fallback & Default Handler

* Define a `fallback` skill that either:

  * Asks a clarifying question
  * Returns a friendly “I’m not sure” message

### Configuration Validation

* At startup, validate that each `skill_id` has a corresponding handler.
* Detect conflicting or overlapping patterns/keywords and warn the developer.

### Pattern-Matching Engine

* Upgrade to a multi-keyword engine (e.g. Aho–Corasick) or light NLP intent matcher to improve direct-routing accuracy.

### Graceful Degradation

* If the LLM provider fails (timeout, rate-limit), fall back to:

  1. A simpler keyword search over all skill names/descriptions
  2. The `fallback` skill

### Security & Permissions

* Audit and sanitize all inputs to prevent injection or unauthorized access.


# Other Considerations

## Migration

You DO NOT need to migrate a existing skills or agent configurations.

There is NO NEED for backwards compatibility, as this is a pre-release sofware,
with no existing users or agents.

Skills should still be exposed within the AgentCard (see /src/agent/api.py)

The implementation must adhere to the @a2a_specification.

Ensure all jinja2 templates are updated to reflect the new routing architecture,
especially in the `agent_config.yaml` templates in `src/agent/templates/`.

## Documentation

The documentation will be updated to reflect these changes, including:
* New skill creation process
* AI routing vs direct routing
* Configuration examples
* CLI changes for skill creation

# Testing

## Unit Tests

Tests will need to be updated to reflect the new routing architecture. You can run tests using the following command `make test`.

## Integration Tests

Integration tests will need to be updated to ensure skills are correctly registered and routed. This includes:
* Testing direct routing with keywords and patterns
* Testing AI routing with LLM selection 
* Ensuring skills can be invoked correctly based on routing mode


