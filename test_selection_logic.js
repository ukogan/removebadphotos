/**
 * Selection Logic Test Suite
 * Tests all combinations of photo selection states and button actions
 */

// Mock data structure to simulate photo groups
const testGroups = [
    {
        group_id: "group1",
        photos: [
            { uuid: "photo1", recommended: true },
            { uuid: "photo2", recommended: false },
            { uuid: "photo3", recommended: false }
        ]
    },
    {
        group_id: "group2", 
        photos: [
            { uuid: "photo4", recommended: false },
            { uuid: "photo5", recommended: true },
            { uuid: "photo6", recommended: false },
            { uuid: "photo7", recommended: false }
        ]
    }
];

// Simulate the photoSelections global variable
let photoSelections = {};

// Simulate the button functions (extracted from app.py logic)
function keepAllPhotos(groupId) {
    // Keep all photos (select NONE for deletion)
    const group = testGroups.find(g => g.group_id === groupId);
    if (group) {
        photoSelections[groupId] = [];
    }
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

function togglePhoto(groupId, photoUuid) {
    // Toggle individual photo selection for deletion
    if (!photoSelections[groupId]) {
        photoSelections[groupId] = [];
    }
    
    const selections = photoSelections[groupId];
    const index = selections.indexOf(photoUuid);
    
    if (index === -1) {
        // Add to deletion selection
        selections.push(photoUuid);
    } else {
        // Remove from deletion selection  
        selections.splice(index, 1);
    }
}

function getPhotoState(groupId, photoUuid) {
    const selections = photoSelections[groupId] || [];
    return selections.includes(photoUuid) ? "DELETE" : "KEEP";
}

// Test Suite Functions
function runAllTests() {
    console.log("🧪 Running Selection Logic Test Suite");
    console.log("=====================================");
    
    testInitialState();
    testKeepAllButton();
    testDeleteDuplicatesButton();  
    testDeleteAllButton();
    testIndividualToggle();
    testComplexScenario();
    
    console.log("=====================================");
    console.log("✅ All tests completed!");
}

function testInitialState() {
    console.log("\n📋 Test 1: Initial State");
    
    // Reset selections
    photoSelections = {};
    
    // Initialize groups with no selections (as per new logic)
    testGroups.forEach(group => {
        photoSelections[group.group_id] = [];
    });
    
    // Verify initial state - all photos should be KEEP
    testGroups.forEach(group => {
        group.photos.forEach(photo => {
            const state = getPhotoState(group.group_id, photo.uuid);
            console.log(`   ${photo.uuid}: ${state} ${photo.recommended ? '⭐' : ''}`);
            assert(state === "KEEP", `${photo.uuid} should be KEEP initially`);
        });
    });
    
    console.log("✅ Test 1 PASSED: All photos start as KEEP");
}

function testKeepAllButton() {
    console.log("\n📋 Test 2: Keep All Button");
    
    // Start with some photos selected for deletion
    photoSelections = {
        "group1": ["photo2", "photo3"],
        "group2": ["photo4", "photo6"]
    };
    
    console.log("Before Keep All:");
    printGroupStates("group1");
    
    // Click Keep All
    keepAllPhotos("group1");
    
    console.log("After Keep All group1:");
    printGroupStates("group1");
    
    // Verify all photos in group1 are now KEEP
    testGroups[0].photos.forEach(photo => {
        const state = getPhotoState("group1", photo.uuid);
        assert(state === "KEEP", `${photo.uuid} should be KEEP after Keep All`);
    });
    
    // Verify group2 is unchanged
    assert(getPhotoState("group2", "photo4") === "DELETE", "group2 should be unchanged");
    
    console.log("✅ Test 2 PASSED: Keep All clears all deletions for group");
}

function testDeleteDuplicatesButton() {
    console.log("\n📋 Test 3: Delete Duplicates Button");
    
    // Reset to all keep
    photoSelections = {
        "group1": [],
        "group2": []
    };
    
    console.log("Before Delete Duplicates:");
    printGroupStates("group1");
    
    // Click Delete Duplicates (keep only recommended)
    deleteAllButOne("group1");
    
    console.log("After Delete Duplicates group1:");
    printGroupStates("group1");
    
    // Verify: recommended photo is KEEP, others are DELETE
    testGroups[0].photos.forEach(photo => {
        const state = getPhotoState("group1", photo.uuid);
        const expectedState = photo.recommended ? "KEEP" : "DELETE";
        console.log(`   Expected: ${photo.uuid} = ${expectedState}, Actual: ${state}`);
        assert(state === expectedState, `${photo.uuid} should be ${expectedState}`);
    });
    
    console.log("✅ Test 3 PASSED: Delete Duplicates keeps only recommended photo");
}

function testDeleteAllButton() {
    console.log("\n📋 Test 4: Delete All Button");
    
    // Start with mixed selections
    photoSelections = {
        "group1": ["photo2"], // Some selected for deletion
        "group2": []         // All kept
    };
    
    console.log("Before Delete All:");
    printGroupStates("group1");
    
    // Click Delete All
    deleteAllPhotos("group1");
    
    console.log("After Delete All group1:");
    printGroupStates("group1");
    
    // Verify all photos are DELETE
    testGroups[0].photos.forEach(photo => {
        const state = getPhotoState("group1", photo.uuid);
        assert(state === "DELETE", `${photo.uuid} should be DELETE after Delete All`);
    });
    
    console.log("✅ Test 4 PASSED: Delete All marks all photos for deletion");
}

function testIndividualToggle() {
    console.log("\n📋 Test 5: Individual Photo Toggle");
    
    // Start with all KEEP
    photoSelections = { "group1": [] };
    
    console.log("Initial state - all KEEP:");
    printGroupStates("group1");
    
    // Toggle photo2 to DELETE
    togglePhoto("group1", "photo2");
    console.log("After toggling photo2 to DELETE:");
    printGroupStates("group1");
    assert(getPhotoState("group1", "photo2") === "DELETE", "photo2 should be DELETE");
    assert(getPhotoState("group1", "photo1") === "KEEP", "photo1 should remain KEEP");
    
    // Toggle photo2 back to KEEP
    togglePhoto("group1", "photo2");
    console.log("After toggling photo2 back to KEEP:");
    printGroupStates("group1");
    assert(getPhotoState("group1", "photo2") === "KEEP", "photo2 should be KEEP again");
    
    // Toggle multiple photos
    togglePhoto("group1", "photo1");
    togglePhoto("group1", "photo3");
    console.log("After toggling photo1 and photo3 to DELETE:");
    printGroupStates("group1");
    assert(getPhotoState("group1", "photo1") === "DELETE", "photo1 should be DELETE");
    assert(getPhotoState("group1", "photo3") === "DELETE", "photo3 should be DELETE");
    assert(getPhotoState("group1", "photo2") === "KEEP", "photo2 should remain KEEP");
    
    console.log("✅ Test 5 PASSED: Individual toggles work correctly");
}

function testComplexScenario() {
    console.log("\n📋 Test 6: Complex Scenario - Button + Individual Actions");
    
    // Start fresh
    photoSelections = { "group1": [] };
    
    console.log("1. Start with all KEEP:");
    printGroupStates("group1");
    
    // Apply Delete Duplicates 
    deleteAllButOne("group1");
    console.log("2. After Delete Duplicates (keep recommended only):");
    printGroupStates("group1");
    
    // Toggle the recommended photo to DELETE
    togglePhoto("group1", "photo1"); // photo1 is recommended
    console.log("3. After manually toggling recommended photo to DELETE:");
    printGroupStates("group1");
    assert(getPhotoState("group1", "photo1") === "DELETE", "Recommended photo should be DELETE");
    
    // Toggle one non-recommended back to KEEP
    togglePhoto("group1", "photo2");
    console.log("4. After toggling photo2 back to KEEP:");
    printGroupStates("group1");
    assert(getPhotoState("group1", "photo2") === "KEEP", "photo2 should be KEEP");
    assert(getPhotoState("group1", "photo3") === "DELETE", "photo3 should still be DELETE");
    
    // Apply Keep All to reset
    keepAllPhotos("group1");
    console.log("5. After Keep All reset:");
    printGroupStates("group1");
    testGroups[0].photos.forEach(photo => {
        assert(getPhotoState("group1", photo.uuid) === "KEEP", `${photo.uuid} should be KEEP after reset`);
    });
    
    console.log("✅ Test 6 PASSED: Complex interactions work correctly");
}

// Helper functions
function printGroupStates(groupId) {
    const group = testGroups.find(g => g.group_id === groupId);
    if (!group) return;
    
    group.photos.forEach(photo => {
        const state = getPhotoState(groupId, photo.uuid);
        const badge = photo.recommended ? " ⭐" : "";
        const stateIcon = state === "DELETE" ? "❌" : "🛡️";
        console.log(`   ${photo.uuid}: ${stateIcon} ${state}${badge}`);
    });
}

function assert(condition, message) {
    if (!condition) {
        console.error(`❌ ASSERTION FAILED: ${message}`);
        throw new Error(message);
    }
}

// Run the tests
runAllTests();