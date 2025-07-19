#!/bin/bash
"""
Virtual Display Setup for WSL2 GUI Testing
Sets up Xvfb virtual display for headless browser testing
"""

echo "🖥️ Setting up Virtual Display for GUI Testing in WSL2..."

# Function to check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        echo "✅ Running with root privileges"
        return 0
    else
        echo "❌ This script requires root privileges"
        echo "   Run with: sudo bash setup_virtual_display.sh"
        return 1
    fi
}

# Install system dependencies
install_dependencies() {
    echo "📦 Installing system dependencies..."

    apt update

    # Core display and browser dependencies
    apt install -y \
        xvfb \
        x11-utils \
        x11-xserver-utils \
        xauth \
        libnss3 \
        libnspr4 \
        libasound2t64 \
        libxss1 \
        libgconf-2-4 \
        libxrandr2 \
        libxcomposite1 \
        libxcursor1 \
        libxdamage1 \
        libxi6 \
        libxtst6 \
        libnss3-dev \
        libgdk-pixbuf2.0-0 \
        libgtk-3-0 \
        libxss1

    # Install browsers
    echo "🌐 Installing browsers..."
    apt install -y chromium-browser firefox-esr

    # Install browser drivers
    echo "🔧 Installing browser drivers..."
    apt install -y chromium-chromedriver

    echo "✅ System dependencies installed"
}

# Setup virtual display service
setup_virtual_display() {
    echo "🖥️ Setting up virtual display service..."

    # Create systemd service for virtual display
    cat > /etc/systemd/system/xvfb.service << 'EOF'
[Unit]
Description=X Virtual Frame Buffer Service
After=network.target

[Service]
Type=forking
User=root
ExecStart=/usr/bin/Xvfb :99 -screen 0 1920x1080x24 -ac +extension GLX +render -noreset
ExecStop=/usr/bin/killall Xvfb
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

    # Enable and start the service
    systemctl daemon-reload
    systemctl enable xvfb
    systemctl start xvfb

    echo "✅ Virtual display service configured"
}

# Create GUI testing environment setup script
create_test_environment() {
    echo "🧪 Creating GUI testing environment..."

    cat > /usr/local/bin/gui-test-env << 'EOF'
#!/bin/bash
# GUI Testing Environment Setup

export DISPLAY=:99
export CHROME_BIN=/usr/bin/chromium-browser
export CHROMIUM_BIN=/usr/bin/chromium-browser

# Check if Xvfb is running
if ! pgrep -x "Xvfb" > /dev/null; then
    echo "Starting virtual display..."
    Xvfb :99 -screen 0 1920x1080x24 -ac +extension GLX +render -noreset &
    sleep 2
fi

echo "🖥️ Virtual display available at :99"
echo "🌐 Chrome binary: $CHROME_BIN"
echo "Ready for GUI testing!"

# Run command if provided
if [ $# -gt 0 ]; then
    exec "$@"
fi
EOF

    chmod +x /usr/local/bin/gui-test-env

    echo "✅ GUI testing environment script created at /usr/local/bin/gui-test-env"
}

# Create Python testing wrapper
create_python_wrapper() {
    echo "🐍 Creating Python GUI testing wrapper..."

    cat > /usr/local/bin/python-gui-test << 'EOF'
#!/bin/bash
# Python GUI Testing Wrapper

# Set environment variables
export DISPLAY=:99
export CHROME_BIN=/usr/bin/chromium-browser
export CHROMIUM_BIN=/usr/bin/chromium-browser

# Ensure virtual display is running
if ! pgrep -x "Xvfb" > /dev/null; then
    echo "Starting virtual display..."
    Xvfb :99 -screen 0 1920x1080x24 -ac +extension GLX +render -noreset &
    sleep 2
fi

# Create virtual environment if it doesn't exist
if [ ! -d "/opt/gui-test-env" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv /opt/gui-test-env
    source /opt/gui-test-env/bin/activate
    pip install selenium webdriver-manager playwright pytest-playwright
    playwright install chromium firefox
fi

# Activate environment and run
source /opt/gui-test-env/bin/activate
exec python3 "$@"
EOF

    chmod +x /usr/local/bin/python-gui-test

    echo "✅ Python GUI testing wrapper created at /usr/local/bin/python-gui-test"
}

# Verify installation
verify_installation() {
    echo "🔍 Verifying installation..."

    # Check if Xvfb is running
    if pgrep -x "Xvfb" > /dev/null; then
        echo "✅ Xvfb virtual display is running"
    else
        echo "❌ Xvfb virtual display is not running"
        return 1
    fi

    # Check browser installations
    if command -v chromium-browser &> /dev/null; then
        echo "✅ Chromium browser installed"
    else
        echo "❌ Chromium browser not found"
    fi

    if command -v firefox &> /dev/null; then
        echo "✅ Firefox browser installed"
    else
        echo "❌ Firefox browser not found"
    fi

    # Test display
    export DISPLAY=:99
    if xset q &> /dev/null; then
        echo "✅ Virtual display is accessible"
    else
        echo "❌ Virtual display is not accessible"
        return 1
    fi

    echo "🎉 Installation verification complete!"
}

# Main execution
main() {
    echo "🚀 WSL2 GUI Testing Setup"
    echo "========================="

    if ! check_root; then
        exit 1
    fi

    install_dependencies
    setup_virtual_display
    create_test_environment
    create_python_wrapper
    verify_installation

    echo ""
    echo "🎉 Setup Complete!"
    echo ""
    echo "Usage:"
    echo "  Regular user can now run:"
    echo "    gui-test-env python3 gui_test_script.py"
    echo "    python-gui-test gui_test_script.py"
    echo ""
    echo "Environment variables:"
    echo "    DISPLAY=:99"
    echo "    CHROME_BIN=/usr/bin/chromium-browser"
    echo ""
}

# Run if executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
