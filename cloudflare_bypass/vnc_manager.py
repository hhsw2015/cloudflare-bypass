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
            
            logger.info(f"第一步：移动鼠标到目标位置: ({final_x}, {final_y})")
            
            # 第一步：只移动鼠标，不点击
            move_cmd = [
                "vncdo", "-s", f"{self.vnc_host}::{self.vnc_port}",
                "move", str(final_x), str(final_y)
            ]
            
            result = subprocess.run(
                move_cmd,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10
            )
            
            logger.info(f"鼠标已移动到: ({final_x}, {final_y}) - 请观察鼠标位置")
            logger.info("停留1秒让您确认位置...")
            time.sleep(1.0)  # 停留1秒让用户看清位置
            
            # 第二步：执行更人性化的点击操作
            logger.info("现在执行人性化点击操作...")
            
            # 先稍微移动鼠标模拟人类行为
            micro_move_cmd = [
                "vncdo", "-s", f"{self.vnc_host}::{self.vnc_port}",
                "move", str(final_x + 1), str(final_y)
            ]
            
            subprocess.run(
                micro_move_cmd,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5
            )
            
            time.sleep(0.1)  # 短暂停顿
            
            # 移回原位置
            move_back_cmd = [
                "vncdo", "-s", f"{self.vnc_host}::{self.vnc_port}",
                "move", str(final_x), str(final_y)
            ]
            
            subprocess.run(
                move_back_cmd,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5
            )
            
            time.sleep(0.2)  # 稍长停顿
            
            # 执行按下
            mousedown_cmd = [
                "vncdo", "-s", f"{self.vnc_host}::{self.vnc_port}",
                "mousedown", "1"
            ]
            
            subprocess.run(
                mousedown_cmd,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5
            )
            
            logger.info("鼠标按下完成，保持0.3秒...")
            time.sleep(0.3)  # 更长的按压时间
            
            # 执行释放
            mouseup_cmd = [
                "vncdo", "-s", f"{self.vnc_host}::{self.vnc_port}",
                "mouseup", "1"
            ]
            
            subprocess.run(
                mouseup_cmd,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5
            )
            
            logger.info("鼠标释放完成 - 人性化点击操作完成")
            
            # 点击后稍微等待
            time.sleep(0.5)
            
            logger.info(f"点击完成: ({final_x}, {final_y}) - 鼠标保持在当前位置")
            
            # 确保鼠标停留在点击位置，不跳回原位
            logger.info("确保鼠标停留在点击位置...")
            stay_cmd = [
                "vncdo", "-s", f"{self.vnc_host}::{self.vnc_port}",
                "move", str(final_x), str(final_y)
            ]
            
            subprocess.run(
                stay_cmd,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5
            )
            
            logger.info(f"鼠标已固定在位置: ({final_x}, {final_y})")
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