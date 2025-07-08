import subprocess
import time
import logging

logger = logging.getLogger(__name__)

class FirefoxContainerClick:
    def __init__(self, container_name="firefox"):
        self.container_name = container_name
        self.display = ":0"  # jlesage/firefox uses DISPLAY=:0
    
    def click_at_position(self, x: int, y: int):
        """Click at specific position in Firefox container"""
        try:
            logger.info(f"Clicking at position ({x}, {y}) in Firefox container")
            
            # Move mouse and click
            move_cmd = [
                "docker", "exec", "-e", f"DISPLAY={self.display}",
                self.container_name, "xdotool", "mousemove", str(x), str(y)
            ]
            
            click_cmd = [
                "docker", "exec", "-e", f"DISPLAY={self.display}",
                self.container_name, "xdotool", "click", "1"
            ]
            
            # Execute move
            subprocess.run(move_cmd, check=True, timeout=10)
            time.sleep(0.5)
            
            # Execute click
            subprocess.run(click_cmd, check=True, timeout=10)
            
            logger.info("Click executed successfully in Firefox container")
            return True
            
        except Exception as e:
            logger.error(f"Click operation failed: {e}")
            return False

# Global instance
firefox_container_click = FirefoxContainerClick()