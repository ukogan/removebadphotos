# UX Wireframes & Visual Mockups
## Photo Deduplication Application

---

## Current vs. Proposed Photo Card Layouts

### Legacy Page: Photo Review Cards

#### CURRENT LAYOUT (Problems)
```
┌──────────────────────────────────────────────────────────┐
│ Group 1: 6 photos • Same location • 2024-01-15          │
├──────────────────────────────────────────────────────────┤
│ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐        │
│ │ [image] │ │ [image] │ │ [image] │ │ [image] │        │
│ │ 150x150 │ │ 150x150 │ │ 150x150 │ │ 150x150 │        │
│ │         │ │         │ │         │ │         │        │
│ ├─────────┤ ├─────────┤ ├─────────┤ ├─────────┤        │
│ │IMG_001  │ │IMG_002  │ │IMG_003  │ │IMG_004  │        │
│ │🛡️❌ [30px]│ │🛡️❌ [30px]│ │🛡️❌ [30px]│ │🛡️❌ [30px]│   ← TOO SMALL!
│ └─────────┘ └─────────┘ └─────────┘ └─────────┘        │
└──────────────────────────────────────────────────────────┘
Issues: Buttons barely visible, unclear selection state
```

#### PROPOSED LAYOUT (Solution)
```
┌──────────────────────────────────────────────────────────┐
│ 📸 Group 1: 6 photos • Same location • Jan 15, 2024     │
│ Status: 4 keep (default), 2 marked for deletion         │
├──────────────────────────────────────────────────────────┤
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐        │
│ │ [image]  🔍 │ │ [image]  🔍 │ │ [image]  🔍 │        │
│ │             │ │             │ │             │        │
│ │   180x180   │ │   180x180   │ │   180x180   │        │
│ │             │ │             │ │             │        │
│ ├─────────────┤ ├─────────────┤ ├─────────────┤        │
│ │IMG_001.HEIC │ │IMG_002.HEIC │ │IMG_003.HEIC │        │
│ │             │ │             │ │             │        │
│ │[Mark Delete]│ │[Mark Delete]│ │[Mark Delete]│        │
│ │   [60x40]   │ │ [SELECTED]  │ │   [60x40]   │        │
│ └─────────────┘ └─────────────┘ └─────────────┘        │
│ KEEP (DEFAULT)  DELETE MARKED   KEEP (DEFAULT)         │
└──────────────────────────────────────────────────────────┘
Improvements: Large buttons, two clear states, preview icons
```

---

## Visual State Indicators

### Photo Selection States
```
KEEP (Default State):
┌─────────────────┐
│ [photo image]🔍 │ ← Preview icon visible on hover
│                 │
│                 │
├─────────────────┤
│ filename.jpg    │
│                 │
│ [Mark for Delete] │ ← Single action button
└─────────────────┘
Border: 1px solid #e5e7eb
Background: Clean white

DELETE MARKED:
┌─────────────────┐ ← Red 3px border  
│ [photo image]🔍 │ 
│    [MARKED]     │ Background tint: rgba(239, 68, 68, 0.05)
│                 │ Semi-transparent overlay
├─────────────────┤
│ filename.jpg    │
│                 │
│ [Remove Mark]   │ ← Button to unmark
└─────────────────┘
Border: 3px solid #ef4444
Background: Light red tint
```

---

## Filters Page Redesign

### CURRENT FILTERS PAGE
```
┌─ Photo Dedup - Smart Filter Interface ─────────┐
│                                                 │
│ ┌─ Stats Bar ─────────────────────────────────┐ │
│ │ 14,060 Photos  │  2,260 Groups  │  TBD GB  │ │ ← TBD is useless
│ └─────────────────────────────────────────────┘ │
│                                                 │
│ ┌─ Filter Panel ────────────────────────────┐   │
│ │                                           │   │
│ │ Years:  [2025] [2024] [2023] [2022]       │   │ ← Basic layout
│ │                                           │   │
│ │ Priority Levels:  [P1] [P2] [P3] [P4]     │   │
│ │                                           │   │
│ │ File Types:  [HEIC] [JPG] [PNG]           │   │
│ │                                           │   │
│ │ Size Range: [====●════] 5-50 MB           │   │
│ │                                           │   │
│ └───────────────────────────────────────────┘   │
│                                                 │
│ [Apply Filters →]                               │
└─────────────────────────────────────────────────┘
Issues: Flat design, no hierarchy, TBD placeholders
```

