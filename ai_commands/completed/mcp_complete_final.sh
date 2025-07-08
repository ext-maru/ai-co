#!/bin/bash
#!/bin/bash
cd /home/aicompany/ai_co

echo "🎯 AI Company MCP - Complete Setup"
echo "=================================="
echo ""
echo "Starting automated MCP setup process..."
echo ""

# Execute the dashboard which handles everything
python3 run_dashboard.py

echo ""
echo "✅ MCP setup process initiated!"
echo ""
echo "The system will:"
echo "1. Monitor setup progress"
echo "2. Create MCP wrapper"
echo "3. Run tests"
echo "4. Show final status"
echo ""
echo "Please wait about 40 seconds for completion."
