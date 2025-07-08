#!/bin/bash
#!/bin/bash
cd /home/aicompany/ai_co

echo "🚀 Executing MCP Final Setup..."
echo ""

# 実行権限付与
chmod +x finalize_mcp.py

# 最終セットアップ実行
python3 finalize_mcp.py

echo ""
echo "✅ MCP setup completed!"
