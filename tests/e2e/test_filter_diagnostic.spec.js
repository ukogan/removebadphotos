/**
 * Diagnostic test for filter interface - troubleshoot the stuck filter process
 */

import { test, expect } from '@playwright/test';

const BASE_URL = 'http://127.0.0.1:5003';

test('Filter Interface Diagnostic', async ({ page }) => {
    test.setTimeout(180000); // 3 minutes
    
    console.log('🔍 Starting filter interface diagnostic...');
    
    // Navigate to filters page
    await page.goto(`${BASE_URL}/filters`);
    console.log('✅ Navigated to filters page');
    
    // Wait for page to load and take screenshot
    await page.waitForLoadState('networkidle');
    await page.screenshot({ path: 'test-results/filter-diagnostic-initial.png', fullPage: true });
    console.log('✅ Page loaded, screenshot taken');
    
    // Check for basic elements
    const statsBar = await page.locator('.stats-bar').count();
    const filterPanel = await page.locator('.filter-panel').count();
    console.log(`📊 Stats bar elements: ${statsBar}`);
    console.log(`🎛️ Filter panel elements: ${filterPanel}`);
    
    // Check if stats are loaded
    const statValues = await page.locator('.stat-value').allTextContents();
    console.log(`📈 Stat values: ${JSON.stringify(statValues)}`);
    
    // Wait for stats to have actual values (not all zeros)
    console.log('⏳ Waiting for library stats to load...');
    try {
        await page.waitForFunction(() => {
            const statValues = document.querySelectorAll('.stat-value');
            if (statValues.length === 0) return false;
            
            const values = Array.from(statValues).map(el => el.textContent.trim());
            console.log('Current stat values:', values);
            
            // Check if at least one stat has a non-zero value
            return values.some(val => val !== '0' && val !== '' && val !== 'Loading...');
        }, { timeout: 60000 });
        console.log('✅ Stats loaded successfully');
    } catch (error) {
        console.log(`❌ Stats loading timeout: ${error.message}`);
        await page.screenshot({ path: 'test-results/filter-diagnostic-stats-timeout.png', fullPage: true });
    }
    
    // Check if any errors appeared
    const errorElements = await page.locator('.error-message, .alert-danger').count();
    if (errorElements > 0) {
        const errorTexts = await page.locator('.error-message, .alert-danger').allTextContents();
        console.log(`❌ Errors found: ${JSON.stringify(errorTexts)}`);
    } else {
        console.log('✅ No error messages found');
    }
    
    // Check console logs for errors
    const logs = [];
    page.on('console', msg => {
        logs.push(`${msg.type()}: ${msg.text()}`);
        console.log(`📝 Console ${msg.type()}: ${msg.text()}`);
    });
    
    // Try to find year buttons
    const yearButtons = await page.locator('[data-year]').count();
    console.log(`📅 Year buttons found: ${yearButtons}`);
    
    if (yearButtons > 0) {
        const yearValues = await page.locator('[data-year]').evaluateAll(buttons => 
            buttons.map(btn => btn.getAttribute('data-year'))
        );
        console.log(`📅 Available years: ${JSON.stringify(yearValues)}`);
        
        // Try to click on year 2024
        const year2024Button = page.locator('[data-year="2024"]');
        const year2024Count = await year2024Button.count();
        console.log(`📅 Year 2024 button count: ${year2024Count}`);
        
        if (year2024Count > 0) {
            console.log('🖱️ Attempting to click year 2024...');
            await year2024Button.click();
            await page.waitForTimeout(2000);
            console.log('✅ Year 2024 clicked');
            
            // Check if button became active
            const isActive = await year2024Button.evaluate(btn => btn.classList.contains('active'));
            console.log(`📅 Year 2024 button is active: ${isActive}`);
            
            await page.screenshot({ path: 'test-results/filter-diagnostic-year-clicked.png', fullPage: true });
        }
    }
    
    // Try to find file type checkboxes
    const fileTypeInputs = await page.locator('input[type="checkbox"]').count();
    console.log(`📁 File type checkboxes found: ${fileTypeInputs}`);
    
    if (fileTypeInputs > 0) {
        const fileTypeValues = await page.locator('input[type="checkbox"]').evaluateAll(inputs => 
            inputs.map(input => ({
                value: input.value,
                checked: input.checked,
                name: input.name
            }))
        );
        console.log(`📁 File type options: ${JSON.stringify(fileTypeValues)}`);
        
        // Try to check HEIC if available
        const heicInput = page.locator('input[value="HEIC"]');
        const heicCount = await heicInput.count();
        if (heicCount > 0) {
            console.log('🖱️ Attempting to check HEIC...');
            await heicInput.check();
            await page.waitForTimeout(1000);
            console.log('✅ HEIC checked');
            
            await page.screenshot({ path: 'test-results/filter-diagnostic-heic-checked.png', fullPage: true });
        }
    }
    
    // Try to find apply filters button
    const applyButton = page.locator('button:has-text("Apply Filters")');
    const applyCount = await applyButton.count();
    console.log(`🔘 Apply Filters button count: ${applyCount}`);
    
    if (applyCount > 0) {
        console.log('🖱️ Attempting to click Apply Filters...');
        await applyButton.click();
        console.log('✅ Apply Filters clicked');
        
        // Wait and see what happens
        await page.waitForTimeout(5000);
        await page.screenshot({ path: 'test-results/filter-diagnostic-applied.png', fullPage: true });
        
        // Check for results
        const clustersCount = await page.locator('#clusters-count').textContent().catch(() => 'not found');
        const photosCount = await page.locator('#selected-photos-count').textContent().catch(() => 'not found');
        console.log(`📊 After applying filters - Clusters: ${clustersCount}, Photos: ${photosCount}`);
        
        // Check for analyze button
        const analyzeButton = page.locator('button:has-text("Analyze Selected")');
        const analyzeCount = await analyzeButton.count();
        const analyzeVisible = analyzeCount > 0 ? await analyzeButton.isVisible() : false;
        console.log(`🔍 Analyze Selected button - Count: ${analyzeCount}, Visible: ${analyzeVisible}`);
    }
    
    // Final screenshot
    await page.screenshot({ path: 'test-results/filter-diagnostic-final.png', fullPage: true });
    
    console.log('🏁 Diagnostic complete');
    console.log(`📝 Console logs (${logs.length} entries):`);
    logs.forEach(log => console.log(`  ${log}`));
});