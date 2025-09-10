#!/bin/bash

# Pokemon MCP Server - Comprehensive Test Suite

echo "🧪 Pokemon MCP Server Test Suite"
echo "================================="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Function to run test and check result
run_test() {
    local test_name="$1"
    local test_command="$2"
    
    echo -e "${BLUE}Testing: $test_name${NC}"
    
    if eval "$test_command" > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓ PASSED${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "  ${RED}✗ FAILED${NC}"
        ((TESTS_FAILED++))
    fi
    echo ""
}

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "🔧 Activating virtual environment..."
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        source venv/Scripts/activate
    else
        source venv/bin/activate
    fi
fi

echo "🧪 Running component tests..."
echo ""

# Test 1: Python imports
run_test "Python imports" "python -c 'import fastapi, httpx, pydantic, uvicorn'"

# Test 2: Server components
run_test "Server components" "python app.py test"

# Test 3: Start server in background for endpoint tests
echo "🚀 Starting server for endpoint tests..."
python app.py > server.log 2>&1 &
SERVER_PID=$!
sleep 3

# Function to test HTTP endpoint
test_endpoint() {
    local endpoint="$1"
    local expected_status="$2"
    
    if command -v curl > /dev/null 2>&1; then
        status=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000$endpoint")
        [ "$status" = "$expected_status" ]
    else
        # Fallback using python
        python -c "
import urllib.request
try:
    response = urllib.request.urlopen('http://localhost:8000$endpoint')
    exit(0 if response.getcode() == $expected_status else 1)
except:
    exit(1)
"
    fi
}

# Test 4: Server health
run_test "Server health endpoint" "test_endpoint '/health' '200'"

# Test 5: Root endpoint  
run_test "Root endpoint" "test_endpoint '/' '200'"

# Test 6: Pokemon list endpoint
run_test "Pokemon list endpoint" "test_endpoint '/resource/pokemon/list' '200'"

# Test 7: Pokemon details endpoint
run_test "Pokemon details endpoint" "test_endpoint '/resource/pokemon/pikachu' '200'"

# Test 8: Search endpoint
run_test "Pokemon search endpoint" "test_endpoint '/resource/pokemon/search?q=pika' '200'"

# Test 9: Compare endpoint
run_test "Pokemon compare endpoint" "test_endpoint '/resource/pokemon/compare?name1=pikachu&name2=charizard' '200'"

# Test 10: Type chart endpoint
run_test "Type chart endpoint" "test_endpoint '/resource/pokemon/types' '200'"

# Test 11: API docs
run_test "API documentation" "test_endpoint '/docs' '200'"

# Clean up: Stop server
echo "🛑 Stopping test server..."
kill $SERVER_PID 2>/dev/null
wait $SERVER_PID 2>/dev/null
rm -f server.log

# Test 12: Interactive test script exists
run_test "Interactive test script" "test -f interactive_test.py"

# Test 13: Project structure
run_test "Project structure" "test -d mcp_server && test -f app.py && test -f requirements.txt"

echo "================================="
echo "🏆 Test Results:"
echo -e "  ${GREEN}✓ Passed: $TESTS_PASSED${NC}"

if [ $TESTS_FAILED -gt 0 ]; then
    echo -e "  ${RED}✗ Failed: $TESTS_FAILED${NC}"
    echo ""
    echo -e "${RED}Some tests failed. Check the output above for details.${NC}"
    exit 1
else
    echo -e "  ${RED}✗ Failed: 0${NC}"
    echo ""
    echo -e "${GREEN}🎉 All tests passed! Server is ready for use.${NC}"
    echo ""
    echo "Quick commands:"
    echo "  ./start_server.sh           - Start the server"
    echo "  python interactive_test.py  - Interactive testing"
    echo "  curl http://localhost:8000/ - Test server manually"
fi