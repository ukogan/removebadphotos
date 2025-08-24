# Photo Dedup Tool - Data Schema

## macOS Photos Library Attributes Reference

### Complete osxphotos.PhotoInfo Attributes
Direct access to macOS Photos database via osxphotos library. **CRITICAL: Always use these exact attribute names.**

#### Core Identity & Files
```python
# Primary Keys
uuid: str                    # Photos library UUID (primary key)
fingerprint: str             # Alternative unique identifier
cloud_guid: str              # iCloud identifier

# File Information  
filename: str                # Current filename in library
original_filename: str       # Original filename when imported
original_filesize: int       # ⚠️ IMPORTANT: Use this, NOT file_size
path: str                    # File path (may be None if cloud-only)
path_derivatives: list       # List of derivative file paths
uti: str                     # Uniform Type Identifier (e.g., 'public.heic')
hexdigest: str               # File hash
```

#### Dates & Times
```python
date: datetime               # Photo taken date (primary timestamp)
date_original: datetime      # Original date from EXIF
date_added: datetime         # When added to Photos library
date_modified: datetime      # Last modification date
date_trashed: datetime       # When moved to trash (if applicable)
tzname: str                  # Timezone name
tzoffset: int                # Timezone offset in seconds
```

#### Image Properties
```python
width: int                   # Current width in pixels
height: int                  # Current height in pixels
original_width: int          # Original image width
original_height: int         # Original image height
orientation: int             # Image orientation (1-8)
original_orientation: int    # Original orientation
```

#### Camera & Device
```python
# Access via exif_info object:
exif_info.camera_make: str   # Camera manufacturer (Canon, Apple, etc.)
exif_info.camera_model: str  # Camera model (iPhone 15 Pro, etc.)
exif_info.lens_model: str    # Lens information
exif_info.iso: int           # ISO setting
exif_info.flash_fired: bool  # Flash usage
```

#### Location
```python
latitude: float              # GPS latitude
longitude: float             # GPS longitude
location: tuple              # (lat, lon) tuple
place: PlaceInfo             # Detailed place information
```

#### Cloud & Sharing
```python
incloud: bool                # Whether stored in iCloud
iscloudasset: bool           # Whether it's a cloud asset
ismissing: bool              # Whether file is missing locally
shared: bool                 # Whether shared with others
shared_library: bool         # Whether in shared library
```

#### Photo Types & Features
```python
isphoto: bool                # Whether it's a photo (vs video)
ismovie: bool                # Whether it's a video
live_photo: bool             # Whether it's a Live Photo
portrait: bool               # Whether it's portrait mode
panorama: bool               # Whether it's a panorama
burst: bool                  # Whether part of burst sequence
hdr: bool                    # Whether HDR enabled
selfie: bool                 # Whether it's a selfie
screenshot: bool             # Whether it's a screenshot
```

#### User Metadata
```python
favorite: bool               # Whether favorited by user
flagged: bool                # Whether flagged by user
hidden: bool                 # Whether hidden by user
intrash: bool                # Whether in trash
title: str                   # User-assigned title
description: str             # User-assigned description
keywords: list               # User-assigned keywords
rating: int                  # User rating (0-5)
```

#### AI/ML Analysis
```python
labels: list                 # Machine learning labels
labels_normalized: list      # Normalized ML labels
face_info: list              # Face detection results
person_info: list            # Person identification
persons: list                # List of person names
```

## Current Implementation Data Structures

### PhotoData (Internal)
Our wrapper around osxphotos.PhotoInfo for processing.

```python
@dataclass  
class PhotoData:
    # Identity
    uuid: str                    # Photos library UUID
    filename: str                # Original filename
    path: str                    # File system path
    
    # Metadata
    timestamp: datetime          # When photo was taken (from osxphotos.date)
    camera_model: str           # From osxphotos.exif_info.camera_model
    
    # Technical Properties
    file_size: int              # From osxphotos.original_filesize ⚠️
    width: int                  # From osxphotos.original_width
    height: int                 # From osxphotos.original_height
    format: str                 # From osxphotos.uti
    
    # Analysis Results (computed)
    quality_score: float        # Our computed quality (0-100)
    perceptual_hash: str        # Our computed pHash
    
    # Processing Status
    analyzed: bool = False      # Whether we've analyzed it
```

