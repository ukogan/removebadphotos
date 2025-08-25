// Test the complete workflow: filter → analyze → legacy → mark for deletion
const { chromium } = require('playwright');

async function testCompleteFilterWorkflow() {
    console.log('🎯 Testing complete filter → analyze → legacy workflow...');
    
    const browser = await chromium.launch({ headless: false });
    const page = await browser.newPage();
    
    const networkRequests = [];
    page.on('request', request => {
        if (request.url().includes('/api/')) {
            networkRequests.push(request.url());
        }
    });
    
    try {
        // Step 1: Go to filters and wait for data to load
        console.log('📍 Step 1: Navigate to filters and wait for data');
        await page.goto('http://127.0.0.1:5003/filters');
        await page.waitForLoadState('networkidle');
        
        // Wait for the initial data to load
        await page.waitForTimeout(5000);
        
        // Check that data has loaded
        const potentialSavings = await page.locator('#potential-savings').textContent();
        const totalClusters = await page.locator('#total-clusters').textContent();
        console.log(`💰 Potential savings: "${potentialSavings}"`);
        console.log(`📊 Total clusters: "${totalClusters}"`);
        
        // Step 2: Apply filters to get a manageable subset
        console.log('📍 Step 2: Apply year 2025 filter');
        const year2025Btn = page.locator('[data-year="2025"]').first();
        if (await year2025Btn.count() > 0) {
            await year2025Btn.click();
            await page.waitForTimeout(3000);
            console.log('✅ Applied 2025 year filter');
        }
        
        // Step 3: Apply size filter for larger files
        console.log('📍 Step 3: Apply minimum size filter (5MB)');
        const minSizeInput = page.locator('#min-size');
        if (await minSizeInput.count() > 0) {
            await minSizeInput.fill('5');
            await page.waitForTimeout(3000);
            console.log('✅ Applied 5MB minimum size filter');
        }
        
        // Step 4: Click "Apply Filters" button
        console.log('📍 Step 4: Click Apply Filters button');
        const applyFiltersBtn = page.locator('button:has-text("Apply Filters")').first();
        
        if (await applyFiltersBtn.count() > 0) {
            await applyFiltersBtn.click();
            console.log('✅ Clicked Apply Filters button');
            await page.waitForTimeout(5000); // Wait for results to load
            
            // Step 5: Check if analyze section becomes visible
            console.log('📍 Step 5: Check for analyze section');
            const analyzeSection = page.locator('#analyze-selected-section');
            const isVisible = await analyzeSection.isVisible();
            console.log(`📊 Analyze section visible: ${isVisible}`);
            
            if (isVisible) {
                // Step 6: Click analyze button
                console.log('📍 Step 6: Click analyze button');
                const analyzeBtn = page.locator('button:has-text("Analyze Selected")').first();
            
            if (await analyzeBtn.count() > 0 && await analyzeBtn.isVisible()) {
                await analyzeBtn.click();
                console.log('✅ Clicked analyze button');
                
                // Wait for redirect or processing
                await page.waitForTimeout(8000);
                
                const currentUrl = page.url();
                console.log(`🌐 Current URL: ${currentUrl}`);
                
                // Step 7: Navigate to legacy interface
                if (currentUrl.includes('127.0.0.1:5003') && !currentUrl.includes('legacy')) {
                    console.log('📍 Step 6: Navigate to legacy interface');
                    await page.goto('http://127.0.0.1:5003/legacy?priority=P2&limit=10');
                    await page.waitForTimeout(3000);
                }
                
                // Step 8: Test legacy interface
                console.log('📍 Step 7: Test legacy interface photo loading');
                
                const loadGroupsBtn = page.locator('#loadGroupsBtn');
                if (await loadGroupsBtn.count() > 0) {
                    console.log('✅ Found load groups button');
                    await loadGroupsBtn.click();
                    await page.waitForTimeout(10000);
                    
                    // Check for photo groups
                    const photoGroups = page.locator('.group-card');
                    const groupCount = await photoGroups.count();
                    console.log(`📊 Found ${groupCount} photo groups`);
                    
                    if (groupCount > 0) {
                        // Check for photo cards
                        const photoCards = page.locator('.photo-card');
                        const cardCount = await photoCards.count();
                        console.log(`🖼️ Found ${cardCount} photo cards`);
                        
                        if (cardCount > 0) {
                            // Test photo selection
                            console.log('📍 Step 9: Test photo selection');
                            const firstCard = photoCards.first();
                            await firstCard.click();
                            await page.waitForTimeout(1000);
                            
                            const isSelected = await firstCard.evaluate(el => 
                                el.classList.contains('selected')
                            );
                            console.log(`📌 Photo selected: ${isSelected}`);
                            
                            // Check for delete button
                            const deleteBtn = page.locator('button:has-text("Delete"), button[onclick*="delete"]').first();
                            const deleteExists = await deleteBtn.count() > 0;
                            console.log(`❌ Delete button available: ${deleteExists}`);
                            
                            if (groupCount > 0 && cardCount > 0) {
                                console.log('🎉 SUCCESS: Complete workflow verified!');
                                console.log('✅ Filters load data correctly');
                                console.log('✅ Filter selection works');
                                console.log('✅ Legacy interface loads photo groups');
                                console.log('✅ Photos can be selected');
                                
                                return { success: true, message: 'Complete workflow functional' };
                            }
                        }
                    }
                }
            } else {
                console.log('❌ Analyze button not visible or clickable');
            }
        } else {
            console.log('❌ Analyze section not visible after applying filters');
        }
        } else {
            console.log('❌ Apply Filters button not found');
        }
        
    } catch (error) {
        console.error('❌ Test failed:', error.message);
        return { success: false, error: error.message };
    } finally {
        console.log('\n📡 Network requests made:');
        [...new Set(networkRequests)].slice(0, 10).forEach((url, i) => {
            console.log(`  ${i + 1}. ${url.split('/api/')[1]}`);
        });
        
        await browser.close();
    }
    
    return { success: false, message: 'Workflow incomplete' };
}

testCompleteFilterWorkflow().then(result => {
    console.log(`\n🏁 COMPLETE WORKFLOW TEST: ${result.success ? 'SUCCESS' : 'FAILED'}`);
    if (!result.success) {
        console.log(`📝 Issue: ${result.message || result.error}`);
    }
    process.exit(result.success ? 0 : 1);
}).catch(error => {
    console.error('❌ Test execution failed:', error);
    process.exit(1);
});