#!/usr/bin/env python3
"""
核心Cloudflare绕过工具 - 简化版
只保留核心逻辑：检测 -> 点击 -> 验证
"""

from cloudflare_bypass_simplified import CloudflareDetector, send_click_to_container, calculate_click_position
import time
import logging

logger = logging.getLogger(__name__)

def bypass_cloudflare(max_attempts: int = 10, timeout: int = 60):
    """
    核心绕过函数
    
    Args:
        max_attempts: 最大尝试次数
        timeout: 总超时时间（秒）
    
    Returns:
        bool: 是否成功绕过
    """
    detector = CloudflareDetector()
    start_time = time.time()
    attempt = 0
    
    logger.info(f"开始Cloudflare绕过，最大尝试次数: {max_attempts}, 超时: {timeout}秒")
    
    while attempt < max_attempts and (time.time() - start_time) < timeout:
        attempt += 1
        logger.info(f"第 {attempt} 次尝试...")
        
        try:
            # 1. 检测Cloudflare验证
            if detector.detect_cloudflare():
                logger.info("✓ 检测到Cloudflare验证")
                
                # 2. 计算点击位置
                click_x, click_y = calculate_click_position(detector.matched_bbox)
                
                # 3. 发送点击命令
                if send_click_to_container(click_x, click_y):
                    logger.info("✓ 点击命令已发送")
                    
                    # 4. 等待验证结果
                    time.sleep(5)
                    
                    # 5. 检查是否通过验证
                    if not detector.detect_cloudflare():
                        logger.info("🎉 验证通过成功！")
                        return True
                    else:
                        logger.warning("❌ 验证未通过，继续尝试...")
                else:
                    logger.error("❌ 点击命令发送失败")
            else:
                logger.debug("未检测到Cloudflare验证")
            
            # 等待下次尝试
            time.sleep(2)
            
        except Exception as e:
            logger.error(f"尝试过程中发生错误: {e}")
            time.sleep(2)
    
    logger.warning(f"绕过失败：已尝试 {attempt} 次，耗时 {time.time() - start_time:.1f} 秒")
    return False


def main():
    """主函数 - 持续监控模式"""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
    
    logger.info("🚀 启动Cloudflare绕过工具（持续监控模式）")
    
    while True:
        try:
            success = bypass_cloudflare(max_attempts=5, timeout=30)
            if success:
                logger.info("✅ 本轮绕过成功，继续监控...")
            else:
                logger.info("⏳ 本轮未检测到验证或绕过失败，继续监控...")
            
            # 监控间隔
            time.sleep(10)
            
        except KeyboardInterrupt:
            logger.info("👋 用户中断，退出程序")
            break
        except Exception as e:
            logger.error(f"程序异常: {e}")
            time.sleep(5)


if __name__ == "__main__":
    main()