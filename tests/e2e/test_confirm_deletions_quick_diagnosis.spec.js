const { test, expect } = require('@playwright/test');

/**
 * QUICK CONFIRM DELETIONS DIAGNOSIS TEST
 * 
 * Based on initial test results, I can see that:
 * 1. Page loads but shows "📡 Loading photos..." and gets stuck
 * 2. Tests timeout because groups never load
 * 
 * This simplified test will diagnose the exact failure point
 */

test.describe('Quick Confirm Deletions Diagnosis', () => {
    test('Diagnose why photos never load and confirm button fails', async ({ page }) => {
        console.log('🔍 DIAGNOSIS: Testing confirm deletions failure point...');
        
        // Track all console logs and network requests
        const logs = [];
        page.on('console', (msg) => {
            const text = msg.text();
            logs.push(`CONSOLE: ${text}`);
            console.log(`[CONSOLE]`, text);
        });
        
        page.on('request', (request) => {
            logs.push(`REQUEST: ${request.method()} ${request.url()}`);
        });
        
        page.on('response', (response) => {
            logs.push(`RESPONSE: ${response.status()} ${response.url()}`);
        });
        
        // Navigate to legacy interface
        console.log('🚀 Step 1: Loading legacy interface...');
        await page.goto('http://127.0.0.1:5003/legacy');
        await page.waitForLoadState('networkidle');
        
        // Check initial page state
        console.log('📋 Step 2: Checking initial page elements...');
        
        // Check if analyze button exists
        const analyzeBtn = await page.locator('#loadGroupsBtn').count();
        console.log(`✅ Analyze button found: ${analyzeBtn > 0}`);
        
        // Check if confirm button exists (should be hidden)
        const confirmBtn = await page.locator('#confirmBtn').count();
        console.log(`✅ Confirm button exists: ${confirmBtn > 0}`);
        
        if (confirmBtn > 0) {
            const confirmBtnText = await page.locator('#confirmBtn').textContent();
            console.log(`📋 Confirm button text: "${confirmBtnText}"`);
        }
        
        // Check current loading state
        const loadingText = await page.locator('body').textContent();
        const isStuckLoading = loadingText.includes('📡 Loading photos...');
        console.log(`📡 Page stuck in loading: ${isStuckLoading}`);
        
        if (isStuckLoading) {
            console.log('❌ ISSUE IDENTIFIED: Page is stuck loading photos');
            console.log('🔧 This explains why confirm deletions never works - no groups load');
            
            // Try to see what's happening with the loading
            await page.waitForTimeout(2000);
            
            // Check if there are any progress updates
            const progressRequests = logs.filter(log => log.includes('/api/progress'));
            console.log(`📊 Progress API calls made: ${progressRequests.length}`);
            
            if (progressRequests.length > 0) {
                console.log('✅ Progress API is being called - backend is working');
                console.log('🔧 Issue likely: Long-running analysis never completes');
            } else {
                console.log('❌ No progress API calls - analyze button might not be working');
            }
        }
        
        // Try clicking analyze button anyway to see what happens
        if (analyzeBtn > 0) {
            console.log('🔲 Step 3: Attempting to click analyze button...');
            
            const loadGroupsBtn = page.locator('#loadGroupsBtn');
            
            // Check if button is clickable
            const isEnabled = await loadGroupsBtn.isEnabled();
            console.log(`📋 Analyze button enabled: ${isEnabled}`);
            
            if (isEnabled) {
                await loadGroupsBtn.click();
                console.log('✅ Analyze button clicked');
                
                // Wait a short time to see what happens
                await page.waitForTimeout(5000);
                
                // Check if button becomes disabled (indicating it's processing)
                const isDisabledAfterClick = await loadGroupsBtn.isDisabled();
                console.log(`📋 Button disabled after click: ${isDisabledAfterClick}`);
                
                // Check if any groups loaded in this time
                const groupCount = await page.locator('.photo-group').count();
                console.log(`📊 Photo groups loaded: ${groupCount}`);
                
                if (groupCount === 0) {
                    console.log('❌ CONFIRMED: No photo groups load even after clicking analyze');
                    console.log('🔧 ROOT CAUSE: Backend analysis is not completing or returning no results');
                }
            }
        }
        
        // Test if we can manually trigger the confirmDeletions function
        console.log('🔲 Step 4: Testing confirmDeletions function directly...');
        
        const functionTest = await page.evaluate(() => {
            const results = {};
            
            // Check if function exists
            results.functionExists = typeof confirmDeletions === 'function';
            
            // Check if required variables exist
            results.photoSelections = typeof photoSelections;
            results.allGroups = typeof allGroups;
            
            // Try to call function directly (this should show alert about no selections)
            if (typeof confirmDeletions === 'function') {
                try {
                    // Temporarily override alert to capture message
                    const originalAlert = window.alert;
                    let alertMessage = null;
                    window.alert = (msg) => { alertMessage = msg; };
                    
                    confirmDeletions();
                    
                    // Restore alert
                    window.alert = originalAlert;
                    
                    results.alertMessage = alertMessage;
                    results.functionCallSucceeded = true;
                } catch (error) {
                    results.functionCallError = error.message;
                    results.functionCallSucceeded = false;
                }
            }
            
            return results;
        });
        
        console.log('📋 Function test results:');
        console.log(`  - confirmDeletions exists: ${functionTest.functionExists}`);
        console.log(`  - photoSelections type: ${functionTest.photoSelections}`);
        console.log(`  - allGroups type: ${functionTest.allGroups}`);
        
        if (functionTest.functionExists) {
            console.log(`  - Function call succeeded: ${functionTest.functionCallSucceeded}`);
            if (functionTest.alertMessage) {
                console.log(`  - Alert message: "${functionTest.alertMessage}"`);
            }
            if (functionTest.functionCallError) {
                console.log(`  - Function error: ${functionTest.functionCallError}`);
            }
        }
        
        // Final diagnosis
        console.log('🎯 FINAL DIAGNOSIS:');
        
        if (!functionTest.functionExists) {
            console.log('❌ CRITICAL: confirmDeletions function does not exist');
            console.log('🔧 FIX: Check if legacy_page_content.html is being served correctly');
        } else if (isStuckLoading) {
            console.log('❌ CRITICAL: Page is stuck in loading state');
            console.log('🔧 FIX: Backend photo analysis is not completing');
            console.log('🔧 RECOMMENDATION: Check backend logs and consider timeout/performance issues');
        } else {
            console.log('✅ Function exists and page loads');
            console.log('🔧 Issue likely: Photo selection state management or button visibility logic');
        }
        
        // Output full log for analysis
        console.log('📋 COMPLETE LOG:');
        logs.forEach((log, i) => console.log(`${i + 1}. ${log}`));
    });
});