### PROPOSED FILTERS PAGE
```
┌─ 🎯 Smart Filters ─────────────────────────────────────┐
│                                                        │
│ ┌─ 📊 Library Overview ────────────────────────────┐   │
│ │ 14,060 Photos • 5.2GB Total • 1.8GB Potential Savings │   │ ← Hide groups count
│ └────────────────────────────────────────────────────┘   │
│                                                        │
│ ┌─ 🎯 Active Filters ──────────────────────────────┐   │
│ │ 2024 • P1-P2 Priority • HEIC+JPG  [Clear All ×] │   │ ← Filter breadcrumb
│ └──────────────────────────────────────────────────┘   │
│                                                        │
│ ┌─ ⚡ Quick Filters ───────────────────────────────┐   │
│ │ 🗓️ Year:                                          │   │
│ │   [2025] [2024✓] [2023] [2022] [All Years]       │   │ ← Visual selection
│ │                                                   │   │
│ │ 🎯 Priority (duplicate likelihood):               │   │
│ │   [P1 High✓] [P2 Medium✓] [P3 Low] [P4 Unlikely]│   │
│ │                                                   │   │
│ │ 📱 File Types:                                    │   │
│ │   [HEIC✓] [JPG✓] [PNG] [Other] [All Types]      │   │
│ └───────────────────────────────────────────────────┘   │
│                                                        │
│ ┌─ ⚙️ Advanced Options ▼ ──────────────────────────┐   │ ← Collapsible
│ │ 📏 File Size: [====●════] 5-50 MB                 │   │
│ │ 📷 Camera: [iPhone 15 Pro ▼]                      │   │
│ │ 📍 Location: [Same location only ☐]               │   │
│ │ ⏱️ Time Range: [Within 30 seconds ▼]             │   │
│ └────────────────────────────────────────────────────┘   │
│                                                        │
│ ┌─ 📊 Results Preview ─────────────────────────────┐   │
│ │ 📷 438 photos match your filters                  │   │ ← Hide groups, show photos count
│ │ 💾 1.2GB potential savings                        │   │
│ └────────────────────────────────────────────────────┘   │
│                                                        │
│ ┌─ Actions ─────────────────────────────────────────┐   │
│ │ [🔍 Review Photos]                                 │   │ ← Single primary action
│ │ [↺ Reset Filters] [📋 Save Filter Set]            │   │
│ └────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────┘
Improvements: Visual hierarchy, live feedback, progressive disclosure
```

---

## Message & Confirmation Redesigns

### Popup Messages: Before vs After

#### 1. Batch Delete Confirmation

**CURRENT (Too verbose):**
```
┌─ Confirm Deletion ─────────────────────────────────┐
│                                                    │
│ Are you sure you want to delete all 15 photos     │
│ marked for deletion? This action cannot be undone. │
│ The photos will be permanently removed from your   │
│ photo library. You can review each photo           │
│ individually before confirming this bulk operation. │
│ Processing time may take several minutes for large │
│ batches. Please ensure you have sufficient storage │
│ space for the deletion process.                    │
│                                                    │
│ Technical details: Photos will be moved to the     │
│ system trash and can be recovered within 30 days   │
│ unless you empty the trash manually.               │
│                                                    │
│ [Review Photos First] [Cancel] [Delete All Photos] │
└────────────────────────────────────────────────────┘
Problems: Way too much text, overwhelming choices
```

**PROPOSED (Concise & clear):**
```
┌─ Mark for Manual Deletion? ─┐
│                              │
│ Mark 15 photos for manual    │
│ deletion?                    │
│                              │
│ [Cancel] [Mark]              │
└──────────────────────────────┘
Improvements: Clear, accurate workflow description
```

#### 2. Processing Complete Message

