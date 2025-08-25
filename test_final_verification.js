// Final verification of the DOM fix and workflow
const { chromium } = require('playwright');

async function testCompleteWorkflow() {
    console.log('🔬 Final verification: DOM fix and filtered analysis workflow...');
    
    const browser = await chromium.launch({ headless: false });
    const page = await browser.newPage();
    
    const errors = [];
    const networkRequests = [];
    const consoleMessages = [];
    
    // Capture JavaScript errors
    page.on('pageerror', error => {
        errors.push({ type: 'page_error', message: error.message });
        console.error('❌ Page error:', error.message);
    });
    
    // Capture console messages
    page.on('console', message => {
        if (message.type() === 'error') {
            errors.push({ type: 'console_error', message: message.text() });
            console.error('❌ Console error:', message.text());
        } else {
            consoleMessages.push({ type: message.type(), text: message.text() });
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
        // Step 1: Navigate and verify no DOM errors
        console.log('📍 Step 1: Navigate to filters and verify DOM fix');
        await page.goto('http://127.0.0.1:5003/filters');
        await page.waitForLoadState('networkidle');
        await page.waitForTimeout(3000);
        
        // Check that the .filter-panel exists (what we fixed the DOM error for)
        const filterPanelExists = await page.locator('.filter-panel').count() > 0;
        console.log(`✅ Filter panel exists: ${filterPanelExists}`);
        
        // Step 2: Apply a filter to trigger the analyze section
        console.log('📍 Step 2: Apply size filter to show analyze section');
        const minSizeInput = page.locator('#min-size');
        if (await minSizeInput.count() > 0) {
            // Set minimum size to 1MB to filter results
            await minSizeInput.fill('1');
            await page.waitForTimeout(2000);
            console.log('✅ Size filter applied (1MB minimum)');
        }
        
        // Step 3: Check if analyze section becomes visible
        console.log('📍 Step 3: Check analyze section visibility');
        const analyzeSection = page.locator('#analyze-selected-section');
        const analyzeSectionVisible = await analyzeSection.isVisible();
        console.log(`📊 Analyze section visible: ${analyzeSectionVisible}`);
        
        if (analyzeSectionVisible) {
            // Step 4: Click the analyze button
            console.log('📍 Step 4: Click analyze button');
            const analyzeButton = page.locator('button:has-text("Analyze Selected Clusters")');
            
            // Clear previous requests
            networkRequests.length = 0;
            
            await analyzeButton.click();
            await page.waitForTimeout(5000); // Wait for network requests
            
            console.log('✅ Analyze button clicked successfully');
            
            // Check network activity
            const filterClustersRequests = networkRequests.filter(req => 
                req.url.includes('/api/filter-clusters') && req.url.includes('include_photos=true')
            );
            
            const saveSessionRequests = networkRequests.filter(req => 
                req.url.includes('/api/save-filter-session')
            );
            
            console.log(`📡 Filter clusters requests: ${filterClustersRequests.length}`);
            console.log(`💾 Save session requests: ${saveSessionRequests.length}`);
            
            // Check for photo UUID extraction messages
            const uuidMessages = consoleMessages.filter(msg => 
                msg.text && msg.text.includes('photo UUIDs')
            );
            console.log(`🔍 Photo UUID messages: ${uuidMessages.length}`);
            
            // Check current URL
            const currentUrl = page.url();
            const redirected = currentUrl.includes('dashboard');
            console.log(`🌐 Current URL: ${currentUrl}`);
            console.log(`↗️ Redirected to dashboard: ${redirected}`);
            
        } else {
            console.log('⚠️ Analyze section not visible - checking current data state');
            
            // Check the JavaScript state
            const dataState = await page.evaluate(() => {
                return {
                    currentFilteredDataExists: typeof window.currentFilteredData !== 'undefined',
                    currentFilteredDataLength: window.currentFilteredData ? window.currentFilteredData.length : 0,
                    currentFiltersExists: typeof window.currentFilters !== 'undefined'
                };
            });
            
            console.log('📊 Data state:', JSON.stringify(dataState, null, 2));
        }
        
        // Step 5: Summary
        console.log('\n📊 FINAL VERIFICATION SUMMARY:');
        console.log(`❌ JavaScript errors: ${errors.length}`);
        console.log(`📄 Console messages: ${consoleMessages.length}`);
        console.log(`📡 Network requests: ${networkRequests.length}`);
        
        // Check for specific DOM error that we fixed
        const line1509Errors = errors.filter(error => 
            error.message && (
                error.message.includes('appendChild') || 
                error.message.includes('Cannot read properties of null')
            )
        );
        
        console.log(`🔧 DOM line 1509 errors: ${line1509Errors.length}`);
        
        if (line1509Errors.length === 0) {
            console.log('✅ DOM FIX VERIFIED: No line 1509 appendChild errors!');
        } else {
            console.log('❌ DOM FIX FAILED: Still seeing appendChild errors!');
        }
        
        // Non-critical 404 errors (assets)
        const assetErrors = errors.filter(error => 
            error.message && error.message.includes('404') && !error.message.includes('api')
        );
        
        const criticalErrors = errors.filter(error => 
            !error.message.includes('404') || error.message.includes('api')
        );
        
        console.log(`⚠️ Asset 404 errors (non-critical): ${assetErrors.length}`);
        console.log(`❌ Critical errors: ${criticalErrors.length}`);
        
        if (errors.length > 0) {
            console.log('\n📝 ERROR DETAILS:');
            errors.forEach((error, index) => {
                const type = error.message.includes('404') ? '⚠️' : '❌';
                console.log(`  ${index + 1}. ${type} ${error.message}`);
            });
        }
        
    } catch (error) {
        console.error('❌ Test failed:', error.message);
        errors.push({ type: 'test_error', message: error.message });
    } finally {
        await browser.close();
    }
    
    // Return success if we have no critical errors and DOM fix is verified
    const line1509Fixed = !errors.some(error => 
        error.message && (
            error.message.includes('appendChild') || 
            error.message.includes('Cannot read properties of null')
        )
    );
    
    const criticalErrorsExist = errors.some(error => 
        !error.message.includes('404') || error.message.includes('api')
    );
    
    return {
        success: line1509Fixed && !criticalErrorsExist,
        domFixVerified: line1509Fixed,
        criticalErrors: criticalErrorsExist,
        totalErrors: errors.length
    };
}

testCompleteWorkflow().then(result => {
    console.log('\n🏁 FINAL RESULTS:');
    console.log(`✅ DOM Fix Verified: ${result.domFixVerified}`);
    console.log(`❌ Critical Errors: ${result.criticalErrors}`);
    console.log(`📊 Total Errors: ${result.totalErrors}`);
    
    if (result.success) {
        console.log('\n🎉 VERIFICATION PASSED! DOM fix is working correctly.');
        process.exit(0);
    } else {
        console.log('\n💥 VERIFICATION FAILED! Issues still exist.');
        process.exit(1);
    }
}).catch(error => {
    console.error('❌ Test execution failed:', error);
    process.exit(1);
});