#!/usr/bin/env python3
"""
Container-specific click methods for Firefox in Docker
"""
import subprocess
import time
import logging
import requests
import json

logger = logging.getLogger(__name__)

class ContainerClickManager:
    def __init__(self, container_name=None, vnc_port=5900):
        self.container_name = container_name
        self.vnc_port = vnc_port
        self.vnc_host = "127.0.0.1"
        self.method = self.detect_available_method()
        logger.info(f"Using container click method: {self.method}")
    
    def detect_available_method(self):
        """Detect which method works for container interaction"""
        methods = [
            ("docker_exec", self.check_docker_exec),
            ("vnc_web", self.check_vnc_web),
            ("selenium_remote", self.check_selenium_remote),
            ("vncdo", self.check_vncdo)
        ]
        
        for method_name, check_func in methods:
            if check_func():
                return method_name
        
        return "vncdo"  # fallback
    
    def check_docker_exec(self):
        """Check if we can execute commands in container"""
        try:
            if self.container_name:
                subprocess.run(["docker", "exec", self.container_name, "echo", "test"], 
                             check=True, capture_output=True)
                return True
        except:
            pass
        return False
    
    def check_vnc_web(self):
        """Check if VNC web interface is available"""
        try:
            response = requests.get(f"http://{self.vnc_host}:{self.vnc_port}", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def check_selenium_remote(self):
        """Check if Selenium remote WebDriver is available"""
        try:
            response = requests.get(f"http://{self.vnc_host}:4444/wd/hub/status", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def check_vncdo(self):
        """Check if vncdo is available"""
        try:
            subprocess.run(["which", "vncdo"], check=True, capture_output=True)
            return True
        except:
            return False
    
    def click_at_position(self, x: int, y: int):
        """Click at specific position using available method"""
        if self.method == "docker_exec":
            return self.docker_exec_click(x, y)
        elif self.method == "vnc_web":
            return self.vnc_web_click(x, y)
        elif self.method == "selenium_remote":
            return self.selenium_remote_click(x, y)
        else:
            return self.vncdo_click(x, y)
    
    def docker_exec_click(self, x: int, y: int):
        """Use docker exec to run xdotool inside container"""
        try:
            logger.info(f"Using docker exec + xdotool to click at ({x}, {y})")
            
            # Check if xdotool is available in container
            subprocess.run([
                "docker", "exec", self.container_name, 
                "which", "xdotool"
            ], check=True, capture_output=True)
            
            # Set DISPLAY environment variable and click
            subprocess.run([
                "docker", "exec", "-e", "DISPLAY=:1", self.container_name,
                "xdotool", "mousemove", str(x), str(y)
            ], check=True)
            
            time.sleep(0.5)
            
            subprocess.run([
                "docker", "exec", "-e", "DISPLAY=:1", self.container_name,
                "xdotool", "click", "1"
            ], check=True)
            
            logger.info("docker exec + xdotool click successful")
            return True
        except Exception as e:
            logger.error(f"docker exec click failed: {e}")
            return False
    
    def vnc_web_click(self, x: int, y: int):
        """Use VNC web interface API for clicking"""
        try:
            logger.info(f"Using VNC web interface to click at ({x}, {y})")
            
            # This would require a VNC web client that exposes an API
            # Most VNC web clients don't have this, but some do
            api_url = f"http://{self.vnc_host}:{self.vnc_port}/api/mouse"
            
            payload = {
                "x": x,
                "y": y,
                "action": "click",
                "button": 1
            }
            
            response = requests.post(api_url, json=payload, timeout=10)
            
            if response.status_code == 200:
                logger.info("VNC web interface click successful")
                return True
            else:
                logger.warning(f"VNC web interface returned status: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"VNC web interface click failed: {e}")
            return False
    
    def selenium_remote_click(self, x: int, y: int):
        """Use Selenium remote WebDriver to click"""
        try:
            from selenium import webdriver
            from selenium.webdriver.common.action_chains import ActionChains
            from selenium.webdriver.chrome.options import Options
            
            logger.info(f"Using Selenium remote WebDriver to click at ({x}, {y})")
            
            # Connect to remote WebDriver in container
            options = Options()
            driver = webdriver.Remote(
                command_executor=f'http://{self.vnc_host}:4444/wd/hub',
                options=options
            )
            
            # Get current page
            current_url = driver.current_url
            
            # Perform click at coordinates
            actions = ActionChains(driver)
            actions.move_by_offset(x, y).click().perform()
            
            driver.quit()
            logger.info("Selenium remote click successful")
            return True
            
        except Exception as e:
            logger.error(f"Selenium remote click failed: {e}")
            return False
    
    def vncdo_click(self, x: int, y: int):
        """Use vncdo to click (most reliable for containers)"""
        try:
            logger.info(f"Using vncdo to click at ({x}, {y})")
            
            # Enhanced vncdo command with better error handling
            commands = [
                # Method 1: Move and click separately
                ["vncdo", "-s", f"{self.vnc_host}::{self.vnc_port}", "move", str(x), str(y)],
                ["vncdo", "-s", f"{self.vnc_host}::{self.vnc_port}", "click", "1"],
                
                # Method 2: Combined command as backup
                ["vncdo", "-s", f"{self.vnc_host}::{self.vnc_port}", "move", str(x), str(y), "click", "1"]
            ]
            
            # Try method 1 first (separate commands)
            try:
                subprocess.run(commands[0], check=True, timeout=10, capture_output=True)
                time.sleep(0.3)
                subprocess.run(commands[1], check=True, timeout=10, capture_output=True)
                logger.info("vncdo separate commands successful")
                return True
            except:
                # Try method 2 (combined command)
                subprocess.run(commands[2], check=True, timeout=10, capture_output=True)
                logger.info("vncdo combined command successful")
                return True
                
        except Exception as e:
            logger.error(f"vncdo click failed: {e}")
            return False

# Global instance - will be configured based on environment
container_click_manager = ContainerClickManager()