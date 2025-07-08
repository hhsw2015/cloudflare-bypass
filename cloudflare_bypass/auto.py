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
                    
                    # If logo detected, log more details about the detection
                    if logo_detected:
                        x1, y1, x2, y2 = cf_logo_detector.matched_bbox
                        logo_width = x2 - x1
                        logo_height = y2 - y1
                        logger.info(f"Logo details: position=({x1},{y1})-({x2},{y2}), size={logo_width}x{logo_height}, confidence={current_threshold}")
                        
                        # Check if logo size seems reasonable for CloudFlare logo
                        if logo_width < 50 or logo_height < 20 or logo_width > 300 or logo_height > 150:
                            logger.warning(f"Detected logo size seems unusual: {logo_width}x{logo_height} - might be false positive")
                            continue  # Skip this detection, try next threshold/mode
                        
                        # Check if logo position seems reasonable (not at screen edges)
                        if x1 < 50 or y1 < 50 or x2 > 1200 or y2 > 800:
                            logger.warning(f"Detected logo at edge of screen: ({x1},{y1})-({x2},{y2}) - might be false positive")
                            continue  # Skip this detection, try next threshold/mode
                        
                        # Check if this is the same logo position as before (might be stuck on wrong element)
                        if hasattr(bypass, '_last_logo_pos') and bypass._last_logo_pos == (x1, y1, x2, y2):
                            logger.warning(f"Same logo position detected again: ({x1},{y1})-({x2},{y2}) - might be wrong element")
                            continue  # Skip this detection, try next threshold/mode
                        
                        # Store current logo position for comparison
                        bypass._last_logo_pos = (x1, y1, x2, y2)
                    
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
                        logger.warning("CloudFlare logo detected but no popup, trying comprehensive click strategies")
                        x1, y1, x2, y2 = cf_logo_detector.matched_bbox
                        logo_center_x = (x1 + x2) // 2
                        logo_center_y = (y1 + y2) // 2
                        
                        # Calculate logo dimensions for better positioning
                        logo_width = x2 - x1
                        logo_height = y2 - y1
                        
                        # More strategic click positions based on common CAPTCHA layouts
                        click_positions = []
                        
                        # Strategy 1: Look for checkbox to the left (most common)
                        # Try even more left positions based on common CAPTCHA layouts
                        # Many CAPTCHA checkboxes are 150-200px left of any text/logo
                        checkbox_distances = [150, 180, 200, 120, 140, 160]  # Much further left
                        
                        for distance in checkbox_distances:
                            click_positions.append((x1 - distance, logo_center_y))
                        
                        # Also try some common absolute positions where checkboxes typically appear
                        common_checkbox_positions = [
                            (300, logo_center_y),  # Common left area
                            (250, logo_center_y),  # Further left
                            (350, logo_center_y),  # Slightly right of common
                            (200, logo_center_y),  # Very left
                        ]
                        
                        # Add common positions that are not too close to detected logo
                        for pos_x, pos_y in common_checkbox_positions:
                            if abs(pos_x - logo_center_x) > 100:  # At least 100px away from logo
                                click_positions.append((pos_x, pos_y))
                        
                        # Focus only on X-axis left positions, no other strategies needed
                        
                        logger.info(f"Logo detected at ({x1}, {y1}) to ({x2}, {y2}), trying {len(click_positions)} positions")
                        
                        # Save debug screenshot with logo marked
                        try:
                            import cv2
                            import subprocess
                            import os
                            
                            # Capture current screenshot for debugging
                            screenshot_path = "debug_logo_detection.png"
                            vncdo_cmd = ["vncdo", "-s", f"127.0.0.1::5900", "capture", screenshot_path]
                            subprocess.run(vncdo_cmd, check=True, timeout=10)
                            
                            # Load and mark the logo area
                            img = cv2.imread(screenshot_path)
                            if img is not None:
                                # Draw rectangle around detected logo
                                cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
                                cv2.putText(img, f"Logo ({x1},{y1})-({x2},{y2})", 
                                          (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                                
                                # Mark all click positions
                                for i, (pos_x, pos_y) in enumerate(click_positions):
                                    cv2.circle(img, (pos_x, pos_y), 5, (0, 0, 255), -1)
                                    cv2.putText(img, str(i+1), (pos_x+8, pos_y+5), 
                                              cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)
                                
                                cv2.imwrite("debug_click_positions.png", img)
                                logger.info("Debug screenshot saved: debug_click_positions.png")
                        except Exception as e:
                            logger.warning(f"Failed to save debug screenshot: {e}")
                        
                        for i, (pos_x, pos_y) in enumerate(click_positions):
                            logger.info(f"Trying strategic click position {i+1}/{len(click_positions)}: ({pos_x}, {pos_y})")
                            logger.info(f"Mouse will move to ({pos_x}, {pos_y}) and pause - please watch the screen")
                            success = safe_click(None, pos_x, pos_y)
                            if success:
                                logger.info(f"Click executed at position ({pos_x}, {pos_y}), waiting for page response...")
                                time.sleep(4)  # Wait even longer for page response
                                # Check if this click worked with multiple detection attempts
                                logo_disappeared = False
                                for check_attempt in range(3):  # Try 3 times to check
                                    try:
                                        time.sleep(1)  # Small delay between checks
                                        if not cf_logo_detector.is_detected():
                                            logo_disappeared = True
                                            break
                                    except:
                                        continue
                                
                                if logo_disappeared:
                                    logger.info(f"SUCCESS! Click position {i+1} worked: ({pos_x}, {pos_y})")
                                    return True
                                else:
                                    logger.info(f"Click position {i+1} didn't work, logo still present after {pos_x}, {pos_y}")
                                    
                                    # If we've tried 3 positions without success, maybe wrong logo detected
                                    if i >= 2:
                                        logger.warning("Multiple clicks failed - might be detecting wrong element or different CAPTCHA type")
                                        # Try a few random positions as last resort
                                        random_positions = [(350, 400), (450, 350), (250, 450)]
                                        for j, (rand_x, rand_y) in enumerate(random_positions):
                                            logger.info(f"Trying random fallback position {j+1}: ({rand_x}, {rand_y})")
                                            safe_click(None, rand_x, rand_y)
                                            time.sleep(2)
                                        break
                            else:
                                logger.warning(f"Click position {i+1} failed to execute: ({pos_x}, {pos_y})")
                        
                        clicked = True
                        logger.info("Tried all click positions, marking as clicked")
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