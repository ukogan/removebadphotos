#!/usr/bin/env python3
"""
Library Analyzer Module - Fast metadata-only analysis for heatmap generation
Handles clustering and priority scoring without downloading images
"""

import osxphotos
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import statistics

@dataclass
class LibraryStats:
    """Overall library statistics for dashboard display."""
    total_photos: int
    date_range_start: datetime
    date_range_end: datetime
    total_size_bytes: int
    estimated_duplicates: int
    potential_savings_bytes: int
    camera_models: List[str]
    has_location_data: bool

@dataclass
class PhotoCluster:
    """Represents a cluster of photos that are likely duplicates."""
    cluster_id: str
    photo_count: int
    time_span_start: datetime
    time_span_end: datetime
    total_size_bytes: int
    potential_savings_bytes: int
    duplicate_probability_score: int  # 0-100
    priority_level: str  # "high", "medium", "low"
    camera_model: Optional[str]
    location_summary: Optional[str]
    photo_uuids: List[str]

@dataclass 
class PhotoMetadata:
    """Lightweight metadata for clustering analysis."""
    uuid: str
    filename: str
    timestamp: datetime
    file_size: int
    camera_model: Optional[str]
    width: int
    height: int
    has_location: bool
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    # Organization metadata
    albums: List[str] = None
    folder_names: List[str] = None
    keywords: List[str] = None
    organization_score: float = 0.0

