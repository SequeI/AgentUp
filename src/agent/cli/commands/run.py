import click


@click.command()
@click.option("--config", "-c", type=click.Path(exists=True), default="agentup.yml", help="Path to agent config file")
@click.option("--host", default="127.0.0.1", help="Host to bind to")
@click.option("--port", "-p", type=click.IntRange(1, 65535), default=8000, help="Port to bind to")
@click.option("--reload/--no-reload", default=True, help="Enable auto-reload")
def run(config, host, port, reload):
    """Start the development server."""
    # Import and call the original dev functionality
    from pathlib import Path

    from . import dev

    return dev.dev.callback(Path(config), host, port, reload)
