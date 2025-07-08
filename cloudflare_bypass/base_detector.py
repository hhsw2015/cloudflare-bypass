from typing import Union, Tuple
import cv2
import numpy as np
from vncdotool import api
import time
import logging
import os
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
        self._connect_vnc()

    def _connect_vnc(self):
        """建立或重新建立 VNC 连接，带重试逻辑"""
        # 避免频繁断开，仅在必要时断开
        if self.client:
            try:
                if self.client.transport and self.client.transport.connected:
                    logger.info("现有 VNC 连接仍然有效，无需重新连接")
                    return
                self.client.disconnect()
                logger.info("已断开现有 VNC 连接")
            except Exception as e:
                logger.warning(f"断开 VNC 连接时出错: {e}")
            self.client = None

        max_retries = 10
        initial_delay = 10  # 初始延迟 10 秒
        retry_interval = 5  # 重试间隔 5 秒
        logger.info(f"等待 {initial_delay} 秒以确保 VNC 服务器启动")
        time.sleep(initial_delay)

        for attempt in range(max_retries):
            try:
                logger.info(f"第 {attempt + 1}/{max_retries} 次尝试: 连接到 VNC 服务器 {self.vnc_host}:{self.vnc_port}")
                self.client = api.connect(f"{self.vnc_host}:{self.vnc_port}", password=self.vnc_password, timeout=30)
                logger.info("VNC 连接成功")
                return
            except ConnectionRefusedError as e:
                logger.error(f"第 {attempt + 1} 次连接失败: 连接被拒绝 - {e}")
                self.client = None
                if attempt < max_retries - 1:
                    logger.info(f"等待 {retry_interval} 秒后重试")
                    time.sleep(retry_interval)
                else:
                    logger.error("无法连接到 VNC 服务器，已达最大重试次数")
                    raise RuntimeError(f"无法连接到 VNC 服务器 {self.vnc_host}:{self.vnc_port}: {e}")
            except Exception as e:
                logger.error(f"第 {attempt + 1} 次连接失败: {e}")
                self.client = None
                if attempt < max_retries - 1:
                    logger.info(f"等待 {retry_interval} 秒后重试")
                    time.sleep(retry_interval)
                else:
                    logger.error("无法连接到 VNC 服务器，已达最大重试次数")
                    raise RuntimeError(f"无法连接到 VNC 服务器 {self.vnc_host}:{self.vnc_port}: {e}")

    def _capture_vnc_screenshot(self):
        """捕获 VNC 屏幕截图，带重试逻辑和连接状态检查"""
        max_retries = 5
        retry_interval = 3
        for attempt in range(max_retries):
            try:
                if self.client is None:
                    logger.warning("VNC 客户端未初始化，尝试重新连接")
                    self._connect_vnc()
                logger.info("正在捕获 VNC 截图")
                self.client.captureScreen("screenshot.png")
                img = cv2.imread("screenshot.png")
                if img is None:
                    raise ValueError("无法读取截图")
                logger.info("VNC 截图捕获成功")
                return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            except AttributeError as e:
                logger.error(f"截图尝试 {attempt + 1} 失败: {e} (可能是客户端对象无效)")
                self.client = None
                try:
                    self._connect_vnc()
                except RuntimeError as conn_err:
                    logger.error(f"重新连接失败: {conn_err}")
                if attempt < max_retries - 1:
                    logger.info(f"等待 {retry_interval} 秒后重试")
                    time.sleep(retry_interval)
                else:
                    logger.error("捕获 VNC 截图失败，已达最大重试次数")
                    raise RuntimeError(f"捕获 VNC 截图失败: {e}")
            except (ConnectionRefusedError, ValueError) as e:
                logger.warning(f"截图尝试 {attempt + 1} 失败: {e}")
                self.client = None
                try:
                    self._connect_vnc()
                except RuntimeError as conn_err:
                    logger.error(f"重新连接失败: {conn_err}")
                if attempt < max_retries - 1:
                    logger.info(f"等待 {retry_interval} 秒后重试")
                    time.sleep(retry_interval)
                else:
                    logger.error("捕获 VNC 截图失败，已达最大重试次数")
                    raise RuntimeError(f"捕获 VNC 截图失败: {e}")
            except Exception as e:
                logger.warning(f"截图尝试 {attempt + 1} 失败: {e}")
                self.client = None
                try:
                    self._connect_vnc()
                except RuntimeError as conn_err:
                    logger.error(f"重新连接失败: {conn_err}")
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
        使用 vncdotool 模拟人类点击，带随机偏移。

        参数:
            - x (int): 点击的 X 坐标。
            - y (int): 点击的 Y 坐标。
            - max_value (int): 坐标的最大随机偏移量。
        """
        try:
            if self.client is None:
                logger.warning("VNC 客户端未初始化，尝试重新连接")
                self._connect_vnc()
            delta_x = random.randint(-max_value, max_value)
            delta_y = random.randint(-max_value, max_value)
            click_x, click_y = x + delta_x, y + delta_y
            logger.info(f"移动鼠标到 ({click_x}, {click_y})")
            self.client.mouseMove(click_x, click_y)
            self.client.mousePress(1)  # 左键按下
            self.client.mouseRelease(1)  # 左键释放
            logger.info(f"点击位置 ({click_x}, {click_y})")
        except Exception as e:
            logger.error(f"点击失败: {e}")
            self.client = None
            self._connect_vnc()
