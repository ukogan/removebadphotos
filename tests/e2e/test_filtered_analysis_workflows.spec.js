/**
 * Comprehensive E2E Tests for Filtered Analysis Workflows
 * Testing 5 different filter combinations to validate photo UUID collection
 * and identify which filter types succeed vs fail
 */

import { test, expect } from '@playwright/test';

// Test configuration
const BASE_URL = 'http://127.0.0.1:5003';
const TEST_TIMEOUT = 120000; // 2 minutes per test

// Helper function to wait for filters interface to be ready
async function waitForFiltersReady(page) {
    await page.waitForSelector('.stats-bar', { timeout: 30000 });
    await page.waitForSelector('.filter-panel', { timeout: 30000 });
    // Wait for stats to populate (indicates data is loaded)
    await page.waitForFunction(() => {
        const statValues = document.querySelectorAll('.stat-value');
        return statValues.length > 0 && 
               Array.from(statValues).some(el => el.textContent.trim() !== '0' && el.textContent.trim() !== '');
    }, { timeout: 30000 });
}

// Helper function to apply filters and capture results
async function applyFiltersAndCapture(page, filters, testName) {
    console.log(`\n=== ${testName} ===`);
    
    // Apply year filter if specified
    if (filters.year) {
        await page.click(`[data-year="${filters.year}"]`);
        console.log(`Applied year filter: ${filters.year}`);
        await page.waitForTimeout(1000); // Wait for UI update
    }
    
    // Apply size filters if specified
    if (filters.minSizeMB) {
        const minSlider = page.locator('#minSize');
        await minSlider.fill(filters.minSizeMB.toString());
        console.log(`Applied min size filter: ${filters.minSizeMB}MB`);
        await page.waitForTimeout(1000);
    }
    
    // Apply file type filter if specified
    if (filters.fileType) {
        await page.check(`input[value="${filters.fileType}"]`);
        console.log(`Applied file type filter: ${filters.fileType}`);
        await page.waitForTimeout(1000);
    }
    
    // Apply filters button
    await page.click('button:has-text("Apply Filters")');
    console.log('Clicked Apply Filters button');
    
    // Wait for results to load
    await page.waitForTimeout(3000);
    
    // Capture filter results
    const results = await page.evaluate(() => {
        const clustersCount = document.querySelector('#clusters-count')?.textContent || '0';
        const photosCount = document.querySelector('#selected-photos-count')?.textContent || '0';
        const analyzeButton = document.querySelector('button:has-text("Analyze Selected")');
        
        return {
            clustersCount: parseInt(clustersCount),
            photosCount: parseInt(photosCount),
            analyzeButtonVisible: analyzeButton && analyzeButton.offsetParent !== null,
            analyzeButtonEnabled: analyzeButton && !analyzeButton.disabled
        };
    });
    
    console.log(`Filter Results - Clusters: ${results.clustersCount}, Photos: ${results.photosCount}`);
    console.log(`Analyze Button - Visible: ${results.analyzeButtonVisible}, Enabled: ${results.analyzeButtonEnabled}`);
    
    return results;
}

