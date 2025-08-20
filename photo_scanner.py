#!/usr/bin/env python3
"""
Photo Scanner Module - Core photo analysis and grouping functionality
Handles metadata extraction, time-based grouping, and similarity detection
"""

import osxphotos
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import imagehash
from PIL import Image
import hashlib
from collections import defaultdict
import os

@dataclass
class PhotoData:
    """Represents a single photo with analysis results."""
    # Identity
    uuid: str
    path: Optional[str]
    filename: str
    
    # Metadata
    timestamp: datetime
    camera_model: Optional[str]
    camera_make: Optional[str]
    
    # Technical Properties
    file_size: int
    width: int
    height: int
    format: str
    
    # Analysis Results
    perceptual_hash: Optional[str] = None
    quality_score: float = 0.0
    analyzed: bool = False

@dataclass
class PhotoGroup:
    """Collection of similar photos that should be reviewed together."""
    group_id: str
    photos: List[PhotoData]
    recommended_photo_uuid: str
    time_window_start: datetime
    time_window_end: datetime
    camera_model: str
    total_size_bytes: int
    potential_savings_bytes: int

class PhotoScanner:
    """Main photo scanning and analysis engine."""
    
    def __init__(self):
        self.photosdb = None
        self._photo_cache = {}
        
    def get_photosdb(self):
        """Get or create PhotosDB connection."""
        if self.photosdb is None:
            self.photosdb = osxphotos.PhotosDB()
        return self.photosdb
    
    def extract_photo_metadata(self, photo) -> PhotoData:
        """Extract metadata from osxphotos Photo object."""
        try:
            # Get basic metadata
            uuid = photo.uuid
            filename = photo.filename or photo.original_filename or f"{uuid}.unknown"
            timestamp = photo.date
            path = photo.path
            
            # Get camera info
            camera_make = None
            camera_model = None
            if photo.exif_info:
                camera_make = getattr(photo.exif_info, 'camera_make', None)
                camera_model = getattr(photo.exif_info, 'camera_model', None)
            
            # Get technical properties
            # Try to get file size - osxphotos might not have direct access
            file_size = 0
            width = 0
            height = 0
            format_str = "unknown"
            
            if hasattr(photo, 'size_bytes'):
                file_size = photo.size_bytes or 0
            
            if photo.width and photo.height:
                width = photo.width
                height = photo.height
                
            if photo.filename:
                format_str = photo.filename.split('.')[-1].upper() if '.' in photo.filename else "unknown"
            
            return PhotoData(
                uuid=uuid,
                path=path,
                filename=filename,
                timestamp=timestamp,
                camera_model=camera_model,
                camera_make=camera_make,
                file_size=file_size,
                width=width,
                height=height,
                format=format_str
            )
            
        except Exception as e:
            print(f"Error extracting metadata for photo {photo.uuid}: {e}")
            # Return minimal data structure to avoid breaking
            return PhotoData(
                uuid=photo.uuid,
                path=None,
                filename=f"{photo.uuid}.unknown",
                timestamp=photo.date or datetime.now(),
                camera_model=None,
                camera_make=None,
                file_size=0,
                width=0,
                height=0,
                format="unknown"
            )
    
    def scan_photos(self, limit: Optional[int] = None) -> List[PhotoData]:
        """Scan Photos library and extract metadata for all photos."""
        print("📡 Scanning Photos library...")
        
        db = self.get_photosdb()
        photos = db.photos()
        
        if limit:
            photos = photos[:limit]
        
        photo_data_list = []
        
        for i, photo in enumerate(photos):
            if i % 100 == 0:  # Progress indicator
                print(f"Processed {i}/{len(photos)} photos...")
            
            photo_data = self.extract_photo_metadata(photo)
            photo_data_list.append(photo_data)
            
            # Cache for later use
            self._photo_cache[photo_data.uuid] = photo_data
        
        print(f"✅ Completed scanning {len(photo_data_list)} photos")
        return photo_data_list
    
    def group_photos_by_time_and_camera(self, photos: List[PhotoData], 
                                      time_window_seconds: int = 10) -> List[PhotoGroup]:
        """Group photos by time window and camera model."""
        print(f"🔍 Grouping photos by {time_window_seconds}-second windows and camera...")
        
        # Filter out photos without timestamps
        valid_photos = [p for p in photos if p.timestamp is not None]
        print(f"📊 {len(valid_photos)} photos have valid timestamps")
        
        # Sort by timestamp
        valid_photos.sort(key=lambda p: p.timestamp)
        
        groups = []
        used_photos = set()
        
        for i, base_photo in enumerate(valid_photos):
            if base_photo.uuid in used_photos:
                continue
                
            # Find photos within time window and same camera
            group_photos = [base_photo]
            time_window_end = base_photo.timestamp + timedelta(seconds=time_window_seconds)
            
            for j, candidate_photo in enumerate(valid_photos[i+1:], i+1):
                if candidate_photo.uuid in used_photos:
                    continue
                    
                # Check time window
                if candidate_photo.timestamp > time_window_end:
                    break  # Photos are sorted, no more candidates
                
                # Check camera model match (allow None matches)
                if (base_photo.camera_model == candidate_photo.camera_model or 
                    (base_photo.camera_model is None and candidate_photo.camera_model is None)):
                    group_photos.append(candidate_photo)
            
            # Only create group if we have multiple photos
            if len(group_photos) > 1:
                # Mark photos as used
                for photo in group_photos:
                    used_photos.add(photo.uuid)
                
                # Calculate group statistics
                total_size = sum(p.file_size for p in group_photos)
                # Assume we keep the largest/newest photo, save the rest
                potential_savings = total_size - max((p.file_size for p in group_photos), default=0)
                
                # Recommend newest photo (latest timestamp)
                recommended_photo = max(group_photos, key=lambda p: p.timestamp)
                
                group = PhotoGroup(
                    group_id=f"group_{len(groups)+1:04d}",
                    photos=group_photos,
                    recommended_photo_uuid=recommended_photo.uuid,
                    time_window_start=base_photo.timestamp,
                    time_window_end=group_photos[-1].timestamp,
                    camera_model=base_photo.camera_model or "Unknown",
                    total_size_bytes=total_size,
                    potential_savings_bytes=potential_savings
                )
                
                groups.append(group)
        
        print(f"✅ Created {len(groups)} photo groups")
        return groups
    
    def compute_perceptual_hash(self, photo_data: PhotoData) -> Optional[str]:
        """Compute perceptual hash for similarity detection."""
        if not photo_data.path or not os.path.exists(photo_data.path):
            return None
            
        try:
            # Open image and compute hash
            with Image.open(photo_data.path) as img:
                # Convert to RGB if needed
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Compute perceptual hash
                hash_obj = imagehash.phash(img)
                return str(hash_obj)
                
        except Exception as e:
            print(f"Error computing hash for {photo_data.filename}: {e}")
            return None
    
    def analyze_photo_quality(self, photo_data: PhotoData) -> float:
        """Basic quality assessment based on resolution and other factors."""
        quality_score = 0.0
        
        # Resolution score (0-40 points)
        pixel_count = photo_data.width * photo_data.height
        if pixel_count > 8000000:  # > 8MP
            quality_score += 40
        elif pixel_count > 4000000:  # > 4MP
            quality_score += 30
        elif pixel_count > 2000000:  # > 2MP
            quality_score += 20
        else:
            quality_score += 10
        
        # File size score (0-30 points) - larger generally better quality
        if photo_data.file_size > 5000000:  # > 5MB
            quality_score += 30
        elif photo_data.file_size > 2000000:  # > 2MB
            quality_score += 20
        elif photo_data.file_size > 1000000:  # > 1MB
            quality_score += 15
        else:
            quality_score += 5
        
        # Format score (0-30 points)
        if photo_data.format.upper() in ['HEIC', 'RAW', 'DNG']:
            quality_score += 30
        elif photo_data.format.upper() in ['JPEG', 'JPG']:
            quality_score += 20
        else:
            quality_score += 10
        
        return min(quality_score, 100.0)  # Cap at 100
    
    def enhanced_grouping_with_similarity(self, groups: List[PhotoGroup]) -> List[PhotoGroup]:
        """Enhance groups with perceptual hash similarity analysis."""
        print("🔬 Computing perceptual hashes for similarity analysis...")
        
        enhanced_groups = []
        
        for group in groups:
            # Compute hashes and quality scores for all photos in group
            for photo in group.photos:
                if not photo.analyzed:
                    photo.perceptual_hash = self.compute_perceptual_hash(photo)
                    photo.quality_score = self.analyze_photo_quality(photo)
                    photo.analyzed = True
            
            # Re-evaluate recommendation based on quality scores
            photos_with_quality = [p for p in group.photos if p.quality_score > 0]
            if photos_with_quality:
                best_photo = max(photos_with_quality, key=lambda p: p.quality_score)
                group.recommended_photo_uuid = best_photo.uuid
            
            enhanced_groups.append(group)
        
        print("✅ Enhanced grouping with similarity analysis complete")
        return enhanced_groups

