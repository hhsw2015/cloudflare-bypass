#!/usr/bin/env python3
"""
Test script for Firefox container click functionality
"""
import logging
from firefox_container_click import firefox_container_click

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_container_setup():
    """Test if the Firefox container is properly setup"""
    print("=== Testing Firefox Container Setup ===")
    
    # Test 1: Check if container is running
    import subprocess
    try:
        result = subprocess.run(["docker", "ps", "--filter", "name=firefox", "--format", "{{.Names}}"], 
                              capture_output=True, text=True)
        if "firefox" in result.stdout:
            print("✓ Firefox container is running")
        else:
            print("✗ Firefox container is not running")
            print("Please start the container first:")
            print("docker run -d --name firefox -p 5800:5800 -p 5900:5900 jlesage/firefox")
            return False
    except Exception as e:
        print(f"✗ Error checking container: {e}")
        return False
    
    # Test 2: Check if xdotool is available
    if firefox_container_click.verify_setup():
        print("✓ xdotool is available in container")
    else:
        print("✗ xdotool not found, attempting installation...")
        if firefox_container_click.install_xdotool():
            print("✓ xdotool installed successfully")
        else:
            print("✗ Failed to install xdotool")
            return False
    
    # Test 3: Get window information
    window_info = firefox_container_click.get_firefox_window_info()
    if window_info:
        print("✓ Can access X11 display in container")
    else:
        print("⚠ Warning: Could not get window info (Firefox might not be open)")
    
    return True

def test_click_functionality():
    """Test clicking functionality"""
    print("\n=== Testing Click Functionality ===")
    
    # Test click at a safe position (center of screen)
    test_positions = [
        (400, 300),  # Center area
        (430, 376),  # Target position
    ]
    
    for x, y in test_positions:
        print(f"Testing click at ({x}, {y})")
        success = firefox_container_click.click_at_position(x, y)
        if success:
            print(f"✓ Click successful at ({x}, {y})")
        else:
            print(f"✗ Click failed at ({x}, {y})")
            # Try alternative methods
            print("Trying alternative methods...")
            alt_success = firefox_container_click.alternative_click_methods(x, y)
            if alt_success:
                print(f"✓ Alternative method successful at ({x}, {y})")
            else:
                print(f"✗ All methods failed at ({x}, {y})")

def main():
    """Main test function"""
    print("Firefox Container Click Test")
    print("=" * 40)
    
    if not test_container_setup():
        print("\nContainer setup failed. Please fix the issues above.")
        return
    
    test_click_functionality()
    
    print("\n=== Test Complete ===")
    print("If all tests passed, the system is ready for CAPTCHA bypass!")

if __name__ == "__main__":
    main()