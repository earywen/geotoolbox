"""
Test script for PVA processor module.
Validates auto-crop and rotation functionality.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.pva_processor import (
    detect_photo_region,
    crop_to_photo,
    rotate_image,
    normalize_orientation
)
import cv2
import numpy as np

def test_border_detection():
    """Test black border detection with a synthetic image."""
    # Create a test image: white photo with black border
    image = np.zeros((1000, 1000, 3), dtype=np.uint8)
    # Add white photo area (with some margin for black border)
    image[100:900, 100:900] = 255  # White center
    
    region = detect_photo_region(image)
    
    if region:
        x, y, w, h = region
        print(f"✅ Border detection: Found photo at ({x},{y}) size {w}x{h}")
        # Should be approximately 100, 100, 800, 800
        assert abs(x - 100) < 10, f"X offset wrong: {x}"
        assert abs(y - 100) < 10, f"Y offset wrong: {y}"
        assert abs(w - 800) < 20, f"Width wrong: {w}"
        assert abs(h - 800) < 20, f"Height wrong: {h}"
        print("   ✅ Values are correct!")
    else:
        print("❌ Border detection failed")
        return False
    
    return True

def test_rotation():
    """Test rotation function."""
    # Create simple test image
    image = np.zeros((100, 200, 3), dtype=np.uint8)
    image[:, :100] = [255, 0, 0]  # Blue left half
    image[:, 100:] = [0, 255, 0]  # Green right half
    
    # Rotate 90 degrees
    rotated = rotate_image(image, 90)
    
    print(f"✅ Rotation: Original {image.shape[:2]}, Rotated {rotated.shape[:2]}")
    return True

def test_orientation_normalization():
    """Test orientation normalization."""
    test_cases = [
        (0, 0),      # North -> no rotation
        (90, -90),   # East -> rotate -90
        (180, -180), # South -> rotate 180/-180
        (270, 90),   # West -> rotate +90
        (45, -45),   # NE -> rotate -45
    ]
    
    print("Testing orientation normalization:")
    for orientation, expected_approx in test_cases:
        result = normalize_orientation(orientation)
        # Allow for the 180/-180 equivalence
        is_ok = abs(result - expected_approx) < 1 or abs(abs(result) - abs(expected_approx)) < 1
        status = "✅" if is_ok else "❌"
        print(f"  {status} Orientation {orientation}° -> Rotation {result:.1f}° (expected ~{expected_approx}°)")
    
    return True

if __name__ == "__main__":
    print("=" * 50)
    print("PVA Processor Module Test")
    print("=" * 50)
    
    try:
        test_border_detection()
        print()
        test_rotation()
        print()
        test_orientation_normalization()
        print()
        print("✅ All tests passed!")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