def main():
    """Test the photo scanner functionality."""
    scanner = PhotoScanner()
    
    # Test with limited photos first
    print("🧪 Testing PhotoScanner with limited dataset...")
    photos = scanner.scan_photos(limit=100)
    
    if not photos:
        print("❌ No photos found")
        return
    
    print(f"📊 Scanned {len(photos)} photos")
    
    # Group photos
    groups = scanner.group_photos_by_time_and_camera(photos)
    
    if not groups:
        print("ℹ️ No photo groups found in sample")
        return
    
    # Show results
    print(f"🎯 Found {len(groups)} potential duplicate groups:")
    for group in groups[:5]:  # Show first 5 groups
        print(f"\nGroup {group.group_id}:")
        print(f"  📅 Time span: {group.time_window_start} to {group.time_window_end}")
        print(f"  📷 Camera: {group.camera_model}")
        print(f"  📸 Photos: {len(group.photos)}")
        print(f"  💾 Total size: {group.total_size_bytes / 1024 / 1024:.1f} MB")
        print(f"  💰 Potential savings: {group.potential_savings_bytes / 1024 / 1024:.1f} MB")
        for photo in group.photos:
            marker = "⭐" if photo.uuid == group.recommended_photo_uuid else "  "
            print(f"    {marker} {photo.filename} - {photo.timestamp}")

if __name__ == "__main__":
    main()