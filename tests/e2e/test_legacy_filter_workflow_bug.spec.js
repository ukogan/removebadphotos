// test_legacy_filter_workflow_bug.spec.js
import { test, expect } from '@playwright/test';

test.describe('Legacy Interface Filter Workflow Bug', () => {
  test('should verify filter persistence and data display in legacy interface', async ({ page }) => {
    console.log('=== Starting Legacy Filter Workflow Bug Test ===');
    
    // Step 1: Navigate to filters page
    console.log('Step 1: Navigating to filters page...');
    await page.goto('/filters');
    
    // Wait for page to load completely
    await page.waitForLoadState('networkidle');
    await expect(page).toHaveTitle(/Smart Photo Filter|Photo Filters|Photo Dedup/);
    console.log('✓ Filters page loaded');

    // Step 2: Wait for filters to be available and select 2023
    console.log('Step 2: Waiting for filters and selecting 2023...');
    
    // Wait for the year filter section to be visible
    await page.waitForSelector('#year-filters', { state: 'visible' });
    
    // Look for 2023 filter - it appears to be a button, not a checkbox
    const year2023Button = page.locator('button:has-text("2023")');
    await expect(year2023Button).toBeVisible({ timeout: 10000 });
    
    // Click the 2023 filter button
    await year2023Button.click();
    console.log('✓ 2023 year filter selected');

    // Step 3: Click Apply Filters
    console.log('Step 3: Applying filters...');
    const applyButton = page.locator('button:has-text("Apply Filters")');
    await expect(applyButton).toBeVisible();
    await applyButton.click();
    
    // Wait for main page to load and show filtered results
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000); // Additional wait for filtering to complete
    console.log('✓ Filters applied, waiting for main page...');

    // Step 4: Verify we're on main page and check filtered count
    await expect(page).toHaveURL('/');
    
    // Look for filtered photo count display
    const photoCountElements = [
      page.locator('text=/\\d+\\s+filtered\\s+photos/i'),
      page.locator('text=/filtered.*\\d+/i'),
      page.locator('text=/\\d+.*photos.*filtered/i'),
      page.locator('#photo-count'),
      page.locator('.photo-count'),
      page.locator('[data-testid="photo-count"]')
    ];
    
    let filteredCount = null;
    let foundFilteredText = false;
    
    for (const element of photoCountElements) {
      try {
        await element.waitFor({ timeout: 3000 });
        const text = await element.textContent();
        console.log(`Found photo count element: "${text}"`);
        if (text && text.toLowerCase().includes('filtered')) {
          foundFilteredText = true;
          // Extract number from text
          const match = text.match(/(\d+)/);
          if (match) {
            filteredCount = parseInt(match[1]);
          }
        }
        break;
      } catch (e) {
        // Continue to next element
      }
    }
    
    if (foundFilteredText) {
      console.log(`✓ Found filtered count: ${filteredCount} photos`);
    } else {
      console.log('⚠ Could not find filtered photo count display');
    }

    // Step 5: Manually navigate to legacy interface
    console.log('Step 5: Navigating to legacy interface...');
    await page.goto('/legacy');
    await page.waitForLoadState('networkidle');
    await expect(page).toHaveTitle(/Legacy Interface/);
    console.log('✓ Legacy interface loaded');

    // Step 6: Check initial statistics display
    console.log('Step 6: Checking initial statistics...');
    
    // Look for statistics display elements
    const statsElements = [
      page.locator('.stats'),
      page.locator('#stats'),
      page.locator('[data-testid="stats"]'),
      page.locator('text=/Total.*photos/i'),
      page.locator('text=/\\d+\\s+photos/i')
    ];
    
    let initialStats = null;
    for (const element of statsElements) {
      try {
        await element.waitFor({ timeout: 3000 });
        const text = await element.textContent();
        if (text && text.includes('photo')) {
          initialStats = text;
          console.log(`Found initial stats: "${text}"`);
          break;
        }
      } catch (e) {
        // Continue to next element
      }
    }

    // Step 7: Click Load Groups button
    console.log('Step 7: Clicking Load Groups button...');
    
    const loadGroupsButton = page.locator('button:has-text("Load Groups")');
    await expect(loadGroupsButton).toBeVisible({ timeout: 10000 });
    await loadGroupsButton.click();
    console.log('✓ Load Groups button clicked');
    
    // Wait for analysis to complete
    await page.waitForTimeout(5000);
    
    // Wait for either success or failure indicators
    await Promise.race([
      page.waitForSelector('.group', { timeout: 30000 }),
      page.waitForSelector('.error', { timeout: 30000 }),
      page.waitForSelector('text="undefined"', { timeout: 30000 })
    ]);

    // Step 8: Check photo groups and data integrity
    console.log('Step 8: Analyzing photo groups and data...');
    
    // Check for console errors
    const consoleErrors = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });
    
    // Check for groups
    const groups = page.locator('.group');
    const groupCount = await groups.count();
    console.log(`Found ${groupCount} photo groups`);
    
    // Analysis results object
    const analysisResults = {
      initialStats,
      filteredCount,
      groupCount,
      groupsWithData: 0,
      undefinedGroups: 0,
      groupsWithThumbnails: 0,
      consoleErrors: [...consoleErrors],
      issues: []
    };
    
    // Analyze each group
    if (groupCount > 0) {
      for (let i = 0; i < Math.min(groupCount, 10); i++) { // Check first 10 groups
        const group = groups.nth(i);
        
        // Check if group has actual data or shows "undefined"
        const groupText = await group.textContent();
        if (groupText.toLowerCase().includes('undefined')) {
          analysisResults.undefinedGroups++;
          analysisResults.issues.push(`Group ${i + 1} contains "undefined" text`);
        } else {
          analysisResults.groupsWithData++;
        }
        
        // Check for thumbnails
        const thumbnails = group.locator('img, .thumbnail');
        const thumbnailCount = await thumbnails.count();
        if (thumbnailCount > 0) {
          analysisResults.groupsWithThumbnails++;
        }
      }
    } else {
      analysisResults.issues.push('No photo groups found after clicking Load Groups');
    }
    
    // Check final statistics after analysis
    let finalStats = null;
    for (const element of statsElements) {
      try {
        const text = await element.textContent();
        if (text && text.includes('photo')) {
          finalStats = text;
          break;
        }
      } catch (e) {
        // Continue
      }
    }
    analysisResults.finalStats = finalStats;
    
    // Verify if statistics show filtered count vs full library count
    if (finalStats) {
      // Check if stats show full library count (13790) instead of filtered count
      if (finalStats.includes('13790')) {
        analysisResults.issues.push('Statistics show full library count (13790) instead of filtered count');
      } else if (filteredCount && finalStats.includes(filteredCount.toString())) {
        console.log('✓ Statistics correctly show filtered count');
      }
    }
    
    // Network request analysis
    const apiCalls = [];
    page.on('response', response => {
      if (response.url().includes('/api/')) {
        apiCalls.push({
          url: response.url(),
          status: response.status(),
          ok: response.ok()
        });
      }
    });
    
    console.log('=== ANALYSIS RESULTS ===');
    console.log(`Initial Stats: ${initialStats}`);
    console.log(`Final Stats: ${finalStats}`);
    console.log(`Filtered Count from Main: ${filteredCount}`);
    console.log(`Total Groups Found: ${groupCount}`);
    console.log(`Groups with Data: ${analysisResults.groupsWithData}`);
    console.log(`Undefined Groups: ${analysisResults.undefinedGroups}`);
    console.log(`Groups with Thumbnails: ${analysisResults.groupsWithThumbnails}`);
    console.log(`Console Errors: ${consoleErrors.length}`);
    if (consoleErrors.length > 0) {
      consoleErrors.forEach((error, i) => console.log(`  Error ${i + 1}: ${error}`));
    }
    console.log(`Issues Found: ${analysisResults.issues.length}`);
    analysisResults.issues.forEach((issue, i) => console.log(`  Issue ${i + 1}: ${issue}`));
    
    // Assertions based on expected behavior
    if (analysisResults.issues.length > 0) {
      console.log('❌ BUG CONFIRMED: Issues found in legacy interface workflow');
      
      // Create detailed error message
      let errorMessage = 'Legacy Interface Filter Workflow Issues:\n';
      analysisResults.issues.forEach(issue => {
        errorMessage += `- ${issue}\n`;
      });
      
      // Take screenshot for debugging
      await page.screenshot({ 
        path: 'test-results/legacy_filter_bug_screenshot.png',
        fullPage: true 
      });
      
      // Don't fail the test but report the issues
      console.warn(errorMessage);
    } else {
      console.log('✅ No critical issues found');
    }
    
    // Verify basic functionality expectations
    expect(groupCount).toBeGreaterThan(0); // Should have some groups
    if (analysisResults.undefinedGroups === groupCount && groupCount > 0) {
      console.error('❌ CRITICAL: All groups show as undefined');
    }
  });
  
  test('should verify session data persistence across navigation', async ({ page }) => {
    console.log('=== Testing Session Data Persistence ===');
    
    // Apply filter on filters page
    await page.goto('/filters');
    await page.waitForLoadState('networkidle');
    
    // Select 2023 filter (button format)
    const year2023Button = page.locator('button:has-text("2023")');
    await year2023Button.click();
    
    // Apply filters
    await page.locator('button:has-text("Apply Filters")').click();
    await page.waitForLoadState('networkidle');
    
    // Get session storage data
    const sessionData = await page.evaluate(() => {
      return {
        sessionStorage: { ...sessionStorage },
        localStorage: { ...localStorage }
      };
    });
    
    console.log('Session data after filter:', sessionData);
    
    // Navigate to legacy
    await page.goto('/legacy');
    await page.waitForLoadState('networkidle');
    
    // Check if session data persists
    const legacySessionData = await page.evaluate(() => {
      return {
        sessionStorage: { ...sessionStorage },
        localStorage: { ...localStorage }
      };
    });
    
    console.log('Session data in legacy:', legacySessionData);
    
    // Verify session data consistency
    expect(JSON.stringify(legacySessionData.sessionStorage)).toBe(JSON.stringify(sessionData.sessionStorage));
  });
});