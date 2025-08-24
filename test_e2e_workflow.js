/**
 * End-to-End Workflow Test Suite
 * Tests the complete user workflow: selection → summary → confirmation → deletion
 */

// Mock data structure to simulate photo groups (same as in app)
const testGroups = [
    {
        group_id: "group1",
        photos: [
            { uuid: "photo1", filename: "IMG_001.jpg", recommended: true },
            { uuid: "photo2", filename: "IMG_002.jpg", recommended: false }
        ]
    },
    {
        group_id: "group2", 
        photos: [
            { uuid: "photo3", filename: "IMG_003.jpg", recommended: false },
            { uuid: "photo4", filename: "IMG_004.jpg", recommended: true },
            { uuid: "photo5", filename: "IMG_005.jpg", recommended: false }
        ]
    }
];

// Simulate the photoSelections global variable (inverted model: selected = DELETE)
let photoSelections = {};

// Simulate the button functions (extracted from app.py logic)
function keepAllPhotos(groupId) {
    // Keep all photos (select NONE for deletion)
    photoSelections[groupId] = [];
}

function deleteAllButOne(groupId) {
    // Delete all except recommended photo (select all EXCEPT recommended for deletion)
    const group = testGroups.find(g => g.group_id === groupId);
    if (group) {
        const recommendedPhoto = group.photos.find(photo => photo.recommended);
        const photoToKeep = recommendedPhoto || group.photos[0];
        
        // Select all photos EXCEPT the one to keep
        photoSelections[groupId] = group.photos
            .filter(photo => photo.uuid !== photoToKeep.uuid)
            .map(photo => photo.uuid);
    }
}

function deleteAllPhotos(groupId) {
    // Delete all photos in the group (select ALL for deletion)
    const group = testGroups.find(g => g.group_id === groupId);
    if (group) {
        photoSelections[groupId] = group.photos.map(photo => photo.uuid);
    }
}

function togglePhotoSelection(groupId, photoUuid) {
    // Toggle individual photo selection for deletion
    if (!photoSelections[groupId]) {
        photoSelections[groupId] = [];
    }
    
    const selections = photoSelections[groupId];
    const index = selections.indexOf(photoUuid);
    
    if (index === -1) {
        // Add to deletion selection (mark for DELETE)
        selections.push(photoUuid);
    } else {
        // Remove from deletion selection (mark for KEEP)
        selections.splice(index, 1);
    }
}

function getPhotoState(groupId, photoUuid) {
    const selections = photoSelections[groupId] || [];
    return selections.includes(photoUuid) ? "DELETE" : "KEEP";
}

// CRITICAL: Selection Summary Logic (should match app.py exactly)
function getSelectionSummary() {
    let totalPhotosToDelete = 0;
    let totalSavings = 0;
    const groupSummaries = [];
    
    Object.keys(photoSelections).forEach(groupId => {
        const group = testGroups.find(g => g.group_id === groupId);
        if (!group) return;
        
        const selectedPhotos = photoSelections[groupId] || [];
        
        // CRITICAL: In inverted model, selected photos = photos to DELETE
        const photosToDelete = group.photos.filter(photo => 
            selectedPhotos.includes(photo.uuid)
        );
        
        if (photosToDelete.length > 0) {
            totalPhotosToDelete += photosToDelete.length;
            // Mock file size calculation
            totalSavings += photosToDelete.length * 2.5; // 2.5MB per photo
            
            groupSummaries.push({
                groupId,
                deleteCount: photosToDelete.length,
                totalCount: group.photos.length,
                deletePhotos: photosToDelete.map(p => p.filename)
            });
        }
    });
    
    return {
        totalPhotosToDelete,
        totalSavings: totalSavings.toFixed(1),
        groupSummaries
    };
}

