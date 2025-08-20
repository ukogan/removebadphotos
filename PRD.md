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

## Future Stages (Not in MVP)

### Stage 5: Enhanced Intelligence
- Face detection and expression analysis
- Advanced composition analysis
- Machine learning quality assessment
- Automatic best-photo selection improvements

### Stage 6: Integration & Scaling  
- Google Photos API integration
- Batch processing for very large libraries (10K+ photos)
- Progress indicators and background processing
- Configuration and preferences system

### Stage 7: Gamification & UX
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