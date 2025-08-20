# Photo Dedup Tool Architecture

**Architecture Change Counter: 2**
**Implementation Status: Stage 3 - Partial (Thumbnail Backend Complete, Frontend Display Issue)**

## Overview

A macOS photo deduplication tool that identifies similar photos in the Photos library and provides a user interface for selecting the best images while marking others for deletion.

## Application Type Decision

**Hybrid Web Application with Python Backend**
**Justification:** 
- Web frontend provides superior photo gallery UI with responsive design
- HTML/CSS/JavaScript better suited for side-by-side photo comparison interface
- Python backend handles macOS Photos library integration via `osxphotos`
- Local Flask/FastAPI server bridges web UI and system integration
- Better user experience for photo selection and metadata display
- Easier to implement drag-and-drop, image zoom, responsive layouts

**Architecture Pattern:** 
- Python backend service running locally (Flask/FastAPI)
- Web frontend served locally (HTML/CSS/JavaScript)
- Backend exposes REST API for photo operations
- Frontend makes AJAX calls to backend for all Photos library interactions

**Alternatives Considered:**
- Pure native desktop: More complex UI development, limited photo gallery capabilities
- Pure web app: Cannot access Photos library or create smart albums

## Technology Stack

**Backend Language:** Python 3
**Frontend:** HTML/CSS/JavaScript 
**Application Type:** Hybrid Local Web Application
**Justification:** Combines web UI advantages with native system integration

**Backend Libraries:**
- `Flask` or `FastAPI` - Local web server and REST API
- `osxphotos` - Access macOS Photos library metadata and images
- `Pillow` (PIL) - Image processing and analysis
- `imagehash` - Perceptual hashing for similarity detection  
- `opencv-python` - Computer vision features (sharpness detection, face detection)
- `exifread` - EXIF metadata parsing

**Frontend Libraries:**
- Vanilla JavaScript (no framework dependencies)
- CSS Grid/Flexbox for responsive photo layouts
- HTML5 for semantic photo gallery structure

**Optional Future Libraries:**
- `face_recognition` - Enhanced face detection and quality scoring
- `numpy` - Numerical operations for image analysis

## System Architecture

### 1. Photo Discovery & Analysis Layer
**Component:** `PhotoLibraryScanner`
- Accesses macOS Photos library via osxphotos
- Extracts metadata: timestamp, camera model, file size, resolution
- Filters photos by configurable time window (default: 10 seconds)
- Groups photos by camera model and time proximity

### 2. Similarity Detection Layer  
**Component:** `SimilarityAnalyzer`
- Computes perceptual hashes for visual similarity
- Analyzes composition similarity using computer vision
- Scores image quality (sharpness, exposure, faces)
- Groups similar photos (max 4 per group)

### 3. Photo Quality Assessment
**Component:** `QualityScorer`
- Analyzes technical quality (sharpness, exposure, noise)
- Detects faces and evaluates expressions
- Considers resolution and file format
- Generates best-photo recommendation per group

### 4. User Interface Layer
**Component:** `PhotoReviewUI`
- Displays photo groups side-by-side with metadata
- Highlights recommended "best" photo with border
- Handles user selection/deselection interactions
- Shows storage savings calculations
- Generates confirmation dialog

### 5. Photo Management Layer
**Component:** `PhotoTagger`
- Tags rejected photos with "marked-for-deletion" 
- Creates timestamped smart albums
- Generates deletion list with metadata
- Exports list for future Google Photos integration

## Data Flow Architecture

```
[Photos Library] → [Scanner] → [Similarity Analyzer] → [Quality Scorer]
                                        ↓
[Photo Groups] → [Review UI] → [User Selection] → [Photo Tagger]
                                        ↓
[Smart Album Creation] → [Deletion List Export]
```

## Data Schema

### PhotoGroup
```python
{
    "id": str,
    "photos": [Photo],
    "recommended_best": Photo.id,
    "total_size": int,
    "potential_savings": int
}
```

### Photo  
```python
{
    "id": str,
    "path": str,
    "timestamp": datetime,
    "camera_model": str,
    "file_size": int,
    "resolution": (width, height),
    "quality_score": float,
    "perceptual_hash": str,
    "metadata": dict
}
```

## Implementation Status

### ✅ COMPLETED - Stage 1: Foundation & Risk Derisking
1. ✅ **Photo Library Access** - osxphotos integration working (14,640 photos accessible)
2. ✅ **Basic Flask Server** - REST API with health, stats, groups endpoints
3. ✅ **Web Interface Foundation** - HTML/CSS/JavaScript framework
4. ✅ **Technology Stack Validation** - Python + Flask + osxphotos confirmed working

### ✅ COMPLETED - Stage 2: Core Photo Analysis  
5. ✅ **Time-based Grouping** - 10-second window algorithm implemented and tested
6. ✅ **Camera Filtering** - Groups photos by same device model
7. ✅ **Quality Assessment** - Multi-factor scoring (resolution + file size + format)
8. ✅ **Photo Metadata Extraction** - Comprehensive data structure with timestamps, camera info
9. ✅ **Group Analysis** - Found real duplicate groups in user's library (73 estimated total)

### 🔄 PARTIALLY COMPLETED - Stage 3: Visual Interface
10. ✅ **Backend Thumbnail Generation** - PIL-based thumbnail creation working
11. ✅ **Thumbnail Serving Endpoint** - `/api/thumbnail/<uuid>` returns JPEG images (19KB tested)
12. ✅ **Photo File Access Solution** - Direct path access + export fallback implemented
13. ✅ **Interactive Selection Interface** - Click-based photo selection with visual feedback
14. ✅ **Storage Calculation** - Real-time deletion impact and savings calculation
15. ✅ **Confirmation Workflow** - Multi-step safety dialogs with detailed breakdown
16. ❌ **Frontend Image Display** - Images not appearing in web interface (NEXT STEP)

### 📋 PENDING - Stage 4: Photos Library Integration
17. **Photo Tagging** - Mark photos for deletion in Photos app
18. **Smart Album Creation** - Organize marked photos with timestamped names
19. **Deletion Lists Export** - CSV/JSON export for user records
20. **macOS Permissions Handling** - Full Disk Access guidance and requirements

## Next Critical Issue: Frontend Image Display
**Problem:** Thumbnail endpoint works (HTTP 200, 19KB JPEG), but images don't display in web interface
**Root Cause:** Likely JavaScript/HTML img tag implementation issue
**Impact:** Users can't visually compare photos, defeating core purpose
**Priority:** HIGH - Must resolve before Stage 4

## Key Design Decisions

**macOS Photos Integration:** Using osxphotos library for read-only access to avoid corrupting library
**No Direct Deletion:** Tool only tags photos - user manually deletes for safety
**Perceptual Hashing:** More reliable than pixel-by-pixel comparison for similar shots
**Quality-based Recommendations:** Combine technical metrics with ML analysis
**Incremental Processing:** Handle large libraries without memory issues

## Security & Privacy Considerations

- Read-only access to Photos library
- No cloud connectivity required for core functionality  
- Local processing of all image analysis
- User controls all deletion decisions
- No sensitive data storage or transmission

## Performance Considerations

- Lazy loading of photo data to manage memory
- Caching of computed hashes and quality scores
- Configurable batch sizes for large libraries
- Background processing with progress indicators

## Risks & Mitigations

See RISKS.md for detailed risk analysis and derisking strategies.