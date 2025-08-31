# RemoveBadPhotos - Product Requirements Document

## Problem Statement

Users accumulate thousands of low-quality photos in their macOS Photos library - blurry shots, overexposed images, underexposed photos, and other quality issues that consume storage space and clutter the library. Manual identification and deletion is extremely time-consuming and error-prone.

## Success Criteria

- Reduce photo library storage by 10-30% through intelligent bad photo identification
- Process 1000+ photos efficiently with configurable quality thresholds
- User can review and approve all deletions before they occur  
- Integration with macOS Photos app for seamless workflow
- Conservative defaults to avoid false positives on important photos

## Product Vision

A macOS desktop application that intelligently identifies poor-quality photos using computer vision techniques, provides a clean interface for user review and selection, and safely marks photos for deletion through the native Photos app workflow.

## Development Stages

### Stage 1: Blur Detection Foundation (Week 1)
**Goal:** Implement core blur detection with modern interface

**User Stories:**
- As a user, I want to set blur sensitivity thresholds so I can control detection strictness
- As a user, I want to see photos grouped by quality level so I can review similar issues together  
- As a user, I want a clean, professional interface so I trust the tool with my photos

**Technical Deliverables:**
- BlurDetector module with Laplacian variance algorithm
- Modern filter-based interface (adapted from TidyLib design)
- Flask API endpoints for blur analysis
- Configurable threshold controls (Very Blurry/Blurry/Slightly Blurry/Sharp)

**Success Criteria:**
- Blur detection accurately identifies very blurry photos (>90% accuracy)
- Interface loads quickly and responds to threshold changes
- Photos can be marked for deletion with 'd' keyboard shortcut

### Stage 2: Enhanced Quality Detection (Week 2-3)
**Goal:** Add exposure and noise detection capabilities

**User Stories:**
- As a user, I want overexposed/underexposed photos detected so I can remove washed-out images
- As a user, I want noisy photos identified so I can clean up low-light shots
- As a user, I want multiple quality issues shown per photo so I understand why it was flagged

**Technical Deliverables:**
- Exposure detection (histogram analysis)
- Noise detection (texture analysis) 
- Multi-criteria quality scoring
- Enhanced UI showing multiple quality indicators per photo

### Stage 3: Photos Library Integration (Week 3-4)  
**Goal:** Complete safe deletion workflow

**User Stories:**
- As a user, I want bad photos tagged in Photos app so I can review before permanent deletion
- As a user, I want a smart album created so I can find flagged photos easily
- As a user, I want undo capabilities so I can recover from mistakes

**Technical Deliverables:**
- Photo tagging using osxphotos
- Smart album creation ("Bad Photos - [Date]")
- CSV export of flagged photos
- Confirmation dialogs and safety checks

### Stage 4: Advanced Features (Future)
- Batch processing for very large libraries (10K+ photos)
- Machine learning quality assessment
- Duplicate detection integration
- Desktop app packaging

## Key Design Principles

### Conservative Approach
- Never delete photos directly - only tag for user review
- Default thresholds set to catch only obviously bad photos
- Clear undo and recovery options
- Multiple confirmation steps

### Professional Interface  
- Clean, modern design inspired by professional photo tools
- Filter-based workflow familiar to users
- Real-time preview of detection results
- Progressive disclosure of advanced options

### Performance Priority
- Fast analysis using efficient computer vision algorithms
- Lazy loading for large photo sets
- Progress indicators for long operations
- Responsive interface during analysis

## Success Metrics

**Accuracy Metrics:**
- >90% accuracy on very blurry photos
- <5% false positive rate on sharp photos  
- User satisfaction with quality recommendations

**Performance Metrics:**
- Analyze 1000 photos in <5 minutes
- UI remains responsive during analysis
- Memory usage stays under 2GB for typical libraries

**User Experience Metrics:**
- Clear understanding of why photos were flagged
- Confidence in deletion recommendations
- Successful library size reduction without regrets