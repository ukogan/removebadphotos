# Stage 5: Heatmap-Based Photo Analysis Plan

**Date:** August 21, 2025  
**Status:** 📋 DESIGN PHASE - For User Review

## Problem Statement

Current approach analyzes all photos at once, leading to:
- Poor performance with large libraries (14k+ photos)
- User fatigue from reviewing hundreds of groups
- Wasted effort on low-value duplicates (small file sizes)
- No way to prioritize high-impact areas

## Proposed Solution: Heatmap Dashboard

### Core Concept
**Interactive heatmap showing "duplicate density" across different dimensions of the photo library, allowing users to drill down into high-value areas for targeted analysis.**

---

## Stage 5A: Library Statistics Dashboard

### Initial Fast Scan (Metadata Only)
```python
# Quick scan - NO image downloads or analysis
- Total photos count
- Date range (oldest → newest)
- File size distribution
- Camera models used
- Location data availability
- Time clustering analysis (burst detection)
```

### Heatmap Visualizations

#### 1. **Time-Based Heatmap** 📅
- **X-axis:** Months/Years
- **Y-axis:** Days of month / Hours of day
- **Color intensity:** Photo density + potential duplicate score
- **Quick rules:**
  - High density periods (vacations, events)
  - Burst photography detection (>5 photos within 60 seconds)
  - Multiple photos same minute = high duplicate probability

#### 2. **Size-Impact Heatmap** 💾
- **X-axis:** File size ranges (0-1MB, 1-5MB, 5-20MB, 20MB+)
- **Y-axis:** Photo count in range
- **Color intensity:** Total space savings potential
- **Priority:** Larger files = higher impact

#### 3. **Camera-Location Heatmap** 📍
- **X-axis:** Camera models
- **Y-axis:** Location clusters (if GPS available)
- **Color intensity:** Duplicate probability score
- **Logic:** Same camera + same location + similar time = likely duplicates

---

## Stage 5B: Smart Targeting Rules

### High-Value Target Detection
```python
def calculate_duplicate_probability_score(metadata):
    score = 0
    
    # Time clustering (40% weight)
    if photos_within_10_seconds >= 2: score += 40
    if photos_within_60_seconds >= 5: score += 20  # Burst mode
    
    # File size impact (30% weight) 
    if avg_file_size > 5MB: score += 30
    if total_cluster_size > 50MB: score += 15
    
    # Camera consistency (20% weight)
    if same_camera_model: score += 20
    
    # Location consistency (10% weight)
    if same_gps_location: score += 10
    
    return min(score, 100)
```

### Recommended Analysis Order
1. **🔥 High Priority** (Score 80-100): Large files, burst photography, same location
2. **⚡ Medium Priority** (Score 50-79): Moderate clustering, mixed file sizes
3. **📋 Low Priority** (Score 0-49): Scattered photos, small files

---

## Stage 5C: User Interface Design

### Dashboard Layout
```
┌─────────────────────────────────────────────────────────────┐
│  📊 PHOTO LIBRARY ANALYSIS DASHBOARD                        │
├─────────────────────────────────────────────────────────────┤
│  📈 Quick Stats                                             │
│  • 14,644 photos • 2019-2025 • 89.2 GB total              │
│  • Estimated 2,847 duplicates • ~12.5 GB potential savings │
└─────────────────────────────────────────────────────────────┘

┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ 🔥 HIGH PRIORITY│ │ ⚡ MEDIUM PRIOR │ │ 📋 LOW PRIORITY │
│                 │ │                 │ │                 │
│ 47 clusters     │ │ 156 clusters    │ │ 89 clusters     │
│ ~8.2 GB savings │ │ ~3.1 GB savings │ │ ~1.2 GB savings │
│                 │ │                 │ │                 │
│ [ANALYZE FIRST] │ │ [ANALYZE NEXT]  │ │ [ANALYZE LAST]  │
└─────────────────┘ └─────────────────┘ └─────────────────┘

📅 TIME HEATMAP (click to zoom)
Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec
███ ░░░ ███ ░░░ ██░ ███ ███ ███ ██░ ░░░ ██░ ███
2019: Light activity          2023: Heavy clustering
2020: Vacation burst         2024: Recent activity  
2021: Low activity           2025: Current year
2022: Event photography

💾 SIZE IMPACT ANALYSIS  
0-1MB:   ████░░░░ (3,247 photos, 1.2GB potential savings)
1-5MB:   ███████░ (8,932 photos, 8.7GB potential savings) ⭐
5-20MB:  ██████░░ (2,341 photos, 2.1GB potential savings) ⭐  
20MB+:   ███░░░░░ (124 photos, 0.5GB potential savings)   ⭐
```

