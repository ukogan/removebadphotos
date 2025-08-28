// JavaScript Performance and Infinite Loop Detection for Photo Deletion Workflow
// Target: Detect client-side bottlenecks, memory leaks, and infinite loops

import { test, expect } from '@playwright/test';

test.describe('JavaScript Performance and Memory Leak Detection', () => {

  test.beforeEach(async ({ page }) => {
    // Enable detailed console logging
    page.on('console', msg => {
      const type = msg.type();
      if (['error', 'warn'].includes(type)) {
        console.log(`🖥️ ${type.toUpperCase()}: ${msg.text()}`);
      }
    });

    // Log unhandled errors
    page.on('pageerror', error => {
      console.log(`❌ JavaScript Error: ${error}`);
    });

    // Monitor long-running scripts
    page.on('dialog', dialog => {
      console.log(`⚠️ Dialog appeared: ${dialog.message()}`);
      dialog.dismiss();
    });
  });

  test('Memory Usage Pattern Analysis', async ({ page }) => {
    console.log('\n🧪 Testing JavaScript memory usage patterns...');

    await page.goto('/legacy');
    
    // Wait for initial load
    await page.waitForTimeout(2000);

    // Get baseline memory
    const initialMemory = await page.evaluate(() => {
      if (!performance.memory) return { usedJSHeapSize: 0, totalJSHeapSize: 0 };
      return {
        used: performance.memory.usedJSHeapSize,
        total: performance.memory.totalJSHeapSize,
        limit: performance.memory.jsHeapSizeLimit,
        timestamp: Date.now()
      };
    });

    console.log(`📊 Initial memory: ${(initialMemory.used / 1024 / 1024).toFixed(2)} MB`);

    // Monitor memory for 15 seconds
    const memoryReadings = [initialMemory];
    const monitoringDuration = 15000;
    const interval = 2000;
    const iterations = Math.floor(monitoringDuration / interval);

    for (let i = 0; i < iterations; i++) {
      await page.waitForTimeout(interval);
      
      const currentMemory = await page.evaluate(() => {
        if (!performance.memory) return { used: 0, total: 0 };
        return {
          used: performance.memory.usedJSHeapSize,
          total: performance.memory.totalJSHeapSize,
          timestamp: Date.now()
        };
      });

      memoryReadings.push(currentMemory);
      
      const memoryMB = (currentMemory.used / 1024 / 1024).toFixed(2);
      const deltaKB = ((currentMemory.used - initialMemory.used) / 1024).toFixed(1);
      console.log(`📊 Memory at ${(i + 1) * interval}ms: ${memoryMB} MB (Δ${deltaKB} KB)`);
    }

    // Analyze memory trend
    let increasingCount = 0;
    let totalIncrease = 0;
    
    for (let i = 1; i < memoryReadings.length; i++) {
      const delta = memoryReadings[i].used - memoryReadings[i - 1].used;
      if (delta > 50000) { // More than 50KB increase
        increasingCount++;
        totalIncrease += delta;
      }
    }

    const avgIncreaseKB = (totalIncrease / 1024) / memoryReadings.length;
    console.log(`📊 Memory analysis:`);
    console.log(`   - Significant increases: ${increasingCount}/${memoryReadings.length - 1}`);
    console.log(`   - Average increase per reading: ${avgIncreaseKB.toFixed(1)} KB`);
    console.log(`   - Total increase: ${((memoryReadings[memoryReadings.length - 1].used - initialMemory.used) / 1024).toFixed(1)} KB`);

    // Memory leak detection
    if (increasingCount >= 3 && avgIncreaseKB > 100) {
      console.log('🚨 POTENTIAL MEMORY LEAK DETECTED');
      console.log('🔍 Memory consistently increasing during idle period');
      
      // This is a finding, not necessarily a test failure
      expect(avgIncreaseKB).toBeLessThan(500); // Allow some increase, but flag major leaks
    } else {
      console.log('✅ No significant memory leak detected');
    }
  });

  test('Long-Running Operation Detection', async ({ page }) => {
    console.log('\n🧪 Testing for long-running JavaScript operations...');

    let longOperationDetected = false;
    let operationDetails = null;

    // Monitor performance marks and measures
    await page.addInitScript(() => {
      const originalSetTimeout = window.setTimeout;
      const originalSetInterval = window.setInterval;
      const originalRequestAnimationFrame = window.requestAnimationFrame;
      
      window.longRunningOperations = [];
      
      // Override setTimeout to catch long delays
      window.setTimeout = function(callback, delay, ...args) {
        if (delay && delay > 5000) {
          window.longRunningOperations.push({
            type: 'setTimeout',
            delay: delay,
            stack: new Error().stack
          });
        }
        return originalSetTimeout.call(this, callback, delay, ...args);
      };

      // Override setInterval to catch frequent operations
      window.setInterval = function(callback, delay, ...args) {
        if (delay && delay < 100) {
          window.longRunningOperations.push({
            type: 'setInterval_fast',
            delay: delay,
            stack: new Error().stack
          });
        }
        return originalSetInterval.call(this, callback, delay, ...args);
      };
    });

    await page.goto('/legacy');
    
    // Monitor page for 10 seconds
    console.log('📊 Monitoring for long-running operations...');
    await page.waitForTimeout(10000);

    // Check for detected long operations
    const longOps = await page.evaluate(() => {
      return window.longRunningOperations || [];
    });

    if (longOps.length > 0) {
      console.log('🚨 LONG-RUNNING OPERATIONS DETECTED:');
      longOps.forEach((op, index) => {
        console.log(`${index + 1}. ${op.type} - delay: ${op.delay}ms`);
        if (op.stack) {
          // Print first few lines of stack trace
          const stackLines = op.stack.split('\n').slice(0, 3);
          stackLines.forEach(line => console.log(`   ${line.trim()}`));
        }
      });
      longOperationDetected = true;
    } else {
      console.log('✅ No problematic long-running operations detected');
    }

    // Test should pass but report findings
    if (longOperationDetected) {
      console.log('⚠️ Consider optimizing detected long-running operations');
    }
  });

  test('API Call Pattern Analysis', async ({ page }) => {
    console.log('\n🧪 Analyzing API call patterns for potential issues...');

    const networkLog = [];
    let duplicateRequests = 0;
    let slowRequests = 0;
    let failedRequests = 0;

    // Monitor network requests
    page.on('request', request => {
      const timestamp = Date.now();
      networkLog.push({
        url: request.url(),
        method: request.method(),
        timestamp: timestamp,
        type: 'request'
      });
    });

    page.on('response', response => {
      const timestamp = Date.now();
      const request = response.request();
      const responseTime = timestamp - (networkLog.find(r => 
        r.url === response.url() && 
        r.type === 'request' && 
        r.timestamp <= timestamp
      )?.timestamp || timestamp);

      networkLog.push({
        url: response.url(),
        method: request.method(),
        status: response.status(),
        timestamp: timestamp,
        responseTime: responseTime,
        type: 'response'
      });

      // Track metrics
      if (responseTime > 5000) slowRequests++;
      if (response.status() >= 400) failedRequests++;
    });

    await page.goto('/legacy');
    
    // Wait for requests to complete
    await page.waitForTimeout(8000);

    // Analyze request patterns
    console.log('\n📊 API Call Analysis:');
    
    // Group requests by URL
    const requestCounts = {};
    const apiRequests = networkLog.filter(entry => 
      entry.url.includes('/api/') && entry.type === 'request'
    );

    apiRequests.forEach(request => {
      const cleanUrl = request.url.split('?')[0]; // Remove query params
      requestCounts[cleanUrl] = (requestCounts[cleanUrl] || 0) + 1;
    });

    console.log('📋 Request frequency:');
    Object.entries(requestCounts).forEach(([url, count]) => {
      const urlPart = url.split('/api/')[1] || url;
      console.log(`   /api/${urlPart}: ${count} requests`);
      
      if (count > 3) {
        console.log(`   🚨 EXCESSIVE REQUESTS: ${count} calls to same endpoint`);
        duplicateRequests += count - 1;
      }
    });

    console.log(`📊 Performance metrics:`);
    console.log(`   - Duplicate/excessive requests: ${duplicateRequests}`);
    console.log(`   - Slow requests (>5s): ${slowRequests}`);
    console.log(`   - Failed requests: ${failedRequests}`);

    // Check for specific problematic patterns
    const groupsRequests = networkLog.filter(entry => 
      entry.url.includes('/api/groups') && entry.type === 'response'
    );

    if (groupsRequests.length > 0) {
      const avgGroupsTime = groupsRequests.reduce((sum, req) => sum + (req.responseTime || 0), 0) / groupsRequests.length;
      console.log(`📊 /api/groups average response time: ${avgGroupsTime.toFixed(0)}ms`);
      
      if (avgGroupsTime > 5000) {
        console.log('🚨 /api/groups is consistently slow - BOTTLENECK IDENTIFIED');
      }
    }

    // Test assertions
    expect(duplicateRequests).toBeLessThan(10); // Allow some duplication but flag excessive
    expect(failedRequests).toBe(0); // No failed requests expected in normal operation
  });

  test('DOM Manipulation Performance', async ({ page }) => {
    console.log('\n🧪 Testing DOM manipulation performance...');

    await page.goto('/legacy');

    // Measure DOM ready state and timing
    const domTiming = await page.evaluate(() => {
      const timing = performance.timing;
      const navigation = performance.getEntriesByType('navigation')[0];
      
      return {
        domContentLoaded: timing.domContentLoadedEventEnd - timing.domContentLoadedEventStart,
        domInteractive: timing.domInteractive - timing.navigationStart,
        loadComplete: timing.loadEventEnd - timing.loadEventStart,
        navigationTiming: navigation ? {
          domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
          loadComplete: navigation.loadEventEnd - navigation.loadEventStart
        } : null
      };
    });

    console.log('📊 DOM Performance Metrics:');
    console.log(`   - DOM Content Loaded: ${domTiming.domContentLoaded}ms`);
    console.log(`   - DOM Interactive: ${domTiming.domInteractive}ms`);
    console.log(`   - Load Complete: ${domTiming.loadComplete}ms`);

    // Test DOM interaction responsiveness
    try {
      console.log('🔍 Testing DOM interaction responsiveness...');
      
      // Wait for groups to potentially load
      await page.waitForTimeout(3000);
      
      // Try to click elements and measure response time
      const clickableElements = await page.locator('button, input[type="checkbox"], .clickable').count();
      console.log(`📊 Found ${clickableElements} interactive elements`);

      if (clickableElements > 0) {
        const clickStart = Date.now();
        try {
          await page.locator('button, input[type="checkbox"], .clickable').first().click({ timeout: 2000 });
          const clickTime = Date.now() - clickStart;
          console.log(`⏱️ Click response time: ${clickTime}ms`);
          
          if (clickTime > 1000) {
            console.log('🚨 SLOW DOM INTERACTION DETECTED');
          }
        } catch (e) {
          console.log('⚠️ Could not test click interaction:', e.message);
        }
      }

    } catch (error) {
      console.log(`⚠️ DOM interaction test error: ${error.message}`);
    }

    // Performance should be reasonable
    expect(domTiming.domInteractive).toBeLessThan(10000); // 10 seconds max for DOM ready
  });

  test('Infinite Loop and Hang Detection', async ({ page }) => {
    console.log('\n🧪 Testing for infinite loops and hangs...');

    // Set up monitoring for stuck scripts
    let scriptHangDetected = false;
    let hangDetails = null;

    // Add script to detect infinite loops
    await page.addInitScript(() => {
      let executionStart = Date.now();
      let longRunningDetected = false;
      
      // Override common loop-causing functions
      const originalSetInterval = window.setInterval;
      window.setInterval = function(callback, delay, ...args) {
        if (delay < 10) {
          console.warn('🚨 Very fast interval detected:', delay + 'ms');
          window.fastIntervals = (window.fastIntervals || 0) + 1;
        }
        return originalSetInterval.call(this, callback, delay, ...args);
      };

      // Monitor for scripts running too long
      const checkLongRunning = () => {
        const runTime = Date.now() - executionStart;
        if (runTime > 10000 && !longRunningDetected) {
          longRunningDetected = true;
          console.warn('🚨 Long-running script detected:', runTime + 'ms');
        }
      };

      setInterval(checkLongRunning, 1000);
    });

    // Navigate and monitor
    const navigationStart = Date.now();
    await page.goto('/legacy');

    // Monitor page for signs of hanging
    const maxWaitTime = 15000; // 15 seconds max
    let pageLoaded = false;
    let timeoutReached = false;

    try {
      // Race between successful load and timeout
      await Promise.race([
        page.waitForSelector('body', { timeout: maxWaitTime }).then(() => {
          pageLoaded = true;
        }),
        page.waitForTimeout(maxWaitTime).then(() => {
          timeoutReached = true;
        })
      ]);

      const navigationTime = Date.now() - navigationStart;
      console.log(`⏱️ Page navigation time: ${navigationTime}ms`);

      if (timeoutReached && !pageLoaded) {
        console.log('🚨 PAGE HANG DETECTED - Navigation exceeded timeout');
        scriptHangDetected = true;
        hangDetails = 'Navigation timeout after ' + maxWaitTime + 'ms';
      }

      // Check for fast intervals
      const fastIntervals = await page.evaluate(() => window.fastIntervals || 0);
      if (fastIntervals > 0) {
        console.log(`🚨 ${fastIntervals} fast intervals detected - potential performance issue`);
      }

      // Monitor CPU usage pattern by checking script execution
      const scriptMetrics = await page.evaluate(() => {
        const nav = performance.getEntriesByType('navigation')[0];
        return nav ? {
          domContentLoaded: nav.domContentLoadedEventEnd - nav.domContentLoadedEventStart,
          domComplete: nav.domComplete - nav.navigationStart,
          scriptExecutionTime: nav.domContentLoadedEventStart - nav.responseEnd
        } : {};
      });

      console.log('📊 Script execution metrics:', scriptMetrics);

      if (scriptMetrics.scriptExecutionTime > 5000) {
        console.log('🚨 LONG SCRIPT EXECUTION TIME DETECTED');
        scriptHangDetected = true;
      }

    } catch (error) {
      console.log(`❌ Hang detection error: ${error}`);
      scriptHangDetected = true;
      hangDetails = error.message;
    }

    // Report findings
    if (scriptHangDetected) {
      console.log('🚨 SCRIPT HANG OR INFINITE LOOP DETECTED');
      if (hangDetails) {
        console.log(`🔍 Details: ${hangDetails}`);
      }
      
      // Capture page state for debugging
      try {
        const pageTitle = await page.title();
        const url = page.url();
        console.log(`📍 Page state: ${pageTitle} at ${url}`);
      } catch (e) {
        console.log('Could not capture page state');
      }
      
      // Allow test to fail to highlight the issue
      expect(scriptHangDetected).toBe(false);
    } else {
      console.log('✅ No infinite loops or script hangs detected');
    }
  });

});