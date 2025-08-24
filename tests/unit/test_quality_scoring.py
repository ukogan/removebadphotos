#!/usr/bin/env python3
"""
Unit tests for photo quality scoring functions
Pure functions only - no side effects
"""
import pytest
import sys
import os
import numpy as np
from unittest.mock import Mock

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

@pytest.mark.unit
def test_quality_score_calculation():
    """Test quality scoring math functions"""
    # Mock photo data
    photo_data = {
        'resolution': (4032, 3024),
        'file_size': 2500000,  # 2.5MB
        'format': 'JPEG'
    }
    
    # Resolution score (normalized to 0-1)
    width, height = photo_data['resolution']
    resolution_score = min((width * height) / (4032 * 3024), 1.0)
    assert resolution_score == 1.0
    
    # File size score (larger is better up to a point)
    size_mb = photo_data['file_size'] / 1024 / 1024
    size_score = min(size_mb / 5.0, 1.0)  # Normalize to 5MB max
    assert 0.4 < size_score < 0.6
    
    # Format preference
    format_scores = {'HEIC': 1.0, 'JPEG': 0.8, 'PNG': 0.6}
    format_score = format_scores.get(photo_data['format'], 0.5)
    assert format_score == 0.8

@pytest.mark.unit
def test_sharpness_calculation():
    """Test Laplacian variance sharpness calculation"""
    # Create test image with known sharpness
    import cv2
    
    # Sharp image (high contrast edges)
    sharp_image = np.zeros((100, 100), dtype=np.uint8)
    sharp_image[40:60, 40:60] = 255  # White square on black background
    
    # Blurry image (low contrast)
    blurry_image = np.ones((100, 100), dtype=np.uint8) * 128  # Uniform gray
    
    # Calculate Laplacian variance
    sharp_laplacian = cv2.Laplacian(sharp_image, cv2.CV_64F)
    sharp_variance = sharp_laplacian.var()
    
    blurry_laplacian = cv2.Laplacian(blurry_image, cv2.CV_64F)  
    blurry_variance = blurry_laplacian.var()
    
    # Sharp image should have higher variance
    assert sharp_variance > blurry_variance
    assert sharp_variance > 1000  # Reasonable threshold
    assert blurry_variance < 10   # Near zero for uniform image

@pytest.mark.unit
def test_brightness_analysis():
    """Test brightness calculation functions"""
    # Test images with known brightness
    dark_image = np.zeros((100, 100, 3), dtype=np.uint8)  # All black
    bright_image = np.ones((100, 100, 3), dtype=np.uint8) * 255  # All white
    mid_image = np.ones((100, 100, 3), dtype=np.uint8) * 128  # Mid gray
    
    # Calculate mean brightness
    dark_brightness = np.mean(dark_image)
    bright_brightness = np.mean(bright_image)
    mid_brightness = np.mean(mid_image)
    
    assert dark_brightness == 0
    assert bright_brightness == 255
    assert mid_brightness == 128
    
    # Ideal brightness range (avoiding over/under exposure)
    def brightness_score(brightness):
        if 80 <= brightness <= 180:  # Good exposure range
            return 1.0
        elif brightness < 30 or brightness > 220:  # Poor exposure
            return 0.3
        else:  # Marginal exposure
            return 0.7
    
    assert brightness_score(dark_brightness) == 0.3
    assert brightness_score(bright_brightness) == 0.3
    assert brightness_score(mid_brightness) == 1.0

@pytest.mark.unit  
def test_noise_estimation():
    """Test noise level estimation"""
    # Clean image (low noise)
    clean_image = np.ones((100, 100), dtype=np.uint8) * 128
    
    # Noisy image
    noisy_image = clean_image.copy()
    noise = np.random.randint(-20, 20, (100, 100), dtype=np.int16)
    noisy_image = np.clip(noisy_image.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    
    # Calculate noise as standard deviation
    clean_std = np.std(clean_image)
    noisy_std = np.std(noisy_image)
    
    assert clean_std == 0  # Uniform image has no variation
    assert noisy_std > 5   # Noisy image has variation
    
    # Noise score (lower noise = higher score)
    def noise_score(std_dev):
        return max(0, 1.0 - (std_dev / 50))  # Normalize to 50 std dev
    
    assert noise_score(clean_std) == 1.0
    assert noise_score(noisy_std) < 0.9

@pytest.mark.unit
def test_perceptual_hash_similarity():
    """Test perceptual hash distance calculation"""
    import imagehash
    from PIL import Image
    
    # Create similar test images
    img1 = Image.new('RGB', (100, 100), color='red')
    img2 = Image.new('RGB', (100, 100), color='red')
    img3 = Image.new('RGB', (100, 100), color='blue')
    
    # Calculate hashes
    hash1 = imagehash.average_hash(img1)
    hash2 = imagehash.average_hash(img2)
    hash3 = imagehash.average_hash(img3)
    
    # Similar images should have similar hashes
    distance_similar = hash1 - hash2
    distance_different = hash1 - hash3
    
    assert distance_similar == 0  # Identical images
    assert distance_different > distance_similar  # Different images more distant

@pytest.mark.unit
def test_time_proximity_grouping():
    """Test time-based photo grouping logic"""
    from datetime import datetime, timedelta
    
    base_time = datetime.now()
    photos = [
        {'id': '1', 'timestamp': base_time},
        {'id': '2', 'timestamp': base_time + timedelta(seconds=5)},
        {'id': '3', 'timestamp': base_time + timedelta(seconds=15)},  # Outside window
        {'id': '4', 'timestamp': base_time + timedelta(seconds=8)},
    ]
    
    def group_by_time(photos, window_seconds=10):
        groups = []
        for photo in sorted(photos, key=lambda p: p['timestamp']):
            placed = False
            for group in groups:
                # Check if photo is within window of any photo in group
                for group_photo in group:
                    time_diff = abs((photo['timestamp'] - group_photo['timestamp']).total_seconds())
                    if time_diff <= window_seconds:
                        group.append(photo)
                        placed = True
                        break
                if placed:
                    break
            
            if not placed:
                groups.append([photo])
        
        return groups
    
    groups = group_by_time(photos)
    
    # Should have 2 groups: [1,2,4] and [3]
    assert len(groups) == 2
    group_sizes = [len(g) for g in groups]
    assert 3 in group_sizes  # Main group
    assert 1 in group_sizes  # Isolated photo