// Helper function to test the full analyze workflow
async function testAnalyzeWorkflow(page, testName, filterResults) {
    console.log(`\n--- Testing Analyze Workflow for ${testName} ---`);
    
    if (!filterResults.analyzeButtonVisible || !filterResults.analyzeButtonEnabled) {
        console.log('❌ Analyze button not available - skipping workflow test');
        return {
            success: false,
            error: 'Analyze button not available',
            stage: 'button_check'
        };
    }
    
    if (filterResults.clustersCount === 0) {
        console.log('❌ No clusters available - skipping workflow test');
        return {
            success: false,
            error: 'No clusters to analyze',
            stage: 'cluster_check'
        };
    }
    
    try {
        // Start analysis
        console.log('🚀 Starting analysis workflow...');
        await page.click('button:has-text("Analyze Selected")');
        
        // Wait for navigation to dashboard
        await page.waitForURL(/\/dashboard/, { timeout: 30000 });
        console.log('✅ Successfully navigated to dashboard');
        
        // Wait for dashboard to load
        await page.waitForSelector('.dashboard-header', { timeout: 30000 });
        console.log('✅ Dashboard loaded');
        
        // Check for filtered mode indicators
        const dashboardState = await page.evaluate(() => {
            const header = document.querySelector('.dashboard-header h1')?.textContent || '';
            const filteredIndicator = document.querySelector('.filtered-mode-indicator')?.textContent || '';
            const analysisStatus = document.querySelector('.analysis-status')?.textContent || '';
            
            return {
                headerText: header,
                filteredIndicator,
                analysisStatus,
                isFilteredMode: header.includes('Filtered') || filteredIndicator.includes('filtered')
            };
        });
        
        console.log(`Dashboard State - Header: "${dashboardState.headerText}"`);
        console.log(`Filtered Mode: ${dashboardState.isFilteredMode}`);
        console.log(`Analysis Status: "${dashboardState.analysisStatus}"`);
        
        // Wait for analysis to complete or show progress
        let analysisCompleted = false;
        let analysisError = null;
        
        for (let i = 0; i < 60; i++) { // Wait up to 60 seconds
            const status = await page.evaluate(() => {
                const progressElement = document.querySelector('.progress-bar');
                const errorElement = document.querySelector('.error-message, .alert-danger');
                const completeElement = document.querySelector('.analysis-complete, .results-summary');
                
                return {
                    hasProgress: progressElement !== null,
                    hasError: errorElement !== null,
                    hasComplete: completeElement !== null,
                    errorText: errorElement?.textContent || '',
                    progressText: progressElement?.textContent || ''
                };
            });
            
            if (status.hasError) {
                analysisError = status.errorText;
                console.log(`❌ Analysis error detected: ${analysisError}`);
                break;
            }
            
            if (status.hasComplete) {
                analysisCompleted = true;
                console.log('✅ Analysis completed successfully');
                break;
            }
            
            if (status.hasProgress) {
                console.log(`⏳ Analysis in progress: ${status.progressText}`);
            }
            
            await page.waitForTimeout(1000);
        }
        
        if (analysisError) {
            return {
                success: false,
                error: analysisError,
                stage: 'analysis_execution',
                dashboardState
            };
        }
        
        if (!analysisCompleted) {
            return {
                success: false,
                error: 'Analysis timeout - did not complete within 60 seconds',
                stage: 'analysis_timeout',
                dashboardState
            };
        }
        
        // Capture final results
        const finalResults = await page.evaluate(() => {
            const duplicateGroups = document.querySelectorAll('.duplicate-group').length;
            const totalPhotos = document.querySelector('.total-photos-analyzed')?.textContent || '0';
            const duplicatesFound = document.querySelector('.duplicates-found')?.textContent || '0';
            
            return {
                duplicateGroups,
                totalPhotos: parseInt(totalPhotos),
                duplicatesFound: parseInt(duplicatesFound)
            };
        });
        
        console.log(`✅ Analysis Results - Groups: ${finalResults.duplicateGroups}, Photos: ${finalResults.totalPhotos}, Duplicates: ${finalResults.duplicatesFound}`);
        
        return {
            success: true,
            stage: 'completed',
            dashboardState,
            finalResults
        };
        
    } catch (error) {
        console.log(`❌ Workflow error: ${error.message}`);
        return {
            success: false,
            error: error.message,
            stage: 'workflow_exception'
        };
    }
}

// Test Path 1: Recent Year (2024) + HEIC file type
test('Filter Path 1: Year 2024 + HEIC file type', async ({ page }) => {
    test.setTimeout(TEST_TIMEOUT);
    
    await page.goto(`${BASE_URL}/filters`);
    await waitForFiltersReady(page);
    
    const filterResults = await applyFiltersAndCapture(page, {
        year: 2024,
        fileType: 'HEIC'
    }, 'Path 1: Year 2024 + HEIC');
    
    // Test the analyze workflow
    const workflowResults = await testAnalyzeWorkflow(page, 'Path 1', filterResults);
    
    // Assertions
    expect(filterResults.clustersCount).toBeGreaterThan(0);
    expect(filterResults.photosCount).toBeGreaterThan(0);
    expect(filterResults.analyzeButtonVisible).toBe(true);
    
    if (workflowResults.success) {
        expect(workflowResults.finalResults.totalPhotos).toBeGreaterThan(0);
    }
    
    console.log(`\n✅ Path 1 Test Results:
    Filter Results: ${JSON.stringify(filterResults, null, 2)}
    Workflow Results: ${JSON.stringify(workflowResults, null, 2)}`);
});

