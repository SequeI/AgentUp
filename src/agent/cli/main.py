import logging
import os
from collections import OrderedDict

import click

from ..utils.version import get_version
from .commands.deploy import deploy
from .commands.init import init
from .commands.plugin import plugin
from .commands.run import run
from .commands.validate import validate


class OrderedGroup(click.Group):
    def __init__(self, name=None, commands=None, **attrs):
        super().__init__(name=name, commands=commands, **attrs)
        self.commands = OrderedDict()

    def add_command(self, cmd, name=None):
        name = name or cmd.name
        self.commands[name] = cmd

    def list_commands(self, ctx):
        return self.commands.keys()


def setup_cli_logging():
    """Sets up unified logging for the CLI using structlog if available."""

    # Check for explicit log level from environment or default to WARNING
    log_level = os.environ.get("AGENTUP_LOG_LEVEL", "WARNING").upper()

    try:
        from agent.config.logging import setup_logging
        from agent.config.model import LoggingConfig

        # Create logging config
        cli_logging_config = LoggingConfig(
            level=log_level,
            format="text",
            console={"colors": True},
            modules={
                "agent.plugins": "WARNING",
                "agent.plugins.manager": "WARNING",
                "pluggy": "WARNING",
            },
        )
        setup_logging(cli_logging_config)
    except (ImportError, Exception):
        # Fallback to standard library logging if structlog config fails
        logging.basicConfig(
            level=getattr(logging, log_level, logging.WARNING),
            format="%(message)s",
        )
        # Suppress specific noisy loggers in fallback mode
        logging.getLogger("agent.plugins").setLevel(logging.WARNING)
        logging.getLogger("agent.plugins.manager").setLevel(logging.WARNING)
        logging.getLogger("pluggy").setLevel(logging.WARNING)


@click.group(
    cls=OrderedGroup, help="AgentUp CLI - Create and Manage agents and plugins.\n\nUse one of the subcommands below."
)
@click.version_option(version=get_version(), prog_name="agentup")
def cli():
    # Set up logging for all CLI commands
    setup_cli_logging()
    """Main entry point for the AgentUp CLI."""
    pass


# Register command groups
cli.add_command(init)
cli.add_command(run)
cli.add_command(deploy)
cli.add_command(validate)
cli.add_command(plugin)


if __name__ == "__main__":
    cli()
