#!/bin/bash
# Setup script for jlesage/firefox container

echo "Setting up Firefox container for automated clicking..."

# 1. Install xdotool in the Firefox container
echo "Installing xdotool in Firefox container..."
docker exec firefox sh -c "
    # Update package list
    apk update
    
    # Install xdotool
    apk add xdotool
    
    # Verify installation
    which xdotool && echo 'xdotool installed successfully' || echo 'xdotool installation failed'
"

# 2. Install additional tools if needed
echo "Installing additional tools..."
docker exec firefox sh -c "
    # Install other useful tools
    apk add xwininfo xprop
    
    echo 'Additional tools installed'
"

# 3. Test the setup
echo "Testing xdotool in container..."
docker exec firefox sh -c "
    export DISPLAY=:0
    xdotool search --name firefox || echo 'Firefox window not found (this is normal if Firefox is not running)'
"

echo "Container setup complete!"
echo "You can now use docker exec commands to control the mouse in the Firefox container."
echo ""
echo "Testing the setup..."
python3 test_firefox_container.py