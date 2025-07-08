from typing import Union
import time
import random
import logging
from cloudflare_bypass.cloudflare_detector import CloudFlareLogoDetector, CloudFlarePopupDetector

logger = logging.getLogger(__name__)

def wait_until(detector, warmup_time: Union[None, int] = None, timeout: int = 20):
    """
    Wait until a detector is detected or timeout is reached.
    """
    if warmup_time:
        time.sleep(warmup_time)

    t0 = time.time()
    while True:
        time.sleep(1)
        if detector.is_detected():
            return detector.matched_bbox

        if time.time() - t0 > timeout:
            break

def click_like_human(client, x: int, y: int, max_value: int = 5):
    """改进的点击函数，接受client参数"""
    delta_x = random.randint(-max_value, max_value)
    delta_y = random.randint(-max_value, max_value)
    try:
        client.mouseMove(x + delta_x, y + delta_y)
        time.sleep(0.1)  # 短暂延迟模拟人类行为
        client.mousePress(1)
        time.sleep(0.05)
        client.mouseRelease(1)
        logger.info(f"点击坐标: ({x + delta_x}, {y + delta_y})")
    except Exception as e:
        logger.error(f"点击失败: {e}")

def improved_bypass(
    mode: str = 'light',
    warmup_time: int = None,
    timeout: int = 30,
    interval: float = 0.5,
    threshold: float = 0.6,  # 降低默认阈值
    max_attempts: int = 5
):
    """
    改进的 CloudFlare 绕过函数
    
    主要改进：
    1. 降低检测阈值，提高检测成功率
    2. 同时尝试多种模式和阈值
    3. 更灵活的检测逻辑
    4. 增加详细日志
    """
    logger.info(f"开始 CloudFlare 绕过检测 - 模式: {mode}, 阈值: {threshold}")
    
    # 可选的预热时间
    if warmup_time is not None and isinstance(warmup_time, (int, float)):
        logger.info(f"预热等待 {warmup_time} 秒")
        time.sleep(warmup_time)

    # 尝试多个阈值，从高到低
    thresholds_to_try = [threshold, threshold - 0.1, threshold - 0.2, 0.4]
    modes_to_try = [mode, 'dark' if mode == 'light' else 'light']  # 也尝试另一种模式
    
    t0 = time.time()
    clicked = False
    detection_attempts = 0
    
    while time.time() - t0 < timeout and detection_attempts < max_attempts:
        detection_attempts += 1
        logger.info(f"第 {detection_attempts} 次检测尝试")
        
        # 尝试不同的模式和阈值组合
        for current_mode in modes_to_try:
            for current_threshold in thresholds_to_try:
                try:
                    logger.info(f"尝试模式: {current_mode}, 阈值: {current_threshold}")
                    
                    # 初始化检测器
                    cf_popup_detector = CloudFlarePopupDetector(mode=current_mode, threshold=current_threshold)
                    cf_logo_detector = CloudFlareLogoDetector(mode=current_mode, threshold=current_threshold)
                    
                    # 检测 popup（验证按钮）
                    popup_detected = cf_popup_detector.is_detected()
                    logo_detected = cf_logo_detector.is_detected()
                    
                    logger.info(f"Popup 检测结果: {popup_detected}, Logo 检测结果: {logo_detected}")
                    
                    # 如果检测到 popup，尝试点击
                    if popup_detected and not clicked:
                        x1, y1, x2, y2 = cf_popup_detector.matched_bbox
                        # 点击 popup 的左侧区域（通常是复选框位置）
                        cx = x1 + int((x2 - x1) * 0.1)
                        cy = (y1 + y2) // 2
                        
                        logger.info(f"检测到 CAPTCHA popup，准备点击坐标: ({cx}, {cy})")
                        click_like_human(cf_popup_detector.client, cx, cy)
                        clicked = True
                        
                        # 点击后等待一段时间让页面响应
                        logger.info("点击完成，等待页面响应...")
                        time.sleep(2)
                        
                        # 检查是否成功（logo 消失）
                        if not cf_logo_detector.is_detected():
                            logger.info("CAPTCHA 绕过成功！Logo 已消失")
                            return True
                    
                    # 如果只检测到 logo 但没有 popup，可能是不同类型的验证
                    elif logo_detected and not popup_detected:
                        logger.warning("检测到 CloudFlare logo 但未检测到 popup，可能是不同类型的验证")
                        # 可以在这里添加其他类型验证的处理逻辑
                    
                except Exception as e:
                    logger.error(f"检测过程中出错 (模式: {current_mode}, 阈值: {current_threshold}): {e}")
                    continue
        
        # 如果已经点击过，检查是否成功
        if clicked:
            try:
                # 重新检测 logo 是否消失
                cf_logo_detector = CloudFlareLogoDetector(mode=mode, threshold=0.6)
                if not cf_logo_detector.is_detected():
                    logger.info("验证成功，CloudFlare logo 已消失")
                    return True
                else:
                    logger.info("点击后 logo 仍然存在，继续监控...")
            except Exception as e:
                logger.error(f"验证检查时出错: {e}")
        
        # 等待下次检测
        time.sleep(interval)
    
    if clicked:
        logger.info("已尝试点击但可能需要更多时间验证")
        return True  # 已经尝试了点击，认为部分成功
    else:
        logger.warning(f"在 {timeout} 秒内未检测到可点击的 CAPTCHA 元素")
        return False

# 为了向后兼容，保留原函数名
def bypass(
    mode: str = 'light',
    warmup_time: int = None,
    timeout: int = 20,
    interval: int = 1,
    threshold: float = 0.8,
):
    """向后兼容的 bypass 函数，调用改进版本"""
    return improved_bypass(
        mode=mode,
        warmup_time=warmup_time,
        timeout=timeout,
        interval=interval,
        threshold=threshold
    )