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
            
            # 第二步：尝试多种点击方式
            logger.info("尝试多种点击方式...")
            
            # 方式1: 标准双击
            logger.info("方式1: 尝试双击...")
            double_click_cmd = [
                "vncdo", "-s", f"{self.vnc_host}::{self.vnc_port}",
                "click", "1",
                "pause", "0.1",
                "click", "1"
            ]
            
            subprocess.run(
                double_click_cmd,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10
            )
            
            time.sleep(1)
            logger.info("双击完成")
            
            # 方式2: 右键点击
            logger.info("方式2: 尝试右键点击...")
            right_click_cmd = [
                "vncdo", "-s", f"{self.vnc_host}::{self.vnc_port}",
                "click", "3"
            ]
            
            subprocess.run(
                right_click_cmd,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5
            )
            
            time.sleep(0.5)
            
            # 方式3: 键盘空格键（有时复选框响应空格）
            logger.info("方式3: 尝试空格键...")
            space_cmd = [
                "vncdo", "-s", f"{self.vnc_host}::{self.vnc_port}",
                "key", "space"
            ]
            
            subprocess.run(
                space_cmd,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5
            )
            
            time.sleep(0.5)
            
            # 方式4: Enter键
            logger.info("方式4: 尝试Enter键...")
            enter_cmd = [
                "vncdo", "-s", f"{self.vnc_host}::{self.vnc_port}",
                "key", "Return"
            ]
            
            subprocess.run(
                enter_cmd,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5
            )
            
            time.sleep(0.5)
            
            # 方式5: 长按左键
            logger.info("方式5: 尝试长按左键...")
            long_press_cmd = [
                "vncdo", "-s", f"{self.vnc_host}::{self.vnc_port}",
                "mousedown", "1",
                "pause", "1.0",  # 长按1秒
                "mouseup", "1"
            ]
            
            subprocess.run(
                long_press_cmd,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=15
            )
            
            logger.info("所有点击方式尝试完成")
            
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