### PhotoGroup (Current Implementation)
Collection of similar photos that should be reviewed together.

```python
@dataclass
class PhotoGroup:
    # Identity
    group_id: str               # Unique identifier for this group
    
    # Photos
    photos: List[PhotoData]     # List of similar photos (2+ photos)
    recommended_photo: PhotoData # Best photo in group (highest quality)
    
    # Grouping Criteria
    time_window_minutes: int    # Time window used for grouping
    camera_model: str           # Shared camera model
    similarity_score: float     # Group similarity (0-1)
    
    # Savings Analysis
    total_size_bytes: int       # Combined size of all photos
    potential_savings_bytes: int # Bytes saved if duplicates deleted
    potential_savings_mb: float  # Savings in MB for display
    photo_count: int            # Number of photos in group
    
    # Creation Info
    created_at: datetime        # When group was created
    priority_score: float       # Used for P1-P10 classification
```

### Cluster (Dashboard Analysis)
High-level duplicate cluster for priority analysis.

```python
class Cluster:
    # Identity
    group_id: str               # Cluster identifier
    
    # Photos & Analysis
    photos: List[PhotoData]     # Photos in cluster
    recommended_photo: PhotoData # Highest quality photo
    duplicate_probability_score: float # 0-1 confidence score
    priority_level: str         # P1-P10 priority classification
    
    # Metrics
    potential_savings_bytes: int # Storage that can be saved
    photo_count: int            # Number of photos
    
    # UI Display
    thumbnail_urls: List[str]   # Thumbnail URLs for preview
    camera_info: str            # Camera model summary
    date_range: str             # Time span of photos
```

### DeletionSession
Tracks a user's photo review session and deletion decisions.

```python  
@dataclass
class DeletionSession:
    # Identity
    session_id: str             # Unique session identifier
    created_at: datetime        # When session started
    
    # Progress
    total_groups: int           # Total groups to review
    groups_reviewed: int        # Groups user has completed
    photos_marked: List[str]    # UUIDs marked for deletion
    
    # Impact Analysis
    total_photos_reviewed: int  # Count of photos seen by user
    photos_selected_for_keeping: int  # Photos user chose to keep  
    photos_selected_for_deletion: int # Photos marked for deletion
    estimated_savings_bytes: int     # Total storage to be freed
    
    # Smart Album Info
    smart_album_name: str       # Name of created smart album
    smart_album_created: bool   # Whether album was successfully created
    
    # Export
    deletion_list_path: str     # Path to exported deletion list
    deletion_list_format: str   # Format (CSV, JSON)
```

## Current API Endpoints & Data

### New Smart Analysis APIs (2024)

#### `/api/library-stats` (Fast Basic Stats)
```json
{
    "success": true,
    "stats": {
        "total_photos": 13794,
        "total_size_gb": 89.2,
        "estimated_duplicates": "TBD",
        "potential_savings_gb": null,
        "date_range_start": "2019-01-01T00:00:00Z",
        "date_range_end": "2024-08-23T23:59:59Z",
        "potential_groups": "TBD",
        "camera_models": ["iPhone 15 Pro", "iPhone 13", ...]
    }
}
```

#### `/api/filter-preview` (Size Filter Preview)
```json
{
    "success": true,
    "filtered_count": 3247,
    "percentage": 23.5,
    "total_photos": 13794
}
```

#### `/api/smart-analysis` (Focused Analysis)
```json
{
    "success": true,
    "dashboard": {
        "library_stats": { /* stats object */ },
        "priority_summary": {
            "P1": {"count": 5, "total_savings_mb": 45.2, "photo_count": 12},
            "P2": {"count": 8, "total_savings_mb": 23.1, "photo_count": 18},
            // ... P3-P10
        },
        "cluster_count": 42
    },
    "analysis_type": "metadata",
    "photos_analyzed": 500
}
```

### Legacy API Responses

