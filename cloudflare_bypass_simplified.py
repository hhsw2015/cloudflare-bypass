#!/usr/bin/env python3
"""
简化的Cloudflare人机验证绕过工具
核心功能：循环检测VMC界面，发现Cloudflare验证时自动点击
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


class CloudflareDetector:
    """Cloudflare验证检测器"""
    
    def __init__(self, threshold: float = 0.6):
        self.threshold = threshold
        self.vnc_host = os.getenv("VNC_HOST", "127.0.0.1")
        self.vnc_port = 5900
        self.matched_bbox = None
        
        # 加载Cloudflare logo模板
        template_path = Path(__file__).parent / "cloudflare_bypass/images/cf_logo.png"
        self.template = cv2.imread(str(template_path), 0)
        if self.template is None:
            logger.error(f"无法加载模板图像: {template_path}")
            raise ValueError(f"无法加载模板图像: {template_path}")
    
    def capture_vnc_screenshot(self):
        """捕获VNC屏幕截图"""
        screenshot_path = "screenshot.png"
        vncdo_cmd = ["vncdo", "-s", f"{self.vnc_host}::{self.vnc_port}", "capture", screenshot_path]
        
        try:
            logger.debug("正在捕获VNC截图...")
            result = subprocess.run(vncdo_cmd, check=True, capture_output=True, timeout=30)
            img = cv2.imread(screenshot_path)
            if img is None:
                raise ValueError(f"无法读取截图: {screenshot_path}")
            return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        except Exception as e:
            logger.error(f"捕获VNC截图失败: {e}")
            raise
    
    def detect_cloudflare(self):
        """检测Cloudflare验证界面"""
        try:
            # 捕获屏幕截图
            img = self.capture_vnc_screenshot()
            img_gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
            
            # 模板匹配
            result = cv2.matchTemplate(img_gray, self.template, cv2.TM_CCOEFF_NORMED)
            _, confidence, _, max_loc = cv2.minMaxLoc(result)
            
            if confidence >= self.threshold:
                h, w = self.template.shape
                top_left = max_loc
                bottom_right = (top_left[0] + w, top_left[1] + h)
                self.matched_bbox = (top_left[0], top_left[1], bottom_right[0], bottom_right[1])
                logger.info(f"检测到Cloudflare验证，置信度: {confidence:.3f}")
                return True
            else:
                logger.debug(f"未检测到Cloudflare验证，置信度: {confidence:.3f}")
                return False
                
        except Exception as e:
            logger.error(f"Cloudflare检测失败: {e}")
            return False


def send_click_to_container(x: int, y: int, container_name: str = "firefox"):
    """向容器发送点击命令"""
    try:
        logger.info(f"向容器 {container_name} 发送点击命令: ({x}, {y})")
        
        # 移动鼠标到指定位置
        move_cmd = [
            "docker", "exec", "-e", "DISPLAY=:0",
            container_name, "xdotool", "mousemove", str(x), str(y)
        ]
        
        # 执行点击
        click_cmd = [
            "docker", "exec", "-e", "DISPLAY=:0",
            container_name, "xdotool", "click", "1"
        ]
        
        # 执行移动命令
        result1 = subprocess.run(move_cmd, capture_output=True, text=True, timeout=10)
        if result1.returncode != 0:
            logger.error(f"鼠标移动失败: {result1.stderr}")
            return False
        
        time.sleep(0.5)  # 短暂延迟
        
        # 执行点击命令
        result2 = subprocess.run(click_cmd, capture_output=True, text=True, timeout=10)
        if result2.returncode != 0:
            logger.error(f"鼠标点击失败: {result2.stderr}")
            return False
        
        logger.info(f"点击命令发送成功: ({x}, {y})")
        return True
        
    except Exception as e:
        logger.error(f"发送点击命令失败: {e}")
        return False


def calculate_click_position(bbox):
    """根据检测到的Cloudflare logo计算点击位置"""
    x1, y1, x2, y2 = bbox
    
    # 点击位置：logo左侧约430像素处，垂直居中
    click_x = 430
    click_y = (y1 + y2) // 2
    
    logger.info(f"计算点击位置: logo位置({x1},{y1})-({x2},{y2}) -> 点击位置({click_x},{click_y})")
    return click_x, click_y


def main_loop():
    """主循环：持续检测VMC界面中的Cloudflare验证"""
    logger.info("开始监控VMC界面中的Cloudflare人机验证...")
    
    detector = CloudflareDetector()
    check_interval = 2  # 检测间隔（秒）
    verification_wait = 5  # 点击后等待验证的时间（秒）
    
    while True:
        try:
            # 检测Cloudflare验证
            if detector.detect_cloudflare():
                logger.info("发现Cloudflare人机验证！")
                
                # 计算点击位置
                click_x, click_y = calculate_click_position(detector.matched_bbox)
                
                # 发送点击命令到容器
                if send_click_to_container(click_x, click_y):
                    logger.info(f"已发送点击命令，等待 {verification_wait} 秒检查验证结果...")
                    time.sleep(verification_wait)
                    
                    # 检查是否通过验证
                    if not detector.detect_cloudflare():
                        logger.info("✅ 人机验证通过成功！")
                        # 可以选择继续监控或退出
                        # break  # 如果只需要通过一次验证就退出，取消注释这行
                    else:
                        logger.info("❌ 验证未通过，继续尝试...")
                else:
                    logger.error("点击命令发送失败")
            else:
                logger.debug("未检测到Cloudflare验证，继续监控...")
            
            # 等待下次检测
            time.sleep(check_interval)
            
        except KeyboardInterrupt:
            logger.info("用户中断，停止监控")
            break
        except Exception as e:
            logger.error(f"监控过程中发生错误: {e}")
            time.sleep(check_interval)


if __name__ == "__main__":
    main_loop()