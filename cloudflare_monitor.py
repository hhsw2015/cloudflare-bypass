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
    
    def __init__(self, debug_mode=False):
        # 基本配置
        self.vnc_host = os.getenv("VNC_HOST", "127.0.0.1")
        self.vnc_port = 5900
        self.container_name = os.getenv("CONTAINER_NAME", "firefox")
        self.threshold = 0.6  # 匹配阈值
        self.debug_mode = debug_mode
        
        # 加载Cloudflare logo模板
        image_dir = Path(__file__).parent / "images"
        template_path = str(image_dir / "cf_logo.png")
        self.template = cv2.imread(template_path, 0)
        if self.template is None:
            raise ValueError(f"无法加载模板图像: {template_path}")
        
        # 加载谷歌语音验证按钮模板
        voice_template_path = str(image_dir / "voice_button.png")
        self.voice_template = cv2.imread(voice_template_path, 0)
        if self.voice_template is None:
            raise ValueError(f"无法加载语音按钮模板图像: {voice_template_path}")
    
    def capture_screenshot(self, max_retries=3, timeout=15):
        """捕获VNC屏幕截图，带重试机制"""
        screenshot_path = "screenshot.png"
        vncdo_cmd = ["vncdo", "-s", f"{self.vnc_host}::{self.vnc_port}", "capture", screenshot_path]
        
        for attempt in range(max_retries):
            try:
                logger.debug(f"截图尝试 {attempt + 1}/{max_retries}")
                subprocess.run(vncdo_cmd, check=True, capture_output=True, timeout=timeout)
                img = cv2.imread(screenshot_path)
                if img is None:
                    raise ValueError(f"无法读取截图")
                return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            except subprocess.TimeoutExpired:
                logger.warning(f"截图超时 (尝试 {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    time.sleep(2)  # 等待2秒后重试
                else:
                    logger.error(f"截图失败: 已达最大重试次数")
                    raise
            except Exception as e:
                logger.warning(f"截图失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)  # 等待2秒后重试
                else:
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
    
    def detect_google_voice_button(self):
        """检测谷歌语音验证按钮"""
        try:
            # 捕获屏幕截图
            img = self.capture_screenshot()
            img_gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
            
            # 调试模式：保存当前截图
            if self.debug_mode:
                debug_screenshot_path = f"debug_voice_screenshot_{int(time.time())}.png"
                cv2.imwrite(debug_screenshot_path, img_gray)
                logger.info(f"调试模式：已保存截图到 {debug_screenshot_path}")
            
            # 模板匹配
            result = cv2.matchTemplate(img_gray, self.voice_template, cv2.TM_CCOEFF_NORMED)
            _, confidence, _, max_loc = cv2.minMaxLoc(result)
            
            # 显示置信度信息
            logger.info(f"谷歌语音按钮检测置信度: {confidence:.3f}, 当前阈值: {self.threshold}")
            
            if confidence >= self.threshold:
                h, w = self.voice_template.shape
                top_left = max_loc
                bottom_right = (top_left[0] + w, top_left[1] + h)
                bbox = (top_left[0], top_left[1], bottom_right[0], bottom_right[1])
                logger.info(f"✅ 检测到谷歌语音验证按钮，置信度: {confidence:.3f}")
                return True, bbox
            else:
                # 尝试多个较低阈值
                lower_thresholds = [0.5, 0.4, 0.3]
                for lower_threshold in lower_thresholds:
                    if confidence >= lower_threshold:
                        logger.warning(f"⚠️ 使用较低阈值({lower_threshold})检测到可能的语音按钮，置信度: {confidence:.3f}")
                        h, w = self.voice_template.shape
                        top_left = max_loc
                        bottom_right = (top_left[0] + w, top_left[1] + h)
                        bbox = (top_left[0], top_left[1], bottom_right[0], bottom_right[1])
                        logger.info(f"按钮位置: ({top_left[0]},{top_left[1]})-({bottom_right[0]},{bottom_right[1]})")
                        return True, bbox
                
                logger.info(f"❌ 未检测到语音按钮，最高置信度: {confidence:.3f}")
                return False, None
                
        except Exception as e:
            logger.error(f"谷歌语音按钮检测失败: {e}")
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
    
    def calculate_voice_button_click_position(self, bbox):
        """计算谷歌语音按钮点击位置"""
        x1, y1, x2, y2 = bbox
        
        # 点击位置：按钮中心
        click_x = (x1 + x2) // 2
        click_y = (y1 + y2) // 2
        
        logger.info(f"计算语音按钮点击位置: 按钮位置({x1},{y1})-({x2},{y2}) -> 点击位置({click_x},{click_y})")
        return click_x, click_y
    
    def handle_google_voice_verification(self, timeout=30):
        """处理谷歌语音验证，返回是否成功点击"""
        logger.info("🔍 开始检测谷歌语音验证按钮...")
        start_time = time.time()
        consecutive_failures = 0
        max_consecutive_failures = 3
        
        while (time.time() - start_time) < timeout:
            try:
                detected, bbox = self.detect_google_voice_button()
                
                if detected:
                    logger.info("发现谷歌语音验证按钮！")
                    
                    # 计算点击位置
                    click_x, click_y = self.calculate_voice_button_click_position(bbox)
                    
                    # 发送点击命令
                    if self.send_click(click_x, click_y):
                        logger.info("✅ 谷歌语音验证按钮点击成功！")
                        return True
                    else:
                        logger.error("❌ 语音按钮点击失败")
                        return False
                
                # 重置连续失败计数
                consecutive_failures = 0
                
            except Exception as e:
                consecutive_failures += 1
                logger.warning(f"检测谷歌语音按钮时出错 ({consecutive_failures}/{max_consecutive_failures}): {e}")
                
                # 如果连续失败次数过多，提前退出
                if consecutive_failures >= max_consecutive_failures:
                    logger.error("连续检测失败次数过多，停止检测谷歌语音验证")
                    break
            
            # 等待一段时间再检测
            time.sleep(3)  # 增加间隔时间，减少VNC压力
        
        logger.info(f"⏰ {timeout}秒内未检测到谷歌语音验证按钮")
        return False
    
    def run_voice_debug_only(self, check_interval=3, voice_timeout=60):
        """
        仅检测谷歌语音按钮的调试模式
        
        Args:
            check_interval: 检测间隔（秒）
            voice_timeout: 谷歌语音验证检测超时时间（秒）
        """
        logger.info("🔧 启动谷歌语音按钮调试模式 - 仅检测语音按钮")
        
        # 直接调用语音验证处理
        voice_success = self.handle_google_voice_verification(timeout=voice_timeout)
        
        if voice_success:
            logger.info("🎉 谷歌语音按钮检测并点击成功！")
            return True
        else:
            logger.info("❌ 谷歌语音按钮检测失败或超时")
            return False
    
    def run_forever(self, check_interval=3, verification_wait=5, exit_on_success=False, voice_timeout=30):
        """
        持续监控模式
        
        Args:
            check_interval: 检测间隔（秒）
            verification_wait: 点击后等待验证的时间（秒）
            exit_on_success: 验证通过后是否退出程序
            voice_timeout: 谷歌语音验证检测超时时间（秒）
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
                            logger.info("✅ Cloudflare人机验证通过成功！")
                            
                            # Cloudflare验证通过后，检测谷歌语音验证按钮
                            voice_success = self.handle_google_voice_verification(timeout=voice_timeout)
                            
                            if voice_success:
                                logger.info("🎉 所有验证完成，程序退出")
                                return True
                            else:
                                # 如果设置了验证通过后退出，即使没有谷歌验证也退出
                                if exit_on_success:
                                    logger.info("👋 Cloudflare验证通过，程序退出")
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
    parser.add_argument("--voice-timeout", type=int, default=30, help="谷歌语音验证检测超时时间（秒），默认为30秒")
    parser.add_argument("--debug", action="store_true", help="启用调试模式，保存截图并显示详细信息")
    parser.add_argument("--voice-only", action="store_true", help="仅检测谷歌语音按钮（调试模式）")
    args = parser.parse_args()
    
    # 创建监控器并运行
    monitor = CloudflareMonitor(debug_mode=args.debug)
    
    if args.voice_only:
        # 仅检测谷歌语音按钮的调试模式
        monitor.run_voice_debug_only(
            check_interval=args.interval,
            voice_timeout=args.voice_timeout
        )
    else:
        # 正常模式：先检测Cloudflare，再检测谷歌语音
        monitor.run_forever(
            check_interval=args.interval,
            verification_wait=args.wait,
            exit_on_success=args.exit,
            voice_timeout=args.voice_timeout
        )