class LibraryAnalyzer:
    """Fast metadata-only analysis for heatmap generation."""
    
    def __init__(self):
        self.photosdb = None
        
    def get_photosdb(self):
        """Get or create PhotosDB connection."""
        if self.photosdb is None:
            self.photosdb = osxphotos.PhotosDB()
        return self.photosdb
    
    def quick_scan_library(self, progress_callback=None) -> Tuple[LibraryStats, List[PhotoMetadata]]:
        """Fast metadata-only scan of entire library."""
        print("🚀 Starting fast library scan (metadata only)...")
        
        db = self.get_photosdb()
        photos = db.photos(intrash=False, movies=False)
        
        photo_metadata_list = []
        total_size = 0
        camera_models = set()
        timestamps = []
        has_location_count = 0
        for i, photo in enumerate(photos):
            # Progress callback for UI updates
            if progress_callback and i % 500 == 0:
                progress_callback(i, len(photos))
            
            # Extract metadata
            try:
                # Get organization metadata
                albums = list(photo.albums) if photo.albums else []
                folder_names = []
                keywords = list(photo.keywords) if photo.keywords else []
                
                # Extract folder information from path
                if photo.path:
                    path_parts = photo.path.split('/')
                    # Look for meaningful folder names (skip system folders)
                    meaningful_folders = []
                    for part in path_parts:
                        if part and not part.startswith('.') and part not in ['Users', 'Pictures', 'Photos']:
                            meaningful_folders.append(part)
                    folder_names = meaningful_folders[-3:] if len(meaningful_folders) > 3 else meaningful_folders
                
                # Calculate organization score
                org_score = self.calculate_organization_score(albums, folder_names, keywords, photo.path)
                
                metadata = PhotoMetadata(
                    uuid=photo.uuid,
                    filename=filename or f"{photo.uuid}.unknown",
                    timestamp=photo.date or datetime.now(),
                    file_size=photo.original_filesize or 0,
                    camera_model=getattr(photo.exif_info, 'camera_model', None) if photo.exif_info else None,
                    width=photo.width or 0,
                    height=photo.height or 0,
                    has_location=bool(photo.location),
                    latitude=photo.location[0] if photo.location else None,
                    longitude=photo.location[1] if photo.location else None,
                    albums=albums,
                    folder_names=folder_names,
                    keywords=keywords,
                    organization_score=org_score
                )
                
                photo_metadata_list.append(metadata)
                total_size += metadata.file_size
                timestamps.append(metadata.timestamp)
                
                if metadata.camera_model:
                    camera_models.add(metadata.camera_model)
                if metadata.has_location:
                    has_location_count += 1
                    
            except Exception as e:
                print(f"⚠️ Error processing photo {photo.uuid}: {e}")
                continue
        
        print(f"✅ Scanned {len(photo_metadata_list)} photos")
        
        # Calculate library statistics
        stats = LibraryStats(
            total_photos=len(photo_metadata_list),
            date_range_start=min(timestamps) if timestamps else datetime.now(),
            date_range_end=max(timestamps) if timestamps else datetime.now(),
            total_size_bytes=total_size,
            estimated_duplicates=0,  # Will be calculated by clustering
            potential_savings_bytes=0,  # Will be calculated by clustering
            camera_models=list(camera_models),
            has_location_data=has_location_count > 0
        )
        
        print(f"📊 Library stats: {stats.total_photos} photos, {total_size / (1024*1024*1024):.1f} GB")
        return stats, photo_metadata_list
    
    def identify_clusters(self, photos: List[PhotoMetadata], time_window_seconds: int = 10) -> List[PhotoCluster]:
        """Group photos into analysis clusters based on metadata."""
        print(f"🔍 Identifying photo clusters (time window: {time_window_seconds}s)...")
        
        # Sort photos by timestamp
        photos.sort(key=lambda p: p.timestamp)
        
        clusters = []
        used_photos = set()
        cluster_counter = 1
        
        for i, base_photo in enumerate(photos):
            if base_photo.uuid in used_photos:
                continue
            
            # Find photos within time window and same camera
            cluster_photos = [base_photo]
            time_window_end = base_photo.timestamp + timedelta(seconds=time_window_seconds)
            
            for j, candidate_photo in enumerate(photos[i+1:], i+1):
                if candidate_photo.uuid in used_photos:
                    continue
                
                # Check time window
                if candidate_photo.timestamp > time_window_end:
                    break  # Photos are sorted
                
                # Check camera model match (allow None matches)
                if (base_photo.camera_model == candidate_photo.camera_model or 
                    (base_photo.camera_model is None and candidate_photo.camera_model is None)):
                    cluster_photos.append(candidate_photo)
            
            # Only create cluster if we have multiple photos
            if len(cluster_photos) > 1:
                # Mark photos as used
                for photo in cluster_photos:
                    used_photos.add(photo.uuid)
                
                # Calculate cluster statistics
                total_size = sum(p.file_size for p in cluster_photos)
                potential_savings = total_size - max((p.file_size for p in cluster_photos), default=0)
                
                # Calculate duplicate probability score
                score = self.calculate_duplicate_probability_score(cluster_photos)
                
                # Determine priority level (10 levels: P1-P10)
                if score >= 90:
                    priority = "P1"  # Highest priority
                elif score >= 80:
                    priority = "P2"
                elif score >= 70:
                    priority = "P3"
                elif score >= 60:
                    priority = "P4"
                elif score >= 50:
                    priority = "P5"
                elif score >= 40:
                    priority = "P6"
                elif score >= 30:
                    priority = "P7"
                elif score >= 20:
                    priority = "P8"
                elif score >= 10:
                    priority = "P9"
                else:
                    priority = "P10"  # Lowest priority
                
                # Create cluster
                cluster = PhotoCluster(
                    cluster_id=f"cluster_{cluster_counter:04d}",
                    photo_count=len(cluster_photos),
                    time_span_start=cluster_photos[0].timestamp,
                    time_span_end=cluster_photos[-1].timestamp,
                    total_size_bytes=total_size,
                    potential_savings_bytes=potential_savings,
                    duplicate_probability_score=score,
                    priority_level=priority,
                    camera_model=base_photo.camera_model,
                    location_summary=self.get_location_summary(cluster_photos),
                    photo_uuids=[p.uuid for p in cluster_photos]
                )
                
                clusters.append(cluster)
                cluster_counter += 1
        
        print(f"✅ Created {len(clusters)} photo clusters")
        return clusters
    
    def calculate_duplicate_probability_score(self, photos: List[PhotoMetadata]) -> int:
        """Calculate duplicate probability score (0-100) for a cluster."""
        score = 0
        
        if len(photos) < 2:
            return 0
        
        # Time clustering analysis (40% weight)
        time_spans = []
        for i in range(len(photos) - 1):
            span = (photos[i+1].timestamp - photos[i].timestamp).total_seconds()
            time_spans.append(span)
        
        avg_time_span = statistics.mean(time_spans) if time_spans else 0
        max_time_span = max(time_spans) if time_spans else 0
        
        if avg_time_span <= 5:  # Very tight clustering
            score += 40
        elif avg_time_span <= 10:  # Tight clustering  
            score += 30
        elif max_time_span <= 60:  # Burst photography
            score += 20
        
        # File size impact (30% weight)
        avg_file_size = statistics.mean(p.file_size for p in photos) / (1024 * 1024)  # MB
        total_cluster_size = sum(p.file_size for p in photos) / (1024 * 1024)  # MB
        
        if avg_file_size > 10:  # Large files
            score += 30
        elif avg_file_size > 5:  # Medium files
            score += 20
        elif avg_file_size > 2:  # Small-medium files
            score += 10
        
        if total_cluster_size > 100:  # High impact cluster
            score += 15
        elif total_cluster_size > 50:  # Medium impact
            score += 10
        
        # Camera consistency (20% weight)
        camera_models = set(p.camera_model for p in photos if p.camera_model)
        if len(camera_models) <= 1:  # Same camera or unknown
            score += 20
        
        # Location consistency (10% weight)
        photos_with_location = [p for p in photos if p.has_location]
        if len(photos_with_location) >= 2:
            # Check if photos are in similar location (within ~100m)
            locations = [(p.latitude, p.longitude) for p in photos_with_location]
            if self.are_locations_similar(locations):
                score += 10
        
        return min(score, 100)
    
    def get_location_summary(self, photos: List[PhotoMetadata]) -> Optional[str]:
        """Generate human-readable location summary for cluster."""
        photos_with_location = [p for p in photos if p.has_location]
        if not photos_with_location:
            return None
        
        if len(photos_with_location) == 1:
            return "Single location"
        
        # Simple clustering - check if all photos are within reasonable distance
        locations = [(p.latitude, p.longitude) for p in photos_with_location]
        if self.are_locations_similar(locations):
            return f"Same location ({len(photos_with_location)} photos)"
        else:
            return f"Multiple locations ({len(photos_with_location)} photos)"
    
    def are_locations_similar(self, locations: List[Tuple[float, float]], 
                             threshold_degrees: float = 0.001) -> bool:
        """Check if GPS locations are within threshold (roughly 100m)."""
        if len(locations) < 2:
            return True
        
        # Filter out None values
        valid_locations = [(lat, lng) for lat, lng in locations if lat is not None and lng is not None]
        if len(valid_locations) < 2:
            return True
        
        lat_values = [loc[0] for loc in valid_locations]
        lng_values = [loc[1] for loc in valid_locations]
        
        lat_range = max(lat_values) - min(lat_values)
        lng_range = max(lng_values) - min(lng_values)
        
        return lat_range <= threshold_degrees and lng_range <= threshold_degrees
    
    def generate_priority_summary(self, clusters: List[PhotoCluster]) -> Dict[str, Dict]:
        """Generate summary statistics by priority level."""
        summary = {}
        
        # Initialize all 10 priority levels
        for i in range(1, 11):
            priority_key = f"P{i}"
            summary[priority_key] = {"count": 0, "photos": 0, "savings_mb": 0}
        
        # Count clusters by priority
        for cluster in clusters:
            priority = cluster.priority_level
            if priority in summary:
                summary[priority]["count"] += 1
                summary[priority]["photos"] += cluster.photo_count
                summary[priority]["savings_mb"] += cluster.potential_savings_bytes / (1024 * 1024)
        
        return summary
    
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

def main():
    """Test the library analyzer functionality."""
    analyzer = LibraryAnalyzer()
    
    print("🧪 Testing LibraryAnalyzer with fast scan...")
    stats, photos = analyzer.quick_scan_library()
    
    print(f"📊 Library: {stats.total_photos} photos, {stats.total_size_bytes / (1024*1024*1024):.1f} GB")
    print(f"📅 Date range: {stats.date_range_start.date()} to {stats.date_range_end.date()}")
    print(f"📷 Cameras: {', '.join(stats.camera_models[:5])}...")
    
    # Test clustering
    clusters = analyzer.identify_clusters(photos[:1000])  # Test with first 1000 photos
    
    if clusters:
        priority_summary = analyzer.generate_priority_summary(clusters)
        print(f"\n🎯 Priority Summary:")
        for priority, data in priority_summary.items():
            print(f"  {priority.upper()}: {data['count']} clusters, {data['photos']} photos, {data['savings_mb']:.1f} MB potential savings")

if __name__ == "__main__":
    main()