**CURRENT (Information overload):**
```
┌─ Processing Complete! ─────────────────────────────────┐
│                                                        │
│ ✅ Deletion process completed successfully!            │
│                                                        │
│ Summary Report:                                        │
│ • 12 photos were permanently deleted from your        │
│   photo library                                       │
│ • Space freed: 145.7 MB                              │
│ • Processing time: 3.2 seconds                        │
│ • Success rate: 100% (no errors encountered)          │
│ • Backup status: Photos moved to system trash         │
│                                                        │
│ Next Steps:                                            │
│ You can continue reviewing more photo groups or       │
│ return to the main dashboard to see updated           │
│ statistics. Your library has been optimized and      │
│ duplicate storage has been reduced.                   │
│                                                        │
│ [Continue Reviewing] [Return to Dashboard] [View Log] │
└────────────────────────────────────────────────────────┘
Problems: Too detailed, choice paralysis
```

**PROPOSED (Toast notification):**
```
┌─ Success ───────────────────────────────────────────────────────┐
│ ✅ 12 photos marked for deletion and added to                   │
│ <link>this Photo Album</link> for your final review            │
│ 146 MB freed                                                    │
└─────────────────────────────────────────────────────────────────┘
Auto-dismiss after 4 seconds
Improvements: Clear next steps, actionable link
```

#### 3. Grouping Information Tooltip

**CURRENT (Technical jargon):**
```
┌─ Why are these grouped? ───────────────────────────────┐
│                                                        │
│ This group contains photos that appear to be           │
│ duplicates based on our analysis algorithm:            │
│                                                        │
│ Technical Analysis Results:                            │
│ • Timestamp similarity: Within 30 seconds             │
│ • Location data: GPS coordinates match (±10 meters)   │
│ • File size comparison: Within 5% variance            │
│ • Visual similarity: 85% match confidence             │
│ • EXIF data correlation: Camera settings identical    │
│ • Hash comparison: Partial match detected             │
│                                                        │
│ Algorithm Confidence: 85%                              │
│ Duplicate Probability: High                            │
│ Recommended Action: Review manually                    │
│                                                        │
│ [Show Technical Details] [Mark as Different] [Close]  │
└────────────────────────────────────────────────────────┘
Problems: Too technical, intimidating
```

**PROPOSED (Simple explanation):**
```
┌─ Similar Photos ─────────────┐
│                              │
│ 6 photos taken within        │
│ 30 seconds at the same       │
│ location.                    │
│                              │
│ [Show Details ▼] [Got it]    │
└──────────────────────────────┘
Improvements: Plain language, optional details
```

---

## Interaction Flow Diagrams

### Current Photo Click Behavior (Confusing)
```
User clicks photo
     ↓
Opens large preview
     ↓
User must find tiny toggle buttons
     ↓
Frustration & missed interactions
```

### Proposed Photo Interaction (Intuitive)
```
Single click photo → Toggle keep/delete (primary action)
     ↓
Visual feedback immediate
     ↓
Success!

Alternative flows:
Double click photo → Large preview
Click 🔍 icon → Large preview  
Hover photo → Show preview icon
```

### New Keyboard Navigation Flow
```
Tab → Focus next photo
Enter → Toggle selection  
Space → Toggle selection
Arrow keys → Navigate within group
D key → Mark for deletion
K key → Mark to keep
Escape → Close modals/deselect
```

---

## Color Palette & Design System

### Primary Colors
- **Keep Green**: `#10b981` (Emerald-500)
- **Delete Red**: `#ef4444` (Red-500)  
- **Neutral Gray**: `#6b7280` (Gray-500)
- **Background**: `#f9fafb` (Gray-50)
- **Text Primary**: `#1f2937` (Gray-800)
- **Text Secondary**: `#6b7280` (Gray-500)

### Button States
```css
/* Primary Action Button */
.btn-primary {
  background: #2563eb;
  color: white;
  height: 44px;
  border-radius: 8px;
  font-weight: 600;
  transition: all 0.2s ease;
}

.btn-primary:hover {
  background: #1d4ed8;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
}

/* Keep Button */
.btn-keep {
  background: #10b981;
  border: 2px solid #059669;
}

.btn-keep:hover {
  background: #059669;
  transform: scale(1.05);
}

/* Delete Button */  
.btn-delete {
  background: #ef4444;
  border: 2px solid #dc2626;
}

.btn-delete:hover {
  background: #dc2626;
  transform: scale(1.05);
}
```

This comprehensive wireframe and design specification provides clear direction for implementing the UX improvements while maintaining the app's functionality and adding intuitive user interactions.