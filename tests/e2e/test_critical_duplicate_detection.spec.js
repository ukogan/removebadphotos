const { test, expect } = require('@playwright/test');

/**
 * Critical Duplicate Detection Validation
 * 
 * Focus on the core issue: Are duplicates actually being found?
 * This test specifically validates the duplicate detection logic works.
 */

const BASE_URL = 'http://127.0.0.1:5003';

test.describe('Critical Duplicate Detection Analysis', () => {

  test.beforeEach(async ({ page }) => {
    // Navigate directly without waiting for network idle
    await page.goto(`${BASE_URL}/filters`);
    await page.waitForTimeout(3000); // Simple wait instead of networkidle
  });

  test('API Validation: Check if analyze-duplicates returns actual results', async ({ page, request }) => {
    console.log('🔍 Testing analyze-duplicates API directly...');
    
    // Test the API endpoint directly
    const response = await request.post(`${BASE_URL}/api/analyze-duplicates`, {
      data: { filters: {} }
    });
    
    expect(response.status()).toBe(200);
    const data = await response.json();
    
    console.log('📊 API Response:', data);
    console.log(`📋 Total groups: ${data.total_groups || 'undefined'}`);
    console.log(`📸 Total photos: ${data.total_photos || 'undefined'}`);
    
    // CRITICAL TEST: Does the API return actual duplicate groups?
    if (data.total_groups === 0 || data.total_groups === undefined) {
      console.log('🚨 CRITICAL ISSUE: analyze-duplicates API returns 0 or undefined groups');
      console.log('🔧 This suggests the unified API is not connected to actual duplicate detection logic');
      
      // Check if it's returning stub data
      if (data.groups && Array.isArray(data.groups) && data.groups.length === 0) {
        console.log('❌ Returning empty groups array - likely stub implementation');
      }
    } else {
      console.log(`✅ SUCCESS: API returns ${data.total_groups} duplicate groups`);
      
      // Validate group structure
      if (data.groups && data.groups.length > 0) {
        const firstGroup = data.groups[0];
        console.log('📸 First group structure:', Object.keys(firstGroup));
        console.log(`📸 Photos in first group: ${firstGroup.photos ? firstGroup.photos.length : 'N/A'}`);
      }
    }
  });

  test('Year 2025 Filter: Verify filtering works and returns results', async ({ page }) => {
    console.log('🧪 Testing Year 2025 filter workflow...');
    
    // Apply year filter
    const yearSelect = page.locator('select[name="year"]');
    await expect(yearSelect).toBeVisible();
    await yearSelect.selectOption('2025');
    
    console.log('✓ Year 2025 filter applied');
    
    // Wait for filter to process
    await page.waitForTimeout(3000);
    
    // Check if cluster count is updated
    const clusterInfo = page.locator('.cluster-info');
    await expect(clusterInfo).toBeVisible();
    
    const clusterText = await clusterInfo.textContent();
    console.log(`📊 Cluster info: ${clusterText}`);
    
    // Extract numbers from cluster text
    const clusterMatch = clusterText.match(/(\d+)\s+clusters/i);
    const clusterCount = clusterMatch ? parseInt(clusterMatch[1]) : 0;
    
    console.log(`📊 Filtered to ${clusterCount} clusters for year 2025`);
    
    // Should be less than total but greater than 0
    expect(clusterCount).toBeGreaterThan(0);
    expect(clusterCount).toBeLessThan(2405); // Total clusters
    
    // Click analyze button
    const analyzeButton = page.locator('button:has-text("Analyze for Duplicates")');
    await expect(analyzeButton).toBeEnabled();
    await analyzeButton.click();
    
    console.log('✓ Clicked Analyze for Duplicates');
    
    // Wait for navigation to duplicates page
    await expect(page).toHaveURL(/.*\/duplicates/, { timeout: 30000 });
    console.log('✓ Redirected to duplicates page');
    
    // Wait for potential results
    await page.waitForTimeout(5000);
    
    // Check for any duplicate groups or error messages
    const duplicateGroups = page.locator('.duplicate-group, .photo-group, [class*="group"], .group');
    const groupCount = await duplicateGroups.count();
    
    console.log(`📋 Found ${groupCount} duplicate groups on page`);
    
    // Check for "no duplicates" or error messages
    const bodyText = await page.textContent('body');
    const hasNoDuplicates = bodyText.toLowerCase().includes('no duplicates') || 
                           bodyText.includes('0 groups') ||
                           bodyText.toLowerCase().includes('no results');
    
    const hasError = bodyText.toLowerCase().includes('error') || 
                    bodyText.toLowerCase().includes('failed');
    
    console.log(`❓ Has "no duplicates" message: ${hasNoDuplicates}`);
    console.log(`❓ Has error messages: ${hasError}`);
    
    if (groupCount === 0 && hasNoDuplicates) {
      console.log('🚨 CONFIRMED: Duplicate detection finds no duplicates for Year 2025 filter');
      console.log('🔧 This indicates the duplicate detection logic is not working properly');
    } else if (groupCount > 0) {
      console.log(`✅ SUCCESS: Found ${groupCount} duplicate groups for Year 2025`);
      
      // Test basic functionality of first group
      const firstGroup = duplicateGroups.first();
      const photosInGroup = firstGroup.locator('img, .photo');
      const photoCount = await photosInGroup.count();
      console.log(`📸 First group has ${photoCount} photos`);
    }
  });

  test('Full Library: Test with no filters to verify base functionality', async ({ page }) => {
    console.log('🧪 Testing full library (no filters)...');
    
    // Ensure no filters are applied
    const yearSelect = page.locator('select[name="year"]');
    await yearSelect.selectOption('');
    
    // Clear any size inputs
    const sizeInputs = page.locator('input[type="number"]');
    const inputCount = await sizeInputs.count();
    for (let i = 0; i < inputCount; i++) {
      await sizeInputs.nth(i).fill('');
    }
    
    console.log('✓ All filters cleared');
    
    await page.waitForTimeout(2000);
    
    // Check total cluster count
    const clusterInfo = page.locator('.cluster-info');
    const clusterText = await clusterInfo.textContent();
    const clusterMatch = clusterText.match(/(\d+)\s+clusters/i);
    const clusterCount = clusterMatch ? parseInt(clusterMatch[1]) : 0;
    
    console.log(`📊 Full library: ${clusterCount} clusters`);
    
    // Should be close to the total 2405
    expect(clusterCount).toBeGreaterThan(2000);
    
    // Analyze full library
    const analyzeButton = page.locator('button:has-text("Analyze for Duplicates")');
    await analyzeButton.click();
    
    await expect(page).toHaveURL(/.*\/duplicates/, { timeout: 30000 });
    console.log('✓ Navigated to duplicates page for full library');
    
    // Wait longer for full library analysis
    await page.waitForTimeout(10000);
    
    // Check results
    const duplicateGroups = page.locator('.duplicate-group, .photo-group, [class*="group"], .group');
    const groupCount = await duplicateGroups.count();
    
    console.log(`📋 Full library duplicate groups: ${groupCount}`);
    
    if (groupCount === 0) {
      console.log('🚨 CRITICAL ISSUE: No duplicate groups found in full library of 14k+ photos');
      console.log('🔧 This strongly suggests the duplicate detection logic is broken');
      
      // Check for specific error messages
      const bodyText = await page.textContent('body');
      if (bodyText.includes('0 groups')) {
        console.log('❌ Page shows "0 groups" - duplicate detection not functioning');
      }
    } else {
      console.log(`✅ SUCCESS: Found ${groupCount} duplicate groups in full library`);
    }
  });

  test('Backend Integration: Check if existing duplicate detection logic exists', async ({ page, request }) => {
    console.log('🔍 Checking backend duplicate detection integration...');
    
    // Test if there are existing endpoints that work
    const endpoints = [
      '/api/library-stats',
      '/api/filter-distributions', 
      '/api/heatmap-data',
      '/api/filter-clusters'
    ];
    
    for (const endpoint of endpoints) {
      const response = await request.get(`${BASE_URL}${endpoint}`);
      console.log(`📊 ${endpoint}: ${response.status()}`);
      
      if (response.status() === 200) {
        const data = await response.json();
        console.log(`  └─ Response keys: ${Object.keys(data).join(', ')}`);
        
        // Check if this endpoint has duplicate/group data
        if (data.total_groups || data.groups || data.duplicates) {
          console.log(`  └─ 🎯 Found duplicate data in ${endpoint}`);
        }
      }
    }
    
    // Test with specific filters to see if backend processes them
    const filteredResponse = await request.get(`${BASE_URL}/api/filter-clusters?year=2025`);
    if (filteredResponse.status() === 200) {
      const filteredData = await filteredResponse.json();
      console.log('📊 Filtered clusters response:', Object.keys(filteredData));
      
      if (filteredData.total_clusters) {
        console.log(`  └─ Year 2025 filter: ${filteredData.total_clusters} clusters`);
      }
    }
  });

  test('Console Error Detection: Check for JavaScript errors', async ({ page }) => {
    console.log('🔍 Monitoring console errors...');
    
    const errors = [];
    const warnings = [];
    
    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      } else if (msg.type() === 'warning') {
        warnings.push(msg.text());
      }
    });
    
    page.on('pageerror', error => {
      errors.push(`Page Error: ${error.message}`);
    });
    
    // Navigate and perform basic workflow
    await page.goto(`${BASE_URL}/filters`);
    await page.waitForTimeout(2000);
    
    const yearSelect = page.locator('select[name="year"]');
    await yearSelect.selectOption('2025');
    await page.waitForTimeout(2000);
    
    const analyzeButton = page.locator('button:has-text("Analyze for Duplicates")');
    await analyzeButton.click();
    
    await page.waitForTimeout(5000);
    
    console.log(`🚨 JavaScript Errors (${errors.length}):`);
    errors.forEach((error, i) => {
      console.log(`  ${i + 1}. ${error}`);
    });
    
    console.log(`⚠️ JavaScript Warnings (${warnings.length}):`);
    warnings.forEach((warning, i) => {
      console.log(`  ${i + 1}. ${warning}`);
    });
    
    if (errors.length > 0) {
      console.log('🔧 JavaScript errors detected - may be causing duplicate detection failures');
    } else {
      console.log('✅ No JavaScript errors detected');
    }
  });
});