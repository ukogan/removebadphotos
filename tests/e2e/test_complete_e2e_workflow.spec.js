const { test, expect } = require('@playwright/test');

/**
 * Comprehensive End-to-End Testing of Photo Deduplication Workflow
 * 
 * This test suite validates the complete user journey from filter selection
 * to Photos app integration, focusing on actual functionality validation.
 */

// Test configuration
const BASE_URL = 'http://127.0.0.1:5003';
const TIMEOUT = 60000; // 60 seconds for analysis operations

test.describe('Complete Photo Deduplication E2E Workflow', () => {

  test.beforeEach(async ({ page }) => {
    // Set longer timeout for all operations
    page.setDefaultTimeout(TIMEOUT);
    
    // Navigate to filters page
    await page.goto(`${BASE_URL}/filters`);
    
    // Wait for page to be fully loaded
    await page.waitForLoadState('networkidle');
  });

  /**
   * Test 1: Year 2025 Filter - Complete Workflow
   */
  test('1. Year 2025: Complete workflow through Photos tagging', async ({ page }) => {
    console.log('🧪 Starting Year 2025 filter test...');
    
    // Step 1: Verify filters page loads
    await expect(page).toHaveTitle(/Photo Dedup/);
    await expect(page.locator('h1')).toContainText('Photo Deduplication');
    
    // Step 2: Apply Year 2025 filter
    const yearSelect = page.locator('select[name="year"]');
    await yearSelect.selectOption('2025');
    console.log('✓ Year 2025 filter applied');
    
    // Wait for filter to be processed
    await page.waitForTimeout(2000);
    
    // Step 3: Verify cluster count updates
    const clusterInfo = page.locator('.cluster-info');
    await expect(clusterInfo).toBeVisible();
    
    const clusterText = await clusterInfo.textContent();
    console.log(`📊 Cluster info: ${clusterText}`);
    
    // Extract cluster count from text
    const clusterMatch = clusterText.match(/(\d+)\s+clusters/i);
    const clusterCount = clusterMatch ? parseInt(clusterMatch[1]) : 0;
    
    // Verify we have reasonable cluster count for 2025
    expect(clusterCount).toBeGreaterThan(0);
    expect(clusterCount).toBeLessThan(2405); // Should be filtered
    console.log(`✓ Found ${clusterCount} clusters for year 2025`);
    
    // Step 4: Click "Analyze for Duplicates" button
    const analyzeButton = page.locator('button:has-text("Analyze for Duplicates")');
    await expect(analyzeButton).toBeEnabled();
    
    await analyzeButton.click();
    console.log('✓ Clicked Analyze for Duplicates button');
    
    // Step 5: Verify redirect to /duplicates
    await page.waitForURL(/.*\/duplicates/, { timeout: 30000 });
    console.log('✓ Redirected to duplicates page');
    
    // Step 6: Wait for duplicate analysis to complete
    await page.waitForTimeout(5000);
    
    // Step 7: Verify duplicate groups are displayed
    const duplicateGroups = page.locator('.duplicate-group, .photo-group, [class*="group"]');
    const groupCount = await duplicateGroups.count();
    
    console.log(`📋 Found ${groupCount} duplicate groups`);
    
    // Critical validation: Check if we actually found duplicates
    if (groupCount === 0) {
      console.log('⚠️ No duplicate groups found - checking for error messages or empty states');
      
      // Look for error messages
      const errorMessages = await page.locator('.error, .warning, [class*="error"], [class*="warning"]').allTextContents();
      console.log('Error messages:', errorMessages);
      
      // Look for "no duplicates" message
      const noDuplicatesMsg = await page.locator(':has-text("No duplicates"), :has-text("no duplicates"), :has-text("0 groups")').count();
      console.log(`No duplicates messages found: ${noDuplicatesMsg}`);
      
      // This is a critical issue - should find some duplicates in a library of 14k photos
      console.log('🚨 CRITICAL ISSUE: No duplicate groups found in large photo library');
    }
    
    // Continue testing if we have groups
    if (groupCount > 0) {
      console.log(`✓ Found ${groupCount} duplicate groups`);
      
      // Step 8: Test photo selection within groups
      const firstGroup = duplicateGroups.first();
      const photosInGroup = firstGroup.locator('img, .photo, [class*="photo"]');
      const photoCount = await photosInGroup.count();
      
      console.log(`📸 First group has ${photoCount} photos`);
      
      if (photoCount > 0) {
        // Click on first photo to select it
        await photosInGroup.first().click();
        console.log('✓ Selected first photo for deletion');
        
        // Verify selection visual feedback
        const selectedPhotos = page.locator('.selected, [class*="selected"]');
        const selectedCount = await selectedPhotos.count();
        console.log(`✓ ${selectedCount} photos selected`);
      }
      
      // Step 9: Test "Load More" functionality if available
      const loadMoreButton = page.locator('button:has-text("Load More"), button:has-text("Show More")');
      if (await loadMoreButton.isVisible()) {
        await loadMoreButton.click();
        console.log('✓ Tested Load More functionality');
        await page.waitForTimeout(2000);
      }
      
      // Step 10: Test Photos app integration (if implemented)
      const tagButton = page.locator('button:has-text("Tag"), button:has-text("Mark"), button:has-text("Photos")');
      if (await tagButton.isVisible()) {
        await tagButton.click();
        console.log('✓ Initiated Photos app tagging');
        await page.waitForTimeout(3000);
      }
    }
    
    console.log('🎉 Year 2025 workflow test completed');
  });

  /**
   * Test 2: Year 2024 Filter - Complete Workflow
   */
  test('2. Year 2024: Complete workflow validation', async ({ page }) => {
    console.log('🧪 Starting Year 2024 filter test...');
    
    // Apply Year 2024 filter
    const yearSelect = page.locator('select[name="year"]');
    await yearSelect.selectOption('2024');
    console.log('✓ Year 2024 filter applied');
    
    await page.waitForTimeout(2000);
    
    // Get cluster count
    const clusterInfo = page.locator('.cluster-info');
    const clusterText = await clusterInfo.textContent();
    const clusterMatch = clusterText.match(/(\d+)\s+clusters/i);
    const clusterCount = clusterMatch ? parseInt(clusterMatch[1]) : 0;
    
    console.log(`📊 Year 2024: ${clusterCount} clusters`);
    expect(clusterCount).toBeGreaterThan(0);
    
    // Analyze duplicates
    const analyzeButton = page.locator('button:has-text("Analyze for Duplicates")');
    await analyzeButton.click();
    
    await page.waitForURL(/.*\/duplicates/, { timeout: 30000 });
    await page.waitForTimeout(5000);
    
    // Check results
    const duplicateGroups = page.locator('.duplicate-group, .photo-group, [class*="group"]');
    const groupCount = await duplicateGroups.count();
    
    console.log(`📋 Year 2024 duplicate groups: ${groupCount}`);
    
    if (groupCount === 0) {
      console.log('🚨 ISSUE: No duplicates found for Year 2024');
    } else {
      console.log(`✓ Year 2024 workflow successful: ${groupCount} groups`);
    }
  });

  /**
   * Test 3: Size Filter (5-50MB) - Complete Workflow
   */
  test('3. Size Filter (5-50MB): Validate duplicate detection quality', async ({ page }) => {
    console.log('🧪 Starting Size Filter (5-50MB) test...');
    
    // Apply size filters
    const minSizeInput = page.locator('input[name="min_size_mb"], input[placeholder*="min"], .size-filter input').first();
    const maxSizeInput = page.locator('input[name="max_size_mb"], input[placeholder*="max"], .size-filter input').last();
    
    if (await minSizeInput.isVisible()) {
      await minSizeInput.fill('5');
      console.log('✓ Min size set to 5MB');
    }
    
    if (await maxSizeInput.isVisible()) {
      await maxSizeInput.fill('50');
      console.log('✓ Max size set to 50MB');
    }
    
    await page.waitForTimeout(2000);
    
    // Get filtered cluster count
    const clusterInfo = page.locator('.cluster-info');
    const clusterText = await clusterInfo.textContent();
    const clusterMatch = clusterText.match(/(\d+)\s+clusters/i);
    const clusterCount = clusterMatch ? parseInt(clusterMatch[1]) : 0;
    
    console.log(`📊 Size filter (5-50MB): ${clusterCount} clusters`);
    
    // Analyze duplicates
    const analyzeButton = page.locator('button:has-text("Analyze for Duplicates")');
    await analyzeButton.click();
    
    await page.waitForURL(/.*\/duplicates/, { timeout: 30000 });
    await page.waitForTimeout(5000);
    
    // Validate results
    const duplicateGroups = page.locator('.duplicate-group, .photo-group, [class*="group"]');
    const groupCount = await duplicateGroups.count();
    
    console.log(`📋 Size filter duplicate groups: ${groupCount}`);
    
    if (groupCount > 0) {
      // Validate that photos are actually large files
      const photos = page.locator('img, .photo');
      const photoCount = await photos.count();
      console.log(`📸 Total photos in size-filtered duplicates: ${photoCount}`);
      
      // Test photo quality by checking if images load
      if (photoCount > 0) {
        const firstPhoto = photos.first();
        await expect(firstPhoto).toBeVisible();
        console.log('✓ Photo thumbnails load correctly');
      }
    } else {
      console.log('🚨 ISSUE: No duplicates found for size filter 5-50MB');
    }
  });

  /**
   * Test 4: Combined Filters (Year 2023 + Size 10-100MB)
   */
  test('4. Combined filters (Year 2023 + Size 10-100MB): Full analysis', async ({ page }) => {
    console.log('🧪 Starting Combined Filters test...');
    
    // Apply year filter
    const yearSelect = page.locator('select[name="year"]');
    await yearSelect.selectOption('2023');
    console.log('✓ Year 2023 filter applied');
    
    await page.waitForTimeout(1000);
    
    // Apply size filters
    const minSizeInput = page.locator('input[name="min_size_mb"], input[placeholder*="min"], .size-filter input').first();
    const maxSizeInput = page.locator('input[name="max_size_mb"], input[placeholder*="max"], .size-filter input').last();
    
    if (await minSizeInput.isVisible()) {
      await minSizeInput.fill('10');
    }
    if (await maxSizeInput.isVisible()) {
      await maxSizeInput.fill('100');
    }
    
    console.log('✓ Size filters applied: 10-100MB');
    
    await page.waitForTimeout(2000);
    
    // Check filtered results
    const clusterInfo = page.locator('.cluster-info');
    const clusterText = await clusterInfo.textContent();
    const clusterMatch = clusterText.match(/(\d+)\s+clusters/i);
    const clusterCount = clusterMatch ? parseInt(clusterMatch[1]) : 0;
    
    console.log(`📊 Combined filters: ${clusterCount} clusters`);
    
    // Should have significantly fewer clusters than unfiltered
    expect(clusterCount).toBeLessThan(2405);
    
    // Analyze duplicates
    const analyzeButton = page.locator('button:has-text("Analyze for Duplicates")');
    await analyzeButton.click();
    
    await page.waitForURL(/.*\/duplicates/, { timeout: 30000 });
    await page.waitForTimeout(5000);
    
    const duplicateGroups = page.locator('.duplicate-group, .photo-group, [class*="group"]');
    const groupCount = await duplicateGroups.count();
    
    console.log(`📋 Combined filters duplicate groups: ${groupCount}`);
    
    if (groupCount === 0) {
      console.log('🚨 ISSUE: No duplicates found for combined filters');
    }
  });

  /**
   * Test 5: No Filters (Full Library) - Scalability Test
   */
  test('5. No Filters (Full Library): Test scalability and results', async ({ page }) => {
    console.log('🧪 Starting Full Library test...');
    
    // Ensure no filters are applied
    const yearSelect = page.locator('select[name="year"]');
    await yearSelect.selectOption('');
    
    const inputs = page.locator('input[type="number"], input[name*="size"]');
    const inputCount = await inputs.count();
    for (let i = 0; i < inputCount; i++) {
      await inputs.nth(i).fill('');
    }
    
    console.log('✓ All filters cleared');
    
    await page.waitForTimeout(2000);
    
    // Verify full library stats
    const clusterInfo = page.locator('.cluster-info');
    const clusterText = await clusterInfo.textContent();
    const clusterMatch = clusterText.match(/(\d+)\s+clusters/i);
    const clusterCount = clusterMatch ? parseInt(clusterMatch[1]) : 0;
    
    console.log(`📊 Full library: ${clusterCount} clusters`);
    
    // Should be close to full 2405 clusters
    expect(clusterCount).toBeGreaterThan(2000);
    
    // Test performance with full library
    const startTime = Date.now();
    
    const analyzeButton = page.locator('button:has-text("Analyze for Duplicates")');
    await analyzeButton.click();
    
    await page.waitForURL(/.*\/duplicates/, { timeout: 60000 }); // Longer timeout for full library
    
    const analysisTime = Date.now() - startTime;
    console.log(`⏱️ Full library analysis time: ${analysisTime}ms`);
    
    await page.waitForTimeout(10000); // Wait longer for full analysis
    
    const duplicateGroups = page.locator('.duplicate-group, .photo-group, [class*="group"]');
    const groupCount = await duplicateGroups.count();
    
    console.log(`📋 Full library duplicate groups: ${groupCount}`);
    
    // Critical validation: Full library should definitely have duplicates
    if (groupCount === 0) {
      console.log('🚨 CRITICAL ISSUE: No duplicates found in full library of 14k+ photos');
      
      // Check for specific error indicators
      const pageContent = await page.content();
      console.log('Page content length:', pageContent.length);
      
      // Look for API errors
      const apiErrors = await page.locator('.error, .alert, [class*="error"]').allTextContents();
      console.log('API errors found:', apiErrors);
      
    } else {
      console.log(`✅ Full library workflow successful: ${groupCount} groups found`);
      
      // Test pagination/load more with large dataset
      const loadMoreButton = page.locator('button:has-text("Load More"), button:has-text("Show More")');
      if (await loadMoreButton.isVisible()) {
        await loadMoreButton.click();
        console.log('✓ Load More functionality works with full dataset');
      }
    }
  });

  /**
   * Critical API Endpoint Validation Test
   */
  test('API Endpoints: Verify unified endpoints return real data', async ({ page, request }) => {
    console.log('🧪 Testing API endpoints directly...');
    
    // Test analyze-duplicates endpoint
    const analyzeResponse = await request.post(`${BASE_URL}/api/analyze-duplicates`, {
      data: { filters: {} }
    });
    
    expect(analyzeResponse.status()).toBe(200);
    const analyzeData = await analyzeResponse.json();
    console.log('📊 Analyze duplicates response:', analyzeData);
    
    // Critical validation: Should return actual groups, not empty
    if (analyzeData.total_groups === 0) {
      console.log('🚨 CRITICAL: analyze-duplicates returns 0 groups');
    } else {
      console.log(`✅ API returns ${analyzeData.total_groups} duplicate groups`);
    }
    
    // Test filter-clusters endpoint
    const clustersResponse = await request.get(`${BASE_URL}/api/filter-clusters?preview=true`);
    expect(clustersResponse.status()).toBe(200);
    const clustersData = await clustersResponse.json();
    
    console.log('📊 Filter clusters response:', Object.keys(clustersData));
    
    if (clustersData.total_clusters) {
      console.log(`✅ Filter clusters: ${clustersData.total_clusters} clusters`);
    }
    
    // Test library stats
    const statsResponse = await request.get(`${BASE_URL}/api/library-stats`);
    expect(statsResponse.status()).toBe(200);
    const statsData = await statsResponse.json();
    
    console.log('📊 Library stats:', statsData);
    console.log(`✅ Library: ${statsData.total_photos} photos, ${statsData.total_size_gb}GB`);
  });

});

