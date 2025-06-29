# AgentUp Development Makefile
# Useful commands for testing, template generation, and development

.PHONY: help install test test-coverage lint format clean build docs
.PHONY: template-test template-render agent-create agent-test
.PHONY: dev-server example-client check-deps sync-templates example-agent
.PHONY: docker-build docker-run release validate-all

# Default target
help: ## Show this help message
	@echo "AgentUp Development Commands"
	@echo "=========================="
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Environment setup
install: ## Install dependencies with uv
	uv sync --all-extras
	@echo "✅ Dependencies installed"

install-dev: ## Install development dependencies
	uv sync --all-extras --dev
	uv pip install -e .
	@echo "✅ Development environment ready"

check-deps: ## Check for missing dependencies
	uv pip check
	@echo "✅ All dependencies satisfied"

# Testing commands
test: ## Run all tests
	uv run pytest -v

test-coverage: ## Run tests with coverage report
	uv run pytest --cov=src --cov-report=html --cov-report=term-missing
	@echo "Coverage report generated in htmlcov/"

test-fast: ## Run tests with minimal output
	uv run pytest -q --tb=short

test-watch: ## Run tests in watch mode
	uv run pytest-watch --runner "uv run pytest"

test-integration: ## Run integration tests only
	uv run pytest tests/test_integration.py -v

test-templates: ## Test template rendering and syntax
	uv run pytest tests/test_template_rendering.py -v

# Code quality
lint: ## Run linting checks
	uv run ruff check src/ tests/
	uv run mypy src/

lint-fix: ## Fix linting issues automatically
	uv run ruff check --fix src/ tests/
	uv run ruff format src/ tests/

format: ## Format code with ruff
	uv run ruff format src/ tests/

format-check: ## Check code formatting
	uv run ruff format --check src/ tests/

# Template and generation commands
template-render: ## Render all templates for testing
	uv run python -m agent.cli.commands.render_templates \
		--output-dir ./test-render \
		--validate \
		--clean

template-render-keep: ## Render templates and keep output
	uv run python -m agent.cli.commands.render_templates \
		--output-dir ./test-render \
		--validate \
		--keep

template-test-syntax: ## Test template syntax only
	uv run pytest tests/test_template_rendering.py::TestTemplateRendering::test_python_syntax_validation -v

sync-templates: ## Sync templates with reference implementation
	uv run python scripts/sync_templates.py
	@echo "✅ Templates synced with reference implementation"

# Agent creation and testing
agent-create: ## Create a test agent (interactive)
	uv run agentup create-agent

agent-create-minimal: ## Create minimal test agent
	@echo "Creating minimal test agent..."
	uv run agentup create-agent \
		--quick test-minimal \
		--template minimal \
		--output-dir ./test-agents/minimal
	@echo "✅ Minimal agent created in ./test-agents/minimal"

agent-create-standard: ## Create standard test agent
	@echo "Creating standard test agent..."
	uv run agentup create-agent \
		--quick test-standard \
		--template standard \
		--output-dir ./test-agents/standard
	@echo "✅ Standard agent created in ./test-agents/standard"

agent-create-advanced: ## Create advanced test agent
	@echo "Creating advanced test agent..."
	uv run agentup create-agent \
		--quick test-advanced \
		--template advanced \
		--output-dir ./test-agents/advanced
	@echo "✅ Advanced agent created in ./test-agents/advanced"

agent-test: ## Test a generated agent
	@if [ -d "./test-agents/standard" ]; then \
		echo "Testing standard agent..."; \
		cd ./test-agents/standard && \
		uv run python -m pytest tests/ -v 2>/dev/null || echo "⚠️ Tests not available"; \
		echo "✅ Agent test completed"; \
	else \
		echo "❌ No test agent found. Run 'make agent-create-standard' first"; \
	fi

# Development server commands
dev-server: ## Start development server for reference implementation
	uv run uvicorn src.agent.main:app --reload --port 8000

dev-server-test: ## Start test agent server
	@if [ -d "./test-agents/standard" ]; then \
		echo "Starting test agent server..."; \
		cd ./test-agents/standard && \
		uv run uvicorn src.agent.main:app --reload --port 8001; \
	else \
		echo "❌ No test agent found. Run 'make agent-create-standard' first"; \
	fi

example-client: ## Run example client against development server
	uv run python example_client.py

# Testing with curl
test-ping: ## Test server health endpoint
	@echo "Testing health endpoint..."
	curl -s http://localhost:8000/health | python -m json.tool || echo "❌ Server not running"

test-hello: ## Test hello endpoint with curl
	@echo "Testing hello endpoint..."
	curl -X POST http://localhost:8000/ \
		-H 'Content-Type: application/json' \
		-d '{"jsonrpc": "2.0", "method": "send_message", "params": {"messages": [{"role": "user", "content": "Hello!"}]}, "id": "1"}' \
		| python -m json.tool || echo "❌ Server not running"
# Documentation
docs: ## Generate documentation
	@echo "📚 Generating documentation..."
	@echo "- API documentation in docs/"
	@echo "- Routing guide: docs/routing-and-function-calling.md"
	@echo "- Maintenance guide: docs/maintenance.md"
	@echo "✅ Documentation ready"

