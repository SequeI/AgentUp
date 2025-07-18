# AgentUp

[![Tests](https://github.com/RedDotDocket/AgentUp/actions/workflows/ci.yml/badge.svg)](https://github.com/RedDotRocket/AgentUp/actions/workflows/ci.yml)
[![Python Version](https://img.shields.io/pypi/pyversions/AgentUp.svg)](https://pypi.org/project/AgentUp/)

<p align="center">
  <img src="assets/agentup_logo.png" alt="AgentUp Logo" width="400"/>
</p>

## Core Philosophy

AgentUp is an Agent framework that empowers developers to build any AI agent they require through a configuration-driven architecture that isolates custom functionality from the core engine, allowing seamless framework upgrades without breaking your agents. With a vibrant open community contributing plugins, developers can leverage shared components or roll their own, all while maintaining consistency across deployments. By decoupling configuration, plugins, and core functionality, AgentUp accelerates development of scalable, maintainable AI agents that evolve with your needs.

## Feature-Rich, Out of the Box

AgentUp provides everything you need to build production-ready AI agents without the guesswork. Its middleware handles rate limiting, caching, input validation, authentication, and more—so you can focus on your Agent's unique capabilities instead of reinventing common patterns.

### Core Features

**Plugin System**
- Build anything with our flexible plugin architecture:
  - Create custom capabilities without modifying core code
  - Leverage community plugins from the open ecosystem (system tools, image processing, etc.)
  - Install plugins with `pip install / uv add <name>` (pin versions if needed!)
  - Version plugins independently from the core framework
  - All plugins are gated by capabilities scopes, ensuring secure access control

**State Management**
- Track conversations persistently with configurable TTL and history
- Choose your storage backend to match your infrastructure:
  - File system for simple deployments
  - Database for structured queries
  - Redis or Valkey for high-performance caching

**Security & Access Control**
- Built-in authentication, authorization, and secure communication patterns
- Granular permission management through scope hierarchy:
  - Control exactly what each plugin can access
  - Seamless integration with OAuth2 and bearer token systems
  - Fine-tune capabilities at every level

**Asynchronous Operations**
- Manage long-running tasks with built-in state tracking
- Push notifications for real-time updates
- Non-blocking execution for better performance

**Agent Discovery**
- Enable agent-to-agent communication through A2A Agent Cards
- Make your agents discoverable and interoperable
- Build multi-agent systems with ease

**AI Provider Flexibility**
- Connect to multiple AI providers without changing your code:
  - OpenAI for GPT models
  - Anthropic for Claude
  - Local models through OpenAI-compatible APIs (Ollama)

**MCP Integration**
- Leverage the growing MCP ecosystem as a client:
  - All MCP servers are gated by capabilities scopes
  - Easily add AgentUp Authentication
  - Expose AgentUp capabilities as MCP endpoints

**CLI-Driven Development**
- Scaffold, develop, and deploy agents entirely from the command line:
  - `agentup agent create` - Create new agents from templates
  - `agentup agent serve` - Start a local development server
  - `agentup plugin` - Generate, install, and cookiecutter new plugin projects

## Project Status

AgentUp is in active development and not yet ready for production use. There will be lots of bugs,
Types need 'tightening up', and the API is still evolving.

## Contributing

I could do with lots of help, so if you are interested in contributing, please get in touch! I always
value contributions, whether they are code, documentation, or just feedback on the project, and wil
do my best to make all feel welcome.

## ⭐ Show Your Support

If you find this project useful or interesting, please consider giving it a star! It helps me know that people are finding value in this work and motivates me to keep improving it.

[![GitHub stars](https://img.shields.io/github/stars/RedDotRocker/AgentUp.svg?style=social&label=Star)](https://github.com/RedDotRocker/AgentUp)

## Quick Start

### Installation

Install AgentUp using pip:
```bash
pip install agentup
```

### Creating Agents

Generate a new agent project with interactive configuration:
```bash
agentup agent create my-agent
cd my-agent
```

Select from available options.

### Starting Development

Launch the development server:
```bash
agentup agent serve
```

Your agent runs at `http://localhost:8000`

From here, you really should read the [documentation](https://agentup.readthedocs.io/en/latest/) to understand how to configure your agent, add plugins, and customize its behavior, there are lots of examples and guides to help you get started!


## License

This project is licensed under the Apache 2.0 License.

## Community

Report bugs and request features through GitHub issues. Community support and development discussions are available through project channels. The documentation provides comprehensive guides and API reference materials along with sample agents and plugins for common use cases.

AgentUp provides a practical approach to AI agent development, balancing functionality with developer productivity. The standards-based design ensures compatibility with the A2A ecosystem while maintaining flexibility for custom implementations.