# RemoveBadPhotos - Technical Architecture

## Overview

A macOS photo quality detection tool that identifies blurry, overexposed, and underexposed photos in the Photos library using computer vision techniques and provides a web-based interface for user review and marking.

## Architecture Pattern

**Hybrid Web Application with Python Backend**
- Python Flask backend running locally
- Modern web frontend served locally  
- REST API communication between frontend and backend
- Integration with macOS Photos app via osxphotos

## Technology Stack

### Backend
- **Language:** Python 3.8+
- **Web Framework:** Flask (lightweight, fast startup)
- **Photos Integration:** osxphotos library
- **Computer Vision:** OpenCV (cv2) for blur/exposure analysis  
- **Image Processing:** Pillow (PIL) for image loading and basic operations
- **Data Storage:** JSON files for settings and session data

### Frontend  
- **Core:** HTML5, CSS3, JavaScript (vanilla, no frameworks)
- **Design:** Modern filter-based interface inspired by TidyLib
- **Layout:** CSS Grid and Flexbox for responsive design
- **Interactions:** Progressive disclosure, keyboard shortcuts

### System Integration
- **Photos Library Access:** osxphotos for reading metadata and images
- **Photo Tagging:** osxphotos for safe photo marking
- **Album Creation:** Smart album generation with timestamps
- **Export:** CSV generation for external tools

## Core Components

### 1. BlurDetector (`blur_detector.py`)
Primary quality analysis module using computer vision techniques.

**Algorithms:**
- **Blur Detection:** Laplacian variance (fast, reliable)
- **Exposure Detection:** Histogram analysis for over/under exposure  
- **Noise Detection:** Texture analysis for low-light quality issues

**Interface:**
```python
class BlurDetector:
    def __init__(self, blur_threshold=100):
        self.blur_threshold = blur_threshold
    
    def analyze_photo(self, image_path: str) -> QualityResult:
        # Returns structured quality assessment
        
    def analyze_batch(self, photo_paths: List[str]) -> List[QualityResult]:
        # Efficient batch processing
```

### 2. Flask Backend (`app.py`)
Lightweight web server providing REST API and serving the interface.

**Key Endpoints:**
- `GET /` - Serve main blur detection interface
- `GET /api/library-stats` - Photo library overview
- `POST /api/analyze-blur` - Analyze photos for quality issues
- `GET/POST /api/blur-settings` - Threshold configuration
- `POST /api/mark-photos` - Tag photos for deletion
- `POST /api/create-album` - Generate smart album

### 3. Photo Library Integration (`photo_scanner.py`)
Handles safe interaction with macOS Photos library.

**Responsibilities:**
- Photos library access and permission management
- Metadata extraction and filtering
- Image file access for analysis
- Photo tagging and album creation

### 4. Modern Web Interface (`blur_detection_interface.html`)
Clean, professional interface adapted from TidyLib design.

**Key Features:**
- Filter-based threshold controls (Very Blurry/Blurry/Slightly Blurry/Sharp)
- Real-time photo count updates
- Progress indicators during analysis
- Photo grid with quality indicators
- Keyboard shortcuts ('d' for mark/unmark)

## Data Flow

### 1. Library Scanning Flow
```
User opens interface → 
Library stats loaded (fast metadata) → 
Filter controls populated with counts →
User adjusts thresholds →
Real-time count updates
```

### 2. Quality Analysis Flow  
```
User clicks "Analyze Photo Quality" →
Backend processes photos in batches →
Progress updates sent to frontend →
Results displayed in photo grid →
User reviews and marks photos
```

### 3. Photo Marking Flow
```
User selects photos to remove →
Confirmation dialog shown →
Photos tagged in library →
Smart album created →
CSV export generated →
Success confirmation
```

## Configuration Management

### Settings Storage (`settings.json`)
```json
{
  "blur_threshold": 100,
  "exposure_sensitivity": 0.7,
  "noise_threshold": 0.8,
  "batch_size": 50,
  "ui_preferences": {
    "default_view": "grid",
    "keyboard_shortcuts": true
  }
}
```

### Session Management
- Temporary analysis results stored in memory
- Photo selections preserved during session
- Undo stack for recovery operations

## Security & Safety

### Photo Library Safety
- Read-only access by default
- Only tag photos, never delete directly
- Multiple confirmation steps for destructive actions
- Smart album creation for easy recovery

### Local Operation
- All processing happens locally (no cloud/external services)
- No photo data leaves the user's machine
- Photos library permissions handled by osxphotos

## Performance Considerations

### Analysis Optimization
- Efficient algorithms (Laplacian variance is fast)
- Batch processing to reduce overhead
- Progress tracking for user feedback
- Memory management for large libraries

### UI Responsiveness  
- Lazy loading for photo grids
- Progressive image loading
- Background processing with progress indicators
- Keyboard shortcuts for power users

## Error Handling

### Graceful Degradation
- Continue analysis if individual photos fail
- Clear error reporting without technical jargon
- Automatic retry for transient failures
- Safe fallbacks for unsupported image formats

### User-Friendly Messages
- "Some photos couldn't be analyzed" vs "cv2.imread() returned None"
- Clear guidance on next steps
- Links to help documentation when appropriate

## Deployment Architecture

### Local Development
- Flask development server on localhost:5003
- Debug mode enabled for development
- Hot reload for frontend changes

### User Distribution (Future)
- Packaged as native macOS app using PyInstaller or similar
- Embedded web server for interface
- Native menu bar integration
- Auto-update capability

## Extension Points

### Future Quality Detectors
- Face detection (avoid deleting photos with people)
- Composition analysis (rule of thirds, etc.)
- Duplicate detection integration
- Custom ML models

### Integration Opportunities
- Google Photos API support
- Adobe Lightroom integration
- External photo management tools
- Command-line interface for automation