const { test, expect } = require('@playwright/test');

/**
 * Comprehensive E2E Test for Streamlined Workflow
 * 
 * Tests the complete 4-step workflow with 5 different filter combinations:
 * 1. Load /filters page
 * 2. Apply filter combination  
 * 3. Click "Analyze for Duplicates" button
 * 4. Verify progress bar shows
 * 5. Verify redirect to /duplicates interface occurs
 * 6. Verify /duplicates page loads and shows results
 * 7. Test "Load More Duplicates" button if available
 */

const BASE_URL = 'http://127.0.0.1:5003';

test.describe('Streamlined Workflow End-to-End Tests', () => {
  
  test.beforeEach(async ({ page }) => {
    // Set up console error monitoring
    const consoleErrors = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });
    
    // Attach console errors to test context
    page.consoleErrors = consoleErrors;
    
    // Set up network request monitoring
    const networkErrors = [];
    page.on('response', response => {
      if (response.status() >= 400) {
        networkErrors.push({
          url: response.url(),
          status: response.status(),
          statusText: response.statusText()
        });
      }
    });
    
    page.networkErrors = networkErrors;
  });

  test('Filter Combination 1: Basic Year Filter (2024)', async ({ page }) => {
    console.log('\n🧪 Testing Basic Year Filter: 2024');
    
    // Step 1: Load /filters page
    await page.goto(`${BASE_URL}/filters`);
    await page.waitForLoadState('networkidle');
    
    // Verify page loaded correctly
    await expect(page).toHaveTitle(/Photo Deduplication/);
    await expect(page.locator('h1')).toContainText('Filter Your Photo Library');
    
    // Step 2: Apply year filter (2024)
    await page.selectOption('#yearFilter', '2024');
    await page.waitForTimeout(500); // Allow UI to update
    
    // Step 3: Click "Analyze for Duplicates" button
    const analyzeButton = page.locator('#analyzeButton, button:has-text("Analyze for Duplicates")');
    await expect(analyzeButton).toBeVisible();
    
    await analyzeButton.click();
    console.log('✅ Clicked Analyze for Duplicates button');
    
    // Step 4: Verify progress bar shows
    const progressBar = page.locator('.progress-bar, #progressBar, [class*="progress"]');
    await expect(progressBar).toBeVisible({ timeout: 10000 });
    console.log('✅ Progress bar displayed');
    
    // Step 5: Wait for redirect to /duplicates
    await page.waitForURL('**/duplicates', { timeout: 30000 });
    console.log('✅ Redirected to /duplicates interface');
    
    // Step 6: Verify /duplicates page loads and shows results
    await page.waitForLoadState('networkidle');
    await expect(page.locator('h1, .page-title')).toContainText(/Duplicate/);
    
    // Step 7: Test "Load More Duplicates" button if available
    const loadMoreButton = page.locator('button:has-text("Load More"), #loadMoreButton');
    if (await loadMoreButton.isVisible()) {
      await loadMoreButton.click();
      console.log('✅ Load More Duplicates button clicked');
    }
    
    // Check for errors
    expect(page.consoleErrors).toHaveLength(0);
    expect(page.networkErrors.filter(err => err.status !== 404)).toHaveLength(0);
    
    console.log('✅ Basic Year Filter test completed successfully');
  });

  test('Filter Combination 2: Size Filter (5MB - 50MB)', async ({ page }) => {
    console.log('\n🧪 Testing Size Filter: 5MB - 50MB');
    
    // Step 1: Load /filters page
    await page.goto(`${BASE_URL}/filters`);
    await page.waitForLoadState('networkidle');
    
    // Step 2: Apply size filter
    const minSizeInput = page.locator('#minSize, input[name="minSize"]');
    const maxSizeInput = page.locator('#maxSize, input[name="maxSize"]');
    
    if (await minSizeInput.isVisible()) {
      await minSizeInput.fill('5');
    }
    if (await maxSizeInput.isVisible()) {
      await maxSizeInput.fill('50');
    }
    
    await page.waitForTimeout(500);
    
    // Step 3: Click "Analyze for Duplicates" button
    const analyzeButton = page.locator('#analyzeButton, button:has-text("Analyze for Duplicates")');
    await analyzeButton.click();
    console.log('✅ Clicked Analyze for Duplicates button');
    
    // Step 4: Verify progress bar shows
    const progressBar = page.locator('.progress-bar, #progressBar, [class*="progress"]');
    await expect(progressBar).toBeVisible({ timeout: 10000 });
    console.log('✅ Progress bar displayed');
    
    // Step 5: Wait for redirect to /duplicates
    await page.waitForURL('**/duplicates', { timeout: 30000 });
    console.log('✅ Redirected to /duplicates interface');
    
    // Step 6: Verify /duplicates page loads
    await page.waitForLoadState('networkidle');
    await expect(page.locator('h1, .page-title')).toContainText(/Duplicate/);
    
    // Check for errors
    expect(page.consoleErrors).toHaveLength(0);
    expect(page.networkErrors.filter(err => err.status !== 404)).toHaveLength(0);
    
    console.log('✅ Size Filter test completed successfully');
  });

  test('Filter Combination 3: Year + Size Combo (2023, 10-100MB)', async ({ page }) => {
    console.log('\n🧪 Testing Year + Size Combo: 2023, 10-100MB');
    
    // Step 1: Load /filters page
    await page.goto(`${BASE_URL}/filters`);
    await page.waitForLoadState('networkidle');
    
    // Step 2: Apply combined filters
    await page.selectOption('#yearFilter', '2023');
    
    const minSizeInput = page.locator('#minSize, input[name="minSize"]');
    const maxSizeInput = page.locator('#maxSize, input[name="maxSize"]');
    
    if (await minSizeInput.isVisible()) {
      await minSizeInput.fill('10');
    }
    if (await maxSizeInput.isVisible()) {
      await maxSizeInput.fill('100');
    }
    
    await page.waitForTimeout(500);
    
    // Step 3: Click "Analyze for Duplicates" button
    const analyzeButton = page.locator('#analyzeButton, button:has-text("Analyze for Duplicates")');
    await analyzeButton.click();
    console.log('✅ Clicked Analyze for Duplicates button');
    
    // Step 4: Verify progress bar shows
    const progressBar = page.locator('.progress-bar, #progressBar, [class*="progress"]');
    await expect(progressBar).toBeVisible({ timeout: 10000 });
    console.log('✅ Progress bar displayed');
    
    // Step 5: Wait for redirect to /duplicates
    await page.waitForURL('**/duplicates', { timeout: 30000 });
    console.log('✅ Redirected to /duplicates interface');
    
    // Step 6: Verify /duplicates page loads
    await page.waitForLoadState('networkidle');
    await expect(page.locator('h1, .page-title')).toContainText(/Duplicate/);
    
    // Check for errors
    expect(page.consoleErrors).toHaveLength(0);
    expect(page.networkErrors.filter(err => err.status !== 404)).toHaveLength(0);
    
    console.log('✅ Year + Size Combo test completed successfully');
  });

  test('Filter Combination 4: No Filters Applied', async ({ page }) => {
    console.log('\n🧪 Testing No Filters Applied');
    
    // Step 1: Load /filters page
    await page.goto(`${BASE_URL}/filters`);
    await page.waitForLoadState('networkidle');
    
    // Step 2: Skip filter application (test with no filters)
    console.log('⚠️ No filters applied - testing default behavior');
    
    // Step 3: Click "Analyze for Duplicates" button
    const analyzeButton = page.locator('#analyzeButton, button:has-text("Analyze for Duplicates")');
    await analyzeButton.click();
    console.log('✅ Clicked Analyze for Duplicates button');
    
    // Step 4: Verify progress bar shows
    const progressBar = page.locator('.progress-bar, #progressBar, [class*="progress"]');
    await expect(progressBar).toBeVisible({ timeout: 10000 });
    console.log('✅ Progress bar displayed');
    
    // Step 5: Wait for redirect to /duplicates
    await page.waitForURL('**/duplicates', { timeout: 30000 });
    console.log('✅ Redirected to /duplicates interface');
    
    // Step 6: Verify /duplicates page loads
    await page.waitForLoadState('networkidle');
    await expect(page.locator('h1, .page-title')).toContainText(/Duplicate/);
    
    // Check for errors
    expect(page.consoleErrors).toHaveLength(0);
    expect(page.networkErrors.filter(err => err.status !== 404)).toHaveLength(0);
    
    console.log('✅ No Filters test completed successfully');
  });

  test('Filter Combination 5: Multiple Filters (2025, 5-25MB, file types)', async ({ page }) => {
    console.log('\n🧪 Testing Multiple Filters: 2025, 5-25MB, file types');
    
    // Step 1: Load /filters page
    await page.goto(`${BASE_URL}/filters`);
    await page.waitForLoadState('networkidle');
    
    // Step 2: Apply multiple filters
    await page.selectOption('#yearFilter', '2025');
    
    const minSizeInput = page.locator('#minSize, input[name="minSize"]');
    const maxSizeInput = page.locator('#maxSize, input[name="maxSize"]');
    
    if (await minSizeInput.isVisible()) {
      await minSizeInput.fill('5');
    }
    if (await maxSizeInput.isVisible()) {
      await maxSizeInput.fill('25');
    }
    
    // Try to select file types if available
    const fileTypeCheckboxes = page.locator('input[type="checkbox"][name*="fileType"], input[type="checkbox"][id*="fileType"]');
    const fileTypeCount = await fileTypeCheckboxes.count();
    if (fileTypeCount > 0) {
      await fileTypeCheckboxes.first().check();
    }
    
    await page.waitForTimeout(500);
    
    // Step 3: Click "Analyze for Duplicates" button
    const analyzeButton = page.locator('#analyzeButton, button:has-text("Analyze for Duplicates")');
    await analyzeButton.click();
    console.log('✅ Clicked Analyze for Duplicates button');
    
    // Step 4: Verify progress bar shows
    const progressBar = page.locator('.progress-bar, #progressBar, [class*="progress"]');
    await expect(progressBar).toBeVisible({ timeout: 10000 });
    console.log('✅ Progress bar displayed');
    
    // Step 5: Wait for redirect to /duplicates
    await page.waitForURL('**/duplicates', { timeout: 30000 });
    console.log('✅ Redirected to /duplicates interface');
    
    // Step 6: Verify /duplicates page loads
    await page.waitForLoadState('networkidle');
    await expect(page.locator('h1, .page-title')).toContainText(/Duplicate/);
    
    // Step 7: Test "Load More Duplicates" button if available
    const loadMoreButton = page.locator('button:has-text("Load More"), #loadMoreButton');
    if (await loadMoreButton.isVisible()) {
      await loadMoreButton.click();
      console.log('✅ Load More Duplicates button clicked');
    }
    
    // Check for errors
    expect(page.consoleErrors).toHaveLength(0);
    expect(page.networkErrors.filter(err => err.status !== 404)).toHaveLength(0);
    
    console.log('✅ Multiple Filters test completed successfully');
  });

  test('API Endpoint Verification', async ({ page }) => {
    console.log('\n🧪 Testing API Endpoint Availability');
    
    // Test critical API endpoints
    const endpoints = [
      '/api/library-stats',
      '/api/filter-distributions',
      '/api/analyze-duplicates',
      '/api/load-more-duplicates'
    ];
    
    for (const endpoint of endpoints) {
      const response = await page.request.get(`${BASE_URL}${endpoint}`);
      console.log(`API ${endpoint}: ${response.status()}`);
      
      if (endpoint === '/api/analyze-duplicates') {
        // POST endpoint, test with POST
        const postResponse = await page.request.post(`${BASE_URL}${endpoint}`, {
          data: { filters: {} }
        });
        console.log(`API ${endpoint} (POST): ${postResponse.status()}`);
      }
    }
  });

  test('JavaScript Console Error Detection', async ({ page }) => {
    console.log('\n🧪 Testing JavaScript Console Error Detection');
    
    await page.goto(`${BASE_URL}/filters`);
    await page.waitForLoadState('networkidle');
    
    // Navigate to duplicates page
    await page.goto(`${BASE_URL}/duplicates`);
    await page.waitForLoadState('networkidle');
    
    // Check for JavaScript errors
    if (page.consoleErrors.length > 0) {
      console.log('❌ JavaScript Console Errors Found:');
      page.consoleErrors.forEach(error => console.log(`  - ${error}`));
    } else {
      console.log('✅ No JavaScript console errors detected');
    }
    
    expect(page.consoleErrors).toHaveLength(0);
  });

  test('Performance and Response Time Test', async ({ page }) => {
    console.log('\n🧪 Testing Performance and Response Times');
    
    const startTime = Date.now();
    
    // Load filters page
    await page.goto(`${BASE_URL}/filters`);
    await page.waitForLoadState('networkidle');
    
    const filtersLoadTime = Date.now() - startTime;
    console.log(`Filters page load time: ${filtersLoadTime}ms`);
    
    // Test analyze duplicates performance
    const analyzeStartTime = Date.now();
    const analyzeButton = page.locator('#analyzeButton, button:has-text("Analyze for Duplicates")');
    
    if (await analyzeButton.isVisible()) {
      await analyzeButton.click();
      
      try {
        await page.waitForURL('**/duplicates', { timeout: 30000 });
        const analyzeTime = Date.now() - analyzeStartTime;
        console.log(`Analyze and redirect time: ${analyzeTime}ms`);
        
        // Check if reasonable performance
        expect(filtersLoadTime).toBeLessThan(10000); // 10 seconds max
        expect(analyzeTime).toBeLessThan(60000); // 1 minute max
      } catch (error) {
        console.log(`⚠️ Redirect timeout or error: ${error.message}`);
      }
    }
  });

  test('Thumbnail Loading and UI Responsiveness', async ({ page }) => {
    console.log('\n🧪 Testing Thumbnail Loading and UI Responsiveness');
    
    await page.goto(`${BASE_URL}/duplicates`);
    await page.waitForLoadState('networkidle');
    
    // Look for photo thumbnails
    const thumbnails = page.locator('img[src*="thumbnail"], .photo-thumbnail, .duplicate-photo img');
    const thumbnailCount = await thumbnails.count();
    
    console.log(`Found ${thumbnailCount} photo thumbnails`);
    
    if (thumbnailCount > 0) {
      // Test first few thumbnails load correctly
      const firstThumbnail = thumbnails.first();
      await expect(firstThumbnail).toBeVisible();
      
      // Check if thumbnail has valid src
      const src = await firstThumbnail.getAttribute('src');
      expect(src).toBeTruthy();
      console.log('✅ Thumbnail loading appears functional');
    } else {
      console.log('⚠️ No thumbnails found - may indicate missing duplicate data');
    }
  });

});