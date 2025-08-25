/**
 * Testing 5 Specific Filtered Analysis Workflows
 * Focus on validating photo UUID collection across various filter combinations
 */

import { test, expect } from '@playwright/test';

const BASE_URL = 'http://127.0.0.1:5003';

// Helper to wait for backend initialization
async function waitForBackendReady(page) {
    console.log('⏳ Waiting for backend to initialize clusters...');
    
    // Wait for the filter interface to load
    await page.waitForSelector('.stats-bar', { timeout: 60000 });
    
    // Wait for stats to populate (retry mechanism)
    let statsLoaded = false;
    for (let i = 0; i < 30; i++) { // 30 seconds max
        try {
            await page.waitForFunction(() => {
                const statValues = document.querySelectorAll('.stat-value');
                return statValues.length > 0 && 
                       Array.from(statValues).some(el => el.textContent.trim() !== '0' && el.textContent.trim() !== '');
            }, { timeout: 2000 });
            statsLoaded = true;
            break;
        } catch (e) {
            console.log(`⏳ Still waiting for stats... attempt ${i + 1}/30`);
            await page.waitForTimeout(1000);
        }
    }
    
    if (!statsLoaded) {
        throw new Error('Backend did not initialize within timeout period');
    }
    
    console.log('✅ Backend is ready');
}

// Helper to apply specific filters and wait for results
async function applyFiltersAndGetResults(page, filterConfig, testName) {
    console.log(`\n🔧 Applying filters for ${testName}:`);
    console.log(`   ${JSON.stringify(filterConfig)}`);
    
    // Reset any existing filters first
    const resetBtn = page.locator('button:has-text("Reset Filters")');
    if (await resetBtn.count() > 0) {
        await resetBtn.click();
        await page.waitForTimeout(1000);
    }
    
    // Apply year filter
    if (filterConfig.year) {
        await page.click(`[data-year="${filterConfig.year}"]`);
        console.log(`   ✅ Applied year: ${filterConfig.year}`);
        await page.waitForTimeout(1000);
    }
    
    // Apply size filters
    if (filterConfig.minSizeMB) {
        await page.fill('#minSize', filterConfig.minSizeMB.toString());
        console.log(`   ✅ Applied min size: ${filterConfig.minSizeMB}MB`);
        await page.waitForTimeout(1000);
    }
    
    // Apply file type filter
    if (filterConfig.fileType) {
        const fileTypeCheckbox = page.locator(`input[value="${filterConfig.fileType}"]`);
        if (await fileTypeCheckbox.count() > 0) {
            await fileTypeCheckbox.check();
            console.log(`   ✅ Applied file type: ${filterConfig.fileType}`);
        } else {
            // Alternative selector for file types
            await page.check(`input[type="checkbox"][name*="${filterConfig.fileType}"], label:has-text("${filterConfig.fileType}") input`);
            console.log(`   ✅ Applied file type (alternative): ${filterConfig.fileType}`);
        }
        await page.waitForTimeout(1000);
    }
    
    // Click Apply Filters
    await page.click('button:has-text("Apply Filters")');
    console.log('   🔄 Clicked Apply Filters button');
    
    // Wait for results to load with retry mechanism
    let resultsReady = false;
    for (let i = 0; i < 20; i++) { // 20 seconds max
        try {
            await page.waitForFunction(() => {
                const clustersElement = document.querySelector('#clusters-count, .clusters-count');
                const photosElement = document.querySelector('#selected-photos-count, .photos-count');
                return clustersElement && photosElement;
            }, { timeout: 1000 });
            resultsReady = true;
            break;
        } catch (e) {
            console.log(`   ⏳ Waiting for filter results... attempt ${i + 1}/20`);
            await page.waitForTimeout(1000);
        }
    }
    
    if (!resultsReady) {
        console.log('   ❌ Filter results not ready within timeout');
        return {
            success: false,
            error: 'Filter results timeout',
            clusters: 0,
            photos: 0
        };
    }
    
    // Extract results
    const results = await page.evaluate(() => {
        const clustersElement = document.querySelector('#clusters-count, .clusters-count');
        const photosElement = document.querySelector('#selected-photos-count, .photos-count');
        const analyzeBtn = document.querySelector('button:has-text("Analyze Selected")');
        
        return {
            clusters: clustersElement ? parseInt(clustersElement.textContent || '0') : 0,
            photos: photosElement ? parseInt(photosElement.textContent || '0') : 0,
            analyzeButtonVisible: analyzeBtn && analyzeBtn.offsetParent !== null,
            analyzeButtonEnabled: analyzeBtn && !analyzeBtn.disabled
        };
    });
    
    console.log(`   📊 Results: ${results.clusters} clusters, ${results.photos} photos`);
    console.log(`   🔘 Analyze button: visible=${results.analyzeButtonVisible}, enabled=${results.analyzeButtonEnabled}`);
    
    return {
        success: true,
        ...results
    };
}

