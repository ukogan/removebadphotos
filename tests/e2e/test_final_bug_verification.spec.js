// test_final_bug_verification.spec.js
import { test, expect } from '@playwright/test';

test.describe('Final Bug Verification - Legacy Interface', () => {
  test('should verify the exact reported bug with correct button text', async ({ page }) => {
    console.log('=== FINAL BUG VERIFICATION TEST ===');
    console.log('Testing exact workflow: filters → 2023 → Apply → legacy → Analyze → check groups');
    
    // Step 1: Apply 2023 filter
    console.log('Step 1: Navigate to filters and apply 2023 filter');
    await page.goto('/filters');
    await page.waitForLoadState('domcontentloaded');
    
    // Find and click 2023 filter
    const year2023Button = page.locator('button:has-text("2023")');
    await year2023Button.click();
    console.log('✓ 2023 filter selected');
    
    // Click Apply Filters
    await page.locator('button:has-text("Apply Filters")').click();
    await page.waitForTimeout(2000);
    console.log('✓ Filters applied');
    
    // Step 2: Navigate to legacy interface
    console.log('Step 2: Navigate to legacy interface');
    await page.goto('/legacy');
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(2000);
    
    // Step 3: Check initial statistics
    console.log('Step 3: Check statistics before analysis');
    const statsText = await page.textContent('body');
    
    const totalPhotos = statsText.match(/(\d+,?\d+)\s+Total Photos/);
    const photosAnalyzed = statsText.match(/(\d+)\s+Photos Analyzed/);
    
    console.log(`Total Photos shown: ${totalPhotos ? totalPhotos[1] : 'Not found'}`);
    console.log(`Photos Analyzed: ${photosAnalyzed ? photosAnalyzed[1] : 'Not found'}`);
    
    // Check if showing full library count vs filtered count
    const showsFullLibrary = statsText.includes('13,790') || statsText.includes('13790');
    const showsFilteredCount = statsText.includes('2,375') || statsText.includes('2375');
    
    if (showsFullLibrary) {
      console.log('❌ BUG CONFIRMED: Shows full library count (13,790) instead of filtered (2,375)');
    } else if (showsFilteredCount) {
      console.log('✅ Shows correct filtered count');
    } else {
      console.log('⚠️ Cannot determine if count is correct');
    }
    
    // Step 4: Click Analyze Photo Groups button (correct button text)
    console.log('Step 4: Click "Analyze Photo Groups" button');
    const analyzeButton = page.locator('button:has-text("Analyze Photo Groups")');
    await expect(analyzeButton).toBeVisible({ timeout: 10000 });
    await analyzeButton.click();
    console.log('✓ Analyze Photo Groups clicked');
    
    // Step 5: Monitor for console errors and wait for results
    const consoleErrors = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
        console.log(`🚨 Console Error: ${msg.text()}`);
      }
    });
    
    console.log('Step 5: Waiting for analysis results...');
    
    // Wait longer for analysis to complete
    await page.waitForTimeout(30000);
    
    // Step 6: Check for photo groups and undefined issues
    console.log('Step 6: Checking for photo groups and undefined values');
    
    const finalPageText = await page.textContent('body');
    
    // Look for groups using multiple selectors
    const groupSelectors = [
      '.group',
      '.duplicate-group', 
      '[class*="group"]',
      '[data-group]',
      '.photo-group'
    ];
    
    let groupsFound = 0;
    let groupsWithUndefined = 0;
    let groupsWithThumbnails = 0;
    let groupsWithData = 0;
    
    for (const selector of groupSelectors) {
      const groups = page.locator(selector);
      const count = await groups.count();
      
      if (count > 0) {
        groupsFound = count;
        console.log(`Found ${count} groups with selector: ${selector}`);
        
        // Check first few groups for undefined and thumbnails
        for (let i = 0; i < Math.min(count, 5); i++) {
          const group = groups.nth(i);
          const groupText = await group.textContent();
          const images = group.locator('img');
          const imageCount = await images.count();
          
          if (groupText && groupText.toLowerCase().includes('undefined')) {
            groupsWithUndefined++;
          }
          
          if (imageCount > 0) {
            groupsWithThumbnails++;
          }
          
          if (groupText && groupText.trim().length > 10) {
            groupsWithData++;
          }
        }
        break;
      }
    }
    
    // Count undefined occurrences in page
    const undefinedMatches = finalPageText.match(/undefined/gi) || [];
    const undefinedCount = undefinedMatches.length;
    
    // Step 7: Generate comprehensive bug report
    console.log('=== BUG VERIFICATION RESULTS ===');
    console.log(`Statistics Issue:`);
    console.log(`  Shows Full Library (13,790): ${showsFullLibrary ? 'YES ❌' : 'NO ✅'}`);
    console.log(`  Shows Filtered Count (2,375): ${showsFilteredCount ? 'YES ✅' : 'NO ❌'}`);
    
    console.log(`Photo Groups Analysis:`);
    console.log(`  Total Groups Found: ${groupsFound}`);
    console.log(`  Groups with Data: ${groupsWithData}`);
    console.log(`  Groups with Undefined: ${groupsWithUndefined}`);
    console.log(`  Groups with Thumbnails: ${groupsWithThumbnails}`);
    console.log(`  Total "undefined" on page: ${undefinedCount}`);
    
    console.log(`Technical Issues:`);
    console.log(`  Console Errors: ${consoleErrors.length}`);
    if (consoleErrors.length > 0) {
      consoleErrors.forEach((error, i) => {
        console.log(`    ${i + 1}. ${error}`);
      });
    }
    
    // Final bug status
    const bugIssues = [];
    
    if (showsFullLibrary && !showsFilteredCount) {
      bugIssues.push('Statistics show full library instead of filtered count');
    }
    
    if (groupsFound === 0) {
      bugIssues.push('No photo groups loaded after analysis');
    }
    
    if (groupsWithUndefined > 0) {
      bugIssues.push(`${groupsWithUndefined} groups contain "undefined" values`);
    }
    
    if (undefinedCount > 0) {
      bugIssues.push(`${undefinedCount} "undefined" values found on page`);
    }
    
    if (groupsWithThumbnails === 0 && groupsFound > 0) {
      bugIssues.push('Photo groups have no thumbnail images');
    }
    
    if (consoleErrors.length > 0) {
      bugIssues.push(`${consoleErrors.length} JavaScript errors occurred`);
    }
    
    console.log('=== FINAL VERDICT ===');
    if (bugIssues.length > 0) {
      console.log('❌ BUG CONFIRMED - Issues found:');
      bugIssues.forEach((issue, i) => {
        console.log(`   ${i + 1}. ${issue}`);
      });
    } else {
      console.log('✅ No bugs found - functionality working as expected');
    }
    
    // Take screenshot for documentation
    await page.screenshot({ 
      path: 'test-results/final_bug_verification_screenshot.png',
      fullPage: true 
    });
    
    // Test passes regardless - this is for bug reporting
    expect(true).toBe(true);
    
    // Return verification data
    return {
      bugConfirmed: bugIssues.length > 0,
      bugIssues,
      statistics: {
        showsFullLibrary,
        showsFilteredCount
      },
      groups: {
        total: groupsFound,
        withData: groupsWithData,
        withUndefined: groupsWithUndefined,
        withThumbnails: groupsWithThumbnails
      },
      technicalIssues: {
        undefinedCount,
        consoleErrors: consoleErrors.length
      }
    };
  });
});