// Test Path 2: Size-based filtering (Min 2MB)
test('Filter Path 2: Min size 2MB', async ({ page }) => {
    test.setTimeout(TEST_TIMEOUT);
    
    await page.goto(`${BASE_URL}/filters`);
    await waitForFiltersReady(page);
    
    const filterResults = await applyFiltersAndCapture(page, {
        minSizeMB: 2
    }, 'Path 2: Min Size 2MB');
    
    const workflowResults = await testAnalyzeWorkflow(page, 'Path 2', filterResults);
    
    expect(filterResults.clustersCount).toBeGreaterThan(0);
    expect(filterResults.photosCount).toBeGreaterThan(0);
    expect(filterResults.analyzeButtonVisible).toBe(true);
    
    if (workflowResults.success) {
        expect(workflowResults.finalResults.totalPhotos).toBeGreaterThan(0);
    }
    
    console.log(`\n✅ Path 2 Test Results:
    Filter Results: ${JSON.stringify(filterResults, null, 2)}
    Workflow Results: ${JSON.stringify(workflowResults, null, 2)}`);
});

// Test Path 3: Year 2023 + JPG file type
test('Filter Path 3: Year 2023 + JPG file type', async ({ page }) => {
    test.setTimeout(TEST_TIMEOUT);
    
    await page.goto(`${BASE_URL}/filters`);
    await waitForFiltersReady(page);
    
    const filterResults = await applyFiltersAndCapture(page, {
        year: 2023,
        fileType: 'JPG'
    }, 'Path 3: Year 2023 + JPG');
    
    const workflowResults = await testAnalyzeWorkflow(page, 'Path 3', filterResults);
    
    expect(filterResults.clustersCount).toBeGreaterThan(0);
    expect(filterResults.photosCount).toBeGreaterThan(0);
    expect(filterResults.analyzeButtonVisible).toBe(true);
    
    if (workflowResults.success) {
        expect(workflowResults.finalResults.totalPhotos).toBeGreaterThan(0);
    }
    
    console.log(`\n✅ Path 3 Test Results:
    Filter Results: ${JSON.stringify(filterResults, null, 2)}
    Workflow Results: ${JSON.stringify(workflowResults, null, 2)}`);
});

// Test Path 4: Conservative size filter (Min 1MB)
test('Filter Path 4: Min size 1MB (conservative)', async ({ page }) => {
    test.setTimeout(TEST_TIMEOUT);
    
    await page.goto(`${BASE_URL}/filters`);
    await waitForFiltersReady(page);
    
    const filterResults = await applyFiltersAndCapture(page, {
        minSizeMB: 1
    }, 'Path 4: Min Size 1MB');
    
    const workflowResults = await testAnalyzeWorkflow(page, 'Path 4', filterResults);
    
    expect(filterResults.clustersCount).toBeGreaterThan(0);
    expect(filterResults.photosCount).toBeGreaterThan(0);
    expect(filterResults.analyzeButtonVisible).toBe(true);
    
    if (workflowResults.success) {
        expect(workflowResults.finalResults.totalPhotos).toBeGreaterThan(0);
    }
    
    console.log(`\n✅ Path 4 Test Results:
    Filter Results: ${JSON.stringify(filterResults, null, 2)}
    Workflow Results: ${JSON.stringify(workflowResults, null, 2)}`);
});

