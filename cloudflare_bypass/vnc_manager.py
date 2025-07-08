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
            
            # 直接移动到目标位置
            logger.info(f"移动鼠标到复选框位置: ({final_x}, {final_y})")
            
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
            
            logger.info(f"鼠标已移动到复选框位置: ({final_x}, {final_y})")
            logger.info("停留2秒让您确认位置...")
            time.sleep(2.0)
            
            # 尝试多种方式确保点击生效
            logger.info("开始尝试触发复选框验证...")
            
            # 方法1：确保鼠标在正确位置并点击
            logger.info("方法1：精确定位并点击...")
            
            # 先确保鼠标在精确位置
            precise_move_cmd = [
                "vncdo", "-s", f"{self.vnc_host}::{self.vnc_port}",
                "move", str(final_x), str(final_y)
            ]
            
            subprocess.run(
                precise_move_cmd,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5
            )
            
            time.sleep(0.5)  # 短暂停顿
            
            # 执行点击
            click_cmd = [
                "vncdo", "-s", f"{self.vnc_host}::{self.vnc_port}",
                "click", "1"
            ]
            
            subprocess.run(
                click_cmd,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5
            )
            
            logger.info("点击完成")
            
            # 方法2：尝试Tab键获得焦点然后空格键
            logger.info("方法2：尝试Tab+Space组合...")
            
            # 按Tab键获得焦点
            tab_cmd = [
                "vncdo", "-s", f"{self.vnc_host}::{self.vnc_port}",
                "key", "Tab"
            ]
            
            subprocess.run(
                tab_cmd,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5
            )
            
            time.sleep(0.3)
            
            # 按空格键激活
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
            
            logger.info("Tab+Space组合完成")
            
            # 方法3：尝试Enter键
            logger.info("方法3：尝试Enter键...")
            
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
            
            logger.info("所有方法尝试完成，等待检查结果...")
            
            logger.info(f"复选框点击完成，强制鼠标停留在目标位置...")
            
            # 强制鼠标停留在目标位置，防止跳回左上角
            time.sleep(0.2)  # 短暂等待
            
            final_move_cmd = [
                "vncdo", "-s", f"{self.vnc_host}::{self.vnc_port}",
                "move", str(final_x), str(final_y)
            ]
            
            subprocess.run(
                final_move_cmd,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5
            )
            
            logger.info(f"鼠标已强制固定在位置: ({final_x}, {final_y})")
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