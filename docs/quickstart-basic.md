# Quickstart, super basic AgentUp agent

For our first example, we'll create a very simple AgentUp agent that echoes back user input. This will demonstrate the basic structure and functionality of an AgentUp agent.

There won't be any external services or complex configurations involved, or even an LLM. This is just a straightforward agent that responds to user messages.

This example will start to expose you to the core concepts of AgentUp, including:
- Agent creation and configuration
- Basic message handling
- Running the agent locally 
- Interacting with the agent via HTTP requests
- Learning how routing logic works
- Understanding the agent's response structure
- Getting a taste of the AgentUP security model

We assume you have AgentUp installed and set up. If you haven't done that yet, please refer to the [installation guide](getting-started/installation.md).

## Step 1: Create the Agent

From anywhere on your system, run the following command to create a new agent named `echo_agent`:

```bash
 agentup agent serve -c agent_config_echo.yaml