const { test, expect } = require('@playwright/test');

// Test configuration
const BASE_URL = 'http://127.0.0.1:5003';
const FILTER_PAGE_URL = `${BASE_URL}/filters`;

test.describe('Filter Interface - Analyze for Duplicates Button', () => {
  test.beforeEach(async ({ page }) => {
    // Set a longer timeout for tests that involve photo processing
    test.setTimeout(60000);
    
    // Navigate to the filter page
    await page.goto(FILTER_PAGE_URL);
    
    // Wait for the page to load completely
    await page.waitForLoadState('domcontentloaded');
    
    // Wait for initial stats to load (indicates page is ready)
    await page.waitForSelector('.stats-bar', { timeout: 10000 });
  });

  test('Test 1: Basic Year Filter (2024) with Analyze for Duplicates button', async ({ page }) => {
    console.log('🧪 Testing Basic Year Filter (2024)...');

    // Wait for year buttons to be available
    await page.waitForSelector('.year-btn', { timeout: 10000 });
    
    // Click on 2024 year filter
    const year2024Button = page.locator('.year-btn:has-text("2024")');
    await expect(year2024Button).toBeVisible({ timeout: 10000 });
    await year2024Button.click();
    
    // Verify the button is selected (has active class)
    await expect(year2024Button).toHaveClass(/active/);
    
    // Click Apply Filters button
    await page.click('button:has-text("🔍 Apply Filters")');
    
    // Wait for filter preview to update
    await page.waitForSelector('#filter-preview', { timeout: 10000 });
    
    // Check if "Analyze for Duplicates" button appears
    const analyzeSection = page.locator('#analyze-selected-section');
    await expect(analyzeSection).toBeVisible({ timeout: 15000 });
    
    const analyzeButton = page.locator('#analyzeForDuplicatesBtn');
    await expect(analyzeButton).toBeVisible();
    await expect(analyzeButton).toContainText('🔍 Analyze for Duplicates');
    
    // Click the Analyze for Duplicates button
    await analyzeButton.click();
    
    // Check that progress bar appears
    const progressContainer = page.locator('#analysisProgress');
    await expect(progressContainer).toBeVisible({ timeout: 5000 });
    
    // Wait for progress updates
    const progressText = page.locator('#progressText');
    await expect(progressText).toContainText('Starting analysis', { timeout: 5000 });
    
    // Wait for analysis to complete and redirect
    await page.waitForURL('**/legacy', { timeout: 30000 });
    
    // Verify we're on the legacy page
    expect(page.url()).toContain('/legacy');
  });

  test('Test 2: Size Filter (5MB-50MB) with analysis workflow', async ({ page }) => {
    console.log('🧪 Testing Size Filter (5MB-50MB)...');

    // Wait for size sliders to be available
    await page.waitForSelector('.dual-range input[type="range"]', { timeout: 10000 });
    
    // Set minimum size to 5MB (slider value calculation may vary)
    const minSlider = page.locator('.dual-range input[type="range"]').first();
    await minSlider.fill('5');
    
    // Set maximum size to 50MB
    const maxSlider = page.locator('.dual-range input[type="range"]').last();
    await maxSlider.fill('50');
    
    // Click Apply Filters button
    await page.click('button:has-text("🔍 Apply Filters")');
    
    // Wait for filter preview to update
    await page.waitForSelector('#filter-preview', { timeout: 10000 });
    
    // Check if "Analyze for Duplicates" button appears
    const analyzeSection = page.locator('#analyze-selected-section');
    await expect(analyzeSection).toBeVisible({ timeout: 15000 });
    
    const analyzeButton = page.locator('#analyzeForDuplicatesBtn');
    await expect(analyzeButton).toBeVisible();
    
    // Click the Analyze for Duplicates button
    await analyzeButton.click();
    
    // Verify progress workflow
    const progressContainer = page.locator('#analysisProgress');
    await expect(progressContainer).toBeVisible({ timeout: 5000 });
    
    // Wait for redirect to legacy page
    await page.waitForURL('**/legacy', { timeout: 30000 });
    expect(page.url()).toContain('/legacy');
  });

  test('Test 3: Year + Size Combo (2023, 10-100MB) end-to-end flow', async ({ page }) => {
    console.log('🧪 Testing Year + Size Combo (2023, 10-100MB)...');

    // Select year 2023
    const year2023Button = page.locator('.year-btn:has-text("2023")');
    await expect(year2023Button).toBeVisible({ timeout: 10000 });
    await year2023Button.click();
    await expect(year2023Button).toHaveClass(/active/);
    
    // Set size range 10-100MB
    const minSlider = page.locator('.dual-range input[type="range"]').first();
    await minSlider.fill('10');
    
    const maxSlider = page.locator('.dual-range input[type="range"]').last();
    await maxSlider.fill('100');
    
    // Apply filters
    await page.click('button:has-text("🔍 Apply Filters")');
    
    // Wait for preview and analyze button
    await page.waitForSelector('#filter-preview', { timeout: 10000 });
    
    const analyzeSection = page.locator('#analyze-selected-section');
    await expect(analyzeSection).toBeVisible({ timeout: 15000 });
    
    // Verify selection summary shows expected values
    const selectedClustersCount = page.locator('#selected-clusters-count');
    const selectedPhotosCount = page.locator('#selected-photos-count');
    
    await expect(selectedClustersCount).toBeVisible();
    await expect(selectedPhotosCount).toBeVisible();
    
    // Click analyze button
    const analyzeButton = page.locator('#analyzeForDuplicatesBtn');
    await analyzeButton.click();
    
    // Monitor progress updates
    const progressContainer = page.locator('#analysisProgress');
    await expect(progressContainer).toBeVisible();
    
    const progressBar = page.locator('#progressBar');
    const progressText = page.locator('#progressText');
    
    // Wait for multiple progress updates
    await expect(progressText).toContainText('Scanning photo library', { timeout: 10000 });
    
    // Wait for completion and redirect
    await page.waitForURL('**/legacy', { timeout: 30000 });
    expect(page.url()).toContain('/legacy');
  });

  test('Test 4: No Filters scenario and analyze behavior', async ({ page }) => {
    console.log('🧪 Testing No Filters scenario...');

    // Don't apply any filters, just check if the analyze button appears
    // The analyze button should only appear when filters are applied
    
    const analyzeSection = page.locator('#analyze-selected-section');
    
    // Initially, the analyze section should be hidden
    await expect(analyzeSection).toBeHidden();
    
    // Try clicking Apply Filters with no filters selected
    await page.click('button:has-text("🔍 Apply Filters")');
    
    // Wait a moment to see if analyze section appears
    await page.waitForTimeout(3000);
    
    // The analyze section should still be hidden or show 0 selections
    const isVisible = await analyzeSection.isVisible();
    
    if (isVisible) {
      // If visible, check that it shows 0 selections
      const selectedClustersCount = page.locator('#selected-clusters-count');
      const clustersText = await selectedClustersCount.textContent();
      expect(clustersText).toBe('0');
    } else {
      // If hidden, that's also acceptable behavior
      await expect(analyzeSection).toBeHidden();
    }
    
    console.log('✅ No filters scenario handled correctly');
  });

  test('Test 5: Multiple Filters combination (2025, 5-25MB, file types)', async ({ page }) => {
    console.log('🧪 Testing Multiple Filters combination...');

    // Select year 2025 (if available)
    const year2025Button = page.locator('.year-btn:has-text("2025")');
    
    // Check if 2025 button exists, if not use 2024
    let yearButton = year2025Button;
    const year2025Exists = await year2025Button.isVisible().catch(() => false);
    
    if (!year2025Exists) {
      yearButton = page.locator('.year-btn:has-text("2024")');
      console.log('📝 2025 not available, using 2024 instead');
    }
    
    await expect(yearButton).toBeVisible({ timeout: 10000 });
    await yearButton.click();
    await expect(yearButton).toHaveClass(/active/);
    
    // Set size range 5-25MB
    const minSlider = page.locator('.dual-range input[type="range"]').first();
    await minSlider.fill('5');
    
    const maxSlider = page.locator('.dual-range input[type="range"]').last();
    await maxSlider.fill('25');
    
    // Select file types (if available)
    const fileTypeOptions = page.locator('.file-type-option');
    const fileTypeCount = await fileTypeOptions.count();
    
    if (fileTypeCount > 0) {
      // Select first available file type
      const firstFileType = fileTypeOptions.first();
      await firstFileType.click();
      console.log('📝 Selected first available file type');
    }
    
    // Apply all filters
    await page.click('button:has-text("🔍 Apply Filters")');
    
    // Wait for filter processing
    await page.waitForSelector('#filter-preview', { timeout: 10000 });
    
    const analyzeSection = page.locator('#analyze-selected-section');
    await expect(analyzeSection).toBeVisible({ timeout: 15000 });
    
    // Click analyze button
    const analyzeButton = page.locator('#analyzeForDuplicatesBtn');
    await analyzeButton.click();
    
    // Monitor complete workflow
    const progressContainer = page.locator('#analysisProgress');
    await expect(progressContainer).toBeVisible();
    
    // Check for different progress states
    const progressText = page.locator('#progressText');
    
    // Should see scanning phase
    await expect(progressText).toContainText('Scanning', { timeout: 10000 });
    
    // Wait for completion and redirect
    await page.waitForURL('**/legacy', { timeout: 30000 });
    expect(page.url()).toContain('/legacy');
  });

  test('Browser Console Error Detection', async ({ page }) => {
    console.log('🧪 Testing for JavaScript console errors...');

    const consoleErrors = [];
    const consoleWarnings = [];
    
    // Listen for console messages
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
      if (msg.type() === 'warning') {
        consoleWarnings.push(msg.text());
      }
    });

    // Apply a simple filter and analyze
    const year2024Button = page.locator('.year-btn:has-text("2024")');
    await expect(year2024Button).toBeVisible({ timeout: 10000 });
    await year2024Button.click();
    
    await page.click('button:has-text("🔍 Apply Filters")');
    
    await page.waitForSelector('#analyze-selected-section', { timeout: 15000 });
    
    const analyzeButton = page.locator('#analyzeForDuplicatesBtn');
    await analyzeButton.click();
    
    // Wait a bit for any async errors
    await page.waitForTimeout(5000);
    
    // Report console issues
    if (consoleErrors.length > 0) {
      console.log('❌ Console Errors Found:', consoleErrors);
    } else {
      console.log('✅ No console errors detected');
    }
    
    if (consoleWarnings.length > 0) {
      console.log('⚠️ Console Warnings Found:', consoleWarnings);
    }
    
    // Fail test if critical errors found
    expect(consoleErrors.filter(err => !err.includes('deprecated')).length).toBe(0);
  });

  test('UI Response Time Performance Test', async ({ page }) => {
    console.log('🧪 Testing UI response times...');

    // Test filter application speed
    const startTime = Date.now();
    
    const year2024Button = page.locator('.year-btn:has-text("2024")');
    await year2024Button.click();
    
    await page.click('button:has-text("🔍 Apply Filters")');
    
    await page.waitForSelector('#analyze-selected-section', { timeout: 15000 });
    
    const filterApplicationTime = Date.now() - startTime;
    console.log(`📊 Filter application took: ${filterApplicationTime}ms`);
    
    // Test analyze button response time
    const analyzeStartTime = Date.now();
    
    const analyzeButton = page.locator('#analyzeForDuplicatesBtn');
    await analyzeButton.click();
    
    await page.waitForSelector('#analysisProgress', { timeout: 5000 });
    
    const analyzeResponseTime = Date.now() - analyzeStartTime;
    console.log(`📊 Analyze button response took: ${analyzeResponseTime}ms`);
    
    // Performance expectations
    expect(filterApplicationTime).toBeLessThan(10000); // 10 seconds max for filter application
    expect(analyzeResponseTime).toBeLessThan(2000);    // 2 seconds max for button response
  });
});