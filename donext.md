# Fix Blur Detection Interface - Next Steps

## Problem Summary
Current interface has fundamental logical flaws:
- Allows filtering by blur levels before analysis runs (impossible)
- Implements 2-page flow instead of required single-page workflow
- Adapted duplicate detection interface incorrectly for blur analysis

## Required Changes

### 1. Simplify Filters (blur_detection_interface.html)
- **Keep only year filter**: Remove "Photo Quality Issues" and "File Types" categories
- **Single analysis button**: "Find Blurry Photos" starts blur analysis
- **Add progress indicator**: Shows analysis progress on same page  
- **Add results section**: Display results after analysis completes

### 2. Fix JavaScript Flow
- Remove blur level filtering logic (`selectedPriorities`)
- Implement proper `analyzePhotos()` function calling `/api/blur-analysis`
- Add progress tracking and results display on same page
- No redirects - everything happens on one page

### 3. Verify API Integration
- Ensure `/api/blur-analysis` endpoint works with simplified filters
- Test end-to-end: year filter → "Find Blurry Photos" → progress → results

### 4. Core Architecture Fix
The fundamental issue: treating blur detection (analysis process) like duplicate detection (filtering process). 

**Correct workflow**: analysis first, then filtering of results
**Current broken workflow**: filtering of unknown results, then redirect

## Implementation Priority
1. Remove impossible quality filters
2. Fix button to call analysis instead of filter application  
3. Add progress indicator and results display
4. Test single-page workflow

This creates the intended user experience: filter by year → analyze for blur → see results on same page.