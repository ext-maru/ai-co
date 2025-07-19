#!/bin/bash
# Setup script for Elder Servants Continue.dev Integration

echo "🚀 Elder Servants Continue.dev Integration Setup"
echo "=============================================="

# Check if running in the correct directory
if [ ! -f "elder_servant_adapter.py" ]; then
    echo "❌ Error: Please run this script from the continue_dev directory"
    exit 1
fi

# Step 1: Install Python dependencies
echo ""
echo "1️⃣ Installing Python dependencies..."
pip install fastapi uvicorn pydantic aiohttp

# Step 2: Check if Continue.dev is installed
echo ""
echo "2️⃣ Checking Continue.dev installation..."
if code --list-extensions | grep -q "continue.continue"; then
    echo "✅ Continue.dev is already installed"
else
    echo "📦 Installing Continue.dev extension..."
    code --install-extension continue.continue
fi

# Step 3: Create logs directory
echo ""
echo "3️⃣ Creating logs directory..."
mkdir -p logs

# Step 4: Create systemd service file (optional)
echo ""
echo "4️⃣ Creating systemd service file..."
cat > elder-servant-adapter.service << EOF
[Unit]
Description=Elder Servant Continue.dev Adapter
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
ExecStart=/usr/bin/python3 $(pwd)/elder_servant_adapter.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo "✅ Service file created: elder-servant-adapter.service"
echo "   To install as system service: sudo cp elder-servant-adapter.service /etc/systemd/system/"

# Step 5: Create startup script
echo ""
echo "5️⃣ Creating startup script..."
cat > start_adapter.sh << 'EOF'
#!/bin/bash
# Start Elder Servant Adapter

echo "🚀 Starting Elder Servant Adapter..."

# Check if already running
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️  Port 8000 is already in use. Adapter might be running."
    echo "   To stop: kill $(lsof -Pi :8000 -sTCP:LISTEN -t)"
    exit 1
fi

# Start in background with logs
nohup python3 elder_servant_adapter.py > logs/adapter.log 2>&1 &
echo $! > adapter.pid

echo "✅ Adapter started with PID: $(cat adapter.pid)"
echo "📝 Logs: tail -f logs/adapter.log"
echo "🛑 To stop: kill $(cat adapter.pid)"
EOF

chmod +x start_adapter.sh

# Step 6: Create Continue.dev config directory
echo ""
echo "6️⃣ Setting up Continue.dev configuration..."
CONTINUE_DIR="$HOME/.continue"
mkdir -p "$CONTINUE_DIR"

# Copy template if Continue directory exists
if [ -d "$CONTINUE_DIR" ]; then
    echo "📁 Continue.dev config directory found"
    echo "   You can copy the config template with:"
    echo "   cp continue_config_template.ts $CONTINUE_DIR/config.ts"
else
    echo "⚠️  Continue.dev config directory not found. It will be created when you first open Continue in VS Code."
fi

# Step 7: Test the setup
echo ""
echo "7️⃣ Ready to test!"
echo ""
echo "📋 Quick Start Guide:"
echo "   1. Start the adapter: ./start_adapter.sh"
echo "   2. Test the integration: python test_integration.py"
echo "   3. Open VS Code and configure Continue.dev"
echo ""
echo "🔧 Manual start options:"
echo "   Development mode: uvicorn elder_servant_adapter:app --reload"
echo "   Production mode: python elder_servant_adapter.py"
echo ""
echo "✅ Setup complete!"
