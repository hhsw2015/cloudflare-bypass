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
        """先移动鼠标并停留，然后点击，让用户看清点击位置"""
        try:
            # 减少随机偏移，只在X轴小幅调整
            delta_x = random.randint(-max_value, max_value)
            delta_y = 0  # Y轴不偏移，保持精确定位
            final_x = x + delta_x
            final_y = y + delta_y
            
            # 第一步：先在页面空白处点击获得焦点
            logger.info("第一步：在页面空白处点击获得窗口焦点...")
            
            # 在页面左上角空白处点击获得焦点
            blank_area_cmd = [
                "vncdo", "-s", f"{self.vnc_host}::{self.vnc_port}",
                "move", "100", "100",
                "click", "1"
            ]
            
            subprocess.run(
                blank_area_cmd,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10
            )
            
            logger.info("窗口焦点已获得，等待1秒...")
            time.sleep(1.0)
            
            # 第二步：移动到目标位置
            logger.info(f"第二步：移动鼠标到目标位置: ({final_x}, {final_y})")
            
            move_cmd = [
                "vncdo", "-s", f"{self.vnc_host}::{self.vnc_port}",
                "move", str(final_x), str(final_y)
            ]
            
            subprocess.run(
                move_cmd,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10
            )
            
            logger.info(f"鼠标已移动到: ({final_x}, {final_y}) - 请观察鼠标位置")
            logger.info("停留1秒让您确认位置...")
            time.sleep(1.0)
            
            # 第三步：执行目标点击
            logger.info("第三步：执行复选框点击...")
            
            # 按下鼠标
            logger.info("按下鼠标...")
            press_cmd = [
                "vncdo", "-s", f"{self.vnc_host}::{self.vnc_port}",
                "mousedown", "1"
            ]
            
            subprocess.run(
                press_cmd,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5
            )
            
            # 立即松开
            logger.info("松开鼠标...")
            release_cmd = [
                "vncdo", "-s", f"{self.vnc_host}::{self.vnc_port}",
                "mouseup", "1"
            ]
            
            subprocess.run(
                release_cmd,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5
            )
            
            logger.info(f"复选框点击完成，鼠标保持在位置: ({final_x}, {final_y})")
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