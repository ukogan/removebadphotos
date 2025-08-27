#!/usr/bin/env python3
"""
LazyPhotoLoader - Bridge between metadata-only clusters and on-demand photo analysis
Implements the lazy loading foundation for Stage 5A performance improvements
"""

import osxphotos
from typing import List, Dict, Optional, Tuple, Callable
from dataclasses import dataclass
from datetime import datetime
import time
from collections import defaultdict

from library_analyzer import LibraryAnalyzer, PhotoCluster, PhotoMetadata
from photo_scanner import PhotoScanner, PhotoData


@dataclass
class ClusterLoadResult:
    """Result of loading a specific cluster for analysis."""
    cluster_id: str
    photos: List[PhotoData]
    load_time_seconds: float
    photo_count: int
    total_size_bytes: int


class LazyPhotoLoader:
    """Bridges metadata-only clusters with on-demand photo analysis."""
    
    def __init__(self, library_analyzer: LibraryAnalyzer, photo_scanner: PhotoScanner):
        self.analyzer = library_analyzer
        self.scanner = photo_scanner
        self._cluster_cache = {}
        self._metadata_cache = {}
        self._cache_timestamp = None
        
    def get_library_metadata_fast(self, progress_callback: Optional[Callable] = None) -> Tuple[Dict, List[PhotoCluster]]:
        """Fast metadata-only scan returning library stats and clusters.
        
        Target: < 5 seconds for 14k+ photos
        Returns: (library_stats_dict, photo_clusters_list)
        """
        print("🚀 LazyPhotoLoader: Starting fast metadata scan...")
        start_time = time.time()
        
        # Use LibraryAnalyzer for fast metadata scan
        stats, photo_metadata = self.analyzer.quick_scan_library(progress_callback)
        
        # Generate clusters from metadata only
        clusters = self.analyzer.identify_clusters(photo_metadata)
        
        # Cache results for filtering operations
        self._metadata_cache = {p.uuid: p for p in photo_metadata}
        self._cluster_cache = {c.cluster_id: c for c in clusters}
        self._cache_timestamp = datetime.now()
        
        # Generate priority summary
        priority_summary = self.analyzer.generate_priority_summary(clusters)
        
        scan_time = time.time() - start_time
        print(f"✅ LazyPhotoLoader: Metadata scan completed in {scan_time:.1f}s")
        print(f"📊 Found {len(clusters)} clusters, {len(photo_metadata)} photos")
        
        # Package library stats for API response
        library_stats = {
            'total_photos': stats.total_photos,
            'total_size_gb': stats.total_size_bytes / (1024**3),
            'date_range_start': stats.date_range_start.isoformat(),
            'date_range_end': stats.date_range_end.isoformat(),
            'camera_models': stats.camera_models[:10],  # Limit for API response
            'cluster_count': len(clusters),
            'priority_summary': priority_summary,
            'scan_time_seconds': scan_time
        }
        
        return library_stats, clusters
    
    def load_filtered_clusters(self, filters: Dict) -> List[PhotoCluster]:
        """Apply filters to cached clusters without rescanning library.
        
        Filters can include:
        - year: int (2024, 2023, etc.)
        - min_size_mb: int 
        - max_size_mb: int
        - priority_levels: List[str] (["P1", "P2"])
        - camera_models: List[str]
        """
        if not self._cluster_cache:
            raise ValueError("No cached clusters available. Run get_library_metadata_fast() first.")
        
        print(f"🔍 LazyPhotoLoader: Applying filters to {len(self._cluster_cache)} clusters...")
        start_time = time.time()
        
        filtered_clusters = list(self._cluster_cache.values())
        original_count = len(filtered_clusters)
        
        # Apply year filter
        if 'year' in filters and filters['year']:
            year = int(filters['year'])
            filtered_clusters = [
                c for c in filtered_clusters 
                if c.time_span_start.year == year or c.time_span_end.year == year
            ]
            print(f"📅 Year {year} filter: {len(filtered_clusters)} clusters remain")
        
        # Apply size filters (dual-handle slider)
        if 'min_size_mb' in filters or 'max_size_mb' in filters:
            # Handle None values properly
            min_size_mb = filters.get('min_size_mb', 0)
            max_size_mb = filters.get('max_size_mb', float('inf'))
            
            # Convert None to defaults
            if min_size_mb is None:
                min_size_mb = 0
            if max_size_mb is None:
                max_size_mb = float('inf')
                
            min_size = min_size_mb * 1024 * 1024  # Convert to bytes
            max_size = max_size_mb * 1024 * 1024
            
            filtered_clusters = [
                c for c in filtered_clusters 
                if min_size <= c.total_size_bytes <= max_size
            ]
            print(f"💾 Size filter ({filters.get('min_size_mb', 0)}-{filters.get('max_size_mb', '∞')} MB): {len(filtered_clusters)} clusters remain")
        
        # Apply priority filter
        if 'priority_levels' in filters and filters['priority_levels']:
            priority_set = set(filters['priority_levels'])
            filtered_clusters = [
                c for c in filtered_clusters 
                if c.priority_level in priority_set
            ]
            print(f"🎯 Priority filter {priority_set}: {len(filtered_clusters)} clusters remain")
        
        # Apply camera filter
        if 'camera_models' in filters and filters['camera_models']:
            camera_set = set(filters['camera_models'])
            filtered_clusters = [
                c for c in filtered_clusters 
                if c.camera_model in camera_set
            ]
            print(f"📷 Camera filter {camera_set}: {len(filtered_clusters)} clusters remain")
        
        # Apply file type filter
        if 'file_types' in filters and filters['file_types']:
            file_type_set = set(ext.upper() for ext in filters['file_types'])
            print(f"📁 Applying file type filter: {file_type_set}")
            
            # Filter clusters by checking if any photos in cluster match file types
            filtered_clusters_by_type = []
            for cluster in filtered_clusters:
                cluster_has_matching_type = False
                
                # Check each photo in cluster for matching file type
                for uuid in cluster.photo_uuids:
                    if uuid in self._metadata_cache:
                        photo_metadata = self._metadata_cache[uuid]
                        filename = photo_metadata.filename
                        if '.' in filename:
                            ext = filename.split('.')[-1].upper()
                            # Normalize JPEG vs JPG
                            if ext == 'JPEG':
                                ext = 'JPG'
                            if ext in file_type_set:
                                cluster_has_matching_type = True
                                break
                
                if cluster_has_matching_type:
                    filtered_clusters_by_type.append(cluster)
            
            filtered_clusters = filtered_clusters_by_type
            print(f"📁 File type filter {file_type_set}: {len(filtered_clusters)} clusters remain")
        
        filter_time = time.time() - start_time
        print(f"✅ LazyPhotoLoader: Filtering completed in {filter_time:.2f}s")
        print(f"📊 Filtered: {original_count} → {len(filtered_clusters)} clusters")
        
        return filtered_clusters
    
    def load_cluster_photos(self, cluster_id: str) -> ClusterLoadResult:
        """Load full PhotoData objects for a specific cluster on-demand.
        
        Target: < 5 seconds per cluster
        Returns: ClusterLoadResult with loaded photos ready for analysis
        """
        print(f"📥 LazyPhotoLoader: Loading photos for cluster {cluster_id}...")
        start_time = time.time()
        
        if cluster_id not in self._cluster_cache:
            raise ValueError(f"Cluster {cluster_id} not found in cache")
        
        cluster = self._cluster_cache[cluster_id]
        
        # Convert PhotoMetadata to PhotoData using PhotoScanner's load method
        photo_uuids = cluster.photo_uuids
        loaded_photos = []
        
        # Get PhotosDB connection
        db = self.analyzer.get_photosdb()
        
        for uuid in photo_uuids:
            try:
                # Get photo from osxphotos
                photo = db.get_photo(uuid)
                if photo:
                    # Convert to PhotoData using scanner's method
                    photo_data = self.scanner.extract_photo_metadata(photo)
                    if photo_data:
                        loaded_photos.append(photo_data)
                        
            except Exception as e:
                print(f"⚠️ Error loading photo {uuid}: {e}")
                continue
        
        load_time = time.time() - start_time
        total_size = sum(p.file_size for p in loaded_photos)
        
        print(f"✅ LazyPhotoLoader: Loaded {len(loaded_photos)} photos in {load_time:.1f}s")
        print(f"💾 Total size: {total_size / (1024*1024):.1f} MB")
        
        return ClusterLoadResult(
            cluster_id=cluster_id,
            photos=loaded_photos,
            load_time_seconds=load_time,
            photo_count=len(loaded_photos),
            total_size_bytes=total_size
        )
    
    def analyze_cluster_photos(self, cluster_id: str, progress_callback: Optional[Callable] = None) -> List:
        """Perform deep analysis on specific cluster only.
        
        Target: < 10 seconds total (load + analyze)
        Returns: List of PhotoGroup objects ready for user review
        """
        print(f"🔬 LazyPhotoLoader: Analyzing cluster {cluster_id}...")
        start_time = time.time()
        
        # Load photos for this cluster
        load_result = self.load_cluster_photos(cluster_id)
        
        if not load_result.photos:
            print(f"⚠️ No photos loaded for cluster {cluster_id}")
            return []
        
        # Perform analysis using PhotoScanner  
        print(f"🎯 Analyzing {len(load_result.photos)} photos...")
        
        # First group by time and camera, then enhance with similarity
        initial_groups = self.scanner.group_photos_by_time_and_camera(load_result.photos, time_window_seconds=10)
        enhanced_groups = self.scanner.enhanced_grouping_with_similarity(initial_groups, progress_callback=progress_callback)
        final_groups = self.scanner.filter_groups_by_visual_similarity(enhanced_groups, similarity_threshold=70.0)
        
        groups = final_groups
        
        analysis_time = time.time() - start_time
        print(f"✅ LazyPhotoLoader: Cluster analysis completed in {analysis_time:.1f}s")
        print(f"📊 Generated {len(groups)} photo groups")
        
        return groups
    
    def get_cluster_by_id(self, cluster_id: str) -> Optional[PhotoCluster]:
        """Retrieve specific cluster metadata."""
        return self._cluster_cache.get(cluster_id)
    
    def get_priority_clusters(self, priority_level: str) -> List[PhotoCluster]:
        """Get all clusters for a specific priority level (P1, P2, etc.)."""
        return [
            cluster for cluster in self._cluster_cache.values()
            if cluster.priority_level == priority_level
        ]
    
    def clear_cache(self):
        """Clear all cached data to free memory."""
        print("🗑️ LazyPhotoLoader: Clearing cache...")
        self._cluster_cache.clear()
        self._metadata_cache.clear()
        self._cache_timestamp = None
        print("✅ Cache cleared")
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics for debugging."""
        return {
            'clusters_cached': len(self._cluster_cache),
            'metadata_cached': len(self._metadata_cache),
            'cache_timestamp': self._cache_timestamp.isoformat() if self._cache_timestamp else None
        }


def main():
    """Test the LazyPhotoLoader functionality."""
    print("🧪 Testing LazyPhotoLoader...")
    
    # Initialize components
    analyzer = LibraryAnalyzer()
    scanner = PhotoScanner()
    loader = LazyPhotoLoader(analyzer, scanner)
    
    # Test fast metadata scan
    print("\n📊 Testing fast metadata scan...")
    stats, clusters = loader.get_library_metadata_fast()
    
    print(f"Library stats: {stats['total_photos']} photos")
    print(f"Found {len(clusters)} clusters")
    
    # Test filtering
    if clusters:
        print(f"\n🔍 Testing cluster filtering...")
        
        # Test year filter
        current_year_filters = {'year': 2024}
        current_year_clusters = loader.load_filtered_clusters(current_year_filters)
        print(f"2024 clusters: {len(current_year_clusters)}")
        
        # Test size filter  
        large_file_filters = {'min_size_mb': 5}
        large_clusters = loader.load_filtered_clusters(large_file_filters)
        print(f"Large file clusters (>5MB): {len(large_clusters)}")
        
        # Test priority filter
        high_priority_filters = {'priority_levels': ['P1', 'P2']}
        priority_clusters = loader.load_filtered_clusters(high_priority_filters)
        print(f"High priority clusters (P1-P2): {len(priority_clusters)}")
    
    # Test cluster loading and analysis
    if clusters:
        test_cluster = clusters[0]
        print(f"\n🔬 Testing cluster analysis: {test_cluster.cluster_id}")
        
        groups = loader.analyze_cluster_photos(test_cluster.cluster_id)
        print(f"Generated {len(groups)} photo groups")
    
    print("\n✅ LazyPhotoLoader testing completed!")


if __name__ == "__main__":
    main()