// Quick test to verify filter fixes are working
const { chromium } = require('playwright');

async function testFiltersFix() {
    console.log('🧪 Testing filters fixes...');
    
    const browser = await chromium.launch({ headless: false });
    const page = await browser.newPage();
    
    try {
        console.log('📍 Step 1: Navigate to filters page');
        await page.goto('http://127.0.0.1:5003/filters');
        await page.waitForLoadState('networkidle');
        await page.waitForTimeout(3000);
        
        console.log('📍 Step 2: Check for NaN/undefined issues');
        
        // Check potential savings display
        const potentialSavings = await page.locator('#potential-savings').textContent();
        console.log(`💰 Potential savings: "${potentialSavings}"`);
        const hasNaN = potentialSavings.includes('NaN');
        console.log(`❌ Contains NaN: ${hasNaN}`);
        
        // Check total clusters display
        const totalClusters = await page.locator('#total-clusters').textContent();
        console.log(`📊 Total clusters: "${totalClusters}"`);
        
        // Check for smart recommendations
        const smartRecs = await page.locator('.smart-recommendations').count();
        console.log(`💡 Smart recommendations sections: ${smartRecs}`);
        
        if (smartRecs > 0) {
            const recContent = await page.locator('.smart-recommendations').textContent();
            console.log(`💡 Recommendation content: "${recContent.substring(0, 100)}..."`);
            const hasUndefined = recContent.includes('undefined');
            console.log(`❌ Contains undefined: ${hasUndefined}`);
        }
        
        console.log('📍 Step 3: Test a simple filter');
        
        // Try to apply a year filter
        const yearBtn = page.locator('[data-year="2025"]').first();
        if (await yearBtn.count() > 0) {
            await yearBtn.click();
            await page.waitForTimeout(2000);
            console.log('✅ Applied 2025 year filter');
            
            // Check if analyze section appears
            const analyzeSection = page.locator('#analyze-selected-section');
            const isVisible = await analyzeSection.isVisible();
            console.log(`📊 Analyze section visible: ${isVisible}`);
        }
        
        const success = !hasNaN && (!smartRecs || smartRecs > 0);
        console.log(`🏁 Test result: ${success ? 'PASSED' : 'FAILED'}`);
        
        return { success };
        
    } catch (error) {
        console.error('❌ Test failed:', error.message);
        return { success: false };
    } finally {
        await browser.close();
    }
}

testFiltersFix().then(result => {
    console.log(`\n🎯 FILTERS FIX TEST: ${result.success ? 'SUCCESS' : 'FAILED'}`);
    process.exit(result.success ? 0 : 1);
}).catch(error => {
    console.error('❌ Test execution failed:', error);
    process.exit(1);
});