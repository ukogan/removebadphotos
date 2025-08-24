# Photo Dedup Tool - Product Requirements Document

## Problem Statement

User has thousands of similar photos in macOS Photos library from burst shots and sequences, consuming excessive storage. Manual deletion is time-consuming and error-prone. Existing tools are either commercial, require photo export, or lack intelligent selection capabilities.

## Success Criteria

- Reduce photo library storage by 20-50% through intelligent duplicate removal
- Process 1000+ photos efficiently without performance issues  
- User can review and approve all deletions before they occur
- Integration with macOS Photos app for seamless workflow

## Development Stages

### Stage 1: Foundation & Risk Derisking (Week 1-2)
**Goal:** Prove core technical feasibility and establish development foundation

**User Stories:**
- As a developer, I want to verify osxphotos can access my Photos library so I can proceed confidently
- As a developer, I want a basic Flask server running so I can build the web interface
- As a user, I want to see a list of my photos in a web browser so I know the system works

**Technical Deliverables:**
- `test_osxphotos.py` - Script that lists photos from library
- Basic Flask server serving HTML page
- Simple web page displaying photo count and basic metadata
- Verify macOS permissions and access requirements

**Success Criteria:**
- osxphotos successfully reads Photos library
- Web server runs on localhost
- User can view basic photo information in browser

**Risk Derisking:**
- Tests highest risk item (Photos library access) immediately
- Establishes both technology stacks work together
- Creates development foundation for all future work

### Stage 2: Core Photo Analysis (Week 3-4)  
**Goal:** Implement photo grouping and similarity detection logic

**User Stories:**
- As a user, I want photos taken within 10 seconds grouped together so I can see potential duplicates
- As a user, I want photos from the same camera grouped together so I avoid mixing different devices
- As a user, I want to see groups of similar photos displayed in the web interface

**Technical Deliverables:**
- Photo scanning and metadata extraction
- Time-based grouping algorithm (10-second windows)
- Camera-based filtering
- Basic perceptual hashing for similarity detection
- Web API endpoints for photo groups
- HTML interface displaying photo groups (metadata only, no images yet)

**Success Criteria:**
- Groups created with 2-4 similar photos per group
- Groups displayed in web interface with timestamps and camera info
- Processing completes for libraries with 500+ photos

### Stage 3: Visual Interface (Week 5-6)
**Goal:** Create functional photo selection interface

**User Stories:**
- As a user, I want to see actual photos side-by-side so I can compare quality visually
- As a user, I want the best photo pre-selected so I can quickly approve good choices
- As a user, I want to click photos to change selections so I can override recommendations
- As a user, I want to see file sizes and potential savings so I understand the impact

**Technical Deliverables:**
- Image serving through Flask (resized thumbnails)
- HTML/CSS photo gallery with selection interface
- JavaScript for photo selection/deselection
- Quality scoring algorithm (basic sharpness detection)
- Storage calculation and display
- Responsive design for different screen sizes

**Success Criteria:**
- Photos display clearly in web interface
- User can select/deselect photos with mouse clicks
- Pre-selection algorithm chooses reasonable "best" photos
- Storage savings calculated and displayed accurately

### Stage 4: Photos Library Integration (Week 7-8)
**Goal:** Complete the workflow with actual Photos app integration

**User Stories:**
- As a user, I want rejected photos tagged in Photos app so I can review before permanent deletion
- As a user, I want a smart album created with rejected photos so I can find them easily
- As a user, I want a deletion list exported so I can use it with other tools
- As a user, I want to confirm all actions before they happen so I don't lose photos accidentally

**Technical Deliverables:**
- Photo tagging functionality using osxphotos
- Smart album creation with timestamped names
- Deletion list export (CSV/JSON)
- Confirmation dialogs and safety checks
- Session management and undo capabilities

**Success Criteria:**
- Tagged photos appear in Photos app with correct metadata
- Smart albums created successfully
- User can manually delete photos from smart album in Photos app
- Deletion lists are accurate and complete

### Stage 5: Enhanced Intelligence & Visual Similarity (Week 9-10)
**Goal:** Improve grouping accuracy and prevent different subjects from being grouped together

**User Stories:**
- As a user, I want only visually similar photos grouped so I don't see unrelated images together
- As a user, I want burst mode photos handled with shorter time windows so I get better precision
- As a user, I want improved quality analysis so the best photos are accurately selected
- As a user, I want composition analysis so similar poses/angles are identified

**Technical Deliverables:**
- Visual similarity filtering using perceptual hash comparison
- Adaptive time windows (3 seconds for burst mode, 10 seconds for normal)
- Advanced image quality analysis with computer vision
- Composition similarity detection
- Face detection and expression analysis
- Filtering threshold configuration (70% similarity minimum)

**Success Criteria:**
- No more than 5% of groups contain visually unrelated photos
- Burst mode photos get appropriate grouping (3-second windows)
- Quality recommendations improve by >80% accuracy
- User can configure similarity thresholds

