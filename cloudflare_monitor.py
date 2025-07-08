#!/usr/bin/env python3
"""
Cloudflare 人机验证监控工具 - 超级简化版
只保留核心监听和点击功能
"""

import cv2
import numpy as np
import subprocess
import time
import logging
import os
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CloudflareMonitor:
    """Cloudflare监控器 - 检测验证并自动点击"""
    
    def __init__(self):
        # 基本配置
        self.vnc_host = os.getenv("VNC_HOST", "127.0.0.1")
        self.vnc_port = 5900
        self.container_name = os.getenv("CONTAINER_NAME", "firefox")
        self.threshold = 0.6  # 匹配阈值
        
        # 加载Cloudflare logo模板
        image_dir = Path(__file__).parent / "images"
        template_path = str(image_dir / "cf_logo.png")
        self.template = cv2.imread(template_path, 0)
        if self.template is None:
            raise ValueError(f"无法加载模板图像: {template_path}")
    
    def capture_screenshot(self):
        """捕获VNC屏幕截图"""
        screenshot_path = "screenshot.png"
        vncdo_cmd = ["vncdo", "-s", f"{self.vnc_host}::{self.vnc_port}", "capture", screenshot_path]
        
        try:
            subprocess.run(vncdo_cmd, check=True, capture_output=True, timeout=10)
            img = cv2.imread(screenshot_path)
            if img is None:
                raise ValueError(f"无法读取截图")
            return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        except Exception as e:
            logger.error(f"截图失败: {e}")
            raise
    
    def detect_cloudflare(self):
        """检测Cloudflare验证界面"""
        try:
            # 捕获屏幕截图
            img = self.capture_screenshot()
            img_gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
            
            # 模板匹配
            result = cv2.matchTemplate(img_gray, self.template, cv2.TM_CCOEFF_NORMED)
            _, confidence, _, max_loc = cv2.minMaxLoc(result)
            
            if confidence >= self.threshold:
                h, w = self.template.shape
                top_left = max_loc
                bottom_right = (top_left[0] + w, top_left[1] + h)
                bbox = (top_left[0], top_left[1], bottom_right[0], bottom_right[1])
                logger.info(f"检测到Cloudflare验证，置信度: {confidence:.3f}")
                return True, bbox
            else:
                return False, None
                
        except Exception as e:
            logger.error(f"检测失败: {e}")
            return False, None
    
    def send_click(self, x, y):
        """向容器发送点击命令"""
        try:
            logger.info(f"向容器 {self.container_name} 发送点击命令: ({x}, {y})")
            
            # 移动鼠标
            move_cmd = [
                "docker", "exec", "-e", "DISPLAY=:0",
                self.container_name, "xdotool", "mousemove", str(x), str(y)
            ]
            
            # 执行点击
            click_cmd = [
                "docker", "exec", "-e", "DISPLAY=:0",
                self.container_name, "xdotool", "click", "1"
            ]
            
            # 执行命令
            subprocess.run(move_cmd, check=True, timeout=5)
            time.sleep(0.5)
            subprocess.run(click_cmd, check=True, timeout=5)
            
            logger.info(f"点击命令发送成功: ({x}, {y})")
            return True
            
        except Exception as e:
            logger.error(f"点击命令发送失败: {e}")
            return False
    
    def calculate_click_position(self, bbox):
        """计算点击位置"""
        x1, y1, x2, y2 = bbox
        
        # 点击位置：logo左侧约430像素处，垂直居中
        click_x = 430
        click_y = (y1 + y2) // 2
        
        logger.info(f"计算点击位置: logo位置({x1},{y1})-({x2},{y2}) -> 点击位置({click_x},{click_y})")
        return click_x, click_y
    
    def run_forever(self, check_interval=3, verification_wait=5, exit_on_success=False):
        """
        持续监控模式
        
        Args:
            check_interval: 检测间隔（秒）
            verification_wait: 点击后等待验证的时间（秒）
            exit_on_success: 验证通过后是否退出程序
        """
        logger.info("🚀 启动Cloudflare监控 - 持续监控模式")
        if exit_on_success:
            logger.info("✓ 验证通过后将自动退出程序")
        else:
            logger.info("✓ 验证通过后将继续监控")
        
        while True:
            try:
                # 检测Cloudflare验证
                detected, bbox = self.detect_cloudflare()
                
                if detected:
                    logger.info("发现Cloudflare人机验证！")
                    
                    # 计算点击位置
                    click_x, click_y = self.calculate_click_position(bbox)
                    
                    # 发送点击命令
                    if self.send_click(click_x, click_y):
                        logger.info(f"等待 {verification_wait} 秒检查验证结果...")
                        time.sleep(verification_wait)
                        
                        # 检查是否通过验证
                        still_detected, _ = self.detect_cloudflare()
                        if not still_detected:
                            logger.info("✅ 人机验证通过成功！")
                            
                            # 如果设置了验证通过后退出，则退出程序
                            if exit_on_success:
                                logger.info("👋 验证通过，程序退出")
                                return True
                        else:
                            logger.info("❌ 验证未通过，继续尝试...")
                    else:
                        logger.error("点击命令发送失败")
                
                # 等待下次检测
                time.sleep(check_interval)
                
            except KeyboardInterrupt:
                logger.info("👋 用户中断，停止监控")
                break
            except Exception as e:
                logger.error(f"监控过程中发生错误: {e}")
                time.sleep(check_interval)
        
        return False


if __name__ == "__main__":
    import argparse
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="Cloudflare 人机验证自动绕过工具")
    parser.add_argument("--exit", action="store_true", help="验证通过后自动退出程序")
    parser.add_argument("--interval", type=int, default=3, help="检测间隔（秒），默认为3秒")
    parser.add_argument("--wait", type=int, default=5, help="点击后等待验证的时间（秒），默认为5秒")
    args = parser.parse_args()
    
    # 创建监控器并运行
    monitor = CloudflareMonitor()
    monitor.run_forever(
        check_interval=args.interval,
        verification_wait=args.wait,
        exit_on_success=args.exit
    )