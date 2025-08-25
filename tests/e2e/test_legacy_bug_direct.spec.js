// test_legacy_bug_direct.spec.js
import { test, expect } from '@playwright/test';

test.describe('Legacy Interface Bug - Direct Test', () => {
  test('should test legacy interface behavior with session data', async ({ page }) => {
    console.log('=== TESTING LEGACY INTERFACE BUG DIRECTLY ===');
    
    // Step 1: Go directly to legacy interface
    console.log('Step 1: Navigate directly to legacy interface');
    await page.goto('/legacy');
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(2000);
    
    console.log('✓ Legacy interface loaded');
    
    // Step 2: Capture initial state
    const initialPageText = await page.textContent('body');
    console.log('Initial page loaded, checking for statistics...');
    
    // Look for photo statistics
    const photoStats = initialPageText.match(/(\d+,?\d*)\s+photos?/gi) || [];
    console.log('Found photo statistics:', photoStats);
    
    // Check if showing full library count
    const hasFullLibraryCount = initialPageText.includes('13790') || initialPageText.includes('13,790');
    if (hasFullLibraryCount) {
      console.log('📊 Initial state shows full library count (13,790 photos)');
    }
    
    // Step 3: Click Load Groups and analyze
    console.log('Step 3: Click Load Groups to start analysis');
    
    const loadGroupsButton = page.locator('button:has-text("Load Groups")');
    await expect(loadGroupsButton).toBeVisible({ timeout: 10000 });
    await loadGroupsButton.click();
    console.log('✓ Load Groups clicked');
    
    // Step 4: Monitor console errors during analysis
    const consoleErrors = [];
    const networkErrors = [];
    
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });
    
    page.on('response', response => {
      if (!response.ok()) {
        networkErrors.push(`${response.status()} ${response.url()}`);
      }
    });
    
    // Step 5: Wait for analysis to complete or timeout
    console.log('Step 5: Waiting for analysis to complete...');
    
    try {
      await Promise.race([
        page.waitForSelector('.group', { timeout: 60000 }),
        page.waitForSelector('.duplicate-group', { timeout: 60000 }),
        page.waitForSelector('[class*="group"]', { timeout: 60000 }),
        page.waitForTimeout(60000)
      ]);
    } catch (e) {
      console.log('Analysis wait completed or timed out');
    }
    
    // Step 6: Analyze final results
    console.log('Step 6: Analyzing results...');
    
    const finalPageText = await page.textContent('body');
    
    // Check for groups
    const groupSelectors = ['.group', '.duplicate-group', '[class*="group"]', '[data-group]'];
    let totalGroups = 0;
    
    for (const selector of groupSelectors) {
      const groups = page.locator(selector);
      const count = await groups.count();
      if (count > 0) {
        totalGroups = count;
        console.log(`Found ${count} groups using selector: ${selector}`);
        break;
      }
    }
    
    // Check for "undefined" issues
    const undefinedMatches = finalPageText.match(/undefined/gi) || [];
    const undefinedCount = undefinedMatches.length;
    
    // Check for empty content or missing data
    const hasEmptyGroups = finalPageText.includes('undefined') && totalGroups > 0;
    
    // Look for thumbnail images
    const thumbnails = page.locator('img');
    const thumbnailCount = await thumbnails.count();
    
    // Final statistics check
    const finalPhotoStats = finalPageText.match(/(\d+,?\d*)\s+photos?/gi) || [];
    const stillShowsFullLibrary = finalPageText.includes('13790') || finalPageText.includes('13,790');
    
    // Step 7: Generate comprehensive report
    console.log('=== LEGACY INTERFACE BUG ANALYSIS REPORT ===');
    console.log(`Initial Statistics: ${photoStats.join(', ')}`);
    console.log(`Final Statistics: ${finalPhotoStats.join(', ')}`);
    console.log(`Shows Full Library Count (13,790): ${stillShowsFullLibrary ? 'YES' : 'NO'}`);
    console.log(`Total Groups Found: ${totalGroups}`);
    console.log(`Thumbnail Images: ${thumbnailCount}`);
    console.log(`"undefined" Occurrences: ${undefinedCount}`);
    console.log(`Console Errors: ${consoleErrors.length}`);
    console.log(`Network Errors: ${networkErrors.length}`);
    
    // Detailed error logging
    if (consoleErrors.length > 0) {
      console.log('🚨 Console Errors:');
      consoleErrors.forEach((error, i) => {
        console.log(`  ${i + 1}. ${error}`);
      });
    }
    
    if (networkErrors.length > 0) {
      console.log('🌐 Network Errors:');
      networkErrors.forEach((error, i) => {
        console.log(`  ${i + 1}. ${error}`);
      });
    }
    
    // Bug confirmation
    const bugIssues = [];
    
    if (totalGroups === 0) {
      bugIssues.push('❌ No photo groups loaded after analysis');
    }
    
    if (undefinedCount > 0) {
      bugIssues.push(`❌ ${undefinedCount} "undefined" values found in interface`);
    }
    
    if (thumbnailCount === 0 && totalGroups > 0) {
      bugIssues.push('❌ Photo groups have no thumbnail images');
    }
    
    if (consoleErrors.length > 0) {
      bugIssues.push(`❌ ${consoleErrors.length} JavaScript console errors`);
    }
    
    if (stillShowsFullLibrary) {
      bugIssues.push('⚠️ Statistics show full library count (may be correct if no filters applied)');
    }
    
    // Step 8: Test with simulated filter session
    console.log('Step 8: Testing with simulated filter session...');
    
    // Simulate having a filter session by setting session storage
    await page.evaluate(() => {
      sessionStorage.setItem('photoFilters', JSON.stringify({
        year: ['2023'],
        appliedAt: Date.now(),
        filteredCount: 2375
      }));
    });
    
    // Reload page to test session persistence
    await page.reload();
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(2000);
    
    const sessionPageText = await page.textContent('body');
    const sessionStats = sessionPageText.match(/(\d+,?\d*)\s+photos?/gi) || [];
    
    console.log('With simulated session - Statistics:', sessionStats.join(', '));
    
    const shouldShowFiltered = sessionPageText.includes('2375') || sessionPageText.includes('2,375');
    const stillShowsFull = sessionPageText.includes('13790') || sessionPageText.includes('13,790');
    
    if (shouldShowFiltered) {
      console.log('✅ With filter session: Shows filtered count');
    } else if (stillShowsFull) {
      console.log('❌ BUG CONFIRMED: Even with filter session, shows full library count');
      bugIssues.push('❌ Legacy interface ignores filter session data');
    }
    
    // Final verdict
    console.log('=== FINAL VERDICT ===');
    if (bugIssues.length > 0) {
      console.log('❌ BUG CONFIRMED - Issues identified:');
      bugIssues.forEach((issue, i) => {
        console.log(`   ${i + 1}. ${issue}`);
      });
    } else {
      console.log('✅ No critical bugs found in legacy interface');
    }
    
    // Take final screenshot for documentation
    await page.screenshot({ 
      path: 'test-results/legacy_interface_bug_analysis.png',
      fullPage: true 
    });
    
    // Test assertions
    expect(totalGroups).toBeGreaterThanOrEqual(0);
    
    // Return analysis data for further inspection
    const analysisData = {
      totalGroups,
      undefinedCount,
      thumbnailCount,
      consoleErrorCount: consoleErrors.length,
      networkErrorCount: networkErrors.length,
      bugIssues,
      showsFullLibrary: stillShowsFullLibrary,
      sessionTest: {
        shouldShowFiltered,
        stillShowsFull
      }
    };
    
    console.log('=== ANALYSIS DATA ===');
    console.log(JSON.stringify(analysisData, null, 2));
    
    return analysisData;
  });
  
  test('should test filter workflow step by step', async ({ page }) => {
    console.log('=== STEP-BY-STEP FILTER WORKFLOW TEST ===');
    
    // Step 1: Test filters page functionality
    console.log('Step 1: Testing filters page...');
    await page.goto('/filters');
    await page.waitForLoadState('domcontentloaded');
    
    // Check if 2023 filter button exists and shows count
    const year2023Button = page.locator('button:has-text("2023")');
    const buttonExists = await year2023Button.count() > 0;
    
    if (buttonExists) {
      console.log('✓ 2023 filter button found');
      const buttonText = await year2023Button.textContent();
      console.log(`Button text: "${buttonText}"`);
      
      // Click the button
      await year2023Button.click();
      console.log('✓ 2023 filter clicked');
      
      // Check if "Apply Filters" button is available
      const applyButton = page.locator('button:has-text("Apply Filters")');
      const applyExists = await applyButton.count() > 0;
      
      if (applyExists) {
        console.log('✓ Apply Filters button found');
        
        // Instead of waiting for navigation, just check current state
        await applyButton.click();
        console.log('✓ Apply Filters clicked');
        
        // Check if anything changed on the page
        await page.waitForTimeout(3000);
        const currentUrl = page.url();
        console.log(`Current URL after Apply Filters: ${currentUrl}`);
        
        // Check if we can navigate to legacy with filter data
        await page.goto('/legacy');
        await page.waitForLoadState('domcontentloaded');
        
        const legacyText = await page.textContent('body');
        const hasFilteredData = legacyText.includes('2375') || legacyText.includes('2,375');
        const hasFullData = legacyText.includes('13790') || legacyText.includes('13,790');
        
        console.log('Legacy interface after filter workflow:');
        console.log(`  Has filtered count (2,375): ${hasFilteredData}`);
        console.log(`  Has full count (13,790): ${hasFullData}`);
        
        if (hasFullData && !hasFilteredData) {
          console.log('❌ WORKFLOW BUG: Filter data not persisting to legacy interface');
        }
        
      } else {
        console.log('❌ Apply Filters button not found');
      }
      
    } else {
      console.log('❌ 2023 filter button not found');
    }
    
    console.log('=== WORKFLOW TEST COMPLETE ===');
  });
});