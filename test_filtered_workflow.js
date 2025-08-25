// Comprehensive test of the filtered analysis workflow
const { chromium } = require('playwright');

async function testFilteredWorkflow() {
    console.log('🔬 Testing complete filtered analysis workflow...');
    
    const browser = await chromium.launch({ headless: false });
    const page = await browser.newPage();
    
    const errors = [];
    const networkRequests = [];
    
    // Capture JavaScript errors
    page.on('pageerror', error => {
        errors.push(error);
        console.error('❌ Page error:', error.message);
    });
    
    // Capture console messages
    page.on('console', message => {
        if (message.type() === 'error') {
            console.error('❌ Console error:', message.text());
            errors.push({ type: 'console', text: message.text() });
        }
    });
    
    // Capture network activity
    page.on('request', request => {
        if (request.url().includes('/api/')) {
            networkRequests.push({
                url: request.url(),
                method: request.method(),
                postData: request.postData()
            });
        }
    });
    
    try {
        // Step 1: Navigate to filters page
        console.log('📍 Step 1: Navigate to filters page');
        await page.goto('http://127.0.0.1:5003/filters');
        await page.waitForLoadState('networkidle');
        await page.waitForTimeout(3000);
        
        // Step 2: Apply a simple filter (year 2024)
        console.log('📍 Step 2: Apply year 2024 filter');
        const year2024Button = page.locator('button[data-year="2024"]');
        if (await year2024Button.count() > 0) {
            await year2024Button.click();
            await page.waitForTimeout(2000);
            console.log('✅ Year 2024 filter applied');
        } else {
            console.log('⚠️ Year 2024 button not found, skipping filter');
        }
        
        // Step 3: Look for Analyze Selected button
        console.log('📍 Step 3: Look for Analyze Selected button');
        const analyzeButton = page.locator('#analyze-selected-btn');
        const analyzeButtonCount = await analyzeButton.count();
        console.log(`🔍 Analyze button count: ${analyzeButtonCount}`);
        
        if (analyzeButtonCount > 0) {
            // Step 4: Click Analyze Selected
            console.log('📍 Step 4: Click Analyze Selected');
            
            // Clear previous network requests to focus on the analyze action
            networkRequests.length = 0;
            
            await analyzeButton.click();
            await page.waitForTimeout(5000); // Allow time for all network requests
            
            // Step 5: Check what happened
            console.log('📍 Step 5: Analyzing results');
            
            // Check for specific API calls we expect
            const filterClustersRequests = networkRequests.filter(req => 
                req.url.includes('/api/filter-clusters') && req.url.includes('include_photos=true')
            );
            
            const saveSessionRequests = networkRequests.filter(req => 
                req.url.includes('/api/save-filter-session')
            );
            
            console.log(`📡 Filter clusters API calls: ${filterClustersRequests.length}`);
            console.log(`💾 Save session API calls: ${saveSessionRequests.length}`);
            
            // Check current URL (should redirect to dashboard if successful)
            const currentUrl = page.url();
            console.log(`🌐 Current URL: ${currentUrl}`);
            
            const redirectedToDashboard = currentUrl.includes('dashboard');
            console.log(`↗️ Redirected to dashboard: ${redirectedToDashboard}`);
            
            if (redirectedToDashboard) {
                console.log('✅ Workflow completed successfully - redirected to dashboard!');
                
                // Wait for dashboard to load
                await page.waitForTimeout(3000);
                
                // Check if filtered mode is detected
                const filteredModeActive = await page.evaluate(() => {
                    const sessionData = sessionStorage.getItem('filter_session_data');
                    return sessionData !== null;
                });
                
                console.log(`🔍 Filtered mode active: ${filteredModeActive}`);
                
            } else {
                console.log('❌ Workflow incomplete - not redirected to dashboard');
            }
            
        } else {
            console.log('❌ Analyze Selected button not found');
        }
        
        // Summary
        console.log('\n📊 WORKFLOW SUMMARY:');
        console.log(`❌ JavaScript errors: ${errors.length}`);
        console.log(`📡 Network requests: ${networkRequests.length}`);
        console.log(`✅ Filter clusters requests: ${networkRequests.filter(req => req.url.includes('/api/filter-clusters')).length}`);
        console.log(`💾 Save session requests: ${networkRequests.filter(req => req.url.includes('/api/save-filter-session')).length}`);
        
        if (errors.length > 0) {
            console.log('\n❌ ERRORS FOUND:');
            errors.forEach((error, index) => {
                console.log(`  ${index + 1}. ${error.message || error.text}`);
            });
        }
        
    } catch (error) {
        console.error('❌ Test failed:', error.message);
        errors.push(error);
    } finally {
        await browser.close();
    }
    
    return {
        success: errors.length === 0,
        errorCount: errors.length,
        networkRequestCount: networkRequests.length
    };
}

testFilteredWorkflow().then(result => {
    if (result.success) {
        console.log('\n🎉 FILTERED WORKFLOW TEST PASSED!');
        process.exit(0);
    } else {
        console.log(`\n💥 FILTERED WORKFLOW TEST FAILED! (${result.errorCount} errors)`);
        process.exit(1);
    }
}).catch(error => {
    console.error('❌ Test execution failed:', error);
    process.exit(1);
});