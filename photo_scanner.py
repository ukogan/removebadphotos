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
import cv2
import numpy as np

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
    
    # Organization metadata
    albums: List[str] = None
    folder_names: List[str] = None
    keywords: List[str] = None
    organization_score: float = 0.0  # Higher = better organized
    
    # Optional fields with defaults
    original_filename: Optional[str] = None
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
    
    def get_unprocessed_photos(self, include_videos: bool = False):
        """Get photos excluding those in trash and already marked for deletion."""
        db = self.get_photosdb()
        all_photos = db.photos(intrash=False, movies=not include_videos)
        
        # Filter out photos already marked for deletion
        photos = []
        marked_for_deletion_count = 0
        for photo in all_photos:
            if photo.keywords and "marked-for-deletion" in photo.keywords:
                marked_for_deletion_count += 1
                continue
            photos.append(photo)
        
        if marked_for_deletion_count > 0:
            print(f"🔄 Excluded {marked_for_deletion_count} photos already marked for deletion")
        
        return photos, marked_for_deletion_count
    
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
            file_size = photo.original_filesize or 0  # Use original_filesize for accurate size
            width = photo.width or 0
            height = photo.height or 0
            
            if photo.original_filename:
                format_str = photo.original_filename.split('.')[-1].upper() if '.' in photo.original_filename else "unknown"
            elif photo.filename:
                format_str = photo.filename.split('.')[-1].upper() if '.' in photo.filename else "unknown"
            else:
                format_str = "unknown"
            
            # Get organization metadata
            albums = list(photo.albums) if photo.albums else []
            folder_names = []
            keywords = list(photo.keywords) if photo.keywords else []
            
            # Extract folder information from path
            if path:
                path_parts = path.split('/')
                # Look for meaningful folder names (skip system folders)
                meaningful_folders = []
                for part in path_parts:
                    if part and not part.startswith('.') and part not in ['Users', 'Pictures', 'Photos']:
                        meaningful_folders.append(part)
                folder_names = meaningful_folders[-3:] if len(meaningful_folders) > 3 else meaningful_folders
            
            # Calculate organization score
            org_score = self.calculate_organization_score(albums, folder_names, keywords, path)
            
            return PhotoData(
                uuid=uuid,
                path=path,
                filename=filename,
                original_filename=photo.original_filename,
                timestamp=timestamp,
                camera_model=camera_model,
                camera_make=camera_make,
                file_size=file_size,
                width=width,
                height=height,
                format=format_str,
                albums=albums,
                folder_names=folder_names,
                keywords=keywords,
                organization_score=org_score
            )
            
        except Exception as e:
            print(f"Error extracting metadata for photo {photo.uuid}: {e}")
            # Return minimal data structure to avoid breaking
            return PhotoData(
                uuid=photo.uuid,
                path=None,
                filename=f"{photo.uuid}.unknown",
                original_filename=getattr(photo, 'original_filename', None),
                timestamp=photo.date or datetime.now(),
                camera_model=None,
                camera_make=None,
                file_size=0,
                width=0,
                height=0,
                format="unknown",
                albums=[],
                folder_names=[],
                keywords=[],
                organization_score=0.0
            )
    
    def calculate_organization_score(self, albums: List[str], folder_names: List[str], 
                                   keywords: List[str], path: Optional[str]) -> float:
        """Calculate organization score (0-100) based on how well-organized a photo is."""
        score = 0.0
        
        # Album organization (0-40 points)
        if albums:
            score += 30  # Base points for being in any album
            if len(albums) > 1:
                score += 10  # Bonus for being in multiple albums (well-organized)
        
        # Folder organization (0-30 points)
        if folder_names:
            score += 15  # Base points for meaningful folder structure
            # Bonus for deeper, more specific organization
            if len(folder_names) >= 2:
                score += 10
            if len(folder_names) >= 3:
                score += 5
        
        # Keywords/tags (0-20 points)
        if keywords:
            score += 10  # Base points for having keywords
            if len(keywords) >= 3:
                score += 10  # Bonus for multiple keywords
        
        # Path specificity (0-10 points)
        if path and '/' in path:
            # More specific paths (deeper folders) get higher scores
            depth = path.count('/')
            if depth >= 4:  # e.g., /Users/name/Pictures/2023/Vacation/
                score += 10
            elif depth >= 3:
                score += 5
        
        return min(score, 100.0)  # Cap at 100
    
    def analyze_image_quality(self, image_path: str) -> float:
        """Analyze image quality using multiple metrics. Returns score 0-100."""
        try:
            # Load image with OpenCV
            img = cv2.imread(image_path)
            if img is None:
                # Try with PIL for formats OpenCV can't handle
                with Image.open(image_path) as pil_img:
                    img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
            
            if img is None:
                return 0.0
            
            # Convert to grayscale for analysis
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # 1. Sharpness analysis using Laplacian variance
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            sharpness_score = min(laplacian_var / 1000.0, 1.0)  # Normalize to 0-1
            
            # 2. Brightness and contrast analysis
            mean_brightness = np.mean(gray)
            brightness_score = 1.0 - abs(mean_brightness - 127.5) / 127.5  # Penalize extreme brightness
            
            # 3. Resolution score (higher resolution = better)
            height, width = img.shape[:2]
            total_pixels = height * width
            resolution_score = min(total_pixels / (4032 * 3024), 1.0)  # Normalize to iPhone max res
            
            # 4. Noise analysis (lower noise = better)
            # Use standard deviation of Gaussian blur difference
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            noise = np.std(gray - blurred)
            noise_score = max(0, 1.0 - noise / 50.0)  # Lower noise is better
            
            # Combine scores with weights
            quality_score = (
                sharpness_score * 0.4 +      # 40% - most important
                brightness_score * 0.2 +     # 20%
                resolution_score * 0.2 +     # 20% 
                noise_score * 0.2            # 20%
            ) * 100
            
            return min(max(quality_score, 0.0), 100.0)  # Clamp to 0-100
            
        except Exception as e:
            print(f"Error analyzing image quality for {image_path}: {e}")
            return 0.0
    
    def scan_photos(self, limit: Optional[int] = None, prioritize_accessible: bool = True) -> List[PhotoData]:
        """Scan Photos library and extract metadata for all photos."""
        print("📡 Scanning Photos library...")
        
        db = self.get_photosdb()
        # Explicitly exclude Recently Deleted photos to prevent duplicate processing
        # of photos that user has already deleted
        all_photos = db.photos(intrash=False, movies=False)
        
        # Filter out photos that are already marked for deletion to prevent reprocessing
        photos = []
        marked_for_deletion_count = 0
        for photo in all_photos:
            if photo.keywords and "marked-for-deletion" in photo.keywords:
                marked_for_deletion_count += 1
                continue
            photos.append(photo)
        
        if marked_for_deletion_count > 0:
            print(f"🔄 Excluded {marked_for_deletion_count} photos already marked for deletion")
        print(f"📊 Processing {len(photos)} photos for analysis")
        
        if prioritize_accessible:
            print("🔍 Prioritizing locally accessible photos for better thumbnail support...")
            # Separate accessible and non-accessible photos
            accessible_photos = []
            non_accessible_photos = []
            
            for photo in photos:
                if photo.path and os.path.exists(photo.path):
                    accessible_photos.append(photo)
                else:
                    non_accessible_photos.append(photo)
            
            print(f"📊 Found {len(accessible_photos)} accessible photos, {len(non_accessible_photos)} cloud-only photos")
            
            # Combine with accessible photos first
            photos = accessible_photos + non_accessible_photos
        
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
    
    def calculate_visual_similarity(self, hash1: str, hash2: str) -> float:
        """Calculate visual similarity between two perceptual hashes.
        Returns similarity percentage (0-100), where 100 = identical."""
        if not hash1 or not hash2:
            return 0.0
        
        try:
            # Convert hash strings back to imagehash objects
            h1 = imagehash.hex_to_hash(hash1)
            h2 = imagehash.hex_to_hash(hash2)
            
            # Calculate Hamming distance
            hamming_distance = h1 - h2
            
            # Convert to similarity percentage
            # phash produces 64-bit hashes, so max distance is 64
            max_distance = 64
            similarity = (1.0 - (hamming_distance / max_distance)) * 100
            
            return max(0.0, min(100.0, similarity))
            
        except Exception as e:
            print(f"Error calculating similarity between hashes {hash1} and {hash2}: {e}")
            return 0.0
    
    def analyze_photo_quality(self, photo_data: PhotoData) -> float:
        """Enhanced quality assessment including organization metadata."""
        quality_score = 0.0
        
        # Resolution score (0-30 points) - reduced to make room for organization
        pixel_count = photo_data.width * photo_data.height
        if pixel_count > 8000000:  # > 8MP
            quality_score += 30
        elif pixel_count > 4000000:  # > 4MP
            quality_score += 22
        elif pixel_count > 2000000:  # > 2MP
            quality_score += 15
        else:
            quality_score += 8
        
        # File size score (0-25 points) - larger generally better quality
        if photo_data.file_size > 5000000:  # > 5MB
            quality_score += 25
        elif photo_data.file_size > 2000000:  # > 2MB
            quality_score += 18
        elif photo_data.file_size > 1000000:  # > 1MB
            quality_score += 12
        else:
            quality_score += 5
        
        # Format score (0-20 points)
        if photo_data.format.upper() in ['HEIC', 'RAW', 'DNG']:
            quality_score += 20
        elif photo_data.format.upper() in ['JPEG', 'JPG']:
            quality_score += 15
        else:
            quality_score += 8
        
        # Organization score (0-25 points) - NEW: Favor organized photos
        org_score = photo_data.organization_score
        if org_score > 0:
            # Scale organization score to 0-25 points
            quality_score += (org_score / 100.0) * 25
            print(f"🗂️ {photo_data.filename} organization bonus: +{(org_score / 100.0) * 25:.1f} pts (albums: {len(photo_data.albums or [])}, folders: {len(photo_data.folder_names or [])})")
        
        return min(quality_score, 100.0)  # Cap at 100
    
    def enhanced_grouping_with_similarity(self, groups: List[PhotoGroup], progress_callback=None) -> List[PhotoGroup]:
        """Enhance groups with perceptual hash similarity analysis."""
        print("🔬 Computing perceptual hashes and image-based quality analysis...")
        
        enhanced_groups = []
        total_photos = sum(len(group.photos) for group in groups)
        photos_processed = 0
        
        for group_idx, group in enumerate(groups):
            # Compute hashes and quality scores for all photos in group
            for photo in group.photos:
                if not photo.analyzed:
                    photos_processed += 1
                    
                    # Report progress if callback provided
                    if progress_callback:
                        progress_callback(
                            step="Analyzing image quality",
                            progress=3,
                            total=4,
                            tooltip=f"Computing quality scores for photo groups using sharpness and composition analysis...",
                            current_operation="Analyzing image quality",
                            current_item=photo.filename,
                            items_processed=photos_processed,
                            total_items=total_photos
                        )
                    
                    photo.perceptual_hash = self.compute_perceptual_hash(photo)
                    
                    # Try image-based quality analysis first, fallback to metadata-based
                    if photo.path and os.path.exists(photo.path):
                        print(f"🔍 Analyzing image quality for {photo.filename}...")
                        photo.quality_score = self.analyze_image_quality(photo.path)
                    else:
                        # Fallback to metadata-based quality analysis
                        photo.quality_score = self.analyze_photo_quality(photo)
                    
                    photo.analyzed = True
                    print(f"📊 Quality score for {photo.filename}: {photo.quality_score:.1f}")
            
            # Re-evaluate recommendation based on quality scores
            photos_with_quality = [p for p in group.photos if p.quality_score > 0]
            if photos_with_quality:
                best_photo = max(photos_with_quality, key=lambda p: p.quality_score)
                group.recommended_photo_uuid = best_photo.uuid
                print(f"⭐ Best photo in group: {best_photo.filename} (score: {best_photo.quality_score:.1f})")
            
            enhanced_groups.append(group)
        
        print("✅ Enhanced grouping with image-based quality analysis complete")
        return enhanced_groups
    
    def filter_groups_by_visual_similarity(self, groups: List[PhotoGroup], 
                                         similarity_threshold: float = 70.0) -> List[PhotoGroup]:
        """Split time-based groups into visually similar subgroups.
        
        Args:
            groups: List of PhotoGroup objects from time-based grouping
            similarity_threshold: Minimum visual similarity percentage (0-100) to group photos
            
        Returns:
            List of refined PhotoGroup objects with visual similarity filtering
        """
        print(f"🔬 Filtering groups by visual similarity (threshold: {similarity_threshold}%)...")
        
        refined_groups = []
        
        for group in groups:
            if len(group.photos) <= 1:
                # Single photo groups don't need similarity filtering
                refined_groups.append(group)
                continue
            
            print(f"📸 Analyzing visual similarity in group {group.group_id} ({len(group.photos)} photos)")
            
            # Compute perceptual hashes for all photos if not already done
            photos_with_hashes = []
            for photo in group.photos:
                if not photo.perceptual_hash:
                    if photo.path and os.path.exists(photo.path):
                        photo.perceptual_hash = self.compute_perceptual_hash(photo)
                
                if photo.perceptual_hash:
                    photos_with_hashes.append(photo)
                else:
                    print(f"⚠️ Could not compute hash for {photo.filename} - including in fallback group")
            
            if len(photos_with_hashes) <= 1:
                # Not enough photos with hashes for similarity analysis
                print(f"ℹ️ Group {group.group_id}: Not enough photos with hashes for similarity analysis")
                refined_groups.append(group)
                continue
            
            # Group photos by visual similarity
            subgroups = []
            used_photos = set()
            
            for i, base_photo in enumerate(photos_with_hashes):
                if base_photo.uuid in used_photos:
                    continue
                
                # Start a new subgroup with the base photo
                similar_photos = [base_photo]
                used_photos.add(base_photo.uuid)
                
                # Find photos similar to the base photo
                for j, candidate_photo in enumerate(photos_with_hashes[i+1:], i+1):
                    if candidate_photo.uuid in used_photos:
                        continue
                    
                    # Calculate visual similarity
                    similarity = self.calculate_visual_similarity(
                        base_photo.perceptual_hash, 
                        candidate_photo.perceptual_hash
                    )
                    
                    if similarity >= similarity_threshold:
                        similar_photos.append(candidate_photo)
                        used_photos.add(candidate_photo.uuid)
                        print(f"  📊 {candidate_photo.filename} is {similarity:.1f}% similar to {base_photo.filename}")
                
                # Create subgroup if we have multiple similar photos
                if len(similar_photos) > 1:
                    subgroups.append(similar_photos)
                    print(f"  ✅ Created subgroup with {len(similar_photos)} visually similar photos")
            
            # Add photos without hashes to a fallback group if any
            photos_without_hashes = [p for p in group.photos if not p.perceptual_hash]
            if photos_without_hashes:
                subgroups.append(photos_without_hashes)
                print(f"  📁 Created fallback group with {len(photos_without_hashes)} photos without hashes")
            
            # Convert subgroups to PhotoGroup objects
            for i, subgroup_photos in enumerate(subgroups):
                if len(subgroup_photos) > 1:  # Only create groups with multiple photos
                    # Calculate subgroup statistics
                    total_size = sum(p.file_size for p in subgroup_photos)
                    potential_savings = total_size - max((p.file_size for p in subgroup_photos), default=0)
                    
                    # Determine recommended photo based on quality score
                    photos_with_quality = [p for p in subgroup_photos if p.quality_score > 0]
                    if photos_with_quality:
                        recommended_photo = max(photos_with_quality, key=lambda p: p.quality_score)
                    else:
                        # Fallback to newest photo
                        recommended_photo = max(subgroup_photos, key=lambda p: p.timestamp)
                    
                    # Create new PhotoGroup
                    subgroup = PhotoGroup(
                        group_id=f"{group.group_id}_sim_{i+1:02d}",
                        photos=subgroup_photos,
                        recommended_photo_uuid=recommended_photo.uuid,
                        time_window_start=min(p.timestamp for p in subgroup_photos),
                        time_window_end=max(p.timestamp for p in subgroup_photos),
                        camera_model=group.camera_model,  # Inherit from parent group
                        total_size_bytes=total_size,
                        potential_savings_bytes=potential_savings
                    )
                    
                    refined_groups.append(subgroup)
                    print(f"  🎯 Created refined group {subgroup.group_id} with {len(subgroup_photos)} photos")
        
        print(f"✅ Visual similarity filtering complete: {len(groups)} groups → {len(refined_groups)} refined groups")
        return refined_groups

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