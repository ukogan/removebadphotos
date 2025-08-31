#!/usr/bin/env python3
"""
Blur Detection Module - Focused computer vision analysis for photo quality assessment
Detects blurry, overexposed, and underexposed photos for removal workflow
"""

import cv2
import numpy as np
from PIL import Image
from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict
from pathlib import Path
import time

@dataclass
class BlurResult:
    """Result of blur analysis for a single photo."""
    photo_uuid: str
    image_path: str
    blur_score: float  # Laplacian variance (higher = sharper)
    blur_level: str  # 'very-blurry', 'blurry', 'slightly-blurry', 'sharp'
    exposure_score: float  # 0-100 (50 = ideal, 0/100 = over/under exposed)
    quality_assessment: str  # Overall assessment
    processing_time_ms: int
    file_size_bytes: int
    resolution: Tuple[int, int]  # (width, height)

class BlurDetector:
    """Fast, dedicated blur detection using Laplacian variance analysis."""
    
    def __init__(self, 
                 blur_threshold_very: float = 50,
                 blur_threshold_moderate: float = 100, 
                 blur_threshold_slight: float = 200):
        """
        Initialize blur detector with configurable thresholds.
        
        Args:
            blur_threshold_very: Below this = very blurry (default: 50)
            blur_threshold_moderate: Below this = blurry (default: 100)  
            blur_threshold_slight: Below this = slightly blurry (default: 200)
            Above slight threshold = sharp
        """
        self.blur_threshold_very = blur_threshold_very
        self.blur_threshold_moderate = blur_threshold_moderate
        self.blur_threshold_slight = blur_threshold_slight
        
    def update_thresholds(self, very: float, moderate: float, slight: float):
        """Update blur detection thresholds."""
        self.blur_threshold_very = very
        self.blur_threshold_moderate = moderate
        self.blur_threshold_slight = slight
    
    def analyze_photo(self, image_path: str, photo_uuid: str = None) -> BlurResult:
        """
        Analyze single photo for blur and exposure quality.
        
        Args:
            image_path: Path to image file
            photo_uuid: Optional UUID for tracking
            
        Returns:
            BlurResult with analysis data
        """
        start_time = time.time()
        
        try:
            # Get file info
            file_path = Path(image_path)
            file_size = file_path.stat().st_size if file_path.exists() else 0
            
            # Load image
            img = None
            try:
                img = cv2.imread(image_path)
            except:
                pass
            
            if img is None:
                # Try with PIL for HEIC and other formats
                try:
                    with Image.open(image_path) as pil_img:
                        img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
                except Exception as e:
                    print(f"⚠️ Could not load image {image_path}: {e}")
                    return self._create_error_result(image_path, photo_uuid, file_size)
            
            if img is None:
                return self._create_error_result(image_path, photo_uuid, file_size)
            
            # Get image dimensions
            height, width = img.shape[:2]
            resolution = (width, height)
            
            # Convert to grayscale for analysis
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # 1. Blur detection using Laplacian variance
            laplacian = cv2.Laplacian(gray, cv2.CV_64F)
            blur_score = laplacian.var()
            
            # 2. Exposure analysis using histogram
            exposure_score = self._analyze_exposure(gray)
            
            # 3. Determine blur level based on thresholds
            blur_level = self._classify_blur_level(blur_score)
            
            # 4. Overall quality assessment
            quality_assessment = self._assess_quality(blur_level, exposure_score)
            
            processing_time = int((time.time() - start_time) * 1000)
            
            return BlurResult(
                photo_uuid=photo_uuid or "unknown",
                image_path=image_path,
                blur_score=blur_score,
                blur_level=blur_level,
                exposure_score=exposure_score,
                quality_assessment=quality_assessment,
                processing_time_ms=processing_time,
                file_size_bytes=file_size,
                resolution=resolution
            )
            
        except Exception as e:
            print(f"❌ Error analyzing {image_path}: {e}")
            return self._create_error_result(image_path, photo_uuid, file_size)
    
    def analyze_batch(self, image_paths: List[Tuple[str, str]], 
                     progress_callback=None) -> List[BlurResult]:
        """
        Analyze multiple photos efficiently.
        
        Args:
            image_paths: List of (image_path, photo_uuid) tuples
            progress_callback: Optional callback(current, total)
            
        Returns:
            List of BlurResult objects
        """
        results = []
        total = len(image_paths)
        
        print(f"🔍 Starting blur analysis of {total} photos...")
        
        for i, (image_path, photo_uuid) in enumerate(image_paths):
            if progress_callback and i % 50 == 0:
                progress_callback(i, total)
            
            result = self.analyze_photo(image_path, photo_uuid)
            results.append(result)
            
            # Progress feedback
            if i % 100 == 0 and i > 0:
                sharp_count = sum(1 for r in results if r.blur_level == 'sharp')
                blurry_count = i + 1 - sharp_count
                print(f"📊 Processed {i+1}/{total} photos: {sharp_count} sharp, {blurry_count} with issues")
        
        print(f"✅ Blur analysis complete: {len(results)} photos analyzed")
        return results
    
    def get_statistics(self, results: List[BlurResult]) -> Dict[str, any]:
        """Generate summary statistics from analysis results."""
        if not results:
            return {}
        
        total = len(results)
        by_level = {'very-blurry': 0, 'blurry': 0, 'slightly-blurry': 0, 'sharp': 0}
        total_size = 0
        processing_times = []
        
        for result in results:
            by_level[result.blur_level] += 1
            total_size += result.file_size_bytes
            processing_times.append(result.processing_time_ms)
        
        # Calculate potential savings (assume we'd remove very blurry and blurry photos)
        problematic_photos = [r for r in results if r.blur_level in ['very-blurry', 'blurry']]
        potential_savings_bytes = sum(r.file_size_bytes for r in problematic_photos)
        
        return {
            'total_analyzed': total,
            'by_quality_level': by_level,
            'quality_issues_found': by_level['very-blurry'] + by_level['blurry'],
            'potential_savings_bytes': potential_savings_bytes,
            'potential_savings_mb': potential_savings_bytes / (1024 * 1024),
            'potential_savings_gb': potential_savings_bytes / (1024 * 1024 * 1024),
            'average_processing_time_ms': np.mean(processing_times) if processing_times else 0,
            'total_library_size_gb': total_size / (1024 * 1024 * 1024)
        }
    
    def _analyze_exposure(self, gray_image) -> float:
        """Analyze image exposure using histogram analysis."""
        try:
            # Calculate histogram
            hist = cv2.calcHist([gray_image], [0], None, [256], [0, 256])
            
            # Calculate percentiles
            total_pixels = gray_image.shape[0] * gray_image.shape[1]
            cumulative = np.cumsum(hist.flatten()) / total_pixels
            
            # Find 5th and 95th percentiles
            p5 = np.argmax(cumulative >= 0.05)
            p95 = np.argmax(cumulative >= 0.95)
            
            # Score based on how well-distributed the histogram is
            # Good exposure: substantial range between 5th and 95th percentiles
            dynamic_range = p95 - p5
            
            # Penalize images with very low or very high average brightness
            mean_brightness = np.mean(gray_image)
            
            # Score from 0-100 (50 = ideal exposure)
            if mean_brightness < 30:  # Underexposed
                exposure_score = (mean_brightness / 30) * 25
            elif mean_brightness > 225:  # Overexposed  
                exposure_score = 100 - ((mean_brightness - 225) / 30) * 25
            else:
                exposure_score = 50  # Good exposure range
            
            # Adjust based on dynamic range
            if dynamic_range < 50:  # Low contrast
                exposure_score *= 0.7
            elif dynamic_range > 200:  # Good contrast
                exposure_score = min(exposure_score * 1.1, 100)
            
            return max(0, min(100, exposure_score))
            
        except Exception:
            return 50  # Default neutral score
    
    def _classify_blur_level(self, blur_score: float) -> str:
        """Classify blur level based on Laplacian variance score."""
        if blur_score < self.blur_threshold_very:
            return 'very-blurry'
        elif blur_score < self.blur_threshold_moderate:
            return 'blurry'
        elif blur_score < self.blur_threshold_slight:
            return 'slightly-blurry'
        else:
            return 'sharp'
    
    def _assess_quality(self, blur_level: str, exposure_score: float) -> str:
        """Generate overall quality assessment."""
        issues = []
        
        if blur_level == 'very-blurry':
            issues.append('Very blurry')
        elif blur_level == 'blurry':
            issues.append('Blurry')
        elif blur_level == 'slightly-blurry':
            issues.append('Slightly blurry')
        
        if exposure_score < 20:
            issues.append('Underexposed')
        elif exposure_score > 80:
            issues.append('Overexposed')
        
        if issues:
            return ', '.join(issues)
        else:
            return 'Good quality'
    
    def _create_error_result(self, image_path: str, photo_uuid: str, file_size: int) -> BlurResult:
        """Create error result when image analysis fails."""
        return BlurResult(
            photo_uuid=photo_uuid or "unknown",
            image_path=image_path,
            blur_score=0.0,
            blur_level='unknown',
            exposure_score=0.0,
            quality_assessment='Analysis failed',
            processing_time_ms=0,
            file_size_bytes=file_size,
            resolution=(0, 0)
        )

def main():
    """Test the blur detector functionality."""
    detector = BlurDetector()
    
    print("🧪 Testing BlurDetector...")
    print(f"Thresholds: Very={detector.blur_threshold_very}, "
          f"Moderate={detector.blur_threshold_moderate}, "
          f"Slight={detector.blur_threshold_slight}")

if __name__ == "__main__":
    main()