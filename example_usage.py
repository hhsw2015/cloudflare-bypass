#!/usr/bin/env python3
"""
Cloudflare 绕过工具使用示例
"""

import time
import logging
from cloudflare_bypass_simplified import CloudflareDetector, send_click_to_container, calculate_click_position
from bypass_core import bypass_cloudflare

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def example_1_simple():
    """简单的单次绕过示例"""
    logger.info("示例 1: 单次绕过尝试")
    
    success = bypass_cloudflare(max_attempts=3, timeout=20)
    if success:
        logger.info("✅ 绕过成功!")
    else:
        logger.info("❌ 绕过失败或未检测到验证")


def example_2_manual():
    """手动检测和点击示例"""
    logger.info("示例 2: 手动检测和点击")
    
    detector = CloudflareDetector()
    
    # 检测Cloudflare验证
    if detector.detect_cloudflare():
        logger.info("检测到Cloudflare验证")
        
        # 计算点击位置
        click_x, click_y = calculate_click_position(detector.matched_bbox)
        logger.info(f"计算的点击位置: ({click_x}, {click_y})")
        
        # 发送点击命令
        if send_click_to_container(click_x, click_y):
            logger.info("点击命令发送成功")
            
            # 等待验证结果
            time.sleep(5)
            
            # 检查是否通过验证
            if not detector.detect_cloudflare():
                logger.info("✅ 验证通过成功!")
            else:
                logger.info("❌ 验证未通过")
        else:
            logger.error("点击命令发送失败")
    else:
        logger.info("未检测到Cloudflare验证")


def example_3_continuous():
    """持续监控示例"""
    logger.info("示例 3: 持续监控模式 (按 Ctrl+C 停止)")
    
    try:
        while True:
            logger.info("开始新一轮检测...")
            
            success = bypass_cloudflare(max_attempts=2, timeout=15)
            if success:
                logger.info("✅ 本轮绕过成功")
            else:
                logger.info("⏳ 本轮未检测到验证或绕过失败")
            
            # 等待间隔
            logger.info("等待 10 秒后继续...")
            time.sleep(10)
            
    except KeyboardInterrupt:
        logger.info("用户中断，停止监控")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        example = sys.argv[1]
    else:
        example = "1"  # 默认运行示例 1
    
    if example == "1":
        example_1_simple()
    elif example == "2":
        example_2_manual()
    elif example == "3":
        example_3_continuous()
    else:
        logger.error(f"未知的示例: {example}")
        logger.info("可用示例: 1 (简单), 2 (手动), 3 (持续)")