## Visual Design Enhancement Stages (Based on UX Research)

### Stage 3.5: Visual Foundation (Phase 1 - Critical Fixes)
**Goal:** Establish professional, trustworthy visual design aligned with photo deduplication standards

**User Stories:**
- As a user, I want a professional-looking interface so I trust the tool with my photos
- As a user, I want conservative selection defaults so I don't accidentally delete photos
- As a user, I want clear visual hierarchy so I can focus on photo comparison decisions

**Critical Issues to Fix:**
- Replace purple gradient dashboard with professional gray palette (#f8f9fa backgrounds)
- Remove all pre-selection defaults - require explicit user action for deletion marking
- Convert to side-by-side comparison cards instead of grid layout
- Implement color-coded selection: Green (keep), Amber (review), Red (delete only in confirmation)
- Use system fonts (-apple-system) for better macOS integration
- Add 8px spacing system for visual consistency

**Success Criteria:**
- Interface looks professional and trustworthy
- No photos pre-selected for deletion by default
- Clear visual distinction between keep/review/delete states
- Consistent spacing and typography throughout

### Stage 4.5: Visual Enhancement (Phase 2 - User Experience)
**Goal:** Improve interaction patterns and information display based on deduplication tool research

**User Stories:**
- As a user, I want hover-based metadata so I can get details without cluttering the interface
- As a user, I want similarity scores displayed so I understand why photos are grouped
- As a user, I want clear feedback when I make selections so I know the system responded

**Enhancement Features:**
- Add hover-based metadata overlays (file size, resolution, timestamp)
- Implement similarity confidence scores (percentage display)
- Add quality assessment indicators (stars, ratings, or badges)
- Single-click selection with immediate visual feedback
- Batch operation counters ("5 photos selected")
- Multi-step confirmation dialogs for safety
- Prominent undo/recovery options

**Success Criteria:**
- Metadata appears cleanly on hover without layout shifts
- Users understand why photos are grouped together
- Clear feedback for all user interactions
- Conservative approach to destructive actions

### Stage 5.5: Visual Polish (Phase 3 - Professional Finish)
**Goal:** Advanced visual features and micro-interactions for professional-grade experience

**User Stories:**
- As a user, I want smooth transitions so the interface feels modern and polished
- As a user, I want expandable groups so I can manage large result sets efficiently
- As a user, I want professional dashboard styling so the tool feels like commercial software

**Polish Features:**
- Professional dashboard redesign with clean statistics display
- Expandable duplicate groups with clear hierarchy
- Tree view options for large result sets
- Smooth transitions for all state changes
- Hover effects with subtle scaling (1.02x)
- Advanced progress indicators and loading states
- Smart grouping by similarity threshold with visual controls
- Professional action buttons and modern card layouts

**Success Criteria:**
- Interface feels as polished as commercial photo management tools
- Users can efficiently navigate large sets of duplicates
- All interactions feel smooth and responsive
- Visual design builds user confidence and trust

## Future Stages (Not in MVP)

### Stage 6: Integration & Scaling  
- Google Photos API integration
- Batch processing for very large libraries (10K+ photos)
- Progress indicators and background processing
- Configuration and preferences system

### Stage 7: Machine Learning & Advanced Analysis
- Deep learning quality assessment
- Automatic best-photo selection improvements using ML
- Advanced composition analysis with neural networks
- Object detection and scene understanding

### Stage 8: Gamification & UX
- Daily review game mode
- Storage achievement tracking
- Social features (share before/after stats)
- Advanced filtering and search capabilities

## Risk Mitigation Built Into Stages

**Stage 1** directly addresses highest risks:
- Photos library access (could kill entire project)
- Web server complexity (could force architecture change)
- Development environment setup

**Stage 2** builds core functionality incrementally:
- Proves image processing performance
- Tests photo grouping algorithms
- Validates core use case before UI complexity

**Stage 3** focuses on user experience:
- Ensures interface is usable before adding complexity
- Tests JavaScript and web UI capabilities
- Validates photo display and selection workflows

**Stage 4** completes integration:
- Only adds Photos app integration after everything else works
- Minimizes risk of corrupting user's photo library
- Provides safety checks and confirmation steps

## Definition of Done per Stage

Each stage must demonstrate:
1. **Functional completeness** - All user stories work end-to-end
2. **Technical stability** - No crashes, reasonable performance
3. **User validation** - Developer (user) can successfully complete workflows
4. **Documentation** - Feature markdown updated with implementation details
5. **Risk assessment** - Any new risks identified and documented

## Success Metrics

**Stage 1:** Technical proof of concept working
**Stage 2:** Photo groups created and displayed  
**Stage 3:** User can select photos and see savings
**Stage 4:** Photos tagged and smart albums created in Photos app

**Overall Success:** User reduces photo library size by significant amount with confidence in the deletion process.