# UX Text Drafts & Copy
## Photo Deduplication Application

---

## Confirmation Messages

### 1. Batch Delete Confirmations

#### Single Photo Delete
**Current**: "Are you sure you want to delete this photo? This action cannot be undone."
**New**: "Mark photo for deletion?"
*Buttons: [Cancel] [Delete]*

#### Small Batch (2-10 photos)
**Current**: "Are you sure you want to delete all 5 photos marked for deletion? This action cannot be undone..."
**New**: "Mark 5 photos for deletion?"
*Buttons: [Cancel] [Delete]*

#### Large Batch (11+ photos)
**Current**: [Long technical explanation about batch operations...]
**New**: "Mark 23 photos for deletion?"
*Buttons: [Cancel] [Delete]*

#### Group Delete All
**Current**: "Delete all photos in this group? This will permanently remove 6 photos from your library..."
**New**: "Mark all 6 photos in this group for deletion?"
*Buttons: [Cancel] [Delete All]*

---

## Success & Status Messages

### 2. Processing Complete Messages

#### Single Photo Processed
**Current**: "Photo deletion completed successfully! 1 photo removed, 12.5 MB freed..."
**New**: *Toast notification*: "Photo marked for deletion"
*Auto-dismiss: 2 seconds*

#### Batch Processing Complete  
**Current**: [Detailed summary with processing time, space freed, success rates...]
**New**: *Toast notification*: "12 photos marked for deletion • 146 MB freed"
*Auto-dismiss: 3 seconds*

#### Large Batch Complete
**Current**: [Verbose success report with next steps...]
**New**: *Toast notification*: "✅ 67 photos marked for deletion • 1.2 GB freed"
*Auto-dismiss: 4 seconds*

#### No Action Needed
**New**: *Toast notification*: "All photos already reviewed"
*Auto-dismiss: 2 seconds*

---

## Information & Help Text

### 3. Grouping Explanations

#### Simple Grouping Tooltip
**Current**: "This group contains photos that appear to be duplicates based on timestamp similarity (within 30 seconds), location data (if available), file size comparison, and visual similarity analysis. The algorithm has identified these as potential duplicates with 85% confidence based on multiple factors including EXIF data correlation..."

**New**: "6 similar photos taken within 30 seconds at the same location."
*Link: "Show details ▼" (expands to technical info)*

#### Technical Details (Expandable)
**New Expanded View**: 
```
Why these are grouped:
• Same time: Within 30 seconds
• Same place: GPS coordinates match  
• Similar size: File sizes within 5%
• Confidence: 85% likely duplicates
```

#### High Confidence Groups
**New**: "Very similar photos - likely duplicates"

#### Medium Confidence Groups  
**New**: "Similar photos - review recommended"

#### Low Confidence Groups
**New**: "Possibly related photos"

---

## Error Messages

### 4. Error States

#### Permission Denied
**Current**: "An error occurred during the photo deletion process. Error code: OSXPHOTOS_DELETE_FAILED_001. Technical details: Permission denied when attempting to move photos to trash. Please check your Photos app permissions in System Preferences and ensure the application has full disk access..."

**New**: "Couldn't mark photos for deletion. Check your Photos app permissions."
*Buttons: [Open Settings] [Try Again]*

#### Photos App Busy
**Current**: "Unable to complete operation. The Photos application may be busy or locked by another process..."
**New**: "Photos app is busy; try closing it and try again."
*Buttons: [Retry] [Cancel]*

#### Network/Storage Error
**Current**: "File system error encountered during photo processing. Error details: Insufficient storage space or network connectivity issues may be preventing..."
**New**: "Not enough storage space to mark for deletion."
*Buttons: [Free Space] [Cancel]*

#### Unknown Error
**Current**: [Long technical error with stack traces...]
**New**: "Something went wrong. Try again in a moment."
*Buttons: [Retry] [Report Issue]*

---

## Progress & Loading Text

### 5. Processing States

#### Initial Analysis
**Current**: "Starting analysis of photo library. This may take several minutes depending on library size..."
**New**: "Analyzing your photos..."
*Progress bar with estimated time*

#### Scanning Photos
**Current**: "Scanning photo metadata and building similarity indexes. Progress: 1,247 / 14,060 photos processed..."
**New**: "Scanning photos... 1,247 of 14,060"
*Simple progress: "12% complete"*

#### Grouping Duplicates
**Current**: "Identifying potential duplicate groups using advanced similarity algorithms..."
**New**: "Finding similar photos..."

#### Almost Done
**Current**: "Finalizing analysis results and preparing user interface..."
**New**: "Almost ready..."

#### Loading Filters
**Current**: "Loading filter interface and initializing lazy loader cache..."
**New**: "Loading filters..."

---

## UI Labels & Navigation

### 6. Button Labels

#### Primary Actions
- **Current**: "Apply Filters to Photo Library"
- **New**: "Review Photos" or "Find Duplicates"

