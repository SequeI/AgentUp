# AgentUp!

**The fastest way to bootstrap full capability A2A-compliant AI agents**

**AgentUp!** is a scaffolding framework that rapidly bootstraps AI agents, giving you everything you
need right out of the box. With AgentUp, you can quickly map AI agents that support multiple AI providers,
Tools (skills), middleware layers, multi-modal input/output, streaming / non-streaming messages,
MCP, authentication, state management, push notifications, and a bucket load more, all 
via a config driven approach using an intuitive command-line interface.

There is too much to cover in this README, so we recommend you check out the
[AgentUp! documentation](https://agentup.readthedocs.io/en/latest/) for
a comprehensive guide on how to use the framework.

For now though, here is a quick way of getting you a running agent in just a few minutes!

## Quick Start (3 minutes to running agent)

### Installation

Install the AgentUp CLI:

```bash
pip install agentup
```

### Create Your First Agent

AgentUp provides 4 templates to get you started quickly:

- **minimal** - Barebone agent (no AI, no external dependencies)
- **standard** - AI-powered agent with MCP (recommended)  
- **full** - Enterprise agent with all features
- **demo** - Example agent showcasing capabilities

To create your first agent, run:

```bash
# Interactive mode (recommended for beginners)
agentup agent create my_first_agent

# Quick standard agent
agentup agent create --quick my_first_agent

# Specific template
agentup agent create --template demo my_demo_agent
```

This will create a new directory with a complete A2A-compliant agent project.

### Configure Your Agent

Navigate to the newly created agent directory:

```bash
cd my_first_agent
```

### Edit the Agent Configuration

Open the `agent_config.yaml` file in your favorite text editor let's configure your agent to do something useful!

First let's add some an AI provider. For example, to use OpenAI, add the following:

```yaml

## Templates

### Minimal Template
- Echo skill for basic text processing
- No AI, no external dependencies
- Perfect for simple automation or webhooks
- Lightweight and fast

### Standard Template (Recommended)
- AI-powered assistant with OpenAI integration
- MCP (Model Context Protocol) filesystem access
- Authentication and basic middleware
- Great for most AI agent use cases

### Full Template
- Enterprise-ready with all features enabled
- Multiple MCP servers (filesystem, GitHub)
- Database (PostgreSQL) and cache (Valkey) support
- Advanced middleware (rate limiting, caching, retry)
- State management and monitoring
- Perfect for production deployments

### Demo Template
- 4 pre-built example skills:
  - File Assistant (MCP file operations)
  - Weather Bot (function calling example)
  - Code Analyzer (repository analysis)
  - Joke Teller (simple conversation)
- Great for learning and showcasing capabilities

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Run the test suite: `uv run python run_tests.py`
5. Submit a pull request

## License

This project is licensed under the Apache 2 License - see the LICENSE file for details.

