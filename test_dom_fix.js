// Simple test to verify DOM fix
const { chromium } = require('playwright');

async function testDOMFix() {
    console.log('🔧 Testing DOM fix for line 1509 error...');
    
    const browser = await chromium.launch({ headless: false });
    const page = await browser.newPage();
    
    const errors = [];
    
    // Capture JavaScript errors
    page.on('pageerror', error => {
        errors.push(error);
        console.error('❌ Page error:', error.message);
    });
    
    page.on('console', message => {
        if (message.type() === 'error') {
            console.error('❌ Console error:', message.text());
            errors.push({ type: 'console', text: message.text() });
        } else {
            console.log('📄 Console:', message.text());
        }
    });
    
    try {
        console.log('🌐 Navigating to filters page...');
        await page.goto('http://127.0.0.1:5003/filters');
        await page.waitForLoadState('networkidle');
        await page.waitForTimeout(3000);
        
        console.log('✅ Page loaded successfully');
        
        // Check if our problematic element (.filter-panel) exists
        const filterPanelExists = await page.locator('.filter-panel').count() > 0;
        console.log(`📋 Filter panel exists: ${filterPanelExists}`);
        
        // Try to trigger the smart recommendations function if possible
        const hasAnalyzeFunction = await page.evaluate(() => {
            return typeof window.displaySmartRecommendations === 'function';
        });
        
        if (hasAnalyzeFunction) {
            console.log('🎯 Testing smart recommendations function...');
            await page.evaluate(() => {
                // Try to trigger the function with test data
                if (window.displaySmartRecommendations) {
                    try {
                        window.displaySmartRecommendations([
                            {
                                title: 'Test Recommendation',
                                description: 'Test description',
                                stats: 'Test stats',
                                filter_key: 'test',
                                filter_value: 'test'
                            }
                        ]);
                        console.log('✅ displaySmartRecommendations function executed without error');
                    } catch (e) {
                        console.error('❌ Error in displaySmartRecommendations:', e.message);
                        throw e;
                    }
                }
            });
        }
        
        // Check if the recommendations panel was created successfully
        const recommendationsPanel = await page.locator('#smart-recommendations').count();
        console.log(`💡 Smart recommendations panel count: ${recommendationsPanel}`);
        
        if (errors.length === 0) {
            console.log('✅ DOM fix successful - no JavaScript errors detected!');
        } else {
            console.log(`❌ Found ${errors.length} errors:`);
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
    
    return errors.length === 0;
}

testDOMFix().then(success => {
    if (success) {
        console.log('\n🎉 DOM fix verification PASSED!');
        process.exit(0);
    } else {
        console.log('\n💥 DOM fix verification FAILED!');
        process.exit(1);
    }
}).catch(error => {
    console.error('❌ Test execution failed:', error);
    process.exit(1);
});