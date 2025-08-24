# Photo Dedup Tool Architecture

**Architecture Change Counter: 4**
**Implementation Status: Stage 4 - COMPLETE, Photos Library Integration Active**

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

### ✅ COMPLETED - Stage 3: Visual Interface
10. ✅ **Backend Thumbnail Generation** - PIL-based thumbnail creation with iCloud download support
11. ✅ **Thumbnail Serving Endpoint** - `/api/thumbnail/<uuid>` and `/api/full-image/<uuid>` working
12. ✅ **Photo File Access Solution** - Direct path access + export fallback + iCloud download
13. ✅ **Interactive Selection Interface** - Click-based photo selection with visual feedback
14. ✅ **Storage Calculation** - Real-time deletion impact and savings calculation
15. ✅ **Confirmation Workflow** - Multi-step safety dialogs with detailed breakdown
16. ✅ **Frontend Image Display** - Photos displaying correctly with thumbnail fallback
17. ✅ **Full-Screen Preview** - Modal preview with arrow key navigation using full-resolution images
18. ✅ **Group Action Buttons** - "Keep All" and "Delete All But Best" functionality
19. ✅ **Image Quality Analysis** - Multi-factor scoring using OpenCV (sharpness, brightness, noise, resolution)
20. ✅ **HEIC Support** - iPhone photos supported via pillow-heif
21. ✅ **Click-to-Open in Photos** - AppleScript integration to open specific photos

### ✅ COMPLETED - Stage 4: Photos Library Integration
22. ✅ **Photo Tagging** - PhotoTagger component with photoscript/AppleScript integration
23. ✅ **Smart Album Creation** - Automated smart album creation with timestamped names
24. ✅ **Deletion Lists Export** - CSV/JSON export to Desktop with full metadata
25. ✅ **Photos App Integration** - Direct keyword tagging via photoscript API
26. ✅ **Workflow Execution** - /api/complete-workflow endpoint executes real tagging
27. ✅ **Error Handling** - Graceful fallback to AppleScript if photoscript fails

## Stage 4 Complete: Full Photos Library Integration
**Current Status:** Complete end-to-end workflow from analysis to Photos app integration
**Latest Addition:** PhotoTagger component with dual-method implementation (photoscript + AppleScript fallback)
**Current Capability:** Users can analyze, select, and automatically tag photos in Photos app with smart album creation
**Integration Level:** Direct Photos app keyword tagging, smart album creation, and comprehensive export

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

## Debuggability Architecture

### HALT Protocol Integration
**H - Hypothesis First:** All debugging starts with diagnostic tests (`make diagnostics`)
**A - Artifact Creation:** Isolated test creation in `tests/debugging/`
**L - Layer Isolation:** 4-tier test pyramid (diagnostics → unit → integration → e2e)
**T - Track Progress:** 30-minute hard limit with 10-minute check-ins

### Service Health Monitoring
**Circuit Breaker Pattern:** All external service calls wrapped in failure detection
**Diagnostic Endpoints:** Each service implements health check interface
**Memory Monitoring:** Continuous tracking with 200MB alert threshold
**Error Cataloging:** All errors documented in ERROR_CATALOG.md with resolution time

### Test Architecture
```
tests/
├── diagnostics/     # < 1 second - System health verification
├── unit/           # < 5 seconds - Pure function testing  
├── integration/    # < 30 seconds - Service interaction testing
├── e2e/           # < 2 minutes - Complete workflow testing
└── debugging/     # One-off debug test isolation
```

### Development Workflow Integration
- **Pre-debugging:** `make debug-start` runs diagnostics + starts timer
- **Debug isolation:** All debugging on `debug/[issue]` branches
- **Progress tracking:** DEBUGGING.md updated every 10 minutes
- **Escalation triggers:** 30-minute limit, memory alerts, architecture counter at 5

### Error Recovery Patterns
**Service Degradation:** PhotoScanner → fallback to cached data
**Memory Issues:** Lazy loading + batch processing + garbage collection
**Library Access:** osxphotos failure → graceful UI degradation
**Thumbnail Generation:** PIL failure → placeholder image serving

## Risks & Mitigations

See RISKS.md for detailed risk analysis and derisking strategies.