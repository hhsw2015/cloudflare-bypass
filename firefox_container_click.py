#!/usr/bin/env python3
"""
Firefox container click manager for jlesage/firefox
"""
import subprocess
import time
import logging

logger = logging.getLogger(__name__)

class FirefoxContainerClick:
    def __init__(self, container_name="firefox"):
        self.container_name = container_name
        self.display = ":0"  # jlesage/firefox uses DISPLAY=:0
        self.setup_complete = self.verify_setup()
        
    def verify_setup(self):
        """Verify that xdotool is available in the container"""
        try:
            result = subprocess.run([
                "docker", "exec", self.container_name, 
                "which", "xdotool"
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                logger.info("xdotool is available in Firefox container")
                return True
            else:
                logger.warning("xdotool not found in container. Please run setup_firefox_container.sh first")
                return False
        except Exception as e:
            logger.error(f"Failed to verify container setup: {e}")
            return False
    
    def install_xdotool(self):
        """Install xdotool in the Firefox container"""
        try:
            logger.info("Installing xdotool in Firefox container...")
            
            # Update and install xdotool
            install_cmd = [
                "docker", "exec", self.container_name, "sh", "-c",
                "apk update && apk add xdotool xwininfo"
            ]
            
            result = subprocess.run(install_cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                logger.info("xdotool installed successfully")
                self.setup_complete = True
                return True
            else:
                logger.error(f"Failed to install xdotool: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Exception during xdotool installation: {e}")
            return False
    
    def get_firefox_window_info(self):
        """Get Firefox window information"""
        try:
            # Find Firefox window
            cmd = [
                "docker", "exec", "-e", f"DISPLAY={self.display}", 
                self.container_name, "xwininfo", "-root", "-tree"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                logger.info("Firefox window info retrieved")
                return result.stdout
            else:
                logger.warning("Could not get window info")
                return None
                
        except Exception as e:
            logger.error(f"Failed to get window info: {e}")
            return None
    
    def click_at_position(self, x: int, y: int):
        """Click at specific position in Firefox container"""
        if not self.setup_complete:
            logger.warning("Container not properly setup. Attempting to install xdotool...")
            if not self.install_xdotool():
                logger.error("Failed to setup container. Cannot proceed with click.")
                return False
        
        try:
            logger.info(f"Clicking at position ({x}, {y}) in Firefox container")
            
            # Method 1: Move mouse and click
            move_cmd = [
                "docker", "exec", "-e", f"DISPLAY={self.display}",
                self.container_name, "xdotool", "mousemove", str(x), str(y)
            ]
            
            click_cmd = [
                "docker", "exec", "-e", f"DISPLAY={self.display}",
                self.container_name, "xdotool", "click", "1"
            ]
            
            # Execute move
            result1 = subprocess.run(move_cmd, capture_output=True, text=True, timeout=10)
            if result1.returncode != 0:
                logger.error(f"Mouse move failed: {result1.stderr}")
                return False
            
            time.sleep(0.5)  # Brief pause
            
            # Execute click
            result2 = subprocess.run(click_cmd, capture_output=True, text=True, timeout=10)
            if result2.returncode != 0:
                logger.error(f"Mouse click failed: {result2.stderr}")
                return False
            
            logger.info("Click executed successfully in Firefox container")
            return True
            
        except Exception as e:
            logger.error(f"Click operation failed: {e}")
            return False
    
    def alternative_click_methods(self, x: int, y: int):
        """Try alternative click methods"""
        methods = [
            self.xdotool_direct_click,
            self.xdotool_window_click,
            self.xdotool_force_click
        ]
        
        for i, method in enumerate(methods, 1):
            logger.info(f"Trying alternative click method {i}")
            if method(x, y):
                logger.info(f"Alternative method {i} successful")
                return True
        
        logger.warning("All alternative click methods failed")
        return False
    
    def xdotool_direct_click(self, x: int, y: int):
        """Direct xdotool click command"""
        try:
            cmd = [
                "docker", "exec", "-e", f"DISPLAY={self.display}",
                self.container_name, "xdotool", "mousemove", str(x), str(y), "click", "1"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except:
            return False
    
    def xdotool_window_click(self, x: int, y: int):
        """Click relative to Firefox window"""
        try:
            # Get Firefox window ID
            find_cmd = [
                "docker", "exec", "-e", f"DISPLAY={self.display}",
                self.container_name, "xdotool", "search", "--name", "firefox"
            ]
            
            result = subprocess.run(find_cmd, capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                return False
            
            window_id = result.stdout.strip().split('\n')[0]
            
            # Click in window
            click_cmd = [
                "docker", "exec", "-e", f"DISPLAY={self.display}",
                self.container_name, "xdotool", "mousemove", "--window", window_id, str(x), str(y), "click", "1"
            ]
            
            result = subprocess.run(click_cmd, capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except:
            return False
    
    def xdotool_force_click(self, x: int, y: int):
        """Force click with window focus"""
        try:
            # Focus and click
            cmd = [
                "docker", "exec", "-e", f"DISPLAY={self.display}",
                self.container_name, "sh", "-c",
                f"xdotool mousemove {x} {y} && sleep 0.2 && xdotool click --clearmodifiers 1"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            return result.returncode == 0
        except:
            return False

# Global instance
firefox_container_click = FirefoxContainerClick()