- **Current**: "Analyze Selected Clusters for Duplicates"  
- **New**: "Review Selected"

- **Current**: "Mark All Photos in Group for Deletion"
- **New**: "Mark all for deletion"

- **Current**: "Confirm Bulk Deletion Operation"
- **New**: "Mark for deletion"

#### Secondary Actions
- **Current**: "Return to Main Dashboard Interface"
- **New**: "Back to Dashboard"

- **Current**: "Clear All Applied Filters and Reset"
- **New**: "Clear Filters"

- **Current**: "Show Advanced Filtering Options"
- **New**: "More Options"

### 7. Status Labels

#### Photo Selection States
- **Unselected**: *No label needed*
- **Keep**: "✅ Keep"  
- **Delete**: "❌ Delete"
- **Processing**: "⏳ Processing..."

#### Group Status
- **Current**: "Group contains 6 photos with high duplicate probability (P1 priority)"
- **New**: "6 photos • High duplicate probability"

- **Current**: "Selection status: 2 marked for keeping, 1 marked for deletion, 3 undecided"
- **New**: "2 keep • 1 delete • 3 undecided"

---

## Filter Interface Text

### 8. Filter Categories

#### Year Selection
**Current**: "Filter by Date Range (Year)"
**New**: "🗓️ Year"

#### Priority Levels
**Current**: "Duplicate Detection Confidence Level"
**New**: "🎯 Priority" 
*Options: "High", "Medium", "Low", "Any"*

#### File Types
**Current**: "Supported Image File Format Types"
**New**: "📱 File Types"

#### Camera Models
**Current**: "Camera Device Model Filter"
**New**: "📷 Camera"

#### File Size Range
**Current**: "File Size Range Selector (Megabytes)"
**New**: "📏 Size"

### 9. Filter Results

#### Results Preview
**Current**: "Query results: 142 photo clusters match your current filter criteria, containing approximately 438 individual photos with estimated storage savings potential of 1.2 GB..."
**New**: "438 photos • 1.2GB potential savings"

#### No Results
**Current**: "No photo clusters match the currently applied filter criteria. Try adjusting your filter settings or clearing filters to see more results..."
**New**: "No matches. Try different filters."
*Button: [Clear Filters]*

#### Loading Results
**Current**: "Applying filter criteria to photo database and recalculating results..."
**New**: "Filtering..."

---

## Help & Onboarding Text

### 10. First-Time User Guidance

#### Welcome Message
**New**: "Find and mark duplicate and similar photos to free up space."

#### Quick Tutorial Steps
1. **New**: "Step 1: Choose filters to find similar photos"
2. **New**: "Step 2: Review groups and mark photos to keep or delete"  
3. **New**: "Step 3: Confirm"
4. **New**: "Go to the Photos app, select all photos marked for deletion, and delete!"

#### Empty State Messages

##### No Photos Found
**New**: "No duplicate photos found. Your library looks clean!"

##### First Visit
**New**: "Click 'Find Duplicates' to start analyzing your photos."

##### All Photos Reviewed
**New**: "Great job! All duplicate groups have been reviewed."

---

## Accessibility & Screen Reader Text

### 11. Alt Text & ARIA Labels

#### Photo Cards
- **Alt text**: "Photo IMG_1234.HEIC taken January 15, 2024"
- **ARIA label**: "Photo 1 of 6 in duplicate group, currently marked to keep"

#### Buttons
- **Keep button**: "Mark photo to keep"
- **Delete button**: "Mark photo for deletion"
- **Preview button**: "View large preview"

#### Status Updates
- **Selection change**: "Photo marked for deletion" (announced to screen readers)
- **Group completion**: "All photos in group reviewed"

---

## Tone & Voice Guidelines

### Writing Principles
1. **Concise**: Maximum 2 sentences for confirmations
2. **Plain language**: No technical jargon  
3. **Action-oriented**: Clear next steps
4. **Reassuring**: Acknowledge user concerns about deletion
5. **Respectful**: Don't assume user knowledge level

### Vocabulary Choices
- **Use**: "Delete", "Remove", "Keep", "Review"
- **Avoid**: "Terminate", "Eliminate", "Process", "Execute"

- **Use**: "Photos", "Pictures", "Images"  
- **Avoid**: "Assets", "Files", "Objects"

- **Use**: "Similar", "Duplicate", "Matching"
- **Avoid**: "Algorithmically correlated", "Metadata aligned"

### Emotional Tone
- **Confident** but not pushy: "Delete 5 photos?" not "You should delete these photos"
- **Helpful** not condescending: "Try different filters" not "You need to adjust your filter settings"
- **Clear** not verbose: "Can't be undone" not "This action is permanent and irreversible"

This comprehensive text guide ensures all user-facing copy is clear, concise, and user-friendly while maintaining the app's functionality and reducing cognitive load.