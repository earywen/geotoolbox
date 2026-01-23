"""
Raster Image Processor

Handles PVA image processing: auto-crop, rotation, georeferencing, feature matching.

Migrated from: modules/pva_processor.py

Dependencies: opencv-python-headless, Pillow
"""

import os
import math
import logging
from typing import Tuple, Optional, Dict, Any

try:
    import cv2
    import numpy as np
    from PIL import Image
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    cv2 = None
    np = None
    Image = None

logger = logging.getLogger(__name__)


# ==========================================
# 1. BLACK BORDER DETECTION & CROP
# ==========================================

def detect_photo_region(image, threshold: int = 30) -> Optional[Tuple[int, int, int, int]]:
    """
    Detect the main photo region by finding the largest non-black rectangle.
    
    PVA scans include black borders with metadata text. This function finds
    the actual photo content by detecting the largest bright rectangular region.
    """
    if not OPENCV_AVAILABLE:
        return None
        
    # Convert to grayscale if needed
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
    
    # Apply threshold to separate black borders from photo content
    _, binary = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY)
    
    # Find contours
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        logger.warning("[PVA Processor] No contours found")
        return None
    
    # Find the largest contour (should be the photo)
    largest_contour = max(contours, key=cv2.contourArea)
    
    # Get bounding rectangle
    x, y, w, h = cv2.boundingRect(largest_contour)
    
    # Validate: photo should be at least 30% of image area
    image_area = image.shape[0] * image.shape[1]
    photo_area = w * h
    
    if photo_area < image_area * 0.3:
        logger.warning(f"[PVA Processor] Detected region too small ({photo_area/image_area*100:.1f}%)")
        return None
    
    logger.info(f"[PVA Processor] Photo region detected: {w}x{h} at ({x},{y})")
    return (x, y, w, h)


def crop_to_photo(image, margin_percent: float = 1.0) -> Tuple:
    """
    Crop image to remove black scanner borders, keeping only the photo content.
    """
    if not OPENCV_AVAILABLE:
        return image, (0, 0, image.shape[1] if hasattr(image, 'shape') else 0, 
                       image.shape[0] if hasattr(image, 'shape') else 0)
    
    region = detect_photo_region(image)
    
    if region is None:
        logger.warning("[PVA Processor] Could not detect photo region, returning original")
        return image, (0, 0, image.shape[1], image.shape[0])
    
    x, y, w, h = region
    
    # Add small margin
    margin_x = int(w * margin_percent / 100)
    margin_y = int(h * margin_percent / 100)
    
    x = max(0, x - margin_x)
    y = max(0, y - margin_y)
    w = min(image.shape[1] - x, w + 2 * margin_x)
    h = min(image.shape[0] - y, h + 2 * margin_y)
    
    cropped = image[y:y+h, x:x+w]
    
    return cropped, (x, y, w, h)


# ==========================================
# 2. ROTATION HANDLING
# ==========================================

def rotate_image(image, angle_degrees: float, expand: bool = True):
    """
    Rotate image by specified angle.
    """
    if not OPENCV_AVAILABLE:
        return image
        
    h, w = image.shape[:2]
    center = (w // 2, h // 2)
    
    # Get rotation matrix
    rotation_matrix = cv2.getRotationMatrix2D(center, angle_degrees, 1.0)
    
    if expand:
        # Calculate new image bounds
        cos_angle = abs(math.cos(math.radians(angle_degrees)))
        sin_angle = abs(math.sin(math.radians(angle_degrees)))
        new_w = int(h * sin_angle + w * cos_angle)
        new_h = int(h * cos_angle + w * sin_angle)
        
        # Adjust rotation matrix for new center
        rotation_matrix[0, 2] += (new_w - w) / 2
        rotation_matrix[1, 2] += (new_h - h) / 2
        
        # Perform rotation
        rotated = cv2.warpAffine(image, rotation_matrix, (new_w, new_h), 
                                  borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0))
    else:
        rotated = cv2.warpAffine(image, rotation_matrix, (w, h))
    
    return rotated


