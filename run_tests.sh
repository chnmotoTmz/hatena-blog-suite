#!/bin/bash
# Test Suite Runner Script

echo "🚀 Hatena Blog Suite - Complete Test Suite"
echo "=========================================="

# Check Python dependencies
echo "🗺 Checking Python dependencies..."
if ! python -c "import requests, bs4" 2>/dev/null; then
    echo "⚠️ Installing Python dependencies..."
    pip install -r requirements-optimized.txt
else
    echo "✅ Python dependencies: OK"
fi

# Check Node.js dependencies
echo "🗺 Checking Node.js dependencies..."
if [ ! -d "node_modules" ]; then
    echo "⚠️ Installing Node.js dependencies..."
    npm install
else
    echo "✅ Node.js dependencies: OK"
fi

# Run Python quick test
echo "🗺 Running Python quick test..."
python quick_test.py
PYTHON_RESULT=$?

if [ $PYTHON_RESULT -eq 0 ]; then
    echo "✅ Python tests: PASSED"
else
    echo "❌ Python tests: FAILED"
fi

# Run Node.js MCP test
echo "🗺 Running MCP server tests..."
node test_mcp_server.js
NODE_RESULT=$?

if [ $NODE_RESULT -eq 0 ]; then
    echo "✅ MCP tests: PASSED"
else
    echo "❌ MCP tests: FAILED"
fi

# Run full Python test suite (optional)
if [ "$1" = "--full" ]; then
    echo "🗺 Running full Python test suite..."
    python test_suite.py
    FULL_RESULT=$?
else
    FULL_RESULT=0
fi

# Summary
echo ""
echo "📊 Test Results Summary"
echo "========================"

if [ $PYTHON_RESULT -eq 0 ] && [ $NODE_RESULT -eq 0 ] && [ $FULL_RESULT -eq 0 ]; then
    echo "🎉 All tests PASSED!"
    echo "🚀 System is ready to use."
    echo ""
    echo "Quick start:"
    echo "  python core/hatena_all.py --blog-id YOUR_BLOG_ID"
    echo "  node mcp/unified-server.js"
    exit 0
else
    echo "⚠️ Some tests FAILED."
    echo "Please check the error messages above."
    exit 1
fi