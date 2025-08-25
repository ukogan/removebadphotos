// Test the fix for filtered data in legacy interface
const { chromium } = require('playwright');

async function testFilteredLegacyFix() {
    console.log('🧪 Testing filtered legacy interface fix...');
    
    const browser = await chromium.launch({ headless: false });
    const page = await browser.newPage();
    
    const networkRequests = [];
    page.on('request', request => {
        if (request.url().includes('/api/')) {
            networkRequests.push(`${request.method()} ${request.url().split('/api/')[1]}`);
        }
    });
    
    try {
        // Step 1: Go to filters page
        console.log('📍 Step 1: Navigate to filters page');
        await page.goto('http://127.0.0.1:5003/filters');
        await page.waitForLoadState('networkidle');
        await page.waitForTimeout(3000);
        
        // Step 2: Apply 2023 year filter
        console.log('📍 Step 2: Apply 2023 year filter');
        const year2023Btn = page.locator('[data-year="2023"]').first();
        if (await year2023Btn.count() > 0) {
            await year2023Btn.click();
            await page.waitForTimeout(2000);
            console.log('✅ Applied 2023 filter');
        }
        
        // Step 3: Click "Apply Filters" to save session
        console.log('📍 Step 3: Click Apply Filters to save filter session');
        const applyFiltersBtn = page.locator('button:has-text("Apply Filters")').first();
        if (await applyFiltersBtn.count() > 0) {
            await applyFiltersBtn.click();
            await page.waitForTimeout(3000);
            console.log('✅ Clicked Apply Filters');
            
            // Should redirect to main page showing filtered results
            const currentUrl = page.url();
            console.log(`📍 Current URL: ${currentUrl}`);
            
            // Look for filtered photo count
            try {
                const filteredText = await page.locator('text=/\\d+ \\(filtered\\) photos/').first().textContent();
                console.log(`📊 Found filtered text: "${filteredText}"`);
            } catch (e) {
                console.log('📊 No filtered text found yet');
            }
        }
        
        // Step 3.5: Click "Analyze Selected" to create the filter session  
        console.log('📍 Step 3.5: Click Analyze Selected to create filter session');
        const analyzeSelectedBtn = page.locator('button:has-text("Analyze Selected")').first();
        if (await analyzeSelectedBtn.count() > 0) {
            await analyzeSelectedBtn.click();
            await page.waitForTimeout(5000);
            console.log('✅ Clicked Analyze Selected - this should create the filter session');
            
            // Wait for analysis to complete
            await page.waitForTimeout(10000);
        } else {
            console.log('⚠️ Analyze Selected button not found - session may not be created');
        }
        
        // Step 4: Navigate to legacy interface
        console.log('📍 Step 4: Navigate to legacy interface');
        await page.goto('http://127.0.0.1:5003/legacy');
        await page.waitForTimeout(2000);
        
        // Step 5: Click load groups button
        console.log('📍 Step 5: Click load groups button');
        const loadBtn = page.locator('button:has-text("Analyze Photo Groups"), button:has-text("Load Groups"), #loadGroupsBtn').first();
        if (await loadBtn.count() > 0) {
            await loadBtn.click();
            console.log('✅ Clicked load groups button');
            
            // Wait for groups to load
            await page.waitForTimeout(8000);
            
            // Step 6: Check if groups loaded with data
            console.log('📍 Step 6: Check if photo groups loaded');
            const groupCards = page.locator('.group-card');
            const groupCount = await groupCards.count();
            console.log(`📊 Found ${groupCount} photo groups`);
            
            if (groupCount > 0) {
                // Check if groups have actual photo data
                const firstGroup = groupCards.first();
                const photosInGroup = await firstGroup.locator('.photo-card, .photo-thumbnail').count();
                console.log(`🖼️ Photos in first group: ${photosInGroup}`);
                
                // Check for undefined values
                const groupText = await firstGroup.textContent();
                const hasUndefined = groupText.includes('undefined');
                console.log(`❌ Has undefined values: ${hasUndefined}`);
                
                if (photosInGroup > 0 && !hasUndefined) {
                    console.log('🎉 SUCCESS: Groups loaded with actual photo data');
                    console.log('✅ Filter session data is being used correctly');
                    return { success: true, groupCount, photosInGroup };
                } else {
                    console.log('❌ FAILED: Groups loaded but missing photo data or have undefined values');
                    return { success: false, issue: 'missing_photo_data', groupCount, photosInGroup, hasUndefined };
                }
            } else {
                console.log('❌ FAILED: No photo groups loaded');
                return { success: false, issue: 'no_groups', groupCount };
            }
        } else {
            console.log('❌ Load groups button not found');
            return { success: false, issue: 'no_load_button' };
        }
        
    } catch (error) {
        console.error('❌ Test failed:', error.message);
        return { success: false, error: error.message };
    } finally {
        console.log('\n📡 Network requests made:');
        [...new Set(networkRequests)].slice(0, 15).forEach((req, i) => {
            console.log(`  ${i + 1}. ${req}`);
        });
        
        await browser.close();
    }
}

testFilteredLegacyFix().then(result => {
    console.log('\n🏁 FILTERED LEGACY FIX TEST RESULTS:');
    if (result.success) {
        console.log('✅ SUCCESS: Filtered legacy interface fix is working!');
        console.log(`📊 Groups loaded: ${result.groupCount}`);
        console.log(`🖼️ Photos per group: ${result.photosInGroup}`);
    } else {
        console.log('❌ FAILED: Filtered legacy interface fix is not working');
        console.log(`📝 Issue: ${result.issue || result.error}`);
        if (result.groupCount !== undefined) console.log(`📊 Groups found: ${result.groupCount}`);
        if (result.photosInGroup !== undefined) console.log(`🖼️ Photos in first group: ${result.photosInGroup}`);
    }
    process.exit(result.success ? 0 : 1);
}).catch(error => {
    console.error('❌ Test execution failed:', error);
    process.exit(1);
});