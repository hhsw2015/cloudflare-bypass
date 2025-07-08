"""
简化版的Cloudflare检测器
"""
from pathlib import Path
import cv2
import numpy as np
import subprocess
import time
import logging
import os

# 配置日志
logger = logging.getLogger(__name__)
image_dir = Path(__file__).parent


class CloudFlareDetector:
    """简化版Cloudflare检测器基类"""
    
    def __init__(self, template_path: str, threshold: float = 0.8):
        """
        初始化检测器
        
        Args:
            template_path: 模板图像路径
            threshold: 匹配阈值
        """
        self.template_path = template_path
        self.template = cv2.imread(template_path, 0)
        if self.template is None:
            logger.error(f"无法加载模板图像: {template_path}")
            raise ValueError(f"无法加载模板图像: {template_path}")
        
        self.threshold = threshold
        self.matched_bbox = None
        self.vnc_host = os.getenv("VNC_HOST", "127.0.0.1")
        self.vnc_port = 5900
    
    def _capture_screenshot(self):
        """捕获VNC屏幕截图"""
        screenshot_path = "screenshot.png"
        vncdo_cmd = ["vncdo", "-s", f"{self.vnc_host}::{self.vnc_port}", "capture", screenshot_path]
        
        try:
            result = subprocess.run(vncdo_cmd, check=True, capture_output=True, timeout=30)
            img = cv2.imread(screenshot_path)
            if img is None:
                raise ValueError(f"无法读取截图: {screenshot_path}")
            return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        except Exception as e:
            logger.error(f"捕获VNC截图失败: {e}")
            raise
    
    def is_detected(self):
        """检测是否存在目标图像"""
        try:
            img = self._capture_screenshot()
            img_gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
            
            # 模板匹配
            result = cv2.matchTemplate(img_gray, self.template, cv2.TM_CCOEFF_NORMED)
            _, confidence, _, max_loc = cv2.minMaxLoc(result)
            
            if confidence >= self.threshold:
                h, w = self.template.shape
                top_left = max_loc
                bottom_right = (top_left[0] + w, top_left[1] + h)
                self.matched_bbox = (top_left[0], top_left[1], bottom_right[0], bottom_right[1])
                logger.info(f"检测成功，置信度: {confidence:.3f}")
                return True
            else:
                logger.debug(f"未检测到目标，置信度: {confidence:.3f}")
                return False
                
        except Exception as e:
            logger.error(f"检测失败: {e}")
            return False


class CloudFlarePopupDetector(CloudFlareDetector):
    def __init__(self, mode: str = 'light', threshold: float = 0.8):
        """
        初始化 CloudFlare 弹窗检测器
        
        Args:
            mode: 模式 ('light' 或 'dark')
            threshold: 匹配阈值
        """
        if mode == 'light':
            template_path = str(image_dir / 'images/cf_popup.png')
        else:
            template_path = str(image_dir / 'images/cf_popup_dark.png')
        
        super().__init__(template_path=template_path, threshold=threshold)


class CloudFlareLogoDetector(CloudFlareDetector):
    def __init__(self, mode: str = 'light', threshold: float = 0.8):
        """
        初始化 CloudFlare logo 检测器
        
        Args:
            mode: 模式 ('light' 或 'dark')
            threshold: 匹配阈值
        """
        if mode == 'light':
            template_path = str(image_dir / 'images/cf_logo.png')
        else:
            template_path = str(image_dir / 'images/cf_logo_dark.png')
        
        super().__init__(template_path=template_path, threshold=threshold)