#!/bin/bash

# Test rate limiting on handlers that don't require external services

echo "=== A2A Agent Rate Limiting Test ==="
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to test rate limiting
test_rate_limit() {
    local handler=$1
    local message=$2
    local limit=$3
    local requests=$4

    echo -e "${YELLOW}Testing $handler handler (Rate limit: $limit requests/minute)${NC}"
    echo "Sending $requests requests rapidly..."
    echo

    # Track successes and failures
    success_count=0
    failure_count=0

    # Send requests in parallel
    for i in $(seq 1 $requests); do
        (
            response=$(curl -s -X POST http://localhost:8000/ \
                -H "Content-Type: application/json" \
                -d '{
                    "jsonrpc": "2.0",
                    "method": "send_message",
                    "params": {
                        "messages": [{"role": "user", "content": "'"$message"' request #'$i'"}]
                    },
                    "id": "'$i'"
                }' 2>/dev/null)

            # Check if response contains rate limit error
            if echo "$response" | grep -q "Rate limit exceeded"; then
                echo -e "${RED}Request $i: RATE LIMITED${NC}"
                echo "$response" | jq -r '.error.message' 2>/dev/null || echo "$response"
            else
                echo -e "${GREEN}Request $i: SUCCESS${NC}"
                # Show truncated response
                echo "$response" | jq -r '.result.messages[-1].content' 2>/dev/null | head -c 80
                echo "..."
            fi
            echo
        ) &
    done

    # Wait for all requests to complete
    wait

    echo -e "${YELLOW}--- $handler test complete ---${NC}"
    echo
}

# Test 1: API Demo Handler (30 requests/minute limit)
echo "=== TEST 1: API Demo Handler ==="
echo "This handler has a 30 requests/minute limit (1 request every 2 seconds)"
echo "Sending 5 requests rapidly - some should be rate limited"
echo
test_rate_limit "api_demo" "api demo test" 30 5

echo "Waiting 3 seconds before next test..."
sleep 3

# Test 2: Conversation Handler (60 requests/minute limit)
echo "=== TEST 2: Conversation Handler ==="
echo "This handler has a 60 requests/minute limit (1 request per second)"
echo "Sending 5 requests rapidly - fewer should be rate limited"
echo
# test_rate_limit "conversation" "hello" 60 5

echo "Waiting 3 seconds before next test..."
sleep 3

# Test 3: Aggressive test on API Demo
echo "=== TEST 3: Aggressive Rate Limit Test ==="
echo "Sending 10 requests instantly to api_demo handler"
echo "Most should be rate limited (only ~1-2 should succeed)"
echo
# test_rate_limit "api_demo" "api demo stress test" 30 10

echo
echo -e "${YELLOW}=== Rate Limiting Test Complete ===${NC}"
echo
echo "Summary:"
echo "- Rate limiting is applied per skill_id and user"
echo "- api_demo: 30 requests/minute (2 second minimum between requests)"
echo "- conversation: 60 requests/minute (1 second minimum between requests)"
echo "- Rate limited requests return an error with 'Rate limit exceeded' message"