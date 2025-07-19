#!/bin/bash

# Example script showing how to test streaming with OAuth2 authentication
# This demonstrates the streaming functionality we just set up

echo "🧪 AgentUp Streaming Test Example with OAuth2"
echo "=============================================="
echo

# Check if agent is running
echo "🔍 Checking if agent is running..."
if ! curl -s http://localhost:8000/ > /dev/null 2>&1; then
    echo "  Agent is not running. Please start it first:"
    echo "   cd /path/to/oauth2_github_agent"
    echo "   agentup agent serve"
    exit 1
fi
echo "Agent is running"
echo

# Set your GitHub token here
export GITHUB_TOKEN="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"

echo "🚀 Testing streaming endpoint with different tools:"
echo

echo "📝 Test 1: Python streaming client"
echo "-----------------------------------"
python ../../scripts/test_streaming.py \
    --url http://localhost:8000 \
    --token "$GITHUB_TOKEN" \
    --message "Hello streaming! Can you count to 3?"

echo
echo "📝 Test 2: Shell streaming client"
echo "---------------------------------"
../../scripts/test_streaming.sh \
    --url http://localhost:8000 \
    --token "$GITHUB_TOKEN" \
    --message "Tell me a short joke"

echo
echo "📝 Test 3: Raw curl streaming (first few events)"
echo "-----------------------------------------------"
timeout 10s curl -N -X POST http://localhost:8000/ \
    -H "Authorization: Bearer $GITHUB_TOKEN" \
    -H "Content-Type: application/json" \
    -H "Accept: text/event-stream" \
    -d '{
        "jsonrpc": "2.0",
        "method": "message/stream",
        "params": {
            "message": {
                "role": "user",
                "parts": [{"kind": "text", "text": "What is 2+2?"}],
                "messageId": "msg-curl-test",
                "kind": "message"
            }
        },
        "id": "req-curl-test"
    }' | head -10

echo
echo "Streaming tests completed!"
echo
echo "💡 Tips:"
echo "- Use --raw flag to see raw SSE data"
echo "- Use --verbose for detailed output"
echo "- Try different message types and lengths"
echo "- Test error handling with invalid tokens"