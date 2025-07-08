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

    # Initialize logo detector only - no popup detection needed
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
                    
                    # Only create new logo detector if mode changed or first time
                    if (cf_logo_detector is None or 
                        cf_logo_detector.template_path != (f"cloudflare_bypass/images/cf_logo{'_dark' if current_mode == 'dark' else ''}.png")):
                        cf_logo_detector = CloudFlareLogoDetector(mode=current_mode, threshold=current_threshold)
                    else:
                        # Just update threshold for existing detector
                        cf_logo_detector.threshold = current_threshold
                    
                    # Only detect logo - no need for popup detection
                    logo_detected = cf_logo_detector.is_detected()
                    
                    logger.info(f"Logo detected: {logo_detected}")
                    
                    # If logo detected, process it
                    if logo_detected and not clicked:
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
                        logger.info("CloudFlare logo detected, using adaptive click positioning")
                        x1, y1, x2, y2 = cf_logo_detector.matched_bbox
                        logo_center_x = (x1 + x2) // 2
                        logo_center_y = (y1 + y2) // 2
                        
                        # Calculate logo dimensions for better positioning
                        logo_width = x2 - x1
                        logo_height = y2 - y1
                        
                        # More strategic click positions based on common CAPTCHA layouts
                        click_positions = []
                        
                        # Strategy 1: Look for checkbox to the left (most common)
                        # Success! Position 436 worked for screen resolution, now make it adaptive to screen size
                        # Get current screen dimensions from the screenshot
                        try:
                            # Capture screenshot to get current screen dimensions
                            import subprocess
                            screenshot_path = "temp_screen_size.png"
                            vncdo_cmd = ["vncdo", "-s", f"127.0.0.1::5900", "capture", screenshot_path]
                            subprocess.run(vncdo_cmd, check=True, timeout=10)
                            
                            import cv2
                            temp_img = cv2.imread(screenshot_path)
                            if temp_img is not None:
                                current_height, current_width = temp_img.shape[:2]
                                logger.info(f"Current screen size: {current_width}x{current_height}")
                                
                                # Reference successful case: 436px worked on what screen size?
                                # Assume reference was 1920x1080 (common resolution)
                                reference_width = 1920
                                reference_success_distance = 160  # 596-436=160
                                
                                # Calculate scale factor based on width
                                scale_factor = current_width / reference_width
                                
                                # Scale the successful distance
                                scaled_base_distance = int(reference_success_distance * scale_factor)
                                
                                logger.info(f"Screen scale factor: {scale_factor:.3f}, scaled_distance: {scaled_base_distance}")
                                
                                # Fix direction: need to INCREASE distance to move LEFT
                                # 461px was 10px right, need to move left by increasing distance from logo
                                fine_tune_offsets = [20, 25, 15, 30, 10, 18]  # INCREASE distance to move LEFT
                                
                                checkbox_distances = []
                                for offset in fine_tune_offsets:
                                    adaptive_distance = scaled_base_distance + offset
                                    checkbox_distances.append(adaptive_distance)
                            else:
                                logger.warning("Could not get screen size, using fallback distances")
                                checkbox_distances = [160, 165, 170, 155, 175, 150]  # Fallback
                        except Exception as e:
                            logger.warning(f"Error getting screen size: {e}, using fallback distances")
                            checkbox_distances = [160, 165, 170, 155, 175, 150]  # Fallback
                        
                        for distance in checkbox_distances:
                            click_positions.append((x1 - distance, logo_center_y))
                        
                        # Try more left absolute positions based on feedback
                        common_checkbox_positions = [
                            (200, logo_center_y),  # Very left
                            (150, logo_center_y),  # Even further left
                            (250, logo_center_y),  # Left area
                            (100, logo_center_y),  # Extremely left
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
                        
                        # Use the first (best) position and adjust 2px left as requested
                        best_pos_x, best_pos_y = click_positions[0]
                        best_pos_x -= 2  # Move 2 pixels left for better positioning
                        
                        # Re-detect logo position to get fresh Y coordinate
                        try:
                            fresh_logo_detected = cf_logo_detector.is_detected()
                            if fresh_logo_detected:
                                fresh_x1, fresh_y1, fresh_x2, fresh_y2 = cf_logo_detector.matched_bbox
                                fresh_logo_center_y = (fresh_y1 + fresh_y2) // 2
                                best_pos_y = fresh_logo_center_y
                                logger.info(f"Updated Y coordinate to fresh logo center: {fresh_logo_center_y}")
                        except Exception as e:
                            logger.warning(f"Error re-detecting logo: {e}, using calculated Y coordinate")
                        
                        logger.info(f"Using optimal position: ({best_pos_x}, {best_pos_y})")
                        
                        # Try clicking at the optimal position multiple times
                        max_click_attempts = 5
                        for attempt in range(max_click_attempts):
                            logger.info(f"Click attempt {attempt + 1}/{max_click_attempts} at position ({best_pos_x}, {best_pos_y})")
                            
                            success = safe_click(None, best_pos_x, best_pos_y)
                            if success:
                                logger.info(f"Click executed, waiting 5 seconds to check result...")
                                time.sleep(5)  # Wait 5 seconds as requested
                                
                                # Check if logo disappeared (verification passed)
                                try:
                                    if not cf_logo_detector.is_detected():
                                        logger.info(f"SUCCESS! Verification passed after attempt {attempt + 1}")
                                        return True
                                    else:
                                        logger.info(f"Attempt {attempt + 1} failed, logo still present. Continuing...")
                                except Exception as e:
                                    logger.warning(f"Error checking logo after attempt {attempt + 1}: {e}")
                            else:
                                logger.warning(f"Click attempt {attempt + 1} failed to execute")
                        
                        logger.warning(f"All {max_click_attempts} attempts failed at optimal position")
                        clicked = True
                        break  # Exit threshold loop after trying multiple attempts
                    
                    # If we found logo, no need to try lower thresholds
                    if logo_detected:
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