// CRITICAL: Deletion Confirmation Logic (should match app.py exactly)
function generateDeletionSummary() {
    const summary = [];
    
    Object.keys(photoSelections).forEach(groupId => {
        const group = testGroups.find(g => g.group_id === groupId);
        if (!group) return;
        
        const selectedPhotos = photoSelections[groupId] || [];
        
        // CRITICAL: In inverted model, selected photos = photos to DELETE
        const photosToDelete = group.photos.filter(photo => 
            selectedPhotos.includes(photo.uuid)
        );
        
        if (photosToDelete.length > 0) {
            summary.push({
                group_id: groupId,
                photos_to_delete: photosToDelete.map(p => ({
                    uuid: p.uuid,
                    filename: p.filename
                })),
                photos_to_keep: group.photos.filter(photo => 
                    !selectedPhotos.includes(photo.uuid)
                ).map(p => ({
                    uuid: p.uuid, 
                    filename: p.filename
                }))
            });
        }
    });
    
    return summary;
}

// Test Suite Functions
function runEndToEndTests() {
    console.log("🧪 Running End-to-End Workflow Test Suite");
    console.log("=============================================");
    
    testScenario1_IndividualSelection();
    testScenario2_ButtonActions();
    testScenario3_MixedActions();
    testScenario4_NoSelections();
    testScenario5_AllSelected();
    
    console.log("=============================================");
    console.log("✅ All end-to-end workflow tests completed!");
}

function testScenario1_IndividualSelection() {
    console.log("\n📋 Scenario 1: Individual Photo Selection");
    
    // Reset
    photoSelections = {};
    testGroups.forEach(group => {
        photoSelections[group.group_id] = [];
    });
    
    console.log("Initial: All photos KEEP");
    printSelectionStates();
    
    // Select photo2 for deletion
    togglePhotoSelection("group1", "photo2");
    console.log("\nAfter selecting photo2 for deletion:");
    printSelectionStates();
    
    // Verify selection summary
    const summary1 = getSelectionSummary();
    console.log(`Selection Summary: ${summary1.totalPhotosToDelete} photos to delete`);
    assert(summary1.totalPhotosToDelete === 1, "Should have 1 photo to delete");
    assert(summary1.groupSummaries[0].deletePhotos[0] === "IMG_002.jpg", "Should delete IMG_002.jpg");
    
    // Verify deletion confirmation
    const deletionSummary1 = generateDeletionSummary();
    console.log("Deletion Summary:");
    deletionSummary1.forEach(group => {
        console.log(`  Group ${group.group_id}: Delete ${group.photos_to_delete.length}, Keep ${group.photos_to_keep.length}`);
        console.log(`    Delete: ${group.photos_to_delete.map(p => p.filename).join(", ")}`);
        console.log(`    Keep: ${group.photos_to_keep.map(p => p.filename).join(", ")}`);
    });
    
    assert(deletionSummary1.length === 1, "Should have 1 group with deletions");
    assert(deletionSummary1[0].photos_to_delete.length === 1, "Should delete 1 photo");
    assert(deletionSummary1[0].photos_to_delete[0].filename === "IMG_002.jpg", "Should delete IMG_002.jpg");
    assert(deletionSummary1[0].photos_to_keep[0].filename === "IMG_001.jpg", "Should keep IMG_001.jpg");
    
    console.log("✅ Scenario 1 PASSED");
}

function testScenario2_ButtonActions() {
    console.log("\n📋 Scenario 2: Button Actions");
    
    // Reset
    photoSelections = {};
    testGroups.forEach(group => {
        photoSelections[group.group_id] = [];
    });
    
    // Test "Delete Duplicates" button
    deleteAllButOne("group2");
    console.log("After 'Delete Duplicates' on group2 (keep recommended photo4):");
    printGroupSelectionStates("group2");
    
    const summary2 = getSelectionSummary();
    console.log(`Selection Summary: ${summary2.totalPhotosToDelete} photos to delete`);
    assert(summary2.totalPhotosToDelete === 2, "Should have 2 photos to delete (photo3, photo5)");
    
    const deletionSummary2 = generateDeletionSummary();
    const group2Summary = deletionSummary2.find(g => g.group_id === "group2");
    assert(group2Summary.photos_to_delete.length === 2, "Should delete 2 photos");
    assert(group2Summary.photos_to_keep.length === 1, "Should keep 1 photo");
    assert(group2Summary.photos_to_keep[0].filename === "IMG_004.jpg", "Should keep recommended IMG_004.jpg");
    
    console.log("✅ Scenario 2 PASSED");
}

