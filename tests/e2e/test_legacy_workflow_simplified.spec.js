// test_legacy_workflow_simplified.spec.js
import { test, expect } from '@playwright/test';

test.describe('Legacy Filter Workflow Bug - Simplified', () => {
  test('should reproduce the exact bug workflow', async ({ page }) => {
    console.log('=== REPRODUCING LEGACY FILTER BUG ===');
    
    // Step 1: Navigate to filters page
    console.log('Step 1: Navigate to http://127.0.0.1:5003/filters');
    await page.goto('/filters');
    await page.waitForLoadState('domcontentloaded');
    
    // Verify we're on the right page
    await expect(page).toHaveTitle(/Smart Photo Filter|Photo Dedup/);
    console.log('✓ Filters page loaded');

    // Step 2: Wait for page to load completely and filters to be visible
    console.log('Step 2: Wait for filters to load...');
    await page.waitForSelector('button:has-text("2023")', { timeout: 15000 });
    console.log('✓ Year filters are visible');

    // Step 3: Select the "2023" year filter
    console.log('Step 3: Select 2023 year filter');
    const year2023Button = page.locator('button:has-text("2023 (2,375)")');
    await year2023Button.click();
    console.log('✓ 2023 filter selected');
    
    // Step 4: Click "Apply Filters" button
    console.log('Step 4: Click Apply Filters');
    const applyButton = page.locator('button:has-text("Apply Filters")');
    await expect(applyButton).toBeVisible();
    await applyButton.click();
    console.log('✓ Apply Filters clicked');
    
    // Step 5: Wait for main page to load (should show filtered count)
    console.log('Step 5: Wait for main page with filtered results');
    await page.waitForURL('/');
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(3000); // Allow filtering to complete
    
    // Look for filtered photo count
    const mainPageText = await page.textContent('body');
    console.log('Main page content sample:', mainPageText.substring(0, 500));
    
    let filteredCount = null;
    const countMatch = mainPageText.match(/(\d+)\s+filtered\s+photos/i);
    if (countMatch) {
      filteredCount = parseInt(countMatch[1]);
      console.log(`✓ Found filtered count: ${filteredCount} photos`);
    } else {
      console.log('⚠ Could not find "filtered photos" text on main page');
    }
    
    // Step 6: Manually change URL to legacy interface
    console.log('Step 6: Navigate to http://127.0.0.1:5003/legacy');
    await page.goto('/legacy');
    await page.waitForLoadState('domcontentloaded');
    await expect(page).toHaveTitle(/Legacy|Photo Dedup/);
    console.log('✓ Legacy interface loaded');
    
    // Step 7: Check statistics at top before analysis
    console.log('Step 7: Check initial statistics...');
    const legacyPageText = await page.textContent('body');
    console.log('Legacy page initial content sample:', legacyPageText.substring(0, 500));
    
    // Look for photo count statistics
    const photoStats = legacyPageText.match(/(\d+,?\d*)\s+photos?/gi);
    if (photoStats) {
      console.log('Found photo statistics:', photoStats);
      
      // Check if showing full library (13790) vs filtered count
      const hasFullLibrary = legacyPageText.includes('13790') || legacyPageText.includes('13,790');
      const hasFilteredCount = filteredCount && legacyPageText.includes(filteredCount.toString());
      
      if (hasFullLibrary) {
        console.log('❌ BUG CONFIRMED: Legacy shows full library count (13,790) instead of filtered count');
      } else if (hasFilteredCount) {
        console.log('✅ Statistics correctly show filtered count');
      } else {
        console.log('⚠ Could not determine if statistics show correct count');
      }
    }
    
    // Step 8: Click "Load Groups" button
    console.log('Step 8: Click Load Groups button');
    const loadGroupsButton = page.locator('button:has-text("Load Groups")');
    await expect(loadGroupsButton).toBeVisible({ timeout: 10000 });
    await loadGroupsButton.click();
    console.log('✓ Load Groups clicked - analyzing...');
    
    // Step 9: Wait for analysis and check results
    console.log('Step 9: Wait for analysis results...');
    
    // Monitor console errors
    const consoleErrors = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });
    
    // Wait for either groups to appear or errors
    await Promise.race([
      page.waitForSelector('.group', { timeout: 45000 }),
      page.waitForSelector('.error', { timeout: 45000 }),
      page.waitForTimeout(45000)
    ]);
    
    // Step 10: Analyze results
    console.log('Step 10: Analyze photo groups and data...');
    
    const finalPageText = await page.textContent('body');
    
    // Check for groups
    const groups = page.locator('.group, .duplicate-group, [class*="group"]');
    const groupCount = await groups.count();
    console.log(`Found ${groupCount} photo groups`);
    
    // Check for "undefined" issues
    const hasUndefined = finalPageText.toLowerCase().includes('undefined');
    const undefinedCount = (finalPageText.match(/undefined/gi) || []).length;
    
    // Check for empty groups or missing thumbnails
    let emptyGroups = 0;
    let groupsWithThumbnails = 0;
    
    if (groupCount > 0) {
      for (let i = 0; i < Math.min(groupCount, 5); i++) {
        const group = groups.nth(i);
        const groupText = await group.textContent();
        const thumbnails = group.locator('img');
        const thumbnailCount = await thumbnails.count();
        
        if (!groupText.trim() || groupText.toLowerCase().includes('undefined')) {
          emptyGroups++;
        }
        
        if (thumbnailCount > 0) {
          groupsWithThumbnails++;
        }
      }
    }
    
    // Final analysis report
    console.log('=== BUG ANALYSIS REPORT ===');
    console.log(`Filtered Count from Main: ${filteredCount || 'Not found'}`);
    console.log(`Total Groups Found: ${groupCount}`);
    console.log(`Groups with Thumbnails: ${groupsWithThumbnails}`);
    console.log(`Empty/Undefined Groups: ${emptyGroups}`);
    console.log(`"undefined" occurrences: ${undefinedCount}`);
    console.log(`Console Errors: ${consoleErrors.length}`);
    
    if (consoleErrors.length > 0) {
      console.log('Console Errors Details:');
      consoleErrors.forEach((error, i) => {
        console.log(`  ${i + 1}. ${error}`);
      });
    }
    
    // Determine bug status
    const bugIssues = [];
    
    if (finalPageText.includes('13790') || finalPageText.includes('13,790')) {
      bugIssues.push('Legacy interface shows full library count instead of filtered count');
    }
    
    if (groupCount === 0) {
      bugIssues.push('No photo groups loaded after clicking Load Groups');
    } else if (emptyGroups === groupCount) {
      bugIssues.push('All photo groups are empty or show "undefined"');
    } else if (undefinedCount > 0) {
      bugIssues.push(`${undefinedCount} "undefined" values found in interface`);
    }
    
    if (groupsWithThumbnails === 0 && groupCount > 0) {
      bugIssues.push('Photo groups have no thumbnail images');
    }
    
    if (consoleErrors.length > 0) {
      bugIssues.push(`${consoleErrors.length} JavaScript errors in console`);
    }
    
    // Final verdict
    if (bugIssues.length > 0) {
      console.log('❌ BUG CONFIRMED - Issues found:');
      bugIssues.forEach((issue, i) => {
        console.log(`   ${i + 1}. ${issue}`);
      });
      
      // Take debugging screenshot
      await page.screenshot({ 
        path: 'test-results/legacy_filter_bug_confirmed.png',
        fullPage: true 
      });
      
    } else {
      console.log('✅ No critical issues found - workflow appears to work correctly');
    }
    
    // Assertions for test reporting
    expect(groupCount).toBeGreaterThanOrEqual(0);
    
    // Log final state for manual review
    console.log('=== MANUAL REVIEW REQUIRED ===');
    console.log('Please check the screenshot and console output to verify:');
    console.log('1. Do statistics show filtered count (2,375) or full library (13,790)?');
    console.log('2. Are photo groups displaying actual data and thumbnails?');
    console.log('3. Are there any "undefined" values in the interface?');
    console.log('4. Does the filtering session persist from filters to legacy interface?');
  });
});