# Stage 4 Implementation: Photos Library Integration

**Date:** August 20, 2025  
**Status:** 🚀 READY TO BEGIN  
**Prerequisites:** ✅ Stage 3 Complete - Visual interface fully functional

## Stage 4 Objectives

### Goal
Complete the workflow with actual Photos app integration, enabling users to tag photos for deletion and create organized smart albums.

### User Stories
- As a user, I want rejected photos tagged in Photos app so I can review before permanent deletion
- As a user, I want a smart album created with rejected photos so I can find them easily  
- As a user, I want a deletion list exported so I can use it with other tools
- As a user, I want to confirm all actions before they happen so I don't lose photos accidentally

## Technical Implementation Plan

### 1. Photo Tagging System
**Endpoint:** `POST /api/tag-photos`
**Input:** List of photo UUIDs to mark for deletion
**Function:** Add "marked-for-deletion" keyword to selected photos

```python
def tag_photos_for_deletion(photo_uuids: List[str], session_id: str) -> dict:
    """Tag photos in Photos app with deletion marker."""
    tagged_count = 0
    errors = []
    
    for uuid in photo_uuids:
        try:
            photo = photosdb.get_photo(uuid)
            # Add keyword using osxphotos
            photo.add_keyword("marked-for-deletion")
            photo.add_keyword(f"session-{session_id}")
            tagged_count += 1
        except Exception as e:
            errors.append(f"{uuid}: {str(e)}")
    
    return {
        "success": len(errors) == 0,
        "tagged_count": tagged_count,
        "errors": errors
    }
```

### 2. Smart Album Creation  
**Function:** Create timestamped smart album containing tagged photos
**Naming:** "Marked for Deletion on MMM-DD at HH:MM to save XXX MB"

```python
def create_smart_album(session_id: str, estimated_savings_mb: float) -> dict:
    """Create smart album with tagged photos."""
    timestamp = datetime.now().strftime("%b-%d at %H:%M")
    album_name = f"Marked for Deletion on {timestamp} to save {estimated_savings_mb:.1f} MB"
    
    # Create smart album with keyword filter
    album = photosdb.create_smart_album(
        name=album_name,
        criteria=[
            {"keyword": "marked-for-deletion"},
            {"keyword": f"session-{session_id}"}
        ]
    )
    
    return {
        "success": True,
        "album_name": album_name,
        "album_id": album.uuid
    }
```

### 3. Deletion List Export
**Formats:** CSV and JSON
**Content:** Photo metadata, file paths, selection rationale

```python
def export_deletion_list(photo_uuids: List[str], format: str = "csv") -> str:
    """Export deletion list for external tools."""
    photos_data = []
    
    for uuid in photo_uuids:
        photo = photosdb.get_photo(uuid)
        photos_data.append({
            "uuid": uuid,
            "filename": photo.original_filename,
            "timestamp": photo.date.isoformat(),
            "file_size_mb": photo.original_filesize / (1024*1024),
            "camera_model": photo.exif_info.camera_model if photo.exif_info else None,
            "quality_score": photo.quality_score,
            "reason": "User selected for deletion"
        })
    
    if format == "csv":
        return export_as_csv(photos_data)
    else:
        return export_as_json(photos_data)
```

### 4. Workflow Integration API
**New Endpoint:** `POST /api/complete-selection`
**Purpose:** Execute full workflow: tag photos + create album + export list

```python
@app.route('/api/complete-selection', methods=['POST'])
def api_complete_selection():
    """Complete the photo selection workflow."""
    data = request.json
    photos_to_delete = data.get('photos_to_delete', [])
    estimated_savings = data.get('estimated_savings_mb', 0)
    
    session_id = generate_session_id()
    
    # Step 1: Tag photos
    tag_result = tag_photos_for_deletion(photos_to_delete, session_id)
    
    # Step 2: Create smart album  
    album_result = create_smart_album(session_id, estimated_savings)
    
    # Step 3: Export deletion list
    csv_export = export_deletion_list(photos_to_delete, "csv")
    json_export = export_deletion_list(photos_to_delete, "json")
    
    return jsonify({
        "success": tag_result["success"] and album_result["success"],
        "tagged_photos": tag_result["tagged_count"],
        "album_name": album_result["album_name"],
        "csv_export": csv_export,
        "json_export": json_export,
        "session_id": session_id
    })
```

## Frontend Integration

### Confirmation Dialog Enhancement
```javascript
function showFinalConfirmation(photosToDelete, estimatedSavings) {
    const dialog = `
        <div class="final-confirmation">
            <h3>🏷️ Ready to Tag Photos for Deletion</h3>
            <p>This will:</p>
            <ul>
                <li>✅ Tag ${photosToDelete.length} photos with "marked-for-deletion"</li>
                <li>📁 Create smart album "Marked for Deletion on ${new Date().toLocaleDateString()}"</li>
                <li>📄 Export deletion list (CSV + JSON)</li>
                <li>💾 Save approximately ${estimatedSavings.toFixed(1)} MB</li>
            </ul>
            <p><strong>⚠️ Important:</strong> Photos will be tagged but not deleted. 
               You must manually delete them from the smart album in Photos app.</p>
        </div>
    `;
    
    if (confirm("Proceed with tagging photos for deletion?")) {
        executeWorkflow(photosToDelete, estimatedSavings);
    }
}
```

## Testing Strategy

### 1. Safe Testing with Limited Photos
- Test with 2-3 photos from one group initially
- Verify keywords appear in Photos app
- Confirm smart album creation works
- Test export functionality

### 2. Permission Verification
- Ensure osxphotos has write permissions
- Handle macOS security prompts gracefully
- Provide user guidance for Full Disk Access

### 3. Rollback Capability
```python
def rollback_session(session_id: str) -> dict:
    """Remove all tags from a session."""
    photos = photosdb.photos(keyword=[f"session-{session_id}"])
    
    for photo in photos:
        photo.remove_keyword("marked-for-deletion")
        photo.remove_keyword(f"session-{session_id}")
    
    return {"success": True, "photos_cleaned": len(photos)}
```

## Success Criteria

### Functional Requirements
- ✅ Photos tagged with keywords in Photos app
- ✅ Smart album created with timestamped name
- ✅ Export files generated (CSV + JSON)
- ✅ User can manually delete from smart album
- ✅ No data loss or corruption

### User Experience
- ✅ Clear confirmation dialogs explaining each step
- ✅ Progress indicators during tagging
- ✅ Success message with next steps
- ✅ Error handling with helpful messages

### Safety Features
- ✅ No automatic deletion (user must manually delete)
- ✅ Session-based tagging for rollback capability
- ✅ Detailed logging of all operations
- ✅ Confirmation required for all destructive actions

## Implementation Priority

1. **Photo Tagging** - Core functionality to mark photos
2. **Smart Album Creation** - Organization and findability  
3. **Export Functionality** - External tool integration
4. **Frontend Integration** - Complete user workflow
5. **Error Handling** - Robust failure recovery
6. **Testing & Validation** - Ensure reliability

## Next Steps

**Ready to implement Stage 4 immediately:**
- Photo selection interface fully functional
- Quality analysis and recommendations working
- Backend infrastructure complete
- Frontend user experience polished

**Implementation approach:**
- Start with photo tagging functionality
- Build incremental testing with real Photos library
- Add safety features and error handling
- Complete with smart album and export features