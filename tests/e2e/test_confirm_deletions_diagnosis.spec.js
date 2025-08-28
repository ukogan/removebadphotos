const { test, expect } = require('@playwright/test');

/**
 * CONFIRM DELETIONS FUNCTIONALITY DIAGNOSTIC TEST
 * 
 * Purpose: Diagnose why the "Confirm Deletions" button isn't working in the photo deduplication application
 * Target: http://127.0.0.1:5003/legacy
 * 
 * This test will systematically verify:
 * 1. Photo group loading workflow
 * 2. Photo selection mechanisms
 * 3. Button visibility and state management
 * 4. Click event handling and function execution
 * 5. API call behavior and network requests
 * 6. Console error detection
 */

test.describe('Confirm Deletions Functionality Diagnosis', () => {
    const BASE_URL = 'http://127.0.0.1:5003';
    
    test.beforeEach(async ({ page }) => {
        // Enable console logging for debugging
        page.on('console', (msg) => {
            console.log(`[BROWSER CONSOLE ${msg.type().toUpperCase()}]`, msg.text());
        });
        
        // Track network requests
        page.on('request', (request) => {
            console.log(`[NETWORK REQUEST]`, request.method(), request.url());
        });
        
        page.on('response', (response) => {
            console.log(`[NETWORK RESPONSE]`, response.status(), response.url());
        });
        
        // Navigate to legacy interface
        console.log('🚀 Navigating to legacy interface...');
        await page.goto(`${BASE_URL}/legacy`);
        await page.waitForLoadState('networkidle');
    });

    test('Step 1: Verify page loads correctly and elements exist', async ({ page }) => {
        console.log('🔍 STEP 1: Verifying page structure and initial elements...');
        
        // Check page title and basic structure
        await expect(page).toHaveTitle(/Photo Deduplication/);
        
        // Verify the main analyze button exists
        const analyzeBtn = page.locator('#loadGroupsBtn');
        await expect(analyzeBtn).toBeVisible();
        await expect(analyzeBtn).toHaveText(/🔍 Analyze Photo Groups/);
        
        console.log('✅ Analyze button found and visible');
        
        // Verify the selection summary section exists but is hidden initially
        const selectionSummary = page.locator('#selectionSummary');
        await expect(selectionSummary).toBeHidden();
        console.log('✅ Selection summary section exists and is initially hidden');
        
        // Verify the confirm button exists but is in hidden container
        const confirmBtn = page.locator('#confirmBtn');
        await expect(confirmBtn).toBeAttached();
        await expect(confirmBtn).toHaveText(/🗑️ Confirm Deletions/);
        console.log('✅ Confirm deletions button exists with correct text');
    });

    test('Step 2: Test photo group loading workflow', async ({ page }) => {
        console.log('🔍 STEP 2: Testing photo group loading workflow...');
        
        const analyzeBtn = page.locator('#loadGroupsBtn');
        const groupStatus = page.locator('#groupStatus');
        
        // Click analyze button and wait for response
        console.log('📱 Clicking analyze button...');
        await analyzeBtn.click();
        
        // Wait for loading state
        await expect(analyzeBtn).toBeDisabled();
        console.log('✅ Button becomes disabled during loading');
        
        // Wait for either success or failure (with generous timeout)
        try {
            await page.waitForFunction(() => {
                const btn = document.getElementById('loadGroupsBtn');
                return !btn.disabled;
            }, { timeout: 60000 });
            console.log('✅ Loading completed within timeout');
        } catch (error) {
            console.log('⚠️ Loading took longer than expected, continuing...');
        }
        
        // Check if groups container has content
        const groupsContainer = page.locator('#groupsContainer');
        const groups = groupsContainer.locator('.photo-group');
        const groupCount = await groups.count();
        console.log(`📊 Found ${groupCount} photo groups`);
        
        if (groupCount === 0) {
            console.log('❌ No photo groups loaded - this could be the root issue');
            
            // Check for any error messages
            const statusText = await groupStatus.textContent();
            console.log(`📋 Status text: "${statusText}"`);
            
            // Check console for errors that might indicate why no groups loaded
            // This will be captured by our console listener
        } else {
            console.log('✅ Photo groups loaded successfully');
        }
    });

    test('Step 3: Test photo selection mechanisms', async ({ page }) => {
        console.log('🔍 STEP 3: Testing photo selection mechanisms...');
        
        // First load photo groups
        await page.locator('#loadGroupsBtn').click();
        
        // Wait for groups to load with extended timeout
        await page.waitForFunction(() => {
            const groups = document.querySelectorAll('.photo-group');
            return groups.length > 0;
        }, { timeout: 60000 });
        
        const groups = page.locator('.photo-group');
        const groupCount = await groups.count();
        console.log(`📊 Testing with ${groupCount} available groups`);
        
        if (groupCount === 0) {
            console.log('⚠️ No groups available for selection testing');
            return;
        }
        
        // Test individual photo selection
        console.log('🖱️ Testing individual photo click selection...');
        const firstGroup = groups.first();
        const photos = firstGroup.locator('.photo');
        const photoCount = await photos.count();
        console.log(`📸 First group has ${photoCount} photos`);
        
        if (photoCount > 0) {
            // Click first photo
            const firstPhoto = photos.first();
            await firstPhoto.click();
            console.log('✅ Clicked first photo');
            
            // Check if photo state changed (look for visual indicators)
            const photoClasses = await firstPhoto.getAttribute('class');
            console.log(`📋 Photo classes after click: ${photoClasses}`);
        }
        
        // Test group action buttons
        console.log('🔘 Testing group action buttons...');
        const deleteDuplicatesBtn = firstGroup.locator('button:has-text("Delete Duplicates")');
        const deleteAllBtn = firstGroup.locator('button:has-text("Delete All Photos")');
        
        if (await deleteDuplicatesBtn.count() > 0) {
            await deleteDuplicatesBtn.click();
            console.log('✅ Clicked "Delete Duplicates" button');
        }
        
        if (await deleteAllBtn.count() > 0) {
            await deleteAllBtn.click();
            console.log('✅ Clicked "Delete All Photos" button');
        }
        
        // Check if selection summary becomes visible
        const selectionSummary = page.locator('#selectionSummary');
        const isVisible = await selectionSummary.isVisible();
        console.log(`📊 Selection summary visible: ${isVisible}`);
        
        if (isVisible) {
            const summaryText = await page.locator('#summaryStats').textContent();
            console.log(`📋 Summary text: "${summaryText}"`);
        }
    });

    test('Step 4: Test confirm deletions button functionality', async ({ page }) => {
        console.log('🔍 STEP 4: Testing confirm deletions button functionality...');
        
        // Load groups and make selections
        await page.locator('#loadGroupsBtn').click();
        await page.waitForFunction(() => {
            const groups = document.querySelectorAll('.photo-group');
            return groups.length > 0;
        }, { timeout: 60000 });
        
        const groups = page.locator('.photo-group');
        const groupCount = await groups.count();
        
        if (groupCount === 0) {
            console.log('❌ Cannot test button - no groups loaded');
            return;
        }
        
        // Make some selections to trigger button visibility
        console.log('🖱️ Making photo selections to trigger button visibility...');
        const firstGroup = groups.first();
        
        // Try clicking "Delete Duplicates" to make selections
        const deleteDuplicatesBtn = firstGroup.locator('button:has-text("Delete Duplicates")');
        if (await deleteDuplicatesBtn.count() > 0) {
            await deleteDuplicatesBtn.click();
            console.log('✅ Clicked Delete Duplicates to make selections');
        }
        
        // Wait a moment for UI to update
        await page.waitForTimeout(1000);
        
        // Check if confirm button becomes visible
        const selectionSummary = page.locator('#selectionSummary');
        const confirmBtn = page.locator('#confirmBtn');
        
        const summaryVisible = await selectionSummary.isVisible();
        console.log(`📊 Selection summary visible: ${summaryVisible}`);
        
        if (summaryVisible) {
            // Test button click detection
            console.log('🔲 Testing confirm button click...');
            
            // Set up promise to wait for console log
            const consolePromise = page.waitForEvent('console', { 
                predicate: (msg) => msg.text().includes('Button clicked!'),
                timeout: 5000 
            }).catch(() => null);
            
            // Click the button
            await confirmBtn.click();
            console.log('✅ Confirm button clicked');
            
            // Wait for console log
            const consoleMsg = await consolePromise;
            if (consoleMsg) {
                console.log('✅ Button click detected in console');
            } else {
                console.log('❌ No button click log detected - event handler may not be working');
            }
            
            // Check for confirmDeletions function execution log
            const functionCallPromise = page.waitForEvent('console', { 
                predicate: (msg) => msg.text().includes('confirmDeletions() called'),
                timeout: 5000 
            }).catch(() => null);
            
            const functionMsg = await functionCallPromise;
            if (functionMsg) {
                console.log('✅ confirmDeletions function execution detected');
            } else {
                console.log('❌ confirmDeletions function execution not detected');
            }
            
        } else {
            console.log('❌ Selection summary not visible - button won\'t be clickable');
            
            // Try to force click the button anyway to test if it's the visibility issue
            console.log('🔧 Attempting to force click hidden button...');
            try {
                await confirmBtn.click({ force: true });
                console.log('⚠️ Forced click succeeded - visibility might be the issue');
            } catch (error) {
                console.log('❌ Even forced click failed:', error.message);
            }
        }
    });

    test('Step 5: Test API call behavior', async ({ page }) => {
        console.log('🔍 STEP 5: Testing API call behavior...');
        
        // Track API calls
        let apiCallMade = false;
        page.on('request', (request) => {
            if (request.url().includes('/api/complete-workflow')) {
                apiCallMade = true;
                console.log('✅ API call to /api/complete-workflow detected');
                console.log('📋 Request method:', request.method());
                console.log('📋 Request headers:', JSON.stringify(request.headers(), null, 2));
            }
        });
        
        page.on('response', (response) => {
            if (response.url().includes('/api/complete-workflow')) {
                console.log('📡 API response status:', response.status());
            }
        });
        
        // Load groups and make selections
        await page.locator('#loadGroupsBtn').click();
        await page.waitForFunction(() => {
            const groups = document.querySelectorAll('.photo-group');
            return groups.length > 0;
        }, { timeout: 60000 });
        
        const groups = page.locator('.photo-group');
        const groupCount = await groups.count();
        
        if (groupCount === 0) {
            console.log('❌ Cannot test API - no groups loaded');
            return;
        }
        
        // Make selections and try to trigger API call
        const firstGroup = groups.first();
        const deleteDuplicatesBtn = firstGroup.locator('button:has-text("Delete Duplicates")');
        
        if (await deleteDuplicatesBtn.count() > 0) {
            await deleteDuplicatesBtn.click();
            await page.waitForTimeout(1000);
            
            const selectionSummary = page.locator('#selectionSummary');
            if (await selectionSummary.isVisible()) {
                const confirmBtn = page.locator('#confirmBtn');
                
                // Set up dialog handler for confirmation
                page.on('dialog', async (dialog) => {
                    console.log('📋 Confirmation dialog appeared:', dialog.message());
                    await dialog.accept();
                });
                
                await confirmBtn.click();
                console.log('✅ Clicked confirm button with dialog handler');
                
                // Wait for potential API call
                await page.waitForTimeout(3000);
                
                if (apiCallMade) {
                    console.log('✅ API call was successfully triggered');
                } else {
                    console.log('❌ No API call detected - function may not be executing properly');
                }
            }
        }
    });

    test('Step 6: Debug JavaScript execution environment', async ({ page }) => {
        console.log('🔍 STEP 6: Debugging JavaScript execution environment...');
        
        // Test if core functions exist
        const functionsExist = await page.evaluate(() => {
            const results = {};
            results.confirmDeletions = typeof confirmDeletions === 'function';
            results.updateSelectionSummary = typeof updateSelectionSummary === 'function';
            results.photoSelections = typeof photoSelections === 'object';
            results.allGroups = typeof allGroups === 'object';
            return results;
        });
        
        console.log('📋 Function availability:', JSON.stringify(functionsExist, null, 2));
        
        // Test photoSelections state
        const selectionState = await page.evaluate(() => {
            if (typeof photoSelections === 'object') {
                return {
                    exists: true,
                    keys: Object.keys(photoSelections),
                    totalSelections: Object.values(photoSelections).reduce((sum, arr) => sum + (arr?.length || 0), 0)
                };
            }
            return { exists: false };
        });
        
        console.log('📋 Selection state:', JSON.stringify(selectionState, null, 2));
        
        // Test if button onclick is properly attached
        const buttonInfo = await page.evaluate(() => {
            const btn = document.getElementById('confirmBtn');
            if (btn) {
                return {
                    exists: true,
                    onclick: btn.onclick?.toString() || 'No onclick handler',
                    addEventListener: btn.eventListeners?.length || 'No event listeners info'
                };
            }
            return { exists: false };
        });
        
        console.log('📋 Button info:', JSON.stringify(buttonInfo, null, 2));
    });

    test('Comprehensive workflow test', async ({ page }) => {
        console.log('🔍 COMPREHENSIVE: End-to-end workflow test...');
        
        // Track all relevant events
        const eventLog = [];
        
        page.on('console', (msg) => {
            eventLog.push(`CONSOLE: ${msg.text()}`);
        });
        
        page.on('request', (request) => {
            if (request.url().includes('api')) {
                eventLog.push(`REQUEST: ${request.method()} ${request.url()}`);
            }
        });
        
        page.on('dialog', async (dialog) => {
            eventLog.push(`DIALOG: ${dialog.message()}`);
            await dialog.accept();
        });
        
        try {
            // Step 1: Load groups
            console.log('📋 Step 1: Loading photo groups...');
            await page.locator('#loadGroupsBtn').click();
            
            await page.waitForFunction(() => {
                const btn = document.getElementById('loadGroupsBtn');
                return !btn.disabled;
            }, { timeout: 60000 });
            
            const groupCount = await page.locator('.photo-group').count();
            console.log(`📊 Loaded ${groupCount} groups`);
            
            if (groupCount > 0) {
                // Step 2: Make selections
                console.log('📋 Step 2: Making photo selections...');
                const firstGroup = page.locator('.photo-group').first();
                const deleteDuplicatesBtn = firstGroup.locator('button:has-text("Delete Duplicates")');
                
                if (await deleteDuplicatesBtn.count() > 0) {
                    await deleteDuplicatesBtn.click();
                    await page.waitForTimeout(1000);
                }
                
                // Step 3: Check if confirm button is visible
                const selectionSummary = page.locator('#selectionSummary');
                const isVisible = await selectionSummary.isVisible();
                console.log(`📊 Confirm button area visible: ${isVisible}`);
                
                if (isVisible) {
                    // Step 4: Click confirm button
                    console.log('📋 Step 3: Clicking confirm button...');
                    const confirmBtn = page.locator('#confirmBtn');
                    await confirmBtn.click();
                    
                    // Wait for processing
                    await page.waitForTimeout(5000);
                } else {
                    console.log('❌ Cannot proceed - confirm button area not visible');
                }
            } else {
                console.log('❌ Cannot proceed - no photo groups loaded');
            }
            
        } catch (error) {
            eventLog.push(`ERROR: ${error.message}`);
        }
        
        // Output event log for analysis
        console.log('📋 COMPLETE EVENT LOG:');
        eventLog.forEach((event, index) => {
            console.log(`${index + 1}. ${event}`);
        });
    });
});