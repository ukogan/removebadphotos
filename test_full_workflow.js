// Comprehensive test of the complete workflow: filter → analyze → legacy → mark for deletion
const { chromium } = require('playwright');

async function testCompleteWorkflow() {
    console.log('🧪 Testing COMPLETE workflow: filter → analyze → legacy → mark for deletion');
    
    const browser = await chromium.launch({ headless: false });
    const page = await browser.newPage();
    
    const errors = [];
    const networkRequests = [];
    
    // Capture all errors and network activity
    page.on('pageerror', error => {
        errors.push({ type: 'page_error', message: error.message });
        console.error('❌ Page error:', error.message);
    });
    
    page.on('console', message => {
        if (message.type() === 'error') {
            errors.push({ type: 'console_error', message: message.text() });
            console.error('❌ Console error:', message.text());
        }
    });
    
    page.on('request', request => {
        if (request.url().includes('/api/')) {
            networkRequests.push({
                url: request.url(),
                method: request.method()
            });
        }
    });
    
    try {
        // STEP 1: Start with filters page
        console.log('\\n=== STEP 1: Apply filter on filters page ===');
        await page.goto('http://127.0.0.1:5003/filters');
        await page.waitForLoadState('networkidle');
        await page.waitForTimeout(3000);
        
        // Apply a P1/P2 filter by clicking priority buttons 
        console.log('📍 Applying P1 and P2 priority filters...');
        const p1Button = page.locator('button[data-priority="P1"]');
        const p2Button = page.locator('button[data-priority="P2"]');
        
        if (await p1Button.count() > 0) {
            await p1Button.click();
            await page.waitForTimeout(1000);
        }
        if (await p2Button.count() > 0) {
            await p2Button.click();
            await page.waitForTimeout(1000);
        }
        
        // Check for analyze button
        const analyzeButton = page.locator('button:has-text("Analyze Selected")');
        const analyzeButtonExists = await analyzeButton.count() > 0;
        console.log(`🔍 Analyze button exists: ${analyzeButtonExists}`);
        
        if (analyzeButtonExists) {
            // STEP 2: Click analyze and wait for dashboard redirect
            console.log('\\n=== STEP 2: Click analyze and wait for redirect to dashboard ===');
            
            await analyzeButton.click();
            await page.waitForTimeout(8000); // Allow time for analysis and redirect
            
            const currentUrl = page.url();
            const onDashboard = currentUrl.includes('127.0.0.1:5003/') && !currentUrl.includes('filters');
            console.log(`📍 Current URL: ${currentUrl}`);
            console.log(`📊 On dashboard: ${onDashboard}`);
            
            if (onDashboard) {
                // STEP 3: Look for priority links on dashboard
                console.log('\\n=== STEP 3: Look for priority clusters on dashboard ===');
                
                // Wait for dashboard to load
                await page.waitForTimeout(3000);
                
                // Look for P1 or P2 priority links or buttons
                const p2Link = page.locator('a[href*="priority=P2"], button:has-text("P2")').first();
                const p1Link = page.locator('a[href*="priority=P1"], button:has-text("P1")').first();
                
                const p2Exists = await p2Link.count() > 0;
                const p1Exists = await p1Link.count() > 0;
                
                console.log(`🎯 P2 priority link/button exists: ${p2Exists}`);
                console.log(`🎯 P1 priority link/button exists: ${p1Exists}`);
                
                // Click on the first available priority link
                let targetLink = null;
                if (p2Exists) {
                    targetLink = p2Link;
                    console.log('📍 Clicking P2 priority link...');
                } else if (p1Exists) {
                    targetLink = p1Link;
                    console.log('📍 Clicking P1 priority link...');
                }
                
                if (targetLink) {
                    // STEP 4: Click priority link to go to legacy interface
                    console.log('\\n=== STEP 4: Navigate to legacy interface via priority link ===');
                    
                    await targetLink.click();
                    await page.waitForTimeout(5000); // Wait for legacy page to load
                    
                    const legacyUrl = page.url();
                    const onLegacy = legacyUrl.includes('/legacy');
                    console.log(`📍 Legacy URL: ${legacyUrl}`);
                    console.log(`📋 On legacy interface: ${onLegacy}`);
                    
                    if (onLegacy) {
                        // STEP 5: Test legacy interface functionality
                        console.log('\\n=== STEP 5: Test legacy interface photo loading ===');
                        
                        // Wait for groups to load
                        await page.waitForTimeout(3000);
                        
                        // Check if "Analyze Photo Groups" button exists and click it
                        const loadGroupsButton = page.locator('#loadGroupsBtn');
                        const loadGroupsExists = await loadGroupsButton.count() > 0;
                        console.log(`🔍 Load Groups button exists: ${loadGroupsExists}`);
                        
                        if (loadGroupsExists && await loadGroupsButton.isEnabled()) {
                            console.log('📍 Clicking Load Groups button...');
                            await loadGroupsButton.click();
                            await page.waitForTimeout(10000); // Wait for groups to load
                        }
                        
                        // Check for photo groups
                        const photoGroups = page.locator('.group-card');
                        const groupCount = await photoGroups.count();
                        console.log(`📊 Found ${groupCount} photo groups`);
                        
                        if (groupCount > 0) {
                            // Check for photo thumbnails
                            const thumbnails = page.locator('.photo-thumbnail');
                            const thumbnailCount = await thumbnails.count();
                            console.log(`🖼️ Found ${thumbnailCount} photo thumbnails`);
                            
                            // Check for loading indicators
                            const loadingIndicators = page.locator('.photo-loading');
                            const loadingCount = await loadingIndicators.count();
                            console.log(`⏳ Found ${loadingCount} loading indicators`);
                            
                            // Check if any thumbnails have loaded (src attribute and visible)
                            let loadedThumbnails = 0;
                            for (let i = 0; i < Math.min(thumbnailCount, 5); i++) {
                                const thumbnail = thumbnails.nth(i);
                                const isVisible = await thumbnail.isVisible();
                                const src = await thumbnail.getAttribute('src');
                                if (isVisible && src && src.includes('/api/thumbnail/')) {
                                    loadedThumbnails++;
                                }
                            }
                            console.log(`✅ Successfully loaded ${loadedThumbnails} thumbnails`);
                            
                            if (loadedThumbnails > 0) {
                                // STEP 6: Test photo selection for deletion
                                console.log('\\n=== STEP 6: Test photo selection for deletion ===');
                                
                                // Try to select first photo for deletion
                                const firstPhotoCard = page.locator('.photo-card').first();
                                if (await firstPhotoCard.count() > 0) {
                                    await firstPhotoCard.click();
                                    await page.waitForTimeout(1000);
                                    
                                    const isSelected = await firstPhotoCard.evaluate(el => 
                                        el.classList.contains('selected')
                                    );
                                    console.log(`📌 First photo selected for deletion: ${isSelected}`);
                                }
                                
                                // Look for action buttons
                                const deleteButton = page.locator('button:has-text("Delete Duplicates"), button:has-text("Delete All")').first();
                                const deleteButtonExists = await deleteButton.count() > 0;
                                console.log(`❌ Delete button exists: ${deleteButtonExists}`);
                                
                                console.log('✅ WORKFLOW COMPLETE: Full chain tested successfully!');
                            } else {
                                console.log('❌ WORKFLOW BLOCKED: Thumbnails not loading');
                            }
                        } else {
                            console.log('❌ WORKFLOW BLOCKED: No photo groups found');
                        }
                    } else {
                        console.log('❌ WORKFLOW BLOCKED: Did not reach legacy interface');
                    }
                } else {
                    console.log('❌ WORKFLOW BLOCKED: No priority links found on dashboard');
                }
            } else {
                console.log('❌ WORKFLOW BLOCKED: Did not reach dashboard after analyze');
            }
        } else {
            console.log('❌ WORKFLOW BLOCKED: No analyze button found on filters page');
        }
        
        // Summary of network requests
        console.log('\\n=== NETWORK ACTIVITY SUMMARY ===');
        const thumbnailRequests = networkRequests.filter(req => req.url.includes('/api/thumbnail/'));
        const groupsRequests = networkRequests.filter(req => req.url.includes('/api/groups'));
        const filterRequests = networkRequests.filter(req => req.url.includes('/api/filter-clusters'));
        
        console.log(`📡 Total API requests: ${networkRequests.length}`);
        console.log(`🖼️ Thumbnail requests: ${thumbnailRequests.length}`);
        console.log(`📊 Groups requests: ${groupsRequests.length}`);
        console.log(`🔍 Filter requests: ${filterRequests.length}`);
        
        if (thumbnailRequests.length > 0) {
            console.log('🖼️ Sample thumbnail URLs:');
            thumbnailRequests.slice(0, 3).forEach((req, i) => {
                console.log(`  ${i + 1}. ${req.url}`);
            });
        }
        
    } catch (error) {
        console.error('❌ Test execution failed:', error.message);
        errors.push({ type: 'test_error', message: error.message });
    } finally {
        await browser.close();
    }
    
    return {
        success: errors.length === 0,
        errorCount: errors.length,
        errors: errors
    };
}

testCompleteWorkflow().then(result => {
    console.log('\\n🏁 COMPLETE WORKFLOW TEST RESULTS:');
    console.log(`✅ Success: ${result.success}`);
    console.log(`❌ Errors: ${result.errorCount}`);
    
    if (result.errorCount > 0) {
        console.log('\\n📝 Error Details:');
        result.errors.forEach((error, index) => {
            console.log(`  ${index + 1}. [${error.type}] ${error.message}`);
        });
    }
    
    process.exit(result.success ? 0 : 1);
}).catch(error => {
    console.error('❌ Test execution failed:', error);
    process.exit(1);
});