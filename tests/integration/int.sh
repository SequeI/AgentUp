#!/bin/bash

# Integration test for echo functionality

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Start the server
echo "Starting AgentUp server..."
uv run agentup agent serve -c tests/integration/agent_config_echo.yaml &
SERVER_PID=$!

# Wait for server to start
echo "Waiting for server to be ready..."
sleep 3

# Check if server is running
if ! ps -p $SERVER_PID > /dev/null; then
    echo -e "${RED}Server failed to start${NC}"
    exit 1
fi

# Run the test request
echo "Running echo test..."
RESPONSE=$(curl -s -X POST http://localhost:8000/ \
      -H "Content-Type: application/json" \
      -H "X-API-Key: sk-strong-key-1-abcd1234xyz" \
      -d '{
        "jsonrpc": "2.0",
        "method": "message/send",
        "params": {
          "message": {
            "role": "user",
            "parts": [{"kind": "text", "text": "hello"}],
            "messageId": "msg-005",
            "contextId": "context-001",
            "kind": "message"
          }
        },
        "id": "req-005"
      }')

# Debug: Print the response
echo "Response received:"
echo "$RESPONSE" | jq .

# Extract the task ID for status check
TASK_ID=$(echo "$RESPONSE" | jq -r '.result.id')

if [ -z "$TASK_ID" ] || [ "$TASK_ID" = "null" ]; then
    echo -e "${RED}Failed to get task ID from response${NC}"
    echo "Response: $RESPONSE"
    kill $SERVER_PID
    exit 1
fi

# Check task status
echo "Checking task status for ID: $TASK_ID"
STATUS_RESPONSE=$(curl -s -X POST http://localhost:8000/ \
      -H "Content-Type: application/json" \
      -H "X-API-Key: sk-strong-key-1-abcd1234xyz" \
      -d "{
        \"jsonrpc\": \"2.0\",
        \"method\": \"tasks/get\",
        \"params\": {
          \"id\": \"$TASK_ID\"
        },
        \"id\": \"req-006\"
      }")

# Validate the echo result
ECHO_TEXT=$(echo "$STATUS_RESPONSE" | jq -r '.result.artifacts[0].parts[0].text')
STATUS_STATE=$(echo "$STATUS_RESPONSE" | jq -r '.result.status.state')

# Stop the server
echo "Stopping server..."
kill $SERVER_PID
wait $SERVER_PID 2>/dev/null

# Check results
echo
echo "Test Results:"
echo "============="

if [ "$ECHO_TEXT" = "Echo: hello" ]; then
    echo -e "${GREEN} Echo test passed: '$ECHO_TEXT'${NC}"
else
    echo -e "${RED} Echo test failed. Expected 'Echo: hello', got '$ECHO_TEXT'${NC}"
    echo "Full response: $STATUS_RESPONSE"
    exit 1
fi

if [ "$STATUS_STATE" = "completed" ]; then
    echo -e "${GREEN} Task status test passed: '$STATUS_STATE'${NC}"
else
    echo -e "${RED} Task status test failed. Expected 'completed', got '$STATUS_STATE'${NC}"
    exit 1
fi

echo
echo -e "${GREEN}All tests passed!${NC}"
exit 0