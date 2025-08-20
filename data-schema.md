# Photo Dedup Tool - Data Schema

## Core Data Structures

### Photo
Primary entity representing a single photo from the macOS Photos library.

```python
@dataclass
class Photo:
    # Identity
    uuid: str                    # Photos library UUID (primary key)
    path: str                    # File system path to photo
    filename: str                # Original filename
    
    # Metadata
    timestamp: datetime          # When photo was taken
    date_created: datetime       # When file was created
    camera_model: str           # Camera/device that took photo
    camera_make: str            # Camera manufacturer
    
    # Technical Properties
    file_size: int              # Size in bytes
    width: int                  # Image width in pixels  
    height: int                 # Image height in pixels
    format: str                 # File format (HEIC, JPEG, etc.)
    
    # Analysis Results
    perceptual_hash: str        # pHash for similarity detection
    quality_score: float        # Overall quality rating (0-100)
    sharpness_score: float      # Image sharpness (0-100)
    face_count: int            # Number of faces detected
    has_smiling_faces: bool     # Whether faces are smiling
    
    # Processing Status
    analyzed: bool = False      # Whether analysis has been run
    selected_for_keeping: bool = False  # User selection status
    marked_for_deletion: bool = False   # Tagged for deletion
```

### PhotoGroup  
Collection of similar photos that should be reviewed together.

```python
@dataclass
class PhotoGroup:
    # Identity
    group_id: str               # Unique identifier for this group
    
    # Photos
    photos: List[Photo]         # List of similar photos (2-4 max)
    recommended_photo_uuid: str # UUID of recommended best photo
    
    # Grouping Criteria
    time_window_start: datetime # Start of time window for grouping
    time_window_end: datetime   # End of time window for grouping  
    camera_model: str           # Shared camera model
    
    # Analysis Results
    similarity_threshold: float  # How similar photos are (0-100)
    total_size_bytes: int       # Combined size of all photos
    potential_savings_bytes: int # Bytes saved if non-selected deleted
    
    # User Interaction
    reviewed: bool = False      # Whether user has reviewed group
    user_selections: List[str]  # UUIDs of photos user wants to keep
    
    # Creation Info
    created_at: datetime        # When group was created
    analysis_version: str       # Version of grouping algorithm used
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

## API Data Transfer Objects

### PhotoGroupResponse
JSON structure for API responses containing photo groups.

```python
{
    "group_id": "group_001",
    "photos": [
        {
            "uuid": "photo_uuid_1",
            "filename": "IMG_1234.HEIC", 
            "timestamp": "2024-01-15T14:30:00Z",
            "camera_model": "iPhone 15 Pro",
            "file_size": 2457600,
            "width": 4032,
            "height": 3024,
            "quality_score": 85.5,
            "thumbnail_url": "/api/thumbnail/photo_uuid_1",
            "selected": false,
            "recommended": true
        }
        // ... more photos
    ],
    "total_size_bytes": 9830400,
    "potential_savings_bytes": 7372800,
    "similarity_score": 92.3
}
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

## Data Flow Architecture

1. **Photo Discovery**: osxphotos → Photo objects → SQLite storage
2. **Analysis Pipeline**: Photos → Image analysis → Updated Photo objects  
3. **Grouping Algorithm**: Photos → PhotoGroup objects → group_photos relationships
4. **Web API Layer**: Database queries → JSON DTOs → HTTP responses
5. **User Interaction**: HTTP requests → Database updates → Session tracking
6. **Export Generation**: Session data → File system exports → User download