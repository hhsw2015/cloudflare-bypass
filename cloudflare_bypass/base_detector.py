from typing import Union, Tuple
import cv2
import numpy as np
from vncdotool import api
import time
import logging
import os
import subprocess
from twisted.internet.error import ConnectionRefusedError

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('vnc_debug.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BaseDetector:
    def __init__(self, template_path: str, threshold: float = 0.8) -> None:
        """
        初始化 BaseDetector，加载模板图像并设置 VNC 连接参数。

        参数:
            - template_path (str): 模板图像文件路径。
            - threshold (float): 匹配阈值（默认为 0.8）。
        """
        self.template = cv2.imread(template_path, 0)
        if self.template is None:
            logger.error(f"无法加载模板图像: {template_path}")
            raise ValueError(f"无法加载模板图像: {template_path}")
        self.threshold = threshold
        self.matched_bbox = None
        self.vnc_host = os.getenv("VNC_HOST", "127.0.0.1")  # 支持环境变量配置
        self.vnc_port = 5900
        self.vnc_password = None  # 无密码，与容器配置一致
        self.client = None
        # 不再预先建立VNC连接，因为我们使用vncdo命令

    def _connect_vnc(self):
        """保留此方法以兼容旧代码，但不再实际建立连接"""
        logger.info("跳过VNC连接建立，使用vncdo命令行工具进行操作")
        pass

    def _capture_vnc_screenshot(self):
        """使用 vncdo 命令捕获 VNC 屏幕截图"""
        max_retries = 5
        retry_interval = 3
        screenshot_path = "screenshot.png"
        vncdo_cmd = ["vncdo", "-s", f"{self.vnc_host}::{self.vnc_port}", "capture", screenshot_path]

        for attempt in range(max_retries):
            try:
                logger.info(f"正在执行 vncdo 命令捕获截图: {' '.join(vncdo_cmd)}")
                result = subprocess.run(
                    vncdo_cmd,
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=30
                )
                logger.info(f"vncdo 命令执行成功: {result.stdout}")
                img = cv2.imread(screenshot_path)
                if img is None:
                    raise ValueError(f"无法读取截图: {screenshot_path}")
                logger.info("VNC 截图捕获成功")
                return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            except subprocess.CalledProcessError as e:
                logger.warning(f"截图尝试 {attempt + 1} 失败: vncdo 命令错误 - {e.stderr}")
                if attempt < max_retries - 1:
                    logger.info(f"等待 {retry_interval} 秒后重试")
                    time.sleep(retry_interval)
                else:
                    logger.error("捕获 VNC 截图失败，已达最大重试次数")
                    raise RuntimeError(f"捕获 VNC 截图失败: {e.stderr}")
            except Exception as e:
                logger.warning(f"截图尝试 {attempt + 1} 失败: {e}")
                if attempt < max_retries - 1:
                    logger.info(f"等待 {retry_interval} 秒后重试")
                    time.sleep(retry_interval)
                else:
                    logger.error("捕获 VNC 截图失败，已达最大重试次数")
                    raise RuntimeError(f"捕获 VNC 截图失败: {e}")

    def _match(self, img: np.ndarray, template: np.ndarray) -> Union[None, Tuple[int]]:
        result = cv2.matchTemplate(img, template, cv2.TM_CCOEFF_NORMED)
        _, confidence, _, max_loc = cv2.minMaxLoc(result)
        if confidence >= self.threshold:
            h, w = template.shape
            top_left = max_loc
            bottom_right = (top_left[0] + w, top_left[1] + h)
            logger.info(f"模板匹配成功，置信度 {confidence}")
            return top_left[0], top_left[1], bottom_right[0], bottom_right[1]
        logger.debug(f"无匹配，置信度 {confidence} 低于阈值 {self.threshold}")
        return None

    def is_detected(self) -> bool:
        """
        检查 VNC 截图中是否检测到模板。

        返回:
            - bool: 如果检测到模板返回 True，否则返回 False。
        """
        try:
            img = self._capture_vnc_screenshot()
            img_gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
            self.matched_bbox = self._match(img_gray, self.template)
            return self.matched_bbox is not None
        except Exception as e:
            logger.error(f"检测失败: {e}")
            return False

    def click_like_human(self, x: int, y: int, max_value: int = 5):
        """
        使用 vncdo 命令模拟人类点击，带随机偏移。

        参数:
            - x (int): 点击的 X 坐标。
            - y (int): 点击的 Y 坐标。
            - max_value (int): 坐标的最大随机偏移量。
        """
        try:
            from cloudflare_bypass.vnc_manager import vnc_manager
            success = vnc_manager.move_and_click(x, y, max_value)
            if success:
                logger.info(f"点击操作成功: ({x}, {y})")
            else:
                logger.warning(f"点击操作失败: ({x}, {y})")
            return success
        except Exception as e:
            logger.error(f"点击操作异常: {e}")
            return False