// Test Path 5: Multiple filters (Year 2024 + Min 1MB + HEIC)
test('Filter Path 5: Multiple filters (2024 + 1MB + HEIC)', async ({ page }) => {
    test.setTimeout(TEST_TIMEOUT);
    
    await page.goto(`${BASE_URL}/filters`);
    await waitForFiltersReady(page);
    
    const filterResults = await applyFiltersAndCapture(page, {
        year: 2024,
        minSizeMB: 1,
        fileType: 'HEIC'
    }, 'Path 5: Multiple Filters');
    
    const workflowResults = await testAnalyzeWorkflow(page, 'Path 5', filterResults);
    
    expect(filterResults.clustersCount).toBeGreaterThan(0);
    expect(filterResults.photosCount).toBeGreaterThan(0);
    expect(filterResults.analyzeButtonVisible).toBe(true);
    
    if (workflowResults.success) {
        expect(workflowResults.finalResults.totalPhotos).toBeGreaterThan(0);
    }
    
    console.log(`\n✅ Path 5 Test Results:
    Filter Results: ${JSON.stringify(filterResults, null, 2)}
    Workflow Results: ${JSON.stringify(workflowResults, null, 2)}`);
});

// Comprehensive summary test that runs after all individual tests
test('Filter Analysis Summary: Cross-path comparison', async ({ page }) => {
    test.setTimeout(TEST_TIMEOUT * 2); // Extra time for comprehensive test
    
    const testPaths = [
        { name: 'Path 1: 2024 + HEIC', filters: { year: 2024, fileType: 'HEIC' } },
        { name: 'Path 2: Min 2MB', filters: { minSizeMB: 2 } },
        { name: 'Path 3: 2023 + JPG', filters: { year: 2023, fileType: 'JPG' } },
        { name: 'Path 4: Min 1MB', filters: { minSizeMB: 1 } },
        { name: 'Path 5: 2024 + 1MB + HEIC', filters: { year: 2024, minSizeMB: 1, fileType: 'HEIC' } }
    ];
    
    const summaryResults = [];
    
    for (const testPath of testPaths) {
        await page.goto(`${BASE_URL}/filters`);
        await waitForFiltersReady(page);
        
        try {
            const filterResults = await applyFiltersAndCapture(page, testPath.filters, testPath.name);
            const workflowResults = await testAnalyzeWorkflow(page, testPath.name, filterResults);
            
            summaryResults.push({
                path: testPath.name,
                filters: testPath.filters,
                filterResults,
                workflowResults,
                success: workflowResults.success
            });
        } catch (error) {
            summaryResults.push({
                path: testPath.name,
                filters: testPath.filters,
                error: error.message,
                success: false
            });
        }
    }
    
    // Generate comprehensive report
    console.log('\n' + '='.repeat(80));
    console.log('COMPREHENSIVE FILTERED ANALYSIS TEST SUMMARY');
    console.log('='.repeat(80));
    
    let successCount = 0;
    let failureCount = 0;
    
    summaryResults.forEach(result => {
        console.log(`\n${result.path}:`);
        console.log(`  Filters: ${JSON.stringify(result.filters)}`);
        
        if (result.success) {
            successCount++;
            console.log(`  ✅ SUCCESS`);
            console.log(`  Clusters: ${result.filterResults.clustersCount}`);
            console.log(`  Photos: ${result.filterResults.photosCount}`);
            if (result.workflowResults.finalResults) {
                console.log(`  Analysis Results: ${JSON.stringify(result.workflowResults.finalResults)}`);
            }
        } else {
            failureCount++;
            console.log(`  ❌ FAILURE`);
            console.log(`  Error: ${result.workflowResults?.error || result.error}`);
            console.log(`  Stage: ${result.workflowResults?.stage || 'unknown'}`);
        }
    });
    
    console.log(`\n${'='.repeat(40)}`);
    console.log(`SUMMARY: ${successCount} successes, ${failureCount} failures`);
    console.log(`Success Rate: ${((successCount / testPaths.length) * 100).toFixed(1)}%`);
    console.log('='.repeat(40));
    
    // Write detailed report to file
    const reportData = {
        timestamp: new Date().toISOString(),
        summary: {
            totalPaths: testPaths.length,
            successes: successCount,
            failures: failureCount,
            successRate: (successCount / testPaths.length) * 100
        },
        results: summaryResults
    };
    
    await page.evaluate((reportData) => {
        console.log('DETAILED REPORT DATA:', JSON.stringify(reportData, null, 2));
    }, reportData);
    
    // At least one path should succeed for the overall test to pass
    expect(successCount).toBeGreaterThan(0);
});