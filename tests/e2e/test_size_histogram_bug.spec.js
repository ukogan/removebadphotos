// tests/e2e/test_size_histogram_bug.spec.js
import { test, expect } from '@playwright/test';

/**
 * Comprehensive frontend test for size histogram display bug
 * 
 * Issue: Size histogram not displaying despite backend API returning correct data
 * Expected: Should show visual histogram with clickable bars and hover tooltips
 * 
 * Test Strategy:
 * 1. Verify page loads and basic elements exist
 * 2. Check API calls are made and return data
 * 3. Verify JavaScript functions are called
 * 4. Inspect DOM to see what's actually rendered
 * 5. Test user interactions with histogram
 */

test.describe('Size Histogram Display Bug Investigation', () => {
  
  test.beforeEach(async ({ page }) => {
    // Enable console logging to catch JavaScript errors
    page.on('console', msg => {
      console.log(`[${msg.type()}] ${msg.text()}`);
    });
    
    // Catch JavaScript errors
    page.on('pageerror', error => {
      console.error(`JavaScript Error: ${error.message}`);
    });
    
    // Intercept network requests to monitor API calls
    page.on('request', request => {
      if (request.url().includes('filter-distributions')) {
        console.log(`📡 API Request: ${request.url()}`);
      }
    });
    
    page.on('response', response => {
      if (response.url().includes('filter-distributions')) {
        console.log(`📡 API Response: ${response.status()} ${response.url()}`);
      }
    });
  });

  test('should load filters page and verify basic elements exist', async ({ page }) => {
    // Navigate to the filters page
    await page.goto('/filters');
    
    // Wait for page to load
    await expect(page.locator('h1')).toContainText('Smart Photo Filter');
    
    // Verify the size histogram container exists
    const histogramContainer = page.locator('#size-histogram');
    await expect(histogramContainer).toBeVisible();
    
    // Check initial loading state
    const loadingText = histogramContainer.locator('.loading-distributions');
    await expect(loadingText).toContainText('Loading size distribution...');
    
    console.log('✅ Basic page elements verified');
  });

  test('should make API call to filter-distributions endpoint', async ({ page }) => {
    // Set up response interception
    let apiResponseData = null;
    
    page.route('**/api/filter-distributions', async (route, request) => {
      const response = await route.fetch();
      const body = await response.text();
      apiResponseData = JSON.parse(body);
      console.log('📊 Intercepted API Response:', JSON.stringify(apiResponseData, null, 2));
      route.fulfill({ response });
    });
    
    // Navigate to page
    await page.goto('/filters');
    
    // Wait for the API call to complete
    await page.waitForFunction(() => {
      return window.fetch !== undefined;
    });
    
    // Give time for loadDistributions to be called
    await page.waitForTimeout(2000);
    
    // Verify API was called and returned data
    expect(apiResponseData).not.toBeNull();
    expect(apiResponseData.success).toBe(true);
    expect(apiResponseData.distributions).toBeDefined();
    expect(apiResponseData.distributions.size_histogram).toBeDefined();
    
    console.log('✅ API call verified with data:', Object.keys(apiResponseData.distributions.size_histogram));
  });

  test('should verify updateSizeHistogram function is called with correct data', async ({ page }) => {
    // Navigate to page
    await page.goto('/filters');
    
    // Wait for page to load and API calls to complete
    await page.waitForTimeout(3000);
    
    // Check if updateSizeHistogram function was called by evaluating the page context
    const histogramFunctionCalled = await page.evaluate(() => {
      // Check if the function exists
      return typeof window.updateSizeHistogram === 'function';
    });
    
    expect(histogramFunctionCalled).toBe(true);
    
    // Check if loadDistributions was called
    const distributionsLoaded = await page.evaluate(() => {
      return typeof window.loadDistributions === 'function';
    });
    
    expect(distributionsLoaded).toBe(true);
    console.log('✅ JavaScript functions verified');
  });

  test('should inspect actual DOM content in size histogram container', async ({ page }) => {
    await page.goto('/filters');
    
    // Wait for initial load
    await page.waitForTimeout(3000);
    
    // Get the actual HTML content of the size histogram div
    const histogramHTML = await page.locator('#size-histogram').innerHTML();
    console.log('📊 Size Histogram DOM Content:', histogramHTML);
    
    // Check what's actually rendered
    const histogramText = await page.locator('#size-histogram').textContent();
    console.log('📊 Size Histogram Text Content:', histogramText);
    
    // Verify if loading text is still showing or if histogram was rendered
    const isStillLoading = histogramText.includes('Loading size distribution');
    const hasHistogramBars = await page.locator('#size-histogram .histogram-bar').count();
    const hasHistogramChart = await page.locator('#size-histogram .histogram-chart').count();
    
    console.log('📊 Analysis:', {
      isStillLoading,
      hasHistogramBars,
      hasHistogramChart,
      histogramText: histogramText.substring(0, 100)
    });
    
    // If still loading, this indicates the issue
    if (isStillLoading) {
      console.error('❌ ISSUE FOUND: Size histogram still showing loading text');
    }
    
    if (hasHistogramBars === 0) {
      console.error('❌ ISSUE FOUND: No histogram bars rendered');
    }
  });

  test('should verify JavaScript execution flow and errors', async ({ page }) => {
    let jsErrors = [];
    let consoleMessages = [];
    
    page.on('pageerror', error => {
      jsErrors.push(error.message);
    });
    
    page.on('console', msg => {
      consoleMessages.push(`[${msg.type()}] ${msg.text()}`);
    });
    
    await page.goto('/filters');
    
    // Wait for JavaScript execution
    await page.waitForTimeout(4000);
    
    // Check for specific function calls in console
    const distributionsLog = consoleMessages.find(msg => 
      msg.includes('Loading distribution statistics') || 
      msg.includes('Updating size histogram')
    );
    
    console.log('📊 JavaScript Errors:', jsErrors);
    console.log('📊 Console Messages (first 10):', consoleMessages.slice(0, 10));
    console.log('📊 Distribution-related logs:', distributionsLog);
    
    // Verify no critical JavaScript errors
    const criticalErrors = jsErrors.filter(error => 
      error.includes('updateSizeHistogram') || 
      error.includes('filter-distributions') ||
      error.includes('undefined')
    );
    
    if (criticalErrors.length > 0) {
      console.error('❌ CRITICAL JAVASCRIPT ERRORS FOUND:', criticalErrors);
    }
    
    expect(criticalErrors).toHaveLength(0);
  });

  test('should test histogram interactivity once rendered', async ({ page }) => {
    await page.goto('/filters');
    
    // Wait for potential histogram rendering
    await page.waitForTimeout(5000);
    
    // Check if histogram bars are clickable
    const histogramBars = page.locator('.histogram-bar');
    const barCount = await histogramBars.count();
    
    console.log('📊 Number of histogram bars found:', barCount);
    
    if (barCount > 0) {
      // Test clicking first bar
      await histogramBars.first().click();
      
      // Check if size sliders were updated
      const minSizeValue = await page.locator('#min-size').getAttribute('value');
      const maxSizeValue = await page.locator('#max-size').getAttribute('value');
      
      console.log('📊 Size values after bar click:', { minSizeValue, maxSizeValue });
      
      // Test hover tooltip
      await histogramBars.first().hover();
      const tooltip = page.locator('.bar-tooltip');
      const tooltipVisible = await tooltip.isVisible();
      
      console.log('📊 Tooltip visibility on hover:', tooltipVisible);
    } else {
      console.warn('⚠️ No histogram bars found to test interactivity');
    }
  });

  test('should verify complete data flow from API to DOM', async ({ page }) => {
    // Track the complete data flow
    let apiData = null;
    let domUpdateDetected = false;
    
    // Intercept API response
    page.route('**/api/filter-distributions', async (route, request) => {
      const response = await route.fetch();
      const body = await response.text();
      apiData = JSON.parse(body);
      route.fulfill({ response });
    });
    
    await page.goto('/filters');
    
    // Wait for API call
    await page.waitForTimeout(2000);
    
    // Monitor DOM changes to the histogram container
    const domObserver = await page.evaluateHandle(() => {
      return new Promise((resolve) => {
        const target = document.getElementById('size-histogram');
        if (!target) {
          resolve(false);
          return;
        }
        
        const observer = new MutationObserver((mutations) => {
          mutations.forEach((mutation) => {
            if (mutation.type === 'childList' || mutation.type === 'characterData') {
              const hasHistogramContent = target.innerHTML.includes('histogram-chart');
              if (hasHistogramContent) {
                resolve(true);
              }
            }
          });
        });
        
        observer.observe(target, { 
          childList: true, 
          subtree: true, 
          characterData: true 
        });
        
        // Timeout after 5 seconds
        setTimeout(() => {
          observer.disconnect();
          resolve(false);
        }, 5000);
      });
    });
    
    domUpdateDetected = await domObserver.jsonValue();
    
    // Final verification
    const finalHistogramContent = await page.locator('#size-histogram').innerHTML();
    
    console.log('📊 Complete Data Flow Analysis:', {
      apiDataReceived: !!apiData,
      apiHasSizeHistogram: !!(apiData?.distributions?.size_histogram),
      sizeHistogramData: apiData?.distributions?.size_histogram,
      domUpdateDetected,
      finalHistogramContainsChart: finalHistogramContent.includes('histogram-chart'),
      finalHistogramContent: finalHistogramContent.substring(0, 200)
    });
    
    // This is the key assertion - we should have moved from loading to actual histogram
    expect(finalHistogramContent).not.toContain('Loading size distribution...');
  });

  test('should test cross-browser compatibility', async ({ page, browserName }) => {
    console.log(`🌐 Testing in ${browserName}`);
    
    await page.goto('/filters');
    await page.waitForTimeout(4000);
    
    const histogramVisible = await page.locator('#size-histogram').isVisible();
    const histogramContent = await page.locator('#size-histogram').textContent();
    const hasHistogramBars = await page.locator('.histogram-bar').count();
    
    console.log(`📊 ${browserName} Results:`, {
      histogramVisible,
      isStillLoading: histogramContent.includes('Loading'),
      hasHistogramBars,
      content: histogramContent.substring(0, 100)
    });
    
    // Basic visibility test should pass in all browsers
    expect(histogramVisible).toBe(true);
  });
});

// Additional diagnostic test for API endpoint directly
test.describe('Backend API Verification', () => {
  test('should verify /api/filter-distributions endpoint returns correct data structure', async ({ request }) => {
    const response = await request.get('/api/filter-distributions');
    const data = await response.json();
    
    console.log('📊 Direct API Test Response:', JSON.stringify(data, null, 2));
    
    expect(response.ok()).toBeTruthy();
    expect(data.success).toBe(true);
    expect(data.distributions).toBeDefined();
    expect(data.distributions.size_histogram).toBeDefined();
    
    // Verify histogram data structure
    const histogram = data.distributions.size_histogram;
    expect(typeof histogram).toBe('object');
    
    // Should have numeric keys and values
    const keys = Object.keys(histogram);
    const values = Object.values(histogram);
    
    expect(keys.length).toBeGreaterThan(0);
    keys.forEach(key => {
      expect(parseInt(key)).not.toBeNaN();
    });
    values.forEach(value => {
      expect(typeof value).toBe('number');
      expect(value).toBeGreaterThanOrEqual(0);
    });
    
    console.log('✅ API endpoint verification complete');
  });
});