# API Key Authentication

**Simple, secure authentication for development and production**

API key authentication provides a straightforward way to secure your AgentUp agent. This guide covers everything from basic setup to advanced configurations with multiple keys and environment management.

## Table of Contents

- [Overview](#overview)
- [Quick Setup](#quick-setup)
- [Configuration Options](#configuration-options)
- [Multiple API Keys](#multiple-api-keys)
- [Environment Variables](#environment-variables)
- [Security Best Practices](#security-best-practices)
- [Testing and Validation](#testing-and-validation)

## Overview

API key authentication in AgentUp provides:

- **Simple Setup** - Get secured in 2 minutes
- **Flexible Configuration** - Headers, query params, or cookies
- **Multiple Keys** - Support for different environments or clients
- **Strong Validation** - Automatic rejection of weak keys
- **A2A Compliance** - Proper security scheme advertising

### When to Use API Keys

| Good For | Not Ideal For |
|-----------|---------------|
| Development and testing | User-facing applications |
| Internal APIs | Third-party integrations |
| Service-to-service auth | OAuth2 required scenarios |
| Simple authentication | Complex authorization needs |
| Microservices | Multi-tenant systems |

## Quick Setup

### Step 1: Generate a Strong API Key

```bash
# Generate a secure API key
python -c "import secrets; print('sk-' + secrets.token_urlsafe(32))"

# Example output: sk-8K2mNx9P7qR4sV5yA3bC6dE9fH2jK5lM8nP1qS4t
```

### Step 2: Configure Your Agent

Add to your `agent_config.yaml`:

```yaml
security:
  enabled: true
  type: "api_key"
  api_key: "sk-8K2mNx9P7qR4sV5yA3bC6dE9fH2jK5lM8nP1qS4t"
```

### Step 3: Test Authentication

```bash
# Start your agent
uv run uvicorn src.agent.main:app --reload --port 8000

# Test with valid API key
curl -H "X-API-Key: sk-8K2mNx9P7qR4sV5yA3bC6dE9fH2jK5lM8nP1qS4t" \
     http://localhost:8000/agent/card

# Should return 200 OK with agent card data
```

## Configuration Options

### Basic Configuration

```yaml
# Simple format (recommended for most use cases)
security:
  enabled: true
  type: "api_key"
  api_key: "sk-your-strong-api-key-here"
```

### Advanced Configuration

```yaml
# Full configuration with all options
security:
  enabled: true
  type: "api_key"
  api_key:
    header_name: "X-API-Key"     # Custom header name
    location: "header"           # Options: header, query, cookie
    keys:                        # Multiple API keys
      - "sk-prod-key-abc123"
      - "sk-staging-key-xyz789"
      - "sk-dev-key-def456"
```

### Location Options

#### Header Authentication (Default)
```yaml
api_key:
  header_name: "X-API-Key"
  location: "header"
  keys: ["sk-your-key-here"]
```

**Usage:**
```bash
curl -H "X-API-Key: sk-your-key-here" http://localhost:8000/agent/card
```

#### Query Parameter Authentication
```yaml
api_key:
  header_name: "api_key"  # Query parameter name
  location: "query"
  keys: ["sk-your-key-here"]
```

**Usage:**
```bash
curl "http://localhost:8000/agent/card?api_key=sk-your-key-here"
```

> **Security Note**: Query parameters may be logged by web servers and proxies. Use headers in production.

#### Cookie Authentication
```yaml
api_key:
  header_name: "auth_token"  # Cookie name
  location: "cookie"
  keys: ["sk-your-key-here"]
```

**Usage:**
```bash
curl -H "Cookie: auth_token=sk-your-key-here" http://localhost:8000/agent/card
```

## Multiple API Keys

### Use Cases for Multiple Keys

- **Environment Separation**: Different keys for dev/staging/prod
- **Client Segmentation**: Separate keys for different applications
- **Key Rotation**: Gradual replacement of keys
- **Team Access**: Different keys for different teams

### Configuration

```yaml
security:
  enabled: true
  type: "api_key"
  api_key:
    header_name: "X-API-Key"
    location: "header"
    keys:
      - "sk-prod-key-2024-01-abcd1234"     # Production
      - "sk-staging-key-2024-01-efgh5678"  # Staging
      - "sk-dev-key-2024-01-ijkl9012"      # Development
      - "sk-client-app-1-mnop3456"         # Client App 1
      - "sk-client-app-2-qrst7890"         # Client App 2
```

### Key Management Best Practices

#### 1. Naming Convention
```
sk-{environment}-{purpose}-{date}-{random}

Examples:
sk-prod-webapp-2024-01-abc123
sk-staging-api-2024-01-def456
sk-dev-testing-2024-01-ghi789
```

#### 2. Key Rotation Strategy
```yaml
# Phase 1: Add new key alongside old key
keys:
  - "sk-prod-old-key-abc123"  # Keep old key active
  - "sk-prod-new-key-def456"  # Add new key

# Phase 2: Update clients to use new key

# Phase 3: Remove old key
keys:
  - "sk-prod-new-key-def456"  # Only new key
```

#### 3. Environment-Specific Files
```bash
# agent_config.prod.yaml
security:
  enabled: true
  type: "api_key"
  api_key: "sk-prod-key-strong-and-secure"

# agent_config.staging.yaml  
security:
  enabled: true
  type: "api_key"
  api_key: "sk-staging-key-for-testing"
```

## Environment Variables

### Why Use Environment Variables?

- **Security**: Keep secrets out of configuration files
- **Flexibility**: Different values per environment
- **CI/CD Integration**: Easy deployment automation
- **Team Collaboration**: Safe to commit configs to version control

### Configuration with Environment Variables

```yaml
# agent_config.yaml (safe to commit)
security:
  enabled: true
  type: "api_key"
  api_key: "${API_KEY}"  # Will be replaced with env var value
```

```bash
# .env file (DO NOT commit)
API_KEY=sk-your-actual-secret-key-here
```

### Environment Variable Formats

#### Simple Substitution
```yaml
api_key: "${API_KEY}"
```

#### With Default Values
```yaml
api_key: "${API_KEY:sk-default-dev-key}"  # Use default if API_KEY not set
```

#### Multiple Keys from Environment
```yaml
api_key:
  keys:
    - "${PROD_API_KEY}"
    - "${STAGING_API_KEY}"
    - "${DEV_API_KEY:sk-default-dev-key}"
```

### Setting Environment Variables

#### Local Development
```bash
# .env file
API_KEY=sk-dev-key-for-local-testing

# Or export directly
export API_KEY=sk-dev-key-for-local-testing
```

#### Production Deployment
```bash
# Docker
docker run -e API_KEY=sk-prod-key-secure app:latest

# Kubernetes
kubectl create secret generic agent-secrets --from-literal=api-key=sk-prod-key

# Systemd
echo "API_KEY=sk-prod-key" >> /etc/environment
```

#### CI/CD Pipelines
```yaml
# GitHub Actions
env:
  API_KEY: ${{ secrets.API_KEY }}

# GitLab CI
variables:
  API_KEY: $API_KEY_SECRET
```

## Security Best Practices

### 🔒 Key Generation

#### Strong API Keys
```bash
# Good: Long, random, prefixed
sk-8K2mNx9P7qR4sV5yA3bC6dE9fH2jK5lM8nP1qS4tU7vW0xY3zA6b

# Bad: Short, predictable, common words
password123
api-key-test
admin-key
```

#### Automated Generation
```python
# generate_api_key.py
import secrets
import string

def generate_api_key(length=32, prefix="sk-"):
    """Generate a cryptographically secure API key."""
    alphabet = string.ascii_letters + string.digits
    key = ''.join(secrets.choice(alphabet) for _ in range(length))
    return f"{prefix}{key}"

# Generate 5 keys for different environments
for env in ["prod", "staging", "dev", "test", "demo"]:
    key = generate_api_key()
    print(f"{env.upper()}_API_KEY={key}")
```

### 🛡️ Storage and Transmission

#### Secure Practices
- Store in environment variables or secure vaults
- Transmit only over HTTPS
- Use headers instead of query parameters
- Implement key rotation procedures
- Monitor for unauthorized usage

#### Avoid These Mistakes
- Hardcoding keys in source code
- Committing keys to version control
- Logging keys in application logs
- Using keys in URLs or query parameters
- Sharing keys through insecure channels

### Monitoring and Auditing

AgentUp automatically logs authentication attempts:

```python
# Enable security event logging
import logging
logging.getLogger("src.agent.security").setLevel(logging.INFO)
```

Example log entries:
```
INFO:src.agent.security.utils:Security event: authentication
WARNING:src.agent.security.utils:Security event failed: authentication
```

### Key Compromise Response

If an API key is compromised:

1. **Immediately remove the key** from configuration
2. **Restart the agent** to apply changes
3. **Generate a new key** with different pattern
4. **Update all clients** with new key
5. **Monitor logs** for unauthorized access attempts
6. **Review access patterns** before compromise

```yaml
# Emergency key rotation
security:
  enabled: true
  type: "api_key"
  api_key:
    keys:
      # Remove compromised key immediately
      # - "sk-compromised-key-remove-now"  # REMOVED
      - "sk-new-secure-replacement-key"    # NEW KEY
```

## Testing and Validation

### Automated Testing Script

```bash
#!/bin/bash
# test-api-key.sh - Validate API key authentication

AGENT_URL="http://localhost:8000"
API_KEY="$1"

if [ -z "$API_KEY" ]; then
    echo "Usage: $0 <api_key>"
    echo "Example: $0 sk-your-api-key-here"
    exit 1
fi

echo "Testing API Key Authentication"
echo "=================================="

# Test 1: Discovery endpoint (should work without auth)
echo "1. Testing discovery endpoint (no auth required)..."
DISCOVERY_STATUS=$(curl -s -w "%{http_code}" "${AGENT_URL}/.well-known/agent.json" -o /dev/null)
if [ "$DISCOVERY_STATUS" = "200" ]; then
    echo "   Discovery endpoint accessible"
else
    echo "   Discovery endpoint failed ($DISCOVERY_STATUS)"
    exit 1
fi

# Test 2: Protected endpoint without key (should fail)
echo "2. Testing protected endpoint without API key..."
NO_AUTH_STATUS=$(curl -s -w "%{http_code}" "${AGENT_URL}/agent/card" -o /dev/null)
if [ "$NO_AUTH_STATUS" = "401" ]; then
    echo "   Protected endpoint correctly requires authentication"
else
    echo "   Protected endpoint should require authentication ($NO_AUTH_STATUS)"
fi

# Test 3: Protected endpoint with wrong key (should fail)
echo "3. Testing protected endpoint with invalid API key..."
WRONG_KEY_STATUS=$(curl -s -w "%{http_code}" -H "X-API-Key: invalid-key" "${AGENT_URL}/agent/card" -o /dev/null)
if [ "$WRONG_KEY_STATUS" = "401" ]; then
    echo "   Invalid API key correctly rejected"
else
    echo "   Invalid API key should be rejected ($WRONG_KEY_STATUS)"
fi

# Test 4: Protected endpoint with correct key (should work)
echo "4. Testing protected endpoint with valid API key..."
RESPONSE=$(curl -s -w "\n%{http_code}" -H "X-API-Key: ${API_KEY}" "${AGENT_URL}/agent/card")
STATUS=$(echo "$RESPONSE" | tail -1)
BODY=$(echo "$RESPONSE" | head -n -1)

if [ "$STATUS" = "200" ]; then
    echo "   Valid API key accepted"
    AGENT_NAME=$(echo "$BODY" | python -c "import sys, json; print(json.load(sys.stdin).get('name', 'Unknown Agent'))")
    echo "   Connected to: $AGENT_NAME"
    
    # Check security scheme in response
    SECURITY_SCHEME=$(echo "$BODY" | python -c "
import sys, json
data = json.load(sys.stdin)
schemes = data.get('securitySchemes', {})
if 'X-API-Key' in schemes:
    print('API Key security scheme correctly advertised')
else:
    print('Warning: API Key security scheme not found in agent card')
")
    echo "   $SECURITY_SCHEME"
else
    echo "   Valid API key rejected ($STATUS)"
    echo "   Error: $BODY"
fi

echo ""
echo "API Key testing completed!"
```

### Key Validation Script

```python
#!/usr/bin/env python3
# validate-api-key.py
import re
import sys

def validate_api_key(api_key):
    """Validate API key strength and format."""
    
    issues = []
    
    # Length check
    if len(api_key) < 8:
        issues.append("Key too short (minimum 8 characters)")
    
    # Weak patterns check
    weak_patterns = ['password', 'test', 'admin', 'key', '123', 'abc']
    for pattern in weak_patterns:
        if pattern.lower() in api_key.lower():
            issues.append(f"Contains weak pattern: {pattern}")
    
    # Character diversity check
    if not re.search(r'[A-Za-z]', api_key):
        issues.append("No letters found")
    
    if not re.search(r'[0-9]', api_key):
        issues.append("No numbers found")
    
    # Good patterns check
    good_patterns = []
    if api_key.startswith('sk-'):
        good_patterns.append("Good prefix (sk-)")
    
    if len(api_key) >= 20:
        good_patterns.append("Good length (20+ characters)")
    
    if re.search(r'[A-Z]', api_key) and re.search(r'[a-z]', api_key):
        good_patterns.append("Mixed case letters")
    
    return issues, good_patterns

def main():
    if len(sys.argv) != 2:
        print("Usage: python validate-api-key.py <api_key>")
        sys.exit(1)
    
    api_key = sys.argv[1]
    issues, good_patterns = validate_api_key(api_key)
    
    print(f"API Key Validation: {api_key}")
    print("=" * 50)
    
    if good_patterns:
        print("Strengths:")
        for pattern in good_patterns:
            print(f"   • {pattern}")
    
    if issues:
        print("Issues:")
        for issue in issues:
            print(f"   • {issue}")
        print("\nRecommendation: Generate a stronger API key")
        sys.exit(1)
    else:
        print("API key passes all validation checks!")

if __name__ == "__main__":
    main()
```

### Integration Testing

```python
# test_api_key_auth.py
import pytest
import httpx
from fastapi.testclient import TestClient

@pytest.fixture
def agent_app():
    """Create test agent with API key auth."""
    from src.agent.main import app
    return app

@pytest.fixture 
def client(agent_app):
    """Create test client."""
    return TestClient(agent_app)

def test_api_key_authentication(client):
    """Test API key authentication flow."""
    
    # Test 1: Discovery endpoint (no auth required)
    response = client.get("/.well-known/agent.json")
    assert response.status_code == 200
    
    # Test 2: Protected endpoint without key
    response = client.get("/agent/card")
    assert response.status_code == 401
    
    # Test 3: Protected endpoint with invalid key
    response = client.get(
        "/agent/card",
        headers={"X-API-Key": "invalid-key"}
    )
    assert response.status_code == 401
    
    # Test 4: Protected endpoint with valid key
    response = client.get(
        "/agent/card", 
        headers={"X-API-Key": "sk-test-key-for-testing"}
    )
    assert response.status_code == 200
    
    # Verify security scheme in response
    agent_card = response.json()
    assert "securitySchemes" in agent_card
    assert "X-API-Key" in agent_card["securitySchemes"]
```

## Migration and Upgrading

### From No Authentication

```yaml
# Before: No security
agent:
  name: "My Agent"

# After: API key security  
agent:
  name: "My Agent"

security:
  enabled: true
  type: "api_key"
  api_key: "sk-your-new-api-key"
```

**Migration checklist:**
1. Generate strong API keys
2. Update configuration
3. Restart agent
4. Update all clients
5. Test thoroughly

### From Bearer Token to API Key

```yaml
# Before: Bearer token
security:
  enabled: true
  type: "bearer"
  bearer_token: "your-bearer-token"

# After: API key
security:
  enabled: true
  type: "api_key"
  api_key: "sk-your-api-key"
```

**Client changes:**
```bash
# Before
curl -H "Authorization: Bearer your-bearer-token" URL

# After  
curl -H "X-API-Key: sk-your-api-key" URL
```

## Next Steps

### Enhanced Security
- **[Bearer Token Authentication](bearer-tokens.md)** - JWT tokens
- **[OAuth2 Authentication](oauth2.md)** - Enterprise integration
- **[Multi-Factor Authentication](../configuration/security.md#mfa)** - Additional security layers

### Production Deployment
- **[Environment Management](../examples/enterprise-agent.md#environments)**
- **[Key Rotation Automation](../configuration/security.md#rotation)**
- **[Monitoring and Alerting](../configuration/middleware.md#monitoring)**

### Advanced Configuration
- **[Custom Headers](../reference/config-schema.md#api-key-headers)**
- **[Rate Limiting](../configuration/middleware.md#rate-limiting)**
- **[Audit Logging](../configuration/security.md#auditing)**

---

**Quick Links:**
- [Documentation Home](../index.md)
- [Authentication Quick Start](quick-start.md)
- [Troubleshooting Guide](../troubleshooting/authentication.md)