#!/usr/bin/env python3
"""
Debug tool for CAPTCHA detection issues
This script will help analyze why CAPTCHA detection is failing
"""
import cv2
import numpy as np
import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def analyze_templates():
    """Analyze the template images"""
    logger.info("=== Analyzing Template Images ===")
    
    template_dir = Path("cloudflare_bypass/images")
    templates = {
        "cf_logo.png": "CloudFlare Logo (Light)",
        "cf_logo_dark.png": "CloudFlare Logo (Dark)", 
        "cf_popup.png": "CloudFlare Popup (Light)",
        "cf_popup_dark.png": "CloudFlare Popup (Dark)"
    }
    
    for filename, description in templates.items():
        template_path = template_dir / filename
        if template_path.exists():
            img = cv2.imread(str(template_path))
            if img is not None:
                h, w = img.shape[:2]
                logger.info(f"{description}: {w}x{h} pixels")
                
                # Analyze color distribution
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                mean_brightness = np.mean(gray)
                logger.info(f"  Average brightness: {mean_brightness:.1f}")
            else:
                logger.error(f"Could not load {filename}")
        else:
            logger.error(f"Template not found: {filename}")

def capture_and_analyze_screenshot():
    """Capture current screenshot and analyze it"""
    logger.info("=== Capturing and Analyzing Current Screenshot ===")
    
    try:
        # Import here to avoid dependency issues
        from cloudflare_bypass.base_detector import BaseDetector
        
        # Create a temporary detector just for screenshot
        temp_detector = BaseDetector("cloudflare_bypass/images/cf_logo.png", threshold=0.5)
        
        # Capture screenshot
        screenshot = temp_detector._capture_vnc_screenshot()
        screenshot_bgr = cv2.cvtColor(screenshot, cv2.COLOR_RGB2BGR)
        
        # Save screenshot for analysis
        cv2.imwrite("debug_screenshot.png", screenshot_bgr)
        logger.info("Screenshot saved as 'debug_screenshot.png'")
        
        # Analyze screenshot
        h, w = screenshot.shape[:2]
        logger.info(f"Screenshot size: {w}x{h}")
        
        # Convert to grayscale for analysis
        gray = cv2.cvtColor(screenshot, cv2.COLOR_RGB2GRAY)
        mean_brightness = np.mean(gray)
        logger.info(f"Screenshot average brightness: {mean_brightness:.1f}")
        
        # Detect if it's likely a light or dark theme
        if mean_brightness > 127:
            suggested_mode = "light"
        else:
            suggested_mode = "dark"
        logger.info(f"Suggested mode based on brightness: {suggested_mode}")
        
        return screenshot, suggested_mode
        
    except Exception as e:
        logger.error(f"Failed to capture screenshot: {e}")
        return None, None

def test_template_matching(screenshot, mode="light"):
    """Test template matching with different thresholds"""
    logger.info(f"=== Testing Template Matching (Mode: {mode}) ===")
    
    if screenshot is None:
        logger.error("No screenshot available for testing")
        return
    
    template_dir = Path("cloudflare_bypass/images")
    
    # Choose templates based on mode
    if mode == "light":
        templates = {
            "cf_logo.png": "CloudFlare Logo",
            "cf_popup.png": "CloudFlare Popup"
        }
    else:
        templates = {
            "cf_logo_dark.png": "CloudFlare Logo", 
            "cf_popup_dark.png": "CloudFlare Popup"
        }
    
    # Convert screenshot to grayscale
    screenshot_gray = cv2.cvtColor(screenshot, cv2.COLOR_RGB2GRAY)
    
    # Test different thresholds
    thresholds = [0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.25]
    
    for template_file, description in templates.items():
        template_path = template_dir / template_file
        if not template_path.exists():
            logger.warning(f"Template not found: {template_file}")
            continue
            
        template = cv2.imread(str(template_path), 0)  # Load as grayscale
        if template is None:
            logger.error(f"Could not load template: {template_file}")
            continue
            
        logger.info(f"\nTesting {description} ({template_file}):")
        
        # Perform template matching
        result = cv2.matchTemplate(screenshot_gray, template, cv2.TM_CCOEFF_NORMED)
        _, max_confidence, _, max_loc = cv2.minMaxLoc(result)
        
        logger.info(f"  Maximum confidence: {max_confidence:.3f}")
        
        # Test each threshold
        for threshold in thresholds:
            if max_confidence >= threshold:
                h, w = template.shape
                top_left = max_loc
                bottom_right = (top_left[0] + w, top_left[1] + h)
                logger.info(f"  ✓ Threshold {threshold}: MATCH at ({top_left[0]}, {top_left[1]}) to ({bottom_right[0]}, {bottom_right[1]})")
                
                # Save visualization for first successful match
                if threshold == thresholds[0] or max_confidence >= 0.6:
                    vis_img = screenshot_bgr.copy()
                    cv2.rectangle(vis_img, top_left, bottom_right, (0, 255, 0), 2)
                    cv2.putText(vis_img, f"{description} ({max_confidence:.3f})", 
                              (top_left[0], top_left[1]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    output_file = f"debug_match_{template_file.replace('.png', '')}.png"
                    cv2.imwrite(output_file, vis_img)
                    logger.info(f"  Match visualization saved: {output_file}")
                break
            else:
                logger.info(f"  ✗ Threshold {threshold}: NO MATCH")

def test_detection_with_detectors():
    """Test detection using the actual detector classes"""
    logger.info("=== Testing with Actual Detector Classes ===")
    
    try:
        from cloudflare_bypass.cloudflare_detector import CloudFlareLogoDetector, CloudFlarePopupDetector
        
        modes = ['light', 'dark']
        thresholds = [0.8, 0.6, 0.4, 0.25]
        
        for mode in modes:
            logger.info(f"\n--- Testing {mode} mode ---")
            for threshold in thresholds:
                logger.info(f"Testing threshold: {threshold}")
                try:
                    logo_detector = CloudFlareLogoDetector(mode=mode, threshold=threshold)
                    popup_detector = CloudFlarePopupDetector(mode=mode, threshold=threshold)
                    
                    logo_detected = logo_detector.is_detected()
                    popup_detected = popup_detector.is_detected()
                    
                    logger.info(f"  Logo detected: {logo_detected}")
                    logger.info(f"  Popup detected: {popup_detected}")
                    
                    if logo_detected:
                        logger.info(f"  Logo bbox: {logo_detector.matched_bbox}")
                    if popup_detected:
                        logger.info(f"  Popup bbox: {popup_detector.matched_bbox}")
                        
                    # If we found something, we can stop testing lower thresholds for this mode
                    if logo_detected or popup_detected:
                        logger.info(f"  ✓ Found elements with {mode} mode at threshold {threshold}")
                        break
                        
                except Exception as e:
                    logger.error(f"  Error with {mode} mode, threshold {threshold}: {e}")
                    
    except Exception as e:
        logger.error(f"Failed to test with detector classes: {e}")

def main():
    """Main debug function"""
    logger.info("Starting CAPTCHA Detection Debug Tool")
    
    # Step 1: Analyze templates
    analyze_templates()
    
    # Step 2: Capture and analyze current screenshot
    screenshot, suggested_mode = capture_and_analyze_screenshot()
    
    # Step 3: Test template matching manually
    if screenshot is not None:
        # Test both modes
        test_template_matching(screenshot, "light")
        test_template_matching(screenshot, "dark")
    
    # Step 4: Test with actual detector classes
    test_detection_with_detectors()
    
    logger.info("Debug analysis complete. Check the generated debug images and logs.")

if __name__ == "__main__":
    main()