# Error Catalog

## Purpose
This catalog documents known errors, their solutions, and debugging time investments to prevent doom loops.

---

## Error Patterns

### Photos Library Access Errors

#### Error: "Photos library not accessible"
**Symptoms:** PhotoScanner fails to initialize, osxphotos raises permissions error
**Root Cause:** macOS Full Disk Access not granted or Photos app not opened recently  
**Quick Test:** `python3 -c "import osxphotos; print(len(osxphotos.PhotosDB().photos()))"`
**Fix:** 
1. Grant Full Disk Access in System Preferences > Privacy & Security
2. Open Photos app to ensure library is accessible
3. Restart application
**Prevention:** Add diagnostic test for library access
**Debugging Time:** 5-15 minutes (first occurrence), <2 minutes (known issue)

#### Error: "Photo file not found at path"  
**Symptoms:** Thumbnail generation fails, file operations error
**Root Cause:** iCloud photos not downloaded locally, optimized storage enabled
**Quick Test:** `os.path.exists(photo.path)` returns False
**Fix:**
1. Use photo.export() method instead of direct path access
2. Implement iCloud download fallback
3. Add file existence check before processing
**Prevention:** Always check file existence before processing
**Debugging Time:** 10-20 minutes (understanding iCloud behavior)

### Image Processing Errors

#### Error: "PIL cannot identify image file"
**Symptoms:** Thumbnail generation crashes on specific photos
**Root Cause:** Corrupted image files, unsupported formats, or HEIC without pillow-heif
**Quick Test:** `PIL.Image.open(path)` in isolation
**Fix:**
1. Install pillow-heif: `pip install pillow-heif`
2. Add try/catch around Image.open()
3. Skip corrupted files with logging
**Prevention:** Robust error handling in thumbnail generation
**Debugging Time:** 5-10 minutes

### Flask Application Errors

#### Error: "Address already in use" 
**Symptoms:** Flask app won't start, port 5000 conflict
**Root Cause:** Another process using port 5000, previous instance not stopped
**Quick Test:** `lsof -i :5000` shows active processes
**Fix:**
1. Kill existing process: `kill $(lsof -t -i:5000)`  
2. Use different port: `flask run --port 5001`
3. Check for zombie processes
**Prevention:** Graceful shutdown handling, port configuration
**Debugging Time:** 2-5 minutes

#### Error: "Internal Server Error" with no stack trace
**Symptoms:** 500 errors in browser, minimal error information
**Root Cause:** Flask debug mode disabled, exceptions swallowed
**Quick Test:** Enable debug mode, check server logs
**Fix:**
1. Set `FLASK_DEBUG=1` environment variable
2. Add proper logging configuration  
3. Return detailed error responses in development
**Prevention:** Always enable debug mode during development
**Debugging Time:** 5-10 minutes

### Memory and Performance Issues

#### Error: "Memory usage exceeds 200MB"
**Symptoms:** System becomes slow, application crashes on large libraries
**Root Cause:** Loading too many full-resolution images into memory
**Quick Test:** Monitor with `ps aux | grep python` or Activity Monitor
**Fix:**
1. Implement lazy loading for photo data
2. Use thumbnails instead of full images  
3. Add garbage collection after processing batches
4. Limit concurrent image processing
**Prevention:** Memory monitoring in diagnostic tests
**Debugging Time:** 20-30 minutes (profiling required)

### OpenCV and Computer Vision Errors

#### Error: "OpenCV module not found"
**Symptoms:** Quality scoring fails, cv2 import errors
**Root Cause:** opencv-python not installed or version conflict
**Quick Test:** `python3 -c "import cv2; print(cv2.__version__)"`
**Fix:**
1. Install opencv-python: `pip install opencv-python`
2. For Apple Silicon: `pip install --upgrade opencv-python`
3. Check for conflicting installations
**Prevention:** Add cv2 import to diagnostic tests
**Debugging Time:** 5-10 minutes

---

## Resolution Patterns

### Quick Wins (< 5 minutes)
- Library import errors → Check pip installs
- Port conflicts → Kill process or change port
- File not found → Check path and permissions
- Module import errors → Verify virtual environment

### Medium Complexity (5-20 minutes)  
- Image format issues → Install codecs, add error handling
- Photos library access → Check macOS permissions
- Memory issues → Implement lazy loading patterns
- API endpoint errors → Check Flask routing and error handling

### Complex Issues (20-30 minutes)
- Performance bottlenecks → Profile and optimize
- iCloud photo handling → Implement export fallback
- Cross-service integration → Add circuit breakers
- Large library processing → Batch processing design

---

## Prevention Strategies

### Architecture Level
- Circuit breaker pattern for external services
- Graceful degradation for missing features  
- Comprehensive error boundaries
- Resource monitoring and limits

### Code Level
- Always check file existence before access
- Wrap external library calls in try/catch
- Use timeouts for long-running operations
- Implement retry logic with backoff

### Testing Level
- Diagnostic tests for all external dependencies
- Unit tests for error conditions
- Integration tests with mocked failures
- E2E tests with realistic error scenarios

---

## Metrics Tracking

### Error Frequency
- Track recurrence of cataloged errors
- Measure time-to-resolution trends
- Monitor new vs. known error ratios

### Process Effectiveness  
- % of debugging sessions under 30 minutes
- % of errors resolved vs. escalated
- Time saved through catalog usage

### System Health
- Memory usage trends during photo processing
- API response time degradation patterns
- Error rate thresholds for escalation