#### `/api/groups` (Photo Group Interface)
```json
{
    "success": true,
    "groups": [
        {
            "group_id": "group_001",
            "photos": [
                {
                    "uuid": "F75A166C-5A0F-4A98-9943-71DAA7080E63",
                    "filename": "IMG_1981.HEIC",
                    "timestamp": "2024-02-21T16:30:05Z",
                    "camera_model": "iPhone 15 Pro",
                    "file_size": 2723244,  
                    "width": 5712,
                    "height": 4284,
                    "quality_score": 87.5,
                    "thumbnail_url": "/api/thumbnail/F75A166C-5A0F-4A98-9943-71DAA7080E63",
                    "recommended": true
                }
            ],
            "total_size_mb": 8.4,
            "potential_savings_mb": 5.1,
            "photo_count": 3,
            "camera_model": "iPhone 15 Pro"
        }
    ],
    "has_more": true,
    "total_groups": 156
}
```

#### Selection State Management (Frontend)
```javascript
// Global selection state (inverted model)
photoSelections = {
    "group_001": ["uuid2", "uuid3"],  // Selected = DELETE
    "group_002": [],                   // None selected = KEEP ALL
}

// Visual states
// Unselected photos: 🛡️ KEEP (green)
// Selected photos: ❌ DELETE (red)
```

### UserSelectionRequest
JSON structure for user photo selections.

```python
{
    "session_id": "session_123",
    "group_id": "group_001", 
    "selected_photo_uuids": ["photo_uuid_1", "photo_uuid_3"],
    "action": "confirm_selections"  # or "skip_group"
}
```

### DeletionSummaryResponse
JSON structure for deletion confirmation.

```python
{
    "session_id": "session_123",
    "photos_to_delete": [
        {
            "uuid": "photo_uuid_2",
            "filename": "IMG_1235.HEIC",
            "file_size": 2450000,
            "timestamp": "2024-01-15T14:30:02Z"
        }
        // ... more photos
    ],
    "total_count": 45,
    "total_size_bytes": 112750000,
    "size_human_readable": "107.5 MB",
    "smart_album_name": "marked for deletion on Jan-15 at 14:45 to save 107.5 MB"
}
```

## Database Schema (SQLite)

