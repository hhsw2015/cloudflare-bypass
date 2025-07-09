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
try:
    import pytesseract
    # 尝试设置tesseract路径（如果需要）
    # pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 显示OCR状态
if OCR_AVAILABLE:
    logger.info("OCR功能可用")
else:
    logger.warning("OCR功能不可用，请安装: pip install pytesseract")

class CloudflareMonitor:
    """Cloudflare监控器 - 检测验证并自动点击"""
    
    def __init__(self, debug_mode=False):
        # 基本配置
        self.vnc_host = os.getenv("VNC_HOST", "127.0.0.1")
        self.vnc_port = 5900
        self.container_name = os.getenv("CONTAINER_NAME", "firefox2")
        self.threshold = 0.5  # 匹配阈值（多模板检测，使用中等阈值）
        self.debug_mode = debug_mode
        
        # 加载Cloudflare logo模板
        image_dir = Path(__file__).parent / "images"
        template_path = str(image_dir / "cf_logo.png")
        self.template = cv2.imread(template_path, 0)
        if self.template is None:
            raise ValueError(f"无法加载模板图像: {template_path}")
        
        # 加载多个谷歌语音验证按钮模板
        self.voice_templates = {}
        template_sizes = ["48_48", "120_120", "512_512"]
        
        for size in template_sizes:
            template_path = str(image_dir / f"voice_button_{size}.png")
            template = cv2.imread(template_path, 0)
            if template is not None:
                self.voice_templates[size] = template
                logger.info(f"已加载语音按钮模板: {size}")
            else:
                logger.warning(f"无法加载语音按钮模板: {template_path}")
        
        if not self.voice_templates:
            raise ValueError("无法加载任何语音按钮模板图像")
    
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
        """检测谷歌语音验证按钮 - 使用多模板检测"""
        try:
            # 捕获屏幕截图
            img = self.capture_screenshot()
            img_gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
            
            # 调试模式：保存当前截图
            if self.debug_mode:
                debug_screenshot_path = f"debug_voice_screenshot_{int(time.time())}.png"
                cv2.imwrite(debug_screenshot_path, img_gray)
                logger.info(f"调试模式：已保存截图到 {debug_screenshot_path}")
            
            best_confidence = 0
            best_bbox = None
            best_template_size = None
            
            # 尝试所有模板
            for size, template in self.voice_templates.items():
                result = cv2.matchTemplate(img_gray, template, cv2.TM_CCOEFF_NORMED)
                _, confidence, _, max_loc = cv2.minMaxLoc(result)
                
                if self.debug_mode:
                    logger.info(f"模板 {size}: 置信度 {confidence:.3f}")
                
                if confidence > best_confidence:
                    best_confidence = confidence
                    h, w = template.shape
                    top_left = max_loc
                    bottom_right = (top_left[0] + w, top_left[1] + h)
                    best_bbox = (top_left[0], top_left[1], bottom_right[0], bottom_right[1])
                    best_template_size = size
            
            # 在调试模式下显示最佳检测结果
            if self.debug_mode and best_bbox:
                x1, y1, x2, y2 = best_bbox
                center_x = (x1 + x2) // 2
                center_y = (y1 + y2) // 2
                logger.info(f"最佳匹配: 模板 {best_template_size}, 置信度 {best_confidence:.3f}")
                logger.info(f"检测到的位置: ({x1},{y1})-({x2},{y2})")
                logger.info(f"检测位置中心: ({center_x}, {center_y})")
                logger.info(f"正确的点击位置应该是: (735, 985)")
            
            if best_confidence >= self.threshold:
                logger.info(f"✅ 检测到谷歌语音按钮，最佳模板: {best_template_size}, 置信度: {best_confidence:.3f}")
                return True, best_bbox
            else:
                if self.debug_mode:
                    logger.info(f"❌ 未检测到语音按钮，最高置信度: {best_confidence:.3f} < 阈值: {self.threshold}")
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
    
    def move_mouse_and_wait(self, x, y, wait_time=1.0):
        """移动鼠标到指定位置并等待"""
        try:
            logger.info(f"移动鼠标到位置: ({x}, {y})")
            
            # 移动鼠标命令
            move_cmd = [
                "docker", "exec", "-e", "DISPLAY=:0",
                self.container_name, "xdotool", "mousemove", str(x), str(y)
            ]
            
            # 执行移动命令
            subprocess.run(move_cmd, check=True, timeout=5)
            logger.info(f"鼠标已移动到 ({x}, {y})，等待 {wait_time} 秒...")
            
            # 等待指定时间
            time.sleep(wait_time)
            
            return True
            
        except Exception as e:
            logger.error(f"鼠标移动失败: {e}")
            return False
    
    def click_at_current_position(self):
        """在当前鼠标位置执行点击"""
        try:
            logger.info("在当前位置执行点击")
            
            # 执行点击命令
            click_cmd = [
                "docker", "exec", "-e", "DISPLAY=:0",
                self.container_name, "xdotool", "click", "1"
            ]
            
            subprocess.run(click_cmd, check=True, timeout=5)
            logger.info("点击执行成功")
            return True
            
        except Exception as e:
            logger.error(f"点击执行失败: {e}")
            return False
    
    def calculate_click_position(self, bbox):
        """计算点击位置"""
        x1, y1, x2, y2 = bbox
        
        # 点击位置：logo左侧约430像素处，垂直居中
        click_x = 430
        click_y = (y1 + y2) // 2
        
        logger.info(f"计算点击位置: logo位置({x1},{y1})-({x2},{y2}) -> 点击位置({click_x},{click_y})")
        return click_x, click_y
    
    def calculate_voice_button_click_position(self, bbox=None):
        """计算谷歌语音按钮点击位置 - 使用固定坐标"""
        # 直接使用固定的正确坐标，不依赖检测位置
        click_x = 735 
        click_y = 985
        
        if bbox:
            x1, y1, x2, y2 = bbox
            logger.info(f"检测到的区域: ({x1},{y1})-({x2},{y2})，但使用固定坐标")
        
        logger.info(f"使用固定点击位置: ({click_x},{click_y})")
        
        return click_x, click_y
    
    def detect_verification_status_by_text(self):
        """
        使用OCR识别验证状态文字
        
        Returns:
            str: 'success' - 验证成功, 'failed' - 验证失败, 'unknown' - 无法确定
        """
        if not OCR_AVAILABLE:
            return 'unknown'
        
        try:
            # 捕获屏幕截图
            img = self.capture_screenshot()
            img_gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
            
            # 保存调试截图
            if self.debug_mode:
                debug_path = f"debug_ocr_screenshot_{int(time.time())}.png"
                cv2.imwrite(debug_path, img_gray)
                logger.info(f"OCR调试：已保存截图到 {debug_path}")
            
            # 简单有效的图像预处理
            # 1. 适度放大（1.5倍）
            height, width = img_gray.shape
            img_resized = cv2.resize(img_gray, (int(width*1.5), int(height*1.5)), interpolation=cv2.INTER_CUBIC)
            
            # 保存处理后的图像用于调试
            if self.debug_mode:
                processed_path = f"debug_ocr_processed_{int(time.time())}.png"
                cv2.imwrite(processed_path, img_resized)
                logger.info(f"OCR调试：已保存处理后图像到 {processed_path}")
            
            # 使用简单但有效的OCR配置
            # 尝试多种PSM模式，选择识别效果最好的
            configs_and_images = [
                (r'--oem 3 --psm 6', img_gray),      # 原图 + 统一文本块
                (r'--oem 3 --psm 6', img_resized),   # 放大图 + 统一文本块
                (r'--oem 3 --psm 3', img_resized),   # 放大图 + 完全自动分页
                (r'--oem 3 --psm 11', img_resized),  # 放大图 + 稀疏文本
            ]
            
            best_text = ""
            best_word_count = 0
            
            for config, img_to_use in configs_and_images:
                try:
                    text = pytesseract.image_to_string(img_to_use, config=config, lang='eng')
                    # 统计有效单词数量（至少2个字符的字母单词）
                    words = [word for word in text.split() if len(word) >= 2 and any(c.isalpha() for c in word)]
                    word_count = len(words)
                    
                    if word_count > best_word_count:
                        best_text = text
                        best_word_count = word_count
                        
                except Exception as e:
                    continue
            
            text = best_text if best_text else ""
            
            # 转换为小写便于匹配
            text_lower = text.lower()
            
            if self.debug_mode:
                logger.info(f"OCR识别到的文字: {text.strip()}")
            
            # Google reCAPTCHA 成功关键词（移除容易误匹配的词）
            success_keywords = [
                'verification complete', 'verification successful', 'verified',
                'success', 'successful', 'completed', 'valid',
                'challenge solved', 'captcha solved', 'passed'
            ]
            
            # Google reCAPTCHA 失败关键词
            failed_keywords = [
                'please try again', 'try again', 'incorrect', 'wrong',
                'verification failed', 'failed', 'error', 'invalid',
                'verification expired', 'expired', 'timeout',
                'multiple correct solutions required', 'please solve more',
                'audio challenge failed', 'challenge failed'
            ]
            
            # Google reCAPTCHA 挑战进行中关键词
            challenge_keywords = [
                'select all squares', 'select all images', 'click verify',
                'i am not a robot', 'im not a robot', 'verify you are human',
                'please complete the security check', 'solve this puzzle',
                'press play to listen', 'enter what you hear', 'verify'
            ]
            
            # Google reCAPTCHA 图像验证对象关键词
            image_challenge_objects = [
                'crosswalks', 'bicycles', 'motorcycles', 'cars', 'buses',
                'traffic lights', 'fire hydrants', 'stairs', 'mountains',
                'bridges', 'chimneys', 'palm trees', 'boats', 'vehicles'
            ]
            
            # 检查是否包含成功关键词
            for keyword in success_keywords:
                if keyword in text_lower:
                    logger.info(f"✅ OCR检测到验证成功关键词: '{keyword}'")
                    return 'success'
            
            # 检查是否包含失败关键词
            for keyword in failed_keywords:
                if keyword in text_lower:
                    logger.info(f"❌ OCR检测到验证失败关键词: '{keyword}'")
                    return 'failed'
            
            # 检查是否包含挑战进行中关键词（使用模糊匹配）
            text_nospace = text_lower.replace(' ', '').replace('\n', '')
            
            for keyword in challenge_keywords:
                # 移除空格进行模糊匹配
                keyword_nospace = keyword.replace(' ', '')
                
                if keyword_nospace in text_nospace:
                    logger.info(f"🔄 OCR检测到验证挑战: '{keyword}'")
                    return 'challenge'
            
            # 检查是否包含图像验证对象关键词
            for obj in image_challenge_objects:
                if obj in text_lower:
                    logger.info(f"🔄 OCR检测到图像验证对象: '{obj}' (说明是图像选择验证)")
                    return 'challenge'
            
            # 智能检查：如果只有"imnotarobot"但没有其他挑战关键词，需要谨慎判断
            text_clean = text_nospace.replace("'", "")
            if 'imnotarobot' in text_clean:
                # 检查是否有其他挑战相关的关键词
                has_challenge_indicators = False
                
                # 检查是否有具体的挑战指示词
                challenge_indicators = [
                    'selectall', 'pressplay', 'enterwhat', 'multiplecorrect', 
                    'pleasesolve', 'clickverify', 'solvethis'
                ]
                
                for indicator in challenge_indicators:
                    if indicator in text_nospace:
                        has_challenge_indicators = True
                        break
                
                # 检查是否有验证对象
                for obj in image_challenge_objects:
                    if obj.replace(' ', '') in text_nospace:
                        has_challenge_indicators = True
                        break
                
                if has_challenge_indicators:
                    logger.info("🔄 OCR检测到'I'm not a robot'验证界面（有挑战指示）")
                    return 'challenge'
                else:
                    # 检查OCR识别质量：如果文字过于碎片化，可能是识别不完整
                    # 统计有意义的单词数量
                    meaningful_words = 0
                    word_fragments = text_lower.split()
                    
                    for word in word_fragments:
                        if len(word) >= 3 and word.isalpha():  # 至少3个字母的纯字母单词
                            meaningful_words += 1
                    
                    # 如果有意义的单词太少，说明OCR识别不完整，保守判断为挑战进行中
                    if meaningful_words < 10:
                        logger.info(f"🔄 OCR识别质量较低（有意义单词数: {meaningful_words}），保守判断为验证进行中")
                        return 'challenge'
                    
                    # OCR识别质量较好的情况下，检查是否在注册界面
                    registration_indicators = [
                        'create an account', 'createanaccount', 'sign up', 'signup',
                        'register', 'registration', 'welcome to'
                    ]
                    
                    still_in_registration = False
                    for indicator in registration_indicators:
                        if indicator.replace(' ', '') in text_nospace:
                            still_in_registration = True
                            logger.info(f"检测到注册界面指示: '{indicator}'")
                            break
                    
                    if still_in_registration:
                        logger.info("✅ OCR检测到'I'm not a robot'在注册界面且无挑战指示，验证已成功")
                        return 'success'
                    else:
                        logger.info("✅ OCR检测到'I'm not a robot'且已离开注册界面，验证已通过")
                        return 'success'
            
            
            # 如果既没有成功也没有失败关键词，说明验证已通过
            logger.info("✅ OCR未检测到任何验证相关关键词，验证可能已通过")
            return 'success'
            
        except Exception as e:
            logger.error(f"OCR文字识别失败: {e}")
            return 'unknown'
    
    def handle_voice_verification_retry(self, voice_x, voice_y, max_retries=10):
        """
        处理语音验证重试逻辑 - 基于OCR检测结果决定是否继续
        
        Args:
            voice_x: 语音按钮X坐标
            voice_y: 语音按钮Y坐标
            max_retries: 最大重试次数（防止无限循环）
        
        Returns:
            bool: 是否验证成功
        """
        retry_button_x, retry_button_y = 805, 855  # 重新开始验证的按钮位置
        
        for attempt in range(max_retries):
            logger.info(f"🔄 语音验证尝试 {attempt + 1}")
            
            # 1. 点击语音按钮
            logger.info(f"点击语音按钮: ({voice_x}, {voice_y})")
            if self.move_mouse_and_wait(voice_x, voice_y, wait_time=1):
                if self.click_at_current_position():
                    logger.info("✅ 语音按钮点击成功")
                else:
                    logger.error("❌ 语音按钮点击失败")
                    continue
            else:
                logger.error("❌ 鼠标移动到语音按钮失败")
                continue
            
            # 2. 等待验证处理
            logger.info("等待5秒让验证处理...")
            time.sleep(5)
            
            # 3. 使用OCR检测验证状态
            if OCR_AVAILABLE:
                status = self.detect_verification_status_by_text()
                if status == 'success':
                    logger.info("🎉 OCR检测到验证成功！")
                    return True
                elif status == 'failed':
                    logger.info("❌ OCR检测到验证失败，点击重新开始按钮继续尝试")
                    
                    # 点击重新开始按钮
                    logger.info(f"点击重新开始按钮: ({retry_button_x}, {retry_button_y})")
                    if self.move_mouse_and_wait(retry_button_x, retry_button_y, wait_time=1):
                        if self.click_at_current_position():
                            logger.info("✅ 重新开始按钮点击成功")
                        else:
                            logger.error("❌ 重新开始按钮点击失败")
                    else:
                        logger.error("❌ 鼠标移动到重新开始按钮失败")
                    
                    # 等待界面刷新
                    logger.info("等待3秒让界面刷新...")
                    time.sleep(3)
                    continue  # 继续下一次尝试
                    
                elif status == 'challenge':
                    logger.info("🔄 OCR检测到验证挑战仍在进行")
                    
                    # 检查是否是语音验证界面（Press PLAY to listen）
                    if 'pressplaytolisten' in text_lower.replace(' ', ''):
                        logger.info("检测到语音验证界面，点击重新开始按钮")
                        # 点击重新开始按钮
                        if self.move_mouse_and_wait(retry_button_x, retry_button_y, wait_time=1):
                            if self.click_at_current_position():
                                logger.info("✅ 重新开始按钮点击成功")
                            else:
                                logger.error("❌ 重新开始按钮点击失败")
                        else:
                            logger.error("❌ 鼠标移动到重新开始按钮失败")
                        
                        # 等待界面刷新
                        logger.info("等待3秒让界面刷新...")
                        time.sleep(3)
                        continue  # 继续下一次尝试
                    else:
                        logger.info("继续尝试语音验证")
                        continue  # 继续下一次尝试
                else:
                    logger.info("OCR未检测到明确状态，假设验证成功")
                    return True
            else:
                logger.warning("OCR不可用，无法判断验证状态，假设成功")
                return True
        
        # 达到最大重试次数
        logger.warning(f"⚠️ 已达到最大重试次数 {max_retries}，停止尝试")
        return False
    
    def run_voice_debug_only(self, check_interval=3, voice_timeout=60):
        """
        仅检测谷歌语音按钮的调试模式
        
        Args:
            check_interval: 检测间隔（秒）
            voice_timeout: 谷歌语音验证检测超时时间（秒）
        """
        logger.info("🔧 启动谷歌语音按钮调试模式")
        
        start_time = time.time()
        while (time.time() - start_time) < voice_timeout:
            try:
                detected, bbox = self.detect_google_voice_button()
                
                if detected:
                    logger.info("发现谷歌语音验证按钮！")
                    click_x, click_y = self.calculate_voice_button_click_position(bbox)
                    
                    # 使用重试逻辑处理语音验证
                    success = self.handle_voice_verification_retry(click_x, click_y)
                    
                    if success:
                        logger.info("🎉 语音验证成功通过！")
                        return True
                    else:
                        logger.error("❌ 语音验证多次尝试后仍未通过")
                        return False
                else:
                    # 即使没有检测到语音按钮，也尝试OCR识别当前状态
                    if OCR_AVAILABLE:
                        logger.info("🔍 尝试OCR识别当前界面状态...")
                        status = self.detect_verification_status_by_text()
                        if status == 'success':
                            logger.info("✅ OCR检测到验证成功状态！")
                            return True
                        elif status == 'failed':
                            logger.info("❌ OCR检测到验证失败状态")
                        elif status == 'challenge':
                            logger.info("🔄 OCR检测到验证挑战正在进行中，尝试点击语音按钮...")
                            # 使用固定坐标点击语音按钮
                            click_x, click_y = 735, 985
                            success = self.handle_voice_verification_retry(click_x, click_y)
                            
                            if success:
                                logger.info("🎉 语音验证成功通过！")
                                return True
                            else:
                                logger.error("❌ 语音验证多次尝试后仍未通过")
                                return False
                        else:
                            if self.debug_mode:
                                logger.info("OCR未检测到明确的验证状态")
                
                time.sleep(check_interval)
                
            except Exception as e:
                logger.error(f"检测过程中发生错误: {e}")
                time.sleep(check_interval)
        
        logger.info(f"⏰ {voice_timeout}秒内未检测到谷歌语音按钮")
        return False
    
    def run_forever(self, check_interval=3, verification_wait=5, exit_on_success=False, voice_timeout=30):
        """
        持续监控模式 - 先检测谷歌验证，再检测Cloudflare验证
        
        Args:
            check_interval: 检测间隔（秒）
            verification_wait: 点击后等待验证的时间（秒）
            exit_on_success: 验证通过后是否退出程序
            voice_timeout: 谷歌语音验证检测超时时间（秒）
        """
        logger.info("🚀 启动验证监控 - 持续监控模式")
        logger.info("检测顺序：1. Cloudflare验证 → 2. 谷歌语音验证")
        
        while True:
            try:
                # 1. 优先检测Cloudflare验证
                cf_detected, cf_bbox = self.detect_cloudflare()
                
                if cf_detected:
                    logger.info("发现Cloudflare人机验证！")
                    click_x, click_y = self.calculate_click_position(cf_bbox)
                    
                    if self.send_click(click_x, click_y):
                        logger.info(f"等待 {verification_wait} 秒检查验证结果...")
                        time.sleep(verification_wait)
                        
                        still_detected, _ = self.detect_cloudflare()
                        if not still_detected:
                            logger.info("✅ Cloudflare人机验证通过成功！")
                            
                            # Cloudflare验证通过后，等待谷歌语音按钮出现
                            logger.info("等待5秒让谷歌语音验证界面加载...")
                            time.sleep(5)
                            
                            # 使用OCR检测当前状态，决定是否需要语音验证
                            logger.info("🔍 检测当前验证状态...")
                            
                            if OCR_AVAILABLE:
                                status = self.detect_verification_status_by_text()
                                if status == 'success':
                                    logger.info("✅ OCR检测到验证已成功！")
                                    success = True
                                elif status == 'challenge':
                                    logger.info("🔄 OCR检测到验证挑战，开始语音验证...")
                                    click_x, click_y = 735, 985
                                    success = self.handle_voice_verification_retry(click_x, click_y)
                                else:
                                    logger.info("🔄 OCR状态未明确，尝试语音验证...")
                                    click_x, click_y = 735, 985
                                    success = self.handle_voice_verification_retry(click_x, click_y)
                            else:
                                logger.info("🔄 OCR不可用，使用固定坐标进行语音验证...")
                                click_x, click_y = 735, 985
                                success = self.handle_voice_verification_retry(click_x, click_y)
                            
                            if success:
                                logger.info("🎉 语音验证完成！")
                            else:
                                logger.info("语音验证尝试完成")
                            
                            if exit_on_success:
                                logger.info("🎉 所有验证完成，程序退出")
                                return True
                        else:
                            logger.info("❌ Cloudflare验证未通过，继续尝试...")
                    else:
                        logger.error("❌ Cloudflare点击命令发送失败")
                
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
    parser.add_argument("--move-to", type=str, help="移动鼠标到指定坐标（格式：x,y）供调试用，不执行点击")
    args = parser.parse_args()
    
    # 创建监控器并运行
    monitor = CloudflareMonitor(debug_mode=args.debug)
    
    # 坐标调试模式
    if args.move_to:
        try:
            coords = args.move_to.split(',')
            if len(coords) != 2:
                logger.error("坐标格式错误，请使用 x,y 格式，例如：--move-to 735,985")
                exit(1)
            
            x, y = int(coords[0].strip()), int(coords[1].strip())
            logger.info(f"🎯 坐标调试模式：移动鼠标到 ({x}, {y})")
            
            if monitor.move_mouse_and_wait(x, y, wait_time=3):
                logger.info(f"✅ 鼠标已移动到 ({x}, {y}) 并停留3秒")
                logger.info("💡 请观察鼠标位置是否正确，然后按 Ctrl+C 退出")
                
                # 保持程序运行，让用户观察鼠标位置
                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    logger.info("👋 坐标调试完成")
            else:
                logger.error("❌ 鼠标移动失败")
        except ValueError:
            logger.error("坐标值必须是整数，例如：--move-to 735,985")
        except Exception as e:
            logger.error(f"坐标调试失败: {e}")
        exit(0)
    
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
