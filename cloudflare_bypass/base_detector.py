from typing import Union, Tuple
import cv2
import numpy as np
from vncdotool import api
import random

class BaseDetector:
    def __init__(self, template_path: str, threshold: float = 0.8) -> None:
        self.template = cv2.imread(template_path, 0)
        self.threshold = threshold
        self.matched_bbox = None
        self.vnc_host = "<你的服务器IP>"  # 替换为实际 IP
        self.vnc_port = 5900
        self.vnc_password = "your_password"  # 替换为实际密码
        self.client = api.connect(f"{self.vnc_host}:{self.vnc_port}", password=self.vnc_password)

    def _capture_vnc_screenshot(self):
        self.client.captureScreen("screenshot.png")
        img = cv2.imread("screenshot.png")
        return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    def _match(self, img: np.ndarray, template: np.ndarray) -> Union[None, Tuple[int]]:
        result = cv2.matchTemplate(img, template, cv2.TM_CCOEFF_NORMED)
        _, confidence, _, max_loc = cv2.minMaxLoc(result)
        if confidence >= self.threshold:
            h, w = template.shape
            top_left = max_loc
            bottom_right = (top_left[0] + w, top_left[1] + h)
            return top_left[0], top_left[1], bottom_right[0], bottom_right[1]
        return None

    def is_detected(self) -> bool:
        img = self._capture_vnc_screenshot()
        img_gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        self.matched_bbox = self._match(img_gray, self.template)
        return self.matched_bbox is not None

    def click_like_human(self, x: int, y: int, max_value: int = 5):
        """使用 vncdotool 模拟鼠标点击"""
        delta_x = random.randint(-max_value, max_value)
        delta_y = random.randint(-max_value, max_value)
        self.client.mouseMove(x + delta_x, y + delta_y)
        self.client.mousePress(1)  # 左键点击
        self.client.mouseRelease(1)