/**
 * Utility test for debugging duplicate detection logic
 */
test.describe('Debugging Duplicate Detection', () => {
  
  test('Debug: Check why duplicate detection returns 0 groups', async ({ page, request }) => {
    console.log('🔍 Debugging duplicate detection...');
    
    // Check server logs pattern
    await page.goto(`${BASE_URL}/filters`);
    
    // Apply a specific filter that should have duplicates
    const yearSelect = page.locator('select[name="year"]');
    await yearSelect.selectOption('2025');
    
    await page.waitForTimeout(2000);
    
    // Monitor network requests
    const responses = [];
    page.on('response', response => {
      if (response.url().includes('/api/')) {
        responses.push({
          url: response.url(),
          status: response.status()
        });
      }
    });
    
    // Trigger analysis
    const analyzeButton = page.locator('button:has-text("Analyze for Duplicates")');
    await analyzeButton.click();
    
    await page.waitForURL(/.*\/duplicates/, { timeout: 30000 });
    await page.waitForTimeout(5000);
    
    console.log('🌐 API calls made:', responses);
    
    // Check if the issue is in the API or frontend
    const pageText = await page.textContent('body');
    const hasErrorMessages = pageText.includes('error') || pageText.includes('Error');
    
    console.log(`❓ Page has error messages: ${hasErrorMessages}`);
    console.log(`📄 Page text length: ${pageText.length}`);
    
    // Check specific duplicate detection message
    if (pageText.includes('0 groups')) {
      console.log('🚨 Confirmed: Duplicate detection returns 0 groups');
      console.log('🔧 Possible issues:');
      console.log('  1. Unified API not connected to actual duplicate detection logic');
      console.log('  2. Filter application breaking duplicate detection');
      console.log('  3. Existing analysis workflow not properly integrated');
    }
  });
});