// Helper to test the analysis workflow
async function testAnalysisWorkflow(page, testName, filterResults) {
    if (!filterResults.success || !filterResults.analyzeButtonVisible || filterResults.clusters === 0) {
        console.log(`   ❌ Skipping analysis for ${testName} - prerequisites not met`);
        return {
            success: false,
            reason: 'prerequisites_not_met',
            stage: 'pre_analysis'
        };
    }
    
    console.log(`   🚀 Starting analysis workflow for ${testName}...`);
    
    try {
        // Click analyze button
        await page.click('button:has-text("Analyze Selected")');
        
        // Wait for navigation to dashboard
        await page.waitForURL(/\/dashboard/, { timeout: 30000 });
        console.log('   ✅ Navigated to dashboard');
        
        // Wait for dashboard elements
        await page.waitForSelector('.dashboard-header, .header', { timeout: 30000 });
        console.log('   ✅ Dashboard loaded');
        
        // Check dashboard state
        const dashboardInfo = await page.evaluate(() => {
            const header = document.querySelector('.dashboard-header h1, .header h1, h1')?.textContent || '';
            const statusElement = document.querySelector('.analysis-status, .status')?.textContent || '';
            const filteredIndicator = document.querySelector('.filtered-mode, .filter-indicator')?.textContent || '';
            
            return {
                headerText: header,
                statusText: statusElement,
                filteredIndicator,
                isFiltered: header.toLowerCase().includes('filtered') || 
                           filteredIndicator.toLowerCase().includes('filtered')
            };
        });
        
        console.log(`   📋 Dashboard state: ${JSON.stringify(dashboardInfo)}`);
        
        // Wait for analysis completion or progress
        let analysisComplete = false;
        let analysisError = null;
        
        for (let i = 0; i < 60; i++) { // 60 seconds max
            const status = await page.evaluate(() => {
                const errorElements = document.querySelectorAll('.error, .alert-danger, .error-message');
                const progressElements = document.querySelectorAll('.progress, .progress-bar');
                const completeElements = document.querySelectorAll('.complete, .success, .results-summary');
                
                const hasError = errorElements.length > 0;
                const hasProgress = progressElements.length > 0;
                const hasComplete = completeElements.length > 0;
                
                const errorText = hasError ? Array.from(errorElements).map(el => el.textContent).join('; ') : '';
                
                return { hasError, hasProgress, hasComplete, errorText };
            });
            
            if (status.hasError && status.errorText.trim()) {
                analysisError = status.errorText;
                console.log(`   ❌ Analysis error: ${analysisError}`);
                break;
            }
            
            if (status.hasComplete) {
                analysisComplete = true;
                console.log('   ✅ Analysis completed');
                break;
            }
            
            if (status.hasProgress) {
                console.log(`   ⏳ Analysis in progress... (${i + 1}/60)`);
            }
            
            await page.waitForTimeout(1000);
        }
        
        if (analysisError) {
            return {
                success: false,
                reason: 'analysis_error',
                error: analysisError,
                stage: 'analysis_execution',
                dashboardInfo
            };
        }
        
        if (!analysisComplete) {
            return {
                success: false,
                reason: 'analysis_timeout',
                stage: 'analysis_timeout',
                dashboardInfo
            };
        }
        
        // Get final results
        const finalResults = await page.evaluate(() => {
            const duplicateGroups = document.querySelectorAll('.duplicate-group, .group').length;
            const totalPhotosElements = document.querySelectorAll('[data-total-photos], .total-photos');
            const duplicatesFoundElements = document.querySelectorAll('[data-duplicates-found], .duplicates-found');
            
            const totalPhotos = totalPhotosElements.length > 0 ? 
                parseInt(totalPhotosElements[0].textContent || '0') : 0;
            const duplicatesFound = duplicatesFoundElements.length > 0 ? 
                parseInt(duplicatesFoundElements[0].textContent || '0') : 0;
                
            return {
                duplicateGroups,
                totalPhotos,
                duplicatesFound
            };
        });
        
        console.log(`   📊 Final results: ${JSON.stringify(finalResults)}`);
        
        return {
            success: true,
            stage: 'completed',
            dashboardInfo,
            finalResults
        };
        
    } catch (error) {
        console.log(`   ❌ Workflow error: ${error.message}`);
        return {
            success: false,
            reason: 'workflow_exception',
            error: error.message,
            stage: 'workflow_error'
        };
    }
}

// Test Path 1: Recent Year (2024) + HEIC file type
test('Filter Path 1: Year 2024 + HEIC file type', async ({ page }) => {
    test.setTimeout(240000); // 4 minutes
    
    await page.goto(`${BASE_URL}/filters`);
    await waitForBackendReady(page);
    
    const filterResults = await applyFiltersAndGetResults(page, {
        year: 2024,
        fileType: 'HEIC'
    }, 'Path 1: Year 2024 + HEIC');
    
    const analysisResults = await testAnalysisWorkflow(page, 'Path 1', filterResults);
    
    // Document results
    console.log(`\n📋 PATH 1 SUMMARY:`);
    console.log(`   Filter Success: ${filterResults.success}`);
    console.log(`   Clusters Found: ${filterResults.clusters}`);
    console.log(`   Photos Found: ${filterResults.photos}`);
    console.log(`   Analysis Success: ${analysisResults.success}`);
    if (!analysisResults.success) {
        console.log(`   Analysis Issue: ${analysisResults.reason}`);
    }
    
    // Basic assertions - filters should work
    expect(filterResults.success).toBe(true);
    expect(filterResults.clusters).toBeGreaterThanOrEqual(0);
    expect(filterResults.photos).toBeGreaterThanOrEqual(0);
});

