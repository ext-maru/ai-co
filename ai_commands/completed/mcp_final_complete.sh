#!/bin/bash
#!/bin/bash
cd /home/aicompany/ai_co

echo "🎯 MCP Final Complete Setup"
echo "=========================="
echo ""

# Step 1: Execute final setup
echo "📌 Running final setup..."
python3 run_final.py

# Step 2: Wait for completion
echo ""
echo "⏳ Waiting for completion..."
sleep 25

# Step 3: Complete check
echo ""
echo "📊 Running complete check..."
python3 mcp_complete_check.py

echo ""
echo "✅ MCP setup process finished!"