### User Workflow
1. **Dashboard Overview** - See entire library stats in <5 seconds
2. **Target Selection** - Click high-priority areas for focused analysis  
3. **Batch Analysis** - Process 10 groups max per session
4. **Progress Tracking** - Visual progress through priority areas
5. **Return Navigation** - Easy return to dashboard for next session

---

## Stage 5D: Technical Implementation

### Fast Metadata Scan
```python
class LibraryAnalyzer:
    def quick_scan_library(self) -> LibraryStats:
        """Fast metadata-only scan - no image downloads"""
        # Process in batches for progress indication
        # Extract: date, size, camera, GPS, filename patterns
        # Return: statistics for heatmap generation
        
    def identify_clusters(self, photos) -> List[PhotoCluster]:
        """Group photos into analysis clusters based on metadata"""
        # Time-based clustering (10-second windows)
        # Location-based clustering (GPS proximity)
        # Camera-based clustering
        # Return: prioritized clusters with duplicate probability scores
```

### Targeted Analysis API
```python
@app.route('/api/analyze-cluster/<cluster_id>')
def analyze_specific_cluster(cluster_id):
    """Deep analysis of specific photo cluster (max 10 groups)"""
    # Download photos for this cluster only
    # Run visual similarity analysis
    # Return: detailed groups ready for user review
```

### Progressive Enhancement
- **Phase 1:** Metadata-only heatmap (fast, always works)
- **Phase 2:** Add thumbnail previews for high-priority clusters
- **Phase 3:** On-demand visual similarity analysis per cluster

---

## Benefits of This Approach

### Performance
- ✅ Dashboard loads in seconds (metadata only)
- ✅ User only waits for analysis when drilling down
- ✅ 10 groups max = manageable cognitive load
- ✅ Progress tracking prevents overwhelm

### User Experience  
- ✅ Clear prioritization - work on high-impact areas first
- ✅ Visual progress through library analysis
- ✅ Can stop/resume anytime
- ✅ Immediate value from first session

### Technical Benefits
- ✅ Scales to any library size
- ✅ Efficient resource usage
- ✅ Can optimize based on user patterns
- ✅ Modular - can enhance incrementally

---

## Implementation Priority

### MVP (Stage 5A): Basic Heatmap
1. Fast metadata scan of entire library
2. Time-based clustering analysis  
3. Simple priority scoring
4. Basic dashboard with 3 priority buckets
5. Drill-down to existing analysis (limited to 10 groups)

### Enhancement (Stage 5B): Rich Heatmaps
1. Interactive time heatmap visualization
2. Size-impact analysis charts
3. Camera/location correlation analysis
4. Improved duplicate probability scoring

### Advanced (Stage 5C): Smart Features
1. Learning from user decisions
2. GPS-based location clustering
3. Face detection clustering (if privacy acceptable)
4. Automated scheduling suggestions

---

## Questions for Review

1. **Priority Order**: Do the heatmap dimensions make sense? Any others to add?
2. **10 Groups Limit**: Is this the right balance for user session length?
3. **Scoring Algorithm**: Are the weights reasonable for duplicate probability?
4. **Dashboard Design**: Is the visual layout intuitive?
5. **Technical Approach**: Any concerns with the metadata-first strategy?

**Ready for implementation approval and any adjustments before coding begins.**