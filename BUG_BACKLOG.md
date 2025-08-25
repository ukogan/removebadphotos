# Bug Backlog - Photo Deduplication Tool

This document tracks known bugs and issues that require future investigation and resolution.

## 🔴 Critical Issues

### 1. Persistent Reappearing "Marked for Deletion" Photos
**Status**: Open  
**Priority**: High  
**Reporter**: User  
**Date Reported**: 2025-08-25  

**Description:**
Photos that were previously marked for deletion and manually deleted from Photos smart albums continue to reappear in new smart albums created by subsequent analysis passes.

**Current Behavior:**
- Photos are correctly tagged with "marked-for-deletion" keyword
- User manually deletes photos from smart album in Photos app
- Same photos appear in newly created smart albums from later analysis runs

**Expected Behavior:**
- Photos marked for deletion should be permanently excluded from all future analysis
- Once deleted, photos should not reappear in any new smart albums

**Investigation Done:**
- Implemented dual-layer filtering (keyword + UUID tracking)
- Added persistent UUID tracking system (`~/.photo_dedup_processed_uuids.json`)
- Enhanced logging and diagnostic tools

**Root Cause Hypothesis:**
1. Photos database synchronization delays between osxphotos and Photos app
2. Possible caching issues in osxphotos library
3. Multiple photo versions (original + edited) with different UUIDs
4. Smart album refresh logic may be re-including photos based on metadata

**Next Steps for Investigation:**
- [ ] Monitor UUID tracking file to see if UUIDs are being saved correctly
- [ ] Test with `photos_db.photos(intrash=True)` to see if deleted photos are in trash
- [ ] Investigate osxphotos database refresh mechanisms
- [ ] Check for photo versions/edits with different UUIDs but same filename
- [ ] Consider implementing photo fingerprinting (hash-based) instead of UUID-only tracking

**Workaround:**
Current dual-layer filtering may reduce frequency but doesn't eliminate the issue.

---

## 🟡 Medium Priority Issues

### 2. Video Files Appearing in Photo Analysis
**Status**: Open  
**Priority**: Medium  
**Reporter**: User  
**Date Reported**: 2025-08-25  

**Description:**
Video files (.mov, .mp4, etc.) are being included in photo duplicate analysis despite being filtered.

**Current Behavior:**
- Videos appear in duplicate groups alongside photos
- Video thumbnails may fail to load properly
- Video quality analysis may produce incorrect results

**Expected Behavior:**
- Videos should be completely excluded from photo duplicate analysis
- Only photo formats (JPEG, HEIC, PNG, etc.) should be processed

**Current Implementation:**
```python
# in get_unprocessed_photos()
all_photos = db.photos(intrash=False, movies=not include_videos)
```

**Investigation Needed:**
- [ ] Verify `movies=False` parameter is working correctly
- [ ] Check if certain video formats are being misclassified as photos
- [ ] Review video filtering logic in all photo scanning endpoints
- [ ] Add explicit file extension filtering as backup

### 3. Photo Thumbnails Not Displaying Preview
**Status**: Open  
**Priority**: Medium  
**Reporter**: User  
**Date Reported**: 2025-08-25  

**Description:**
Some photos show "❌ Could not load image" instead of thumbnail previews.

**Current Behavior:**
- Certain photos fail to load thumbnails
- Error messages appear in place of photo previews
- Full-size images may also fail to load

**Expected Behavior:**
- All photos should display thumbnail previews
- Graceful fallback for unsupported formats

**Error Patterns Observed:**
```
PIL.UnidentifiedImageError: cannot identify image file '/var/.../IMG_XXXX.HEIC'
```

**Investigation Needed:**
- [ ] Check HEIC/HEIF support configuration
- [ ] Verify pillow-heif installation and compatibility
- [ ] Review thumbnail generation error handling
- [ ] Add format-specific thumbnail generation
- [ ] Implement fallback thumbnail generation methods

---

## 🟢 Low Priority Issues

### 4. Progress Tracking Inconsistencies
**Status**: Open  
**Priority**: Low  
**Date Reported**: 2025-08-25  

**Description:**
Progress reporting during analysis may show inconsistent or unclear status updates.

**Investigation Needed:**
- [ ] Review progress callback mechanisms
- [ ] Standardize progress reporting format
- [ ] Add ETA calculations for long operations

### 5. UI/UX Improvements
**Status**: Open  
**Priority**: Low  
**Date Reported**: Various  

**Items to Consider:**
- [ ] Add batch selection controls for photo groups
- [ ] Implement undo/redo for photo selections
- [ ] Add keyboard shortcuts for navigation
- [ ] Improve mobile responsiveness
- [ ] Add dark mode support

---

## 📋 Bug Triage Process

### Priority Levels:
- **🔴 Critical**: Breaks core functionality, affects data integrity
- **🟡 Medium**: Impacts user experience, has workarounds
- **🟢 Low**: Minor issues, cosmetic problems

### Investigation Workflow:
1. **Reproduce**: Create minimal reproduction steps
2. **Isolate**: Identify root cause through debugging
3. **Design**: Plan solution approach
4. **Implement**: Code and test fix
5. **Validate**: Verify fix doesn't introduce regressions

### Testing Requirements:
- [ ] Unit tests for critical path fixes
- [ ] Integration tests for workflow changes
- [ ] Manual testing with real photo library
- [ ] Performance regression testing

---

## 🔧 Debugging Tools Available

### Current Diagnostic Endpoints:
- `GET /api/debug-filename/<filename>` - Search for specific photos
- `GET /api/stats` - Library statistics and exclusion counts
- `GET /api/progress` - Real-time analysis progress

### Log Files:
- Server logs show filtering statistics and errors
- UUID tracking file: `~/.photo_dedup_processed_uuids.json`

### Debugging Commands:
```bash
# Check UUID tracking file
cat ~/.photo_dedup_processed_uuids.json

# Test specific photo search
curl "http://127.0.0.1:5003/api/debug-filename/problematic_photo_name"

# Monitor server logs for filtering stats
tail -f server_logs | grep "Excluded.*photos"
```

---

## 📝 Notes

- This backlog should be reviewed regularly during development cycles
- High-priority bugs should be addressed before adding new features
- Consider user impact and frequency when prioritizing fixes
- Document any new bugs discovered during testing

**Last Updated**: 2025-08-25
**Next Review**: TBD