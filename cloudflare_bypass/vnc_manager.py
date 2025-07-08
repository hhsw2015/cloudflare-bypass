"""
VNC操作管理器 - 使用vncdo命令执行鼠标操作，避免连接管理问题
"""
import logging
import time
import os
import subprocess
import random

logger = logging.getLogger(__name__)

class VNCManager:
    """VNC操作管理器，使用vncdo命令"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VNCManager, cls).__new__(cls)
            cls._instance.vnc_host = os.getenv("VNC_HOST", "127.0.0.1")
            cls._instance.vnc_port = 5900
        return cls._instance
    
    def click(self, x: int, y: int, max_value: int = 5):
        """使用vncdo命令执行点击操作"""
        try:
            # 添加随机偏移模拟人类行为
            delta_x = random.randint(-max_value, max_value)
            delta_y = random.randint(-max_value, max_value)
            final_x = x + delta_x
            final_y = y + delta_y
            
            logger.info(f"使用vncdo执行点击操作: ({final_x}, {final_y})")
            
            # 构建vncdo命令
            vncdo_cmd = [
                "vncdo", "-s", f"{self.vnc_host}::{self.vnc_port}",
                "move", str(final_x), str(final_y),
                "click", "1"
            ]
            
            # 执行命令
            result = subprocess.run(
                vncdo_cmd,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=15
            )
            
            logger.info(f"vncdo点击命令执行成功: {result.stdout}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"vncdo点击命令失败: {e.stderr}")
            return False
        except subprocess.TimeoutExpired:
            logger.error("vncdo点击命令超时")
            return False
        except Exception as e:
            logger.error(f"vncdo点击操作异常: {e}")
            return False
    
    def move_and_click(self, x: int, y: int, max_value: int = 2):
        """移动到精确位置并点击，鼠标保持在该位置"""
        try:
            # 减少随机偏移，只在X轴小幅调整
            delta_x = random.randint(-max_value, max_value)
            delta_y = 0  # Y轴不偏移，保持精确定位
            final_x = x + delta_x
            final_y = y + delta_y
            
            logger.info(f"使用vncdo执行移动和点击: ({final_x}, {final_y})")
            
            # 使用单个命令完成移动和点击，避免鼠标跳回
            click_cmd = [
                "vncdo", "-s", f"{self.vnc_host}::{self.vnc_port}",
                "move", str(final_x), str(final_y),
                "pause", "1",  # 停留1秒
                "click", "1"
            ]
            
            result = subprocess.run(
                click_cmd,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=15
            )
            
            logger.info(f"鼠标移动并点击成功: ({final_x}, {final_y})")
            logger.info("鼠标将保持在当前位置")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"vncdo操作失败: {e.stderr}")
            return False
        except subprocess.TimeoutExpired:
            logger.error("vncdo操作超时")
            return False
        except Exception as e:
            logger.error(f"vncdo操作异常: {e}")
            return False
    
    def get_client(self):
        """为了兼容性保留，但不再使用"""
        return self
    
    def disconnect(self):
        """无需断开连接，因为使用命令行工具"""
        pass

# 全局VNC管理器实例
vnc_manager = VNCManager()