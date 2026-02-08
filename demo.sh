#!/usr/bin/env bash
# Bash version of demo for Linux/Mac

BASE_URL="http://localhost:8000/api/v1"
API_URL="http://localhost:8000"

echo ""
echo "================================================================================"
echo "  Pipeline Orchestration Endpoint - Demo"
echo "================================================================================"
echo ""

# Check if API is running
echo "Checking API..."
if ! curl -s "$API_URL/docs" > /dev/null; then
    echo "❌ API not responding at $API_URL"
    echo ""
    echo "Start it with:"
    echo "  python -m uvicorn app.main:app --reload"
    echo ""
    exit 1
fi
echo "✅ API is running"
echo ""

echo "Select demo:"
echo "  1 - Basic (3 routers, 1 switch)"
echo "  2 - Medium (5 routers, 3 switches)"
echo "  3 - Large (8 routers, 4 switches)"
echo "  4 - Fast (skip analysis)"
echo "  0 - Exit"
echo ""
read -p "Enter choice: " choice

case $choice in
    0) echo "Goodbye!"; exit ;;
    1) NAME="basic"; ROUTERS=3; SWITCHES=1; ANALYSIS="true"; SEED="" ;;
    2) NAME="medium"; ROUTERS=5; SWITCHES=3; ANALYSIS="true"; SEED=42 ;;
    3) NAME="large"; ROUTERS=8; SWITCHES=4; ANALYSIS="true"; SEED=123 ;;
    4) NAME="fast"; ROUTERS=3; SWITCHES=1; ANALYSIS="false"; SEED="" ;;
    *) echo "Invalid choice"; exit 1 ;;
esac

echo ""
echo "================================================================================"
echo "  DEMO: $(echo $NAME | tr a-z A-Z)"
echo "================================================================================"
echo ""

# Build payload
PAYLOAD="{\"topology_name\":\"demo-$NAME\",\"num_routers\":$ROUTERS,\"num_switches\":$SWITCHES,\"run_analysis\":$ANALYSIS"
if [ -n "$SEED" ]; then
    PAYLOAD="$PAYLOAD,\"seed\":$SEED"
fi
PAYLOAD="$PAYLOAD}"

echo "Sending request..."
RESPONSE=$(curl -s -X POST "$BASE_URL/run-pipeline" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD")

echo ""
echo "Response:"
echo "$RESPONSE" | jq '.' 2>/dev/null || echo "$RESPONSE"
echo ""