### photos table
```sql
CREATE TABLE photos (
    uuid TEXT PRIMARY KEY,
    path TEXT NOT NULL,
    filename TEXT NOT NULL,
    timestamp DATETIME NOT NULL,
    date_created DATETIME,
    camera_model TEXT,
    camera_make TEXT,
    file_size INTEGER,
    width INTEGER,
    height INTEGER,
    format TEXT,
    perceptual_hash TEXT,
    quality_score REAL,
    sharpness_score REAL, 
    face_count INTEGER DEFAULT 0,
    has_smiling_faces BOOLEAN DEFAULT FALSE,
    analyzed BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### photo_groups table  
```sql
CREATE TABLE photo_groups (
    group_id TEXT PRIMARY KEY,
    time_window_start DATETIME,
    time_window_end DATETIME,
    camera_model TEXT,
    similarity_threshold REAL,
    total_size_bytes INTEGER,
    potential_savings_bytes INTEGER,
    recommended_photo_uuid TEXT,
    reviewed BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    analysis_version TEXT,
    FOREIGN KEY (recommended_photo_uuid) REFERENCES photos (uuid)
);
```

### group_photos table (many-to-many)
```sql  
CREATE TABLE group_photos (
    group_id TEXT,
    photo_uuid TEXT,
    selected_for_keeping BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (group_id, photo_uuid),
    FOREIGN KEY (group_id) REFERENCES photo_groups (group_id),
    FOREIGN KEY (photo_uuid) REFERENCES photos (uuid)
);
```

### deletion_sessions table
```sql
CREATE TABLE deletion_sessions (
    session_id TEXT PRIMARY KEY,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    total_groups INTEGER,
    groups_reviewed INTEGER DEFAULT 0,
    total_photos_reviewed INTEGER DEFAULT 0,
    photos_selected_for_keeping INTEGER DEFAULT 0,
    photos_selected_for_deletion INTEGER DEFAULT 0,
    estimated_savings_bytes INTEGER DEFAULT 0,
    smart_album_name TEXT,
    smart_album_created BOOLEAN DEFAULT FALSE,
    deletion_list_path TEXT,
    deletion_list_format TEXT DEFAULT 'json'
);
```

## File System Data

### Thumbnail Cache Structure
```
/tmp/photo_dedup_cache/
├── thumbnails/
│   ├── {photo_uuid}_thumb.jpg     # 200x200 thumbnails
│   ├── {photo_uuid}_preview.jpg   # 800x600 previews  
│   └── ...
├── cache.db                       # SQLite cache database
└── session_{session_id}.json      # Session state backup
```

### Export File Formats

#### Deletion List JSON
```json
{
    "session_id": "session_123",
    "created_at": "2024-01-15T14:45:00Z",
    "photos_for_deletion": [
        {
            "uuid": "photo_uuid_2",
            "path": "/Users/user/Pictures/Photos Library.photoslibrary/...",
            "filename": "IMG_1235.HEIC",
            "timestamp": "2024-01-15T14:30:02Z",
            "file_size": 2450000,
            "camera_model": "iPhone 15 Pro",
            "reason": "not_selected_in_group_001"
        }
    ],
    "summary": {
        "total_count": 45,
        "total_size_bytes": 112750000,
        "estimated_savings": "107.5 MB"
    }
}
```

#### Deletion List CSV  
```csv
uuid,filename,timestamp,file_size,camera_model,reason,group_id
photo_uuid_2,IMG_1235.HEIC,2024-01-15T14:30:02Z,2450000,iPhone 15 Pro,not_selected,group_001
photo_uuid_4,IMG_1237.HEIC,2024-01-15T14:30:04Z,2475000,iPhone 15 Pro,not_selected,group_001
```

## CRITICAL Developer Notes

### ⚠️ Common osxphotos Attribute Mistakes

**ALWAYS use these exact patterns to avoid AttributeError:**

```python
# ✅ CORRECT file size access
file_size = photo.original_filesize  # NOT photo.file_size

# ✅ CORRECT camera access  
if hasattr(photo, 'exif_info') and photo.exif_info:
    camera_model = getattr(photo.exif_info, 'camera_model', None)
    camera_make = getattr(photo.exif_info, 'camera_make', None)

# ❌ WRONG - will cause AttributeError
# camera_model = photo.camera_model

# ✅ CORRECT dimensions
width = photo.original_width   # NOT photo.width for original size
height = photo.original_height

# ✅ CORRECT date access
timestamp = photo.date  # Primary timestamp
```

### Performance Guidelines
- **Fast operations**: `photo.uuid`, `photo.filename`, `photo.date`, `photo.original_filesize`
- **Medium operations**: `photo.exif_info`, camera details, location data
- **Slow operations**: `photo.path` (if cloud-only), face detection, ML labels
- **For UI responsiveness**: Limit to 1000 photos for camera model extraction

## Current Data Flow (August 2024)

### Smart Analysis Flow
1. **Library Stats**: Fast scan using basic osxphotos attributes
2. **Size Filtering**: Filter entire library by `original_filesize`
3. **Smart Analysis**: Process top N largest files only
4. **Group Creation**: Time/camera clustering via PhotoScanner  
5. **Priority Classification**: P1-P10 based on savings potential
6. **Dashboard Display**: Real-time priority summary

### Photo Selection Flow  
1. **Group Loading**: `/api/groups` with pre-computed clusters
2. **Individual Selection**: Frontend inverted model (selected = DELETE)
3. **Visual Feedback**: Real-time 🛡️ KEEP / ❌ DELETE states
4. **Confirmation**: Backend validates selection consistency  
5. **Smart Album Creation**: Export to Photos.app for review

### Export & Action Flow
1. **Session Tracking**: DeletionSession for progress
2. **File Export**: CSV/JSON with photo metadata
3. **Smart Album**: Photos.app integration for safe review
4. **User Decision**: Manual deletion outside app for safety