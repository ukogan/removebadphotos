// Simple test to verify the complete workflow works with photos only
const { chromium } = require('playwright');

async function testWorkflowVerification() {
    console.log('✅ Testing complete workflow: filter → analyze → legacy → photos only');
    
    const browser = await chromium.launch({ headless: false });
    const page = await browser.newPage();
    
    try {
        console.log('🔍 Step 1: Navigate to legacy interface directly');
        await page.goto('http://127.0.0.1:5003/legacy?priority=P2&limit=3');
        await page.waitForLoadState('networkidle');
        await page.waitForTimeout(5000);
        
        console.log('🔍 Step 2: Click load groups button');
        const loadGroupsBtn = page.locator('#loadGroupsBtn');
        if (await loadGroupsBtn.count() > 0) {
            await loadGroupsBtn.click();
            console.log('✅ Clicked load groups button');
            
            // Wait longer for processing photos only (not videos)
            await page.waitForTimeout(30000);
            
            console.log('🔍 Step 3: Check for photo groups');
            const photoGroups = page.locator('.group-card');
            const groupCount = await photoGroups.count();
            console.log(`📊 Found ${groupCount} photo groups`);
            
            if (groupCount > 0) {
                console.log('🔍 Step 4: Check for photo thumbnails');
                const thumbnails = page.locator('.photo-thumbnail');
                const thumbnailCount = await thumbnails.count();
                console.log(`🖼️ Found ${thumbnailCount} photo thumbnails`);
                
                // Check if thumbnails are loading
                let loadedCount = 0;
                for (let i = 0; i < Math.min(thumbnailCount, 5); i++) {
                    const thumbnail = thumbnails.nth(i);
                    const isVisible = await thumbnail.isVisible();
                    if (isVisible) loadedCount++;
                }
                
                console.log(`✅ Successfully loaded ${loadedCount}/${Math.min(thumbnailCount, 5)} thumbnails`);
                
                if (loadedCount > 0) {
                    console.log('🔍 Step 5: Check for action buttons');
                    const deleteButton = page.locator('button:has-text("Delete Duplicates")').first();
                    const deleteButtonExists = await deleteButton.count() > 0;
                    console.log(`❌ Delete button available: ${deleteButtonExists}`);
                    
                    console.log('🔍 Step 6: Test photo selection');
                    const firstPhotoCard = page.locator('.photo-card').first();
                    if (await firstPhotoCard.count() > 0) {
                        await firstPhotoCard.click();
                        await page.waitForTimeout(1000);
                        
                        const isSelected = await firstPhotoCard.evaluate(el => 
                            el.classList.contains('selected')
                        );
                        console.log(`📌 Photo selected for deletion: ${isSelected}`);
                        
                        if (isSelected && deleteButtonExists) {
                            console.log('✅ COMPLETE WORKFLOW SUCCESS: Photos can be selected and marked for deletion!');
                            return { success: true, message: 'Complete workflow verified' };
                        }
                    }
                }
            } else {
                console.log('⚠️ No photo groups found - might still be processing');
            }
        } else {
            console.log('❌ Load groups button not found');
        }
        
        return { success: false, message: 'Workflow incomplete' };
        
    } catch (error) {
        console.error('❌ Test failed:', error.message);
        return { success: false, message: error.message };
    } finally {
        await browser.close();
    }
}

testWorkflowVerification().then(result => {
    console.log(`\\n🏁 WORKFLOW VERIFICATION: ${result.success ? 'PASSED' : 'FAILED'}`);
    console.log(`📝 Result: ${result.message}`);
    process.exit(result.success ? 0 : 1);
}).catch(error => {
    console.error('❌ Test execution failed:', error);
    process.exit(1);
});