function testScenario3_MixedActions() {
    console.log("\n📋 Scenario 3: Mixed Button + Individual Actions");
    
    // Reset
    photoSelections = {};
    testGroups.forEach(group => {
        photoSelections[group.group_id] = [];
    });
    
    // Apply Delete Duplicates to group1
    deleteAllButOne("group1");
    console.log("After 'Delete Duplicates' on group1:");
    printGroupSelectionStates("group1");
    
    // Then manually toggle the recommended photo to DELETE
    togglePhotoSelection("group1", "photo1"); // photo1 is recommended
    console.log("After manually toggling recommended photo1 to DELETE:");
    printGroupSelectionStates("group1");
    
    const summary3 = getSelectionSummary();
    console.log(`Selection Summary: ${summary3.totalPhotosToDelete} photos to delete`);
    assert(summary3.totalPhotosToDelete === 2, "Should have 2 photos to delete (both in group1)");
    
    const deletionSummary3 = generateDeletionSummary();
    const group1Summary = deletionSummary3.find(g => g.group_id === "group1");
    assert(group1Summary.photos_to_delete.length === 2, "Should delete all 2 photos");
    assert(group1Summary.photos_to_keep.length === 0, "Should keep 0 photos");
    
    console.log("✅ Scenario 3 PASSED");
}

function testScenario4_NoSelections() {
    console.log("\n📋 Scenario 4: No Photos Selected for Deletion");
    
    // Reset - all photos kept
    photoSelections = {};
    testGroups.forEach(group => {
        photoSelections[group.group_id] = [];
    });
    
    console.log("All photos in KEEP state:");
    printSelectionStates();
    
    const summary4 = getSelectionSummary();
    console.log(`Selection Summary: ${summary4.totalPhotosToDelete} photos to delete`);
    assert(summary4.totalPhotosToDelete === 0, "Should have 0 photos to delete");
    
    const deletionSummary4 = generateDeletionSummary();
    assert(deletionSummary4.length === 0, "Should have no groups with deletions");
    
    console.log("✅ Scenario 4 PASSED");
}

function testScenario5_AllSelected() {
    console.log("\n📋 Scenario 5: All Photos Selected for Deletion");
    
    // Reset
    photoSelections = {};
    
    // Select all photos for deletion
    testGroups.forEach(group => {
        deleteAllPhotos(group.group_id);
    });
    
    console.log("All photos selected for deletion:");
    printSelectionStates();
    
    const summary5 = getSelectionSummary();
    console.log(`Selection Summary: ${summary5.totalPhotosToDelete} photos to delete`);
    assert(summary5.totalPhotosToDelete === 5, "Should have all 5 photos to delete");
    
    const deletionSummary5 = generateDeletionSummary();
    assert(deletionSummary5.length === 2, "Should have 2 groups with deletions");
    
    let totalToDelete = 0;
    let totalToKeep = 0;
    deletionSummary5.forEach(group => {
        totalToDelete += group.photos_to_delete.length;
        totalToKeep += group.photos_to_keep.length;
    });
    
    assert(totalToDelete === 5, "Should delete all 5 photos");
    assert(totalToKeep === 0, "Should keep 0 photos");
    
    console.log("✅ Scenario 5 PASSED");
}

// Helper functions
function printSelectionStates() {
    testGroups.forEach(group => {
        console.log(`  Group ${group.group_id}:`);
        group.photos.forEach(photo => {
            const state = getPhotoState(group.group_id, photo.uuid);
            const icon = state === "DELETE" ? "❌" : "🛡️";
            console.log(`    ${photo.filename}: ${icon} ${state}`);
        });
    });
}

function printGroupSelectionStates(groupId) {
    const group = testGroups.find(g => g.group_id === groupId);
    if (!group) return;
    
    console.log(`  Group ${group.group_id}:`);
    group.photos.forEach(photo => {
        const state = getPhotoState(group.group_id, photo.uuid);
        const icon = state === "DELETE" ? "❌" : "🛡️";
        const badge = photo.recommended ? " (recommended)" : "";
        console.log(`    ${photo.filename}: ${icon} ${state}${badge}`);
    });
}

function assert(condition, message) {
    if (!condition) {
        console.error(`❌ ASSERTION FAILED: ${message}`);
        throw new Error(message);
    }
}

// Run the comprehensive end-to-end tests
runEndToEndTests();