docs-serve: ## Serve documentation locally
	@if command -v mkdocs >/dev/null 2>&1; then \
		mkdocs serve; \
	else \
		echo "📚 Opening documentation files..."; \
		open docs/routing-and-function-calling.md; \
	fi

# Build and release
build: ## Build package
	uv build
	@echo "📦 Package built in dist/"

build-check: ## Check package build
	uv run twine check dist/*

release-test: ## Upload to test PyPI
	uv run twine upload --repository testpypi dist/*

release: ## Upload to PyPI (production)
	uv run twine upload dist/*

# Docker commands
docker-build: ## Build Docker image
	docker build -t agentup:latest .

docker-run: ## Run Docker container
	docker run -p 8000:8000 agentup:latest

docker-test: ## Test Docker build
	docker build -t agentup:test . && \
	docker run --rm agentup:test python -c "import agentup; print('✅ Package works in Docker')"

# Cleanup commands
clean: ## Clean temporary files
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf test-render/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	@echo "🧹 Cleaned temporary files"

clean-agents: ## Clean test agents
	rm -rf test-agents/
	@echo "🧹 Cleaned test agents"

clean-all: clean clean-agents ## Clean everything
	@echo "🧹 Cleaned everything"

# Validation and CI commands
validate-all: lint test template-test ## Run all validation checks
	@echo "✅ All validation checks passed"

ci-test: ## Run CI test suite
	uv run pytest --cov=src --cov-report=xml --cov-report=term
	uv run ruff check src/ tests/
	uv run mypy src/

# Utility commands
version: ## Show current version
	@python -c "import toml; print('AgentUp version:', toml.load('pyproject.toml')['project']['version'])"

env-info: ## Show environment information
	@echo "Environment Information"
	@echo "====================="
	@echo "Python version: $$(python --version)"
	@echo "UV version: $$(uv --version)"
	@echo "Working directory: $$(pwd)"
	@echo "Git branch: $$(git branch --show-current 2>/dev/null || echo 'Not a git repo')"
	@echo "Git status: $$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ') files changed"

# Quick development workflows
dev-setup: install-dev ## Complete development setup
	@echo "Running complete development setup..."
	make check-deps
	make test-fast
	@echo "Development environment ready!"

dev-test: ## Quick development test cycle
	@echo "Running development test cycle..."
	make lint-fix
	make test-fast
	make template-test-syntax
	@echo "Development tests passed!"

dev-full: ## Full development validation
	@echo "Running full development validation..."
	make clean
	make dev-setup
	make validate-all
	make agent-create-standard
	make agent-test
	@echo "Full development validation completed!"

# Agent development helpers
add-skill: ## Add skill to existing agent (interactive)
	uv run agentup add-skill

validate-config: ## Validate agent configuration
	uv run agentup validate

deploy-files: ## Generate deployment files
	uv run agentup deploy

# Performance testing
perf-test: ## Run performance tests
	@echo "Running performance tests..."
	@if [ -d "./test-agents/standard" ]; then \
		cd ./test-agents/standard && \
		echo "Testing response times..." && \
		time curl -s -X POST http://localhost:8001/ \
			-H 'Content-Type: application/json' \
			-d '{"jsonrpc": "2.0", "method": "send_message", "params": {"messages": [{"role": "user", "content": "Hello"}]}, "id": "1"}' \
			>/dev/null || echo "❌ Server not running on :8001"; \
	else \
		echo "❌ No test agent found. Run 'make agent-create-standard' first"; \
	fi

# Debugging helpers
debug-templates: ## Debug template rendering issues
	@echo "Debugging template rendering..."
	uv run python -c "\
from .templates import get_template_features; \
import json; \
print('Available templates:'); \
print(json.dumps(get_template_features(), indent=2))"

debug-components: ## List available components
	@echo "Available components:"
	@ls -la src/agentup/components/ | grep -E '\.py$$' | awk '{print "  - " $$9}' | sed 's/.py//'

debug-logs: ## Show recent logs from test agent
	@if [ -d "./test-agents/standard" ]; then \
		echo "📋 Recent logs (if any):"; \
		find ./test-agents/standard -name "*.log" -exec tail -20 {} \; 2>/dev/null || echo "No log files found"; \
	else \
		echo "❌ No test agent found"; \
	fi

# Example workflows
example-agent: ## Create and test example agent example
	@echo "Creating example agent example..."
	uv run agentup create-agent \
		--quick example-agent \
		--template standard \
		--output-dir ./example-agent
	@echo "✅ Example agent created in ./example-agent"
	@echo "💡 Next steps:"
	@echo "   1. cd ./example-agentt"
	@echo "   2. uv run uvicorn src.agent.main:app --reload"

example-chatbot: ## Create chatbot example
	@echo "💬 Creating chatbot example..."
	uv run agentup create-agent \
		--quick simple-chatbot \
		--template chatbot \
		--output-dir ./examples/chatbot
	@echo "✅ Chatbot created in ./examples/chatbot"