def normalize_orientation(orientation: float) -> float:
    """
    Convert IGN orientation to rotation angle needed for North-up alignment.
    """
    # Normalize to 0-360 range
    orientation = orientation % 360
    
    # For North-up, we rotate by negative orientation
    rotation = -orientation
    
    # Keep in -180 to 180 range for minimal rotation
    if rotation < -180:
        rotation += 360
    elif rotation > 180:
        rotation -= 360
        
    return rotation


# ==========================================
# 3. FEATURE MATCHING (AUTO-ALIGNMENT)
# ==========================================

def find_keypoints(image, max_features: int = 1000) -> Tuple[Any, Any]:
    """
    Detect keypoints and compute descriptors using ORB.
    """
    if not OPENCV_AVAILABLE:
        return None, None
        
    # Convert to grayscale
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image
    
    # Create ORB detector
    orb = cv2.ORB_create(nfeatures=max_features)
    
    # Detect and compute
    keypoints, descriptors = orb.detectAndCompute(gray, None)
    
    logger.debug(f"[PVA Processor] Found {len(keypoints)} keypoints")
    return keypoints, descriptors


def match_images(img1, img2, min_matches: int = 10) -> Optional[Any]:
    """
    Find homography transformation between two images using feature matching.
    """
    if not OPENCV_AVAILABLE:
        return None
        
    # Find keypoints and descriptors
    kp1, desc1 = find_keypoints(img1)
    kp2, desc2 = find_keypoints(img2)
    
    if desc1 is None or desc2 is None:
        logger.warning("[PVA Processor] Could not compute descriptors")
        return None
    
    if len(kp1) < min_matches or len(kp2) < min_matches:
        logger.warning(f"[PVA Processor] Not enough keypoints: {len(kp1)}, {len(kp2)}")
        return None
    
    # Match descriptors using BFMatcher
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
    matches = bf.knnMatch(desc1, desc2, k=2)
    
    # Apply Lowe's ratio test
    good_matches = []
    for m, n in matches:
        if m.distance < 0.75 * n.distance:
            good_matches.append(m)
    
    logger.info(f"[PVA Processor] Found {len(good_matches)} good matches")
    
    if len(good_matches) < min_matches:
        logger.warning(f"[PVA Processor] Not enough good matches: {len(good_matches)} < {min_matches}")
        return None
    
    # Extract matched point coordinates
    src_pts = np.float32([kp1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
    dst_pts = np.float32([kp2[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)
    
    # Find homography using RANSAC
    homography, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
    
    if homography is None:
        logger.warning("[PVA Processor] Could not compute homography")
        return None
    
    inliers = mask.ravel().sum()
    logger.info(f"[PVA Processor] Homography computed with {inliers} inliers")
    
    return homography


def align_to_reference(pva_image, reference_image,
                       output_size: Optional[Tuple[int, int]] = None) -> Optional[Any]:
    """
    Align a PVA image to a reference image (typically a modern mosaic).
    """
    if not OPENCV_AVAILABLE:
        return None
        
    homography = match_images(pva_image, reference_image)
    
    if homography is None:
        return None
    
    if output_size is None:
        output_size = (reference_image.shape[1], reference_image.shape[0])
    
    # Warp the PVA image
    aligned = cv2.warpPerspective(pva_image, homography, output_size)
    
    return aligned


# ==========================================
# 4. COMPLETE PROCESSING PIPELINE
# ==========================================

def process_pva_image(
    input_path: str,
    output_path: str,
    orientation: Optional[float] = None,
    reference_path: Optional[str] = None,
    auto_crop: bool = True,
    apply_rotation: bool = True
) -> Dict[str, Any]:
    """
    Complete PVA processing pipeline.
    """
    if not OPENCV_AVAILABLE:
        return {"success": False, "error": "OpenCV not available"}
    
    result = {
        "success": False,
        "input": input_path,
        "output": output_path,
        "steps": []
    }
    
    try:
        # Load image
        image = cv2.imread(input_path)
        if image is None:
            raise ValueError(f"Could not load image: {input_path}")
        
        original_size = (image.shape[1], image.shape[0])
        result["original_size"] = original_size
        result["steps"].append("loaded")
        
        # Step 1: Auto-crop
        if auto_crop:
            image, crop_region = crop_to_photo(image)
            result["crop_region"] = crop_region
            result["steps"].append("cropped")
            logger.info(f"[PVA Processor] Cropped to {image.shape[1]}x{image.shape[0]}")
        
        # Step 2: Rotation
        if apply_rotation and orientation is not None:
            rotation_angle = normalize_orientation(orientation)
            if abs(rotation_angle) > 1:  # Only rotate if significant
                image = rotate_image(image, rotation_angle)
                result["rotation_applied"] = rotation_angle
                result["steps"].append("rotated")
                logger.info(f"[PVA Processor] Rotated by {rotation_angle:.1f}°")
        
        # Step 3: Feature matching alignment (if reference provided)
        if reference_path and os.path.exists(reference_path):
            reference = cv2.imread(reference_path)
            if reference is not None:
                aligned = align_to_reference(image, reference)
                if aligned is not None:
                    image = aligned
                    result["steps"].append("aligned")
                    logger.info("[PVA Processor] Aligned to reference")
                else:
                    logger.warning("[PVA Processor] Alignment failed, using rotated image")
        
        # Save processed image
        cv2.imwrite(output_path, image)
        result["processed_size"] = (image.shape[1], image.shape[0])
        result["success"] = True
        result["steps"].append("saved")
        
        logger.info(f"[PVA Processor] Saved processed image: {output_path}")
        
    except Exception as e:
        result["error"] = str(e)
        logger.error(f"[PVA Processor] Error: {e}")
    
    return result


def create_georeferenced_pva(
    input_path: str,
    footprint: Dict[str, float],
    orientation: Optional[float] = None,
    auto_crop: bool = True,
    apply_rotation: bool = True
) -> Dict[str, Any]:
    """
    Process PVA and create properly georeferenced output with world file.
    
    This is the main entry point for improved PVA georeferencing.
    """
    if not OPENCV_AVAILABLE:
        return {"success": False, "error": "OpenCV not available"}
    
    result = {
        "success": False,
        "input": input_path,
        "original_footprint": footprint
    }
    
    try:
        # Load image
        image = cv2.imread(input_path)
        if image is None:
            raise ValueError(f"Could not load image: {input_path}")
        
        original_h, original_w = image.shape[:2]
        
        # Auto-crop
        crop_offset_x, crop_offset_y = 0, 0
        if auto_crop:
            image, (crop_x, crop_y, crop_w, crop_h) = crop_to_photo(image)
            crop_offset_x = crop_x
            crop_offset_y = crop_y
            
            # Recalculate footprint based on crop
            lon_range = footprint['max_lon'] - footprint['min_lon']
            lat_range = footprint['max_lat'] - footprint['min_lat']
            
            pixel_lon = lon_range / original_w
            pixel_lat = lat_range / original_h
            
            new_footprint = {
                'min_lon': footprint['min_lon'] + (crop_x * pixel_lon),
                'max_lon': footprint['min_lon'] + ((crop_x + crop_w) * pixel_lon),
                'min_lat': footprint['max_lat'] - ((crop_y + crop_h) * pixel_lat),
                'max_lat': footprint['max_lat'] - (crop_y * pixel_lat)
            }
            result["adjusted_footprint"] = new_footprint
        else:
            new_footprint = footprint
        
        # Apply rotation if provided
        if apply_rotation and orientation is not None:
            rotation_angle = normalize_orientation(orientation)
            if abs(rotation_angle) > 1:
                image = rotate_image(image, rotation_angle)
                result["rotation_applied"] = rotation_angle
        
        # Save processed image (overwrite original)
        cv2.imwrite(input_path, image)
        
        # Create world file with adjusted footprint
        from modules.qgis_export.worldfile_writer import create_world_file, create_prj_file, EPSG_WEB_MERCATOR
        
        new_h, new_w = image.shape[:2]
        create_world_file(input_path, new_footprint, new_w, new_h, target_crs=EPSG_WEB_MERCATOR)
        create_prj_file(input_path, epsg=EPSG_WEB_MERCATOR)
        
        result["success"] = True
        result["final_size"] = (new_w, new_h)
        
    except Exception as e:
        result["error"] = str(e)
        logger.error(f"[PVA Processor] Error: {e}")
    
    return result
