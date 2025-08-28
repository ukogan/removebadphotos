// Comprehensive diagnostic tests for photo deletion workflow hanging issue
// Target: Identify exact bottleneck in workflow with only 4 photos (2 groups of 2)

import { test, expect } from '@playwright/test';

test.describe('Photo Deletion Workflow Performance Diagnostics', () => {
  
  test.beforeEach(async ({ page }) => {
    // Enable console logging for debugging
    page.on('console', msg => {
      console.log(`🖥️ Console ${msg.type()}: ${msg.text()}`);
    });
    
    // Enable network request monitoring
    page.on('request', request => {
      console.log(`📤 Request: ${request.method()} ${request.url()}`);
    });
    
    page.on('response', response => {
      console.log(`📥 Response: ${response.status()} ${response.url()} (${response.request().timing()?.responseEnd || 'no timing'}ms)`);
    });
    
    // Enable error logging
    page.on('pageerror', error => {
      console.log(`❌ Page Error: ${error}`);
    });
  });

  test('API Endpoint Performance - /api/groups with limit=10', async ({ page }) => {
    console.log('\n🧪 Testing /api/groups endpoint performance...');
    
    const startTime = Date.now();
    
    try {
      // Direct API call to /api/groups with limit=10
      const response = await page.request.get('/api/groups?limit=10');
      const endTime = Date.now();
      const responseTime = endTime - startTime;
      
      console.log(`⏱️ /api/groups response time: ${responseTime}ms`);
      
      // Test should complete within 5 seconds
      expect(responseTime).toBeLessThan(5000);
      expect(response.status()).toBe(200);
      
      const data = await response.json();
      console.log(`📊 Groups returned: ${data.groups?.length || 0}`);
      console.log(`📊 Total photos: ${data.total_photos || 0}`);
      
      // With only 4 photos, we should get quick response
      expect(data.groups).toBeDefined();
      expect(Array.isArray(data.groups)).toBe(true);
      
    } catch (error) {
      console.log(`❌ /api/groups failed: ${error}`);
      throw error;
    }
  });

  test('API Endpoint Performance - /api/complete-workflow', async ({ page }) => {
    console.log('\n🧪 Testing /api/complete-workflow endpoint performance...');
    
    // First get some photo UUIDs to test with
    const groupsResponse = await page.request.get('/api/groups?limit=2');
    expect(groupsResponse.status()).toBe(200);
    
    const groupsData = await groupsResponse.json();
    console.log(`📊 Got ${groupsData.groups?.length || 0} groups for workflow test`);
    
    if (!groupsData.groups || groupsData.groups.length === 0) {
      console.log('⚠️ No groups available for workflow test');
      return;
    }
    
    // Collect photo UUIDs from first group
    const firstGroup = groupsData.groups[0];
    const photoUuids = firstGroup.photos?.map(p => p.uuid).slice(0, 2) || [];
    
    if (photoUuids.length === 0) {
      console.log('⚠️ No photo UUIDs available for workflow test');
      return;
    }
    
    console.log(`🎯 Testing workflow with ${photoUuids.length} photos: ${photoUuids}`);
    
    const startTime = Date.now();
    
    try {
      const response = await page.request.post('/api/complete-workflow', {
        data: {
          photo_uuids: photoUuids,
          estimated_savings_mb: 10
        },
        timeout: 15000 // 15 second timeout
      });
      
      const endTime = Date.now();
      const responseTime = endTime - startTime;
      
      console.log(`⏱️ /api/complete-workflow response time: ${responseTime}ms`);
      console.log(`📊 Response status: ${response.status()}`);
      
      // Workflow should complete within 10 seconds for 2 photos
      expect(responseTime).toBeLessThan(10000);
      expect(response.status()).toBe(200);
      
      const data = await response.json();
      console.log(`✅ Workflow result: ${JSON.stringify(data, null, 2)}`);
      
    } catch (error) {
      console.log(`❌ /api/complete-workflow failed: ${error}`);
      throw error;
    }
  });

  test('Step-by-Step Legacy Page Workflow Timing', async ({ page }) => {
    console.log('\n🧪 Testing legacy page step-by-step workflow timing...');
    
    // Step 1: Navigate to legacy page
    console.log('🚀 Step 1: Loading legacy page...');
    const step1Start = Date.now();
    await page.goto('/legacy');
    await page.waitForLoadState('networkidle', { timeout: 10000 });
    const step1Time = Date.now() - step1Start;
    console.log(`⏱️ Step 1 (Page load): ${step1Time}ms`);
    
    // Step 2: Wait for groups to load automatically
    console.log('🚀 Step 2: Waiting for groups to load...');
    const step2Start = Date.now();
    
    try {
      // Wait for either groups to appear or error message
      await Promise.race([
        page.waitForSelector('.group-card', { timeout: 15000 }),
        page.waitForSelector('.error', { timeout: 15000 }),
        page.waitForSelector('[data-testid="no-groups"]', { timeout: 15000 })
      ]);
      
      const step2Time = Date.now() - step2Start;
      console.log(`⏱️ Step 2 (Groups load): ${step2Time}ms`);
      
      // Check what loaded
      const groupCards = await page.locator('.group-card').count();
      const errorMessage = await page.locator('.error').count();
      
      console.log(`📊 Groups loaded: ${groupCards}`);
      console.log(`📊 Error messages: ${errorMessage}`);
      
      if (groupCards === 0 && errorMessage === 0) {
        console.log('⚠️ No groups or errors found - checking page state');
        const bodyContent = await page.locator('body').textContent();
        console.log(`📝 Page content: ${bodyContent?.substring(0, 500)}...`);
      }
      
    } catch (error) {
      const step2Time = Date.now() - step2Start;
      console.log(`❌ Step 2 TIMEOUT after ${step2Time}ms: ${error}`);
      
      // Capture page state at timeout
      const bodyContent = await page.locator('body').textContent();
      console.log(`📝 Page content at timeout: ${bodyContent?.substring(0, 500)}...`);
      throw error;
    }
    
    // Step 3: Test photo selection if groups are available
    const groupCards = await page.locator('.group-card').count();
    if (groupCards > 0) {
      console.log('🚀 Step 3: Testing photo selection...');
      const step3Start = Date.now();
      
      // Click first photo checkbox
      const firstCheckbox = page.locator('.photo-item input[type="checkbox"]').first();
      await firstCheckbox.click({ timeout: 5000 });
      
      const step3Time = Date.now() - step3Start;
      console.log(`⏱️ Step 3 (Photo selection): ${step3Time}ms`);
      
      // Step 4: Test delete confirmation button
      console.log('🚀 Step 4: Testing delete confirmation...');
      const step4Start = Date.now();
      
      const deleteButton = page.locator('button:has-text("Confirm Deletions")');
      await deleteButton.click({ timeout: 5000 });
      
      // Wait for confirmation dialog or processing
      try {
        await Promise.race([
          page.waitForSelector('.confirmation-dialog', { timeout: 5000 }),
          page.waitForSelector('.processing', { timeout: 5000 }),
          page.waitForSelector('.success', { timeout: 5000 })
        ]);
        
        const step4Time = Date.now() - step4Start;
        console.log(`⏱️ Step 4 (Delete confirmation): ${step4Time}ms`);
        
      } catch (error) {
        const step4Time = Date.now() - step4Start;
        console.log(`❌ Step 4 TIMEOUT after ${step4Time}ms: ${error}`);
        throw error;
      }
    }
  });

  test('JavaScript Memory and Performance Monitoring', async ({ page }) => {
    console.log('\n🧪 Testing JavaScript performance and memory usage...');
    
    // Enable runtime to monitor performance
    await page.goto('/legacy');
    
    // Get initial memory usage
    const initialMetrics = await page.evaluate(() => {
      return {
        usedJSHeapSize: performance.memory?.usedJSHeapSize || 0,
        totalJSHeapSize: performance.memory?.totalJSHeapSize || 0,
        jsHeapSizeLimit: performance.memory?.jsHeapSizeLimit || 0,
        timing: performance.timing
      };
    });
    
    console.log(`📊 Initial memory usage: ${(initialMetrics.usedJSHeapSize / 1024 / 1024).toFixed(2)} MB`);
    
    // Wait for page to load and monitor for 10 seconds
    await page.waitForTimeout(2000);
    
    let memoryIncreasing = false;
    let consecutiveIncreases = 0;
    let lastMemoryUsage = initialMetrics.usedJSHeapSize;
    
    for (let i = 0; i < 5; i++) {
      await page.waitForTimeout(2000);
      
      const currentMetrics = await page.evaluate(() => {
        return {
          usedJSHeapSize: performance.memory?.usedJSHeapSize || 0,
          totalJSHeapSize: performance.memory?.totalJSHeapSize || 0
        };
      });
      
      const memoryDiff = currentMetrics.usedJSHeapSize - lastMemoryUsage;
      const memoryMB = (currentMetrics.usedJSHeapSize / 1024 / 1024).toFixed(2);
      
      console.log(`📊 Memory at ${(i + 1) * 2}s: ${memoryMB} MB (${memoryDiff > 0 ? '+' : ''}${(memoryDiff / 1024).toFixed(1)} KB)`);
      
      if (memoryDiff > 100000) { // More than 100KB increase
        consecutiveIncreases++;
        if (consecutiveIncreases >= 3) {
          memoryIncreasing = true;
        }
      } else {
        consecutiveIncreases = 0;
      }
      
      lastMemoryUsage = currentMetrics.usedJSHeapSize;
    }
    
    if (memoryIncreasing) {
      console.log('⚠️ Potential memory leak detected - memory consistently increasing');
    } else {
      console.log('✅ Memory usage appears stable');
    }
    
    // Check for infinite loops by monitoring CPU usage patterns
    const performanceEntries = await page.evaluate(() => {
      return performance.getEntriesByType('navigation')[0];
    });
    
    console.log(`📊 DOM content loaded: ${performanceEntries.domContentLoadedEventEnd - performanceEntries.domContentLoadedEventStart}ms`);
    console.log(`📊 Page load complete: ${performanceEntries.loadEventEnd - performanceEntries.loadEventStart}ms`);
  });

  test('Network Request Waterfall Analysis', async ({ page }) => {
    console.log('\n🧪 Analyzing network request patterns...');
    
    const requestLog = [];
    
    page.on('request', request => {
      requestLog.push({
        url: request.url(),
        method: request.method(),
        timestamp: Date.now(),
        type: 'request'
      });
    });
    
    page.on('response', response => {
      requestLog.push({
        url: response.url(),
        status: response.status(),
        timestamp: Date.now(),
        type: 'response'
      });
    });
    
    const startTime = Date.now();
    await page.goto('/legacy');
    
    // Wait for initial requests to complete
    await page.waitForTimeout(5000);
    
    // Sort and analyze request patterns
    requestLog.sort((a, b) => a.timestamp - b.timestamp);
    
    console.log('\n📊 Request Timeline:');
    let apiGroupsStartTime = null;
    let apiGroupsEndTime = null;
    
    requestLog.forEach((entry, index) => {
      const relativeTime = entry.timestamp - startTime;
      console.log(`${relativeTime}ms - ${entry.type}: ${entry.method || ''} ${entry.url} ${entry.status || ''}`);
      
      if (entry.url.includes('/api/groups') && entry.type === 'request') {
        apiGroupsStartTime = entry.timestamp;
      }
      if (entry.url.includes('/api/groups') && entry.type === 'response') {
        apiGroupsEndTime = entry.timestamp;
      }
    });
    
    if (apiGroupsStartTime && apiGroupsEndTime) {
      const apiGroupsTime = apiGroupsEndTime - apiGroupsStartTime;
      console.log(`\n⏱️ /api/groups total time: ${apiGroupsTime}ms`);
      
      if (apiGroupsTime > 5000) {
        console.log('🚨 /api/groups is taking longer than 5 seconds - BOTTLENECK IDENTIFIED');
      }
    }
    
    // Check for stuck requests (no response after 10 seconds)
    const stuckRequests = requestLog.filter(entry => 
      entry.type === 'request' && 
      !requestLog.find(resp => resp.type === 'response' && resp.url === entry.url && resp.timestamp > entry.timestamp)
    );
    
    if (stuckRequests.length > 0) {
      console.log('\n🚨 STUCK REQUESTS DETECTED:');
      stuckRequests.forEach(req => {
        console.log(`- ${req.method} ${req.url}`);
      });
    }
  });

  test('Backend API Health Check', async ({ page }) => {
    console.log('\n🧪 Testing backend API health...');
    
    const endpoints = [
      '/api/health',
      '/api/stats',
      '/api/cache-stats'
    ];
    
    for (const endpoint of endpoints) {
      console.log(`🔍 Testing ${endpoint}...`);
      const startTime = Date.now();
      
      try {
        const response = await page.request.get(endpoint, { timeout: 5000 });
        const endTime = Date.now();
        const responseTime = endTime - startTime;
        
        console.log(`✅ ${endpoint}: ${response.status()} (${responseTime}ms)`);
        
        if (response.ok()) {
          const data = await response.json();
          console.log(`📊 Response: ${JSON.stringify(data, null, 2).substring(0, 200)}...`);
        }
        
      } catch (error) {
        console.log(`❌ ${endpoint} failed: ${error}`);
      }
    }
  });

  test('Comprehensive Workflow Hang Detection', async ({ page }) => {
    console.log('\n🧪 Running comprehensive workflow hang detection...');
    
    const hangDetectionTimeout = 20000; // 20 seconds max
    let workflowCompleted = false;
    let hangPoint = null;
    
    try {
      // Navigate to legacy page
      console.log('📍 Checkpoint 1: Loading legacy page...');
      await page.goto('/legacy', { timeout: 10000 });
      
      console.log('📍 Checkpoint 2: Waiting for page load...');
      await page.waitForLoadState('domcontentloaded', { timeout: 10000 });
      
      console.log('📍 Checkpoint 3: Waiting for groups or error...');
      const groupsOrError = await Promise.race([
        page.waitForSelector('.group-card', { timeout: hangDetectionTimeout }),
        page.waitForSelector('.error', { timeout: hangDetectionTimeout }),
        page.waitForSelector('[data-testid="loading"]', { timeout: 2000 }).then(() => null)
      ]);
      
      if (groupsOrError === null) {
        console.log('📍 Checkpoint 4: Found loading state, waiting longer...');
        await page.waitForSelector('.group-card, .error', { timeout: hangDetectionTimeout - 2000 });
      }
      
      const groupCount = await page.locator('.group-card').count();
      const errorCount = await page.locator('.error').count();
      
      console.log(`📊 Final state: ${groupCount} groups, ${errorCount} errors`);
      
      if (groupCount > 0) {
        console.log('📍 Checkpoint 5: Testing photo interaction...');
        
        // Try to click first photo
        const firstPhoto = page.locator('.photo-item').first();
        await firstPhoto.click({ timeout: 5000 });
        
        console.log('📍 Checkpoint 6: Workflow completed successfully!');
        workflowCompleted = true;
      } else if (errorCount > 0) {
        const errorText = await page.locator('.error').textContent();
        console.log(`📍 Workflow completed with error: ${errorText}`);
        workflowCompleted = true;
      }
      
    } catch (error) {
      hangPoint = error.message;
      console.log(`🚨 WORKFLOW HANG DETECTED: ${hangPoint}`);
      
      // Capture page state at hang point
      const url = page.url();
      const title = await page.title();
      const bodyText = await page.locator('body').textContent();
      
      console.log(`📍 Hang details:`);
      console.log(`- URL: ${url}`);
      console.log(`- Title: ${title}`);
      console.log(`- Body length: ${bodyText?.length || 0} chars`);
      console.log(`- Body preview: ${bodyText?.substring(0, 300)}...`);
    }
    
    // Final assessment
    if (workflowCompleted) {
      console.log('✅ Workflow completed without hanging');
    } else {
      console.log('🚨 Workflow hang confirmed');
      expect(workflowCompleted).toBe(true); // This will fail and show hang point
    }
  });

});