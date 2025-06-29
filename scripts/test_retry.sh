#!/bin/bash

# Test script for retry middleware functionality

echo "=== A2A Retry Middleware Test ==="
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}This script tests the retry middleware by using the api_demo handler${NC}"
echo -e "${BLUE}which includes @retryable(max_retries=3) in its decorators.${NC}"
echo
echo "The api_demo handler doesn't normally fail, so we'll send malformed requests"
echo "or test with network conditions that might cause failures."
echo

# Function to test retry behavior
test_retry_scenario() {
    local test_name=$1
    local content=$2
    local expected_behavior=$3

    echo -e "${YELLOW}Test: $test_name${NC}"
    echo "Content: $content"
    echo "Expected: $expected_behavior"
    echo

    response=$(curl -s -X POST http://localhost:8000/ \
        -H "Content-Type: application/json" \
        -d '{
            "jsonrpc": "2.0",
            "method": "send_message",
            "params": {
                "messages": [{"role": "user", "content": "'"$content"'"}]
            },
            "id": "retry-test"
        }' 2>/dev/null)

    if echo "$response" | grep -q "error"; then
        echo -e "${RED}Failed with error:${NC}"
        echo "$response" | jq -r '.error.message' 2>/dev/null || echo "$response"
    else
        echo -e "${GREEN}Success:${NC}"
        echo "$response" | jq -r '.result.messages[-1].content' 2>/dev/null | head -c 100
        echo "..."
    fi
    echo
    echo "Check server logs for retry attempts..."
    echo
}

# Test 1: Normal api_demo request (should succeed immediately)
test_retry_scenario \
    "Normal API Demo Request" \
    "api demo normal test" \
    "Should succeed on first attempt"

# Test 2: Add manual retry handler for better testing
echo -e "${YELLOW}=== Adding Manual Retry Test Handler ===${NC}"
echo
echo "For better retry testing, add this handler to your src/agent/handlers.py:"
echo
cat << 'EOF'
@register_handler("retry_test")
@retryable(max_retries=3, delay=1, backoff=2)
@logged(level='INFO')
async def handle_retry_test(task: Task) -> str:
    """Test handler that randomly fails."""
    import random

    messages = MessageProcessor.extract_messages(task)
    latest_message = MessageProcessor.get_latest_user_message(messages)
    content = latest_message.get('content', '') if latest_message else ''

    # 70% chance of failure
    if random.random() < 0.7:
        raise Exception("Simulated failure for retry testing")

    return f"RETRY TEST SUCCESS! Content: {content}"
EOF
echo
echo "And add this to routing rules in agent_config.yaml:"
echo
cat << 'EOF'
- skill_id: retry_test
  keywords: ["retry test", "test retry", "rtest"]
  patterns: ["retry.*test.*", "test.*retry.*"]
EOF
echo
echo "Then restart your server and run:"
echo "curl -X POST http://localhost:8000/ -H 'Content-Type: application/json' -d '{"
echo "  \"jsonrpc\": \"2.0\","
echo "  \"method\": \"send_message\","
echo "  \"params\": {"
echo "    \"messages\": [{\"role\": \"user\", \"content\": \"retry test\"}]"
echo "  },"
echo "  \"id\": \"1\""
echo "}'"
echo
echo -e "${GREEN}Watch the server logs to see retry attempts with delays!${NC}"

# Test with existing handlers to simulate some failure scenarios
echo -e "${YELLOW}=== Testing Potential Failure Scenarios ===${NC}"
echo

# Test 3: Large content that might cause issues
test_retry_scenario \
    "Large Content Test" \
    "api demo $(python3 -c "print('x' * 1000)")" \
    "Large content might trigger retries"

# Test 4: Special characters that might cause parsing issues
test_retry_scenario \
    "Special Characters Test" \
    "api demo test with special chars: {}[]()@#$%^&*" \
    "Special characters might trigger retries"

echo -e "${YELLOW}=== Retry Test Complete ===${NC}"
echo
echo "Notes:"
echo "- The built-in api_demo handler has @retryable(max_retries=3)"
echo "- For better testing, add a handler that intentionally fails sometimes"
echo "- Watch server logs for retry attempts with exponential backoff"
echo "- Retry delays: 1s, 2s, 4s (with backoff=2)"