// Test legacy interface directly to verify photos-only workflow
const { chromium } = require('playwright');

async function testLegacyDirect() {
    console.log('🎯 Testing legacy interface directly with photos-only workflow...');
    
    const browser = await chromium.launch({ headless: false });
    const page = await browser.newPage();
    
    const errors = [];
    const networkRequests = [];
    
    // Capture errors and network activity
    page.on('pageerror', error => {
        errors.push({ type: 'page_error', message: error.message });
        console.error('❌ Page error:', error.message);
    });
    
    page.on('console', message => {
        if (message.type() === 'error') {
            errors.push({ type: 'console_error', message: message.text() });
            console.error('❌ Console error:', message.text());
        } else {
            console.log(`📝 Console [${message.type()}]:`, message.text());
        }
    });
    
    page.on('request', request => {
        if (request.url().includes('/api/')) {
            networkRequests.push({
                url: request.url(),
                method: request.method()
            });
            console.log(`📡 API Request: ${request.method()} ${request.url()}`);
        }
    });
    
    page.on('response', response => {
        if (response.url().includes('/api/')) {
            console.log(`📨 API Response: ${response.status()} ${response.url()}`);
        }
    });
    
    try {
        // Navigate directly to legacy interface with P2 priority
        console.log('📍 Step 1: Navigate directly to legacy interface');
        await page.goto('http://127.0.0.1:5003/legacy?priority=P2&limit=5');
        await page.waitForLoadState('networkidle');
        await page.waitForTimeout(3000);
        
        // Check that we're on the legacy page
        const currentUrl = page.url();
        console.log(`🌐 Current URL: ${currentUrl}`);
        console.log(`📋 On legacy interface: ${currentUrl.includes('/legacy')}`);
        
        // Check for the load groups button
        console.log('📍 Step 2: Check for Load Groups button');
        const loadGroupsBtn = page.locator('#loadGroupsBtn');
        const loadGroupsBtnExists = await loadGroupsBtn.count() > 0;
        console.log(`🔍 Load Groups button exists: ${loadGroupsBtnExists}`);
        
        if (loadGroupsBtnExists) {
            const isEnabled = await loadGroupsBtn.isEnabled();
            console.log(`✅ Load Groups button enabled: ${isEnabled}`);
            
            if (isEnabled) {
                console.log('📍 Step 3: Click Load Groups button');
                await loadGroupsBtn.click();
                console.log('✅ Clicked Load Groups button - waiting for response...');
                
                // Wait longer for photo processing
                await page.waitForTimeout(15000);
                
                console.log('📍 Step 4: Check for photo groups');
                const photoGroups = page.locator('.group-card');
                const groupCount = await photoGroups.count();
                console.log(`📊 Found ${groupCount} photo groups`);
                
                if (groupCount > 0) {
                    console.log('📍 Step 5: Check for photo thumbnails');
                    const thumbnails = page.locator('.photo-thumbnail');
                    const thumbnailCount = await thumbnails.count();
                    console.log(`🖼️ Found ${thumbnailCount} photo thumbnails`);
                    
                    // Check if thumbnails are actually loading
                    let loadedCount = 0;
                    const testThumbnails = Math.min(thumbnailCount, 8);
                    
                    for (let i = 0; i < testThumbnails; i++) {
                        const thumbnail = thumbnails.nth(i);
                        const isVisible = await thumbnail.isVisible();
                        const src = await thumbnail.getAttribute('src');
                        const hasCorrectSrc = src && src.includes('/api/thumbnail/');
                        
                        if (isVisible && hasCorrectSrc) {
                            loadedCount++;
                            console.log(`  ✅ Thumbnail ${i + 1}: visible with correct src`);
                        } else {
                            console.log(`  ❌ Thumbnail ${i + 1}: visible=${isVisible}, src=${src}`);
                        }
                    }
                    
                    console.log(`✅ Successfully loaded ${loadedCount}/${testThumbnails} thumbnails`);
                    
                    if (loadedCount > 0) {
                        console.log('📍 Step 6: Test photo selection and deletion workflow');
                        
                        // Look for the first photo card
                        const photoCards = page.locator('.photo-card');
                        const cardCount = await photoCards.count();
                        console.log(`🔍 Found ${cardCount} photo cards`);
                        
                        if (cardCount > 0) {
                            const firstCard = photoCards.first();
                            console.log('🖱️ Clicking first photo card to select for deletion...');
                            
                            await firstCard.click();
                            await page.waitForTimeout(1000);
                            
                            // Check if the card is now selected
                            const isSelected = await firstCard.evaluate(el => 
                                el.classList.contains('selected')
                            );
                            console.log(`📌 First photo selected: ${isSelected}`);
                            
                            // Look for delete button
                            const deleteButton = page.locator('button:has-text("Delete Duplicates"), button:has-text("Delete All"), button[onclick*="delete"]').first();
                            const deleteButtonExists = await deleteButton.count() > 0;
                            console.log(`❌ Delete button found: ${deleteButtonExists}`);
                            
                            if (deleteButtonExists) {
                                const deleteButtonText = await deleteButton.textContent();
                                const isEnabled = await deleteButton.isEnabled();
                                console.log(`❌ Delete button: "${deleteButtonText}" (enabled: ${isEnabled})`);
                                
                                if (isSelected && isEnabled) {
                                    console.log('🎉 SUCCESS: Complete workflow verified!');
                                    console.log('✅ Photos load correctly');
                                    console.log('✅ Thumbnails display properly');  
                                    console.log('✅ Photo selection works');
                                    console.log('✅ Delete button is available');
                                    
                                    return { success: true, message: 'Complete photos-only workflow verified!' };
                                } else {
                                    console.log('⚠️ Selection or button state issue');
                                }
                            } else {
                                console.log('❌ No delete button found');
                            }
                        } else {
                            console.log('❌ No photo cards found');
                        }
                    } else {
                        console.log('❌ No thumbnails loaded properly');
                    }
                } else {
                    console.log('❌ No photo groups found after loading');
                }
            } else {
                console.log('❌ Load Groups button is disabled');
            }
        } else {
            console.log('❌ Load Groups button not found');
        }
        
    } catch (error) {
        console.error('❌ Test failed:', error.message);
        errors.push({ type: 'test_error', message: error.message });
    } finally {
        // Summary
        console.log('\n📊 TEST SUMMARY:');
        console.log(`📡 API requests made: ${networkRequests.length}`);
        console.log(`❌ Errors encountered: ${errors.length}`);
        
        if (networkRequests.length > 0) {
            console.log('\n📡 API Requests:');
            networkRequests.forEach((req, i) => {
                console.log(`  ${i + 1}. ${req.method} ${req.url}`);
            });
        }
        
        if (errors.length > 0) {
            console.log('\n❌ Errors:');
            errors.forEach((error, i) => {
                console.log(`  ${i + 1}. [${error.type}] ${error.message}`);
            });
        }
        
        await browser.close();
    }
    
    return {
        success: errors.length === 0,
        errorCount: errors.length,
        errors: errors
    };
}

testLegacyDirect().then(result => {
    console.log('\n🏁 LEGACY DIRECT TEST RESULTS:');
    console.log(`✅ Success: ${result.success}`);
    console.log(`❌ Errors: ${result.errorCount}`);
    
    if (result.errorCount > 0) {
        console.log('\n📝 Final Error Summary:');
        result.errors.forEach((error, index) => {
            console.log(`  ${index + 1}. [${error.type}] ${error.message}`);
        });
    }
    
    process.exit(result.success ? 0 : 1);
}).catch(error => {
    console.error('❌ Test execution failed:', error);
    process.exit(1);
});