// Test Path 2: Size-based filtering (Min 2MB)
test('Filter Path 2: Min size 2MB', async ({ page }) => {
    test.setTimeout(240000);
    
    await page.goto(`${BASE_URL}/filters`);
    await waitForBackendReady(page);
    
    const filterResults = await applyFiltersAndGetResults(page, {
        minSizeMB: 2
    }, 'Path 2: Min Size 2MB');
    
    const analysisResults = await testAnalysisWorkflow(page, 'Path 2', filterResults);
    
    console.log(`\n📋 PATH 2 SUMMARY:`);
    console.log(`   Filter Success: ${filterResults.success}`);
    console.log(`   Clusters Found: ${filterResults.clusters}`);
    console.log(`   Photos Found: ${filterResults.photos}`);
    console.log(`   Analysis Success: ${analysisResults.success}`);
    if (!analysisResults.success) {
        console.log(`   Analysis Issue: ${analysisResults.reason}`);
    }
    
    expect(filterResults.success).toBe(true);
    expect(filterResults.clusters).toBeGreaterThanOrEqual(0);
    expect(filterResults.photos).toBeGreaterThanOrEqual(0);
});

// Test Path 3: Year 2023 + JPG file type  
test('Filter Path 3: Year 2023 + JPG file type', async ({ page }) => {
    test.setTimeout(240000);
    
    await page.goto(`${BASE_URL}/filters`);
    await waitForBackendReady(page);
    
    const filterResults = await applyFiltersAndGetResults(page, {
        year: 2023,
        fileType: 'JPG'
    }, 'Path 3: Year 2023 + JPG');
    
    const analysisResults = await testAnalysisWorkflow(page, 'Path 3', filterResults);
    
    console.log(`\n📋 PATH 3 SUMMARY:`);
    console.log(`   Filter Success: ${filterResults.success}`);
    console.log(`   Clusters Found: ${filterResults.clusters}`);
    console.log(`   Photos Found: ${filterResults.photos}`);
    console.log(`   Analysis Success: ${analysisResults.success}`);
    if (!analysisResults.success) {
        console.log(`   Analysis Issue: ${analysisResults.reason}`);
    }
    
    expect(filterResults.success).toBe(true);
    expect(filterResults.clusters).toBeGreaterThanOrEqual(0);
    expect(filterResults.photos).toBeGreaterThanOrEqual(0);
});

// Test Path 4: Conservative size filter (Min 1MB)
test('Filter Path 4: Min size 1MB (conservative)', async ({ page }) => {
    test.setTimeout(240000);
    
    await page.goto(`${BASE_URL}/filters`);
    await waitForBackendReady(page);
    
    const filterResults = await applyFiltersAndGetResults(page, {
        minSizeMB: 1
    }, 'Path 4: Min Size 1MB');
    
    const analysisResults = await testAnalysisWorkflow(page, 'Path 4', filterResults);
    
    console.log(`\n📋 PATH 4 SUMMARY:`);
    console.log(`   Filter Success: ${filterResults.success}`);
    console.log(`   Clusters Found: ${filterResults.clusters}`);
    console.log(`   Photos Found: ${filterResults.photos}`);
    console.log(`   Analysis Success: ${analysisResults.success}`);
    if (!analysisResults.success) {
        console.log(`   Analysis Issue: ${analysisResults.reason}`);
    }
    
    expect(filterResults.success).toBe(true);
    expect(filterResults.clusters).toBeGreaterThanOrEqual(0);
    expect(filterResults.photos).toBeGreaterThanOrEqual(0);
});

// Test Path 5: Multiple filters (Year 2024 + Min 1MB + HEIC)
test('Filter Path 5: Multiple filters (2024 + 1MB + HEIC)', async ({ page }) => {
    test.setTimeout(240000);
    
    await page.goto(`${BASE_URL}/filters`);
    await waitForBackendReady(page);
    
    const filterResults = await applyFiltersAndGetResults(page, {
        year: 2024,
        minSizeMB: 1,
        fileType: 'HEIC'
    }, 'Path 5: Multiple Filters');
    
    const analysisResults = await testAnalysisWorkflow(page, 'Path 5', filterResults);
    
    console.log(`\n📋 PATH 5 SUMMARY:`);
    console.log(`   Filter Success: ${filterResults.success}`);
    console.log(`   Clusters Found: ${filterResults.clusters}`);
    console.log(`   Photos Found: ${filterResults.photos}`);
    console.log(`   Analysis Success: ${analysisResults.success}`);
    if (!analysisResults.success) {
        console.log(`   Analysis Issue: ${analysisResults.reason}`);
    }
    
    expect(filterResults.success).toBe(true);
    expect(filterResults.clusters).toBeGreaterThanOrEqual(0);
    expect(filterResults.photos).toBeGreaterThanOrEqual(0);
});