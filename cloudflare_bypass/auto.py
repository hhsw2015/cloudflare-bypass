from typing import Union
import time
import random
import logging
from cloudflare_bypass.cloudflare_detector import CloudFlareLogoDetector, CloudFlarePopupDetector
from cloudflare_bypass.vnc_manager import vnc_manager

# Configure logging
logger = logging.getLogger(__name__)

def wait_until(detector, warmup_time: Union[None, int] = None, timeout: int = 20):
    """
    Wait until a detector is detected or timeout is reached.

    Parameters:
        - detector: An instance of a detector.
        - warmup_time (int or None): Optional warm-up time before starting to detect.
        - timeout (int): Maximum time to wait for detection.

    Returns:
        - Union[None, Tuple[int]]: Bounding box coordinates if detection occurs, else None.
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


def click_like_human_improved(client, x: int, y: int, max_value: int = 5):
    """Improved click function with better human-like behavior"""
    delta_x = random.randint(-max_value, max_value)
    delta_y = random.randint(-max_value, max_value)
    try:
        final_x = x + delta_x
        final_y = y + delta_y
        logger.info(f"Moving mouse to ({final_x}, {final_y})")
        client.mouseMove(final_x, final_y)
        time.sleep(0.2)  # Brief delay to simulate human behavior
        client.mousePress(1)
        time.sleep(0.1)
        client.mouseRelease(1)
        logger.info(f"Click completed at: ({final_x}, {final_y})")
    except Exception as e:
        logger.error(f"Click failed: {e}")


def click_like_human(x: int, y: int, max_value: int = 5):
    """Legacy function for backward compatibility"""
    # This will be called by the old code, but we need a client reference
    # For now, create a temporary detector to get client
    try:
        temp_detector = CloudFlarePopupDetector()
        click_like_human_improved(temp_detector.client, x, y, max_value)
    except Exception as e:
        logger.error(f"Legacy click failed: {e}")


def bypass(
    mode: str = 'light',
    warmup_time: int = None,
    timeout: int = 30,
    interval: float = 0.5,
    threshold: float = 0.6,
    max_attempts: int = 5
):
    """
    Improved CloudFlare bypass function with better VNC connection management.
    """
    logger.info(f"Starting CloudFlare bypass - mode: {mode}, threshold: {threshold}")
    
    # Optional warmup time
    if warmup_time is not None and isinstance(warmup_time, (int, float)):
        logger.info(f"Warmup wait: {warmup_time} seconds")
        time.sleep(warmup_time)

    # Initialize detectors once to avoid repeated VNC connections
    cf_popup_detector = None
    cf_logo_detector = None
    
    # Try multiple thresholds from high to low
    thresholds_to_try = [threshold, max(0.4, threshold - 0.1), max(0.3, threshold - 0.2), 0.25]
    modes_to_try = [mode, 'dark' if mode == 'light' else 'light']
    
    t0 = time.time()
    clicked = False
    detection_attempts = 0
    
    while time.time() - t0 < timeout and detection_attempts < max_attempts:
        detection_attempts += 1
        logger.info(f"Detection attempt {detection_attempts}")
        
        # Try different mode and threshold combinations
        for current_mode in modes_to_try:
            for current_threshold in thresholds_to_try:
                try:
                    logger.info(f"Trying mode: {current_mode}, threshold: {current_threshold}")
                    
                    # Only create new detectors if mode changed or first time
                    if (cf_popup_detector is None or 
                        cf_popup_detector.template_path != (f"cloudflare_bypass/images/cf_popup{'_dark' if current_mode == 'dark' else ''}.png")):
                        cf_popup_detector = CloudFlarePopupDetector(mode=current_mode, threshold=current_threshold)
                        cf_logo_detector = CloudFlareLogoDetector(mode=current_mode, threshold=current_threshold)
                    else:
                        # Just update threshold for existing detectors
                        cf_popup_detector.threshold = current_threshold
                        cf_logo_detector.threshold = current_threshold
                    
                    # Detect popup and logo
                    popup_detected = cf_popup_detector.is_detected()
                    logo_detected = cf_logo_detector.is_detected()
                    
                    logger.info(f"Popup detected: {popup_detected}, Logo detected: {logo_detected}")
                    
                    # Strategy 1: If popup detected, try to click
                    if popup_detected and not clicked:
                        x1, y1, x2, y2 = cf_popup_detector.matched_bbox
                        cx = x1 + int((x2 - x1) * 0.1)
                        cy = (y1 + y2) // 2
                        
                        logger.info(f"CAPTCHA popup detected, clicking at: ({cx}, {cy})")
                        success = safe_click(None, cx, cy)
                        if success:
                            clicked = True
                            logger.info("Click completed, waiting for page response...")
                            time.sleep(3)
                            
                            # Check if successful
                            if not cf_logo_detector.is_detected():
                                logger.info("CAPTCHA bypass successful! Logo disappeared")
                                return True
                    
                    # Strategy 2: If only logo detected but no popup
                    elif logo_detected and not popup_detected and not clicked:
                        logger.warning("CloudFlare logo detected but no popup, trying alternative strategies")
                        x1, y1, x2, y2 = cf_logo_detector.matched_bbox
                        
                        # Try clicking in the verification area (usually below or to the side of logo)
                        click_positions = [
                            ((x1 + x2) // 2, y2 + 30),  # Below logo
                            (x1 - 80, (y1 + y2) // 2),  # Left of logo (common checkbox position)
                            (x2 + 30, (y1 + y2) // 2),  # Right of logo
                        ]
                        
                        for pos_x, pos_y in click_positions:
                            logger.info(f"Trying click position: ({pos_x}, {pos_y})")
                            success = safe_click(None, pos_x, pos_y)
                            if success:
                                time.sleep(2)
                                # Check if this click worked
                                if not cf_logo_detector.is_detected():
                                    logger.info("Alternative click strategy successful!")
                                    return True
                        
                        clicked = True
                        break  # Exit threshold loop after trying alternative strategies
                    
                    # If we found something, no need to try lower thresholds
                    if popup_detected or logo_detected:
                        break
                        
                except Exception as e:
                    logger.error(f"Error during detection (mode: {current_mode}, threshold: {current_threshold}): {e}")
                    continue
            
            # If we found and clicked something, no need to try other modes
            if clicked:
                break
        
        # If already clicked, check if successful
        if clicked:
            try:
                time.sleep(2)  # Wait a bit more
                if not cf_logo_detector.is_detected():
                    logger.info("Verification successful, CloudFlare logo disappeared")
                    return True
                else:
                    logger.info("Logo still present after click, continuing monitoring...")
            except Exception as e:
                logger.error(f"Error during verification check: {e}")
        
        # Wait before next detection
        time.sleep(interval)
    
    if clicked:
        logger.info("Click attempted but may need more time for verification")
        return True
    else:
        logger.warning(f"No clickable CAPTCHA elements detected within {timeout} seconds")
        return False


def safe_click(client, x: int, y: int, max_value: int = 5):
    """Safe click function using vncdo commands"""
    try:
        # Use VNC manager's vncdo-based click method
        success = vnc_manager.move_and_click(x, y, max_value)
        if success:
            logger.info(f"Click operation successful at: ({x}, {y})")
        else:
            logger.warning(f"Click operation failed at: ({x}, {y})")
        return success
        
    except Exception as e:
        logger.error(f"Click operation exception: {e}")
        return False