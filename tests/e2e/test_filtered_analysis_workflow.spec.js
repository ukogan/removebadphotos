const { test, expect } = require('@playwright/test');

test.describe('Filtered Analysis Workflow Investigation', () => {
  test.setTimeout(120000); // 2 minutes timeout for comprehensive testing

  test('Complete filtered analysis workflow - detailed diagnostic', async ({ page, context }) => {
    console.log('\n🔍 Starting comprehensive filtered analysis workflow test...\n');
    
    // Enable request/response logging for debugging
    const requests = [];
    const responses = [];
    const consoleErrors = [];
    const networkErrors = [];

    page.on('console', msg => {
      console.log(`[BROWSER] ${msg.type()}: ${msg.text()}`);
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    page.on('request', request => {
      requests.push({
        url: request.url(),
        method: request.method(),
        timestamp: new Date().toISOString()
      });
    });

    page.on('response', response => {
      responses.push({
        url: response.url(),
        status: response.status(),
        statusText: response.statusText(),
        timestamp: new Date().toISOString()
      });
    });

    page.on('requestfailed', request => {
      networkErrors.push({
        url: request.url(),
        failure: request.failure().errorText,
        timestamp: new Date().toISOString()
      });
    });

    try {
      // STEP 1: Navigate to filter interface
      console.log('📍 STEP 1: Navigating to filter interface...');
      await page.goto('http://127.0.0.1:5003/filters');
      
      // Wait for the page to fully load and check for initial errors
      await page.waitForLoadState('networkidle');
      await page.screenshot({ path: '/Users/urikogan/code/dedup/test-results/filter-interface-loaded.png', fullPage: true });
      
      // Verify filter interface is loaded properly
      await expect(page.locator('h1')).toContainText('Smart Filter Interface');
      console.log('✅ Filter interface loaded successfully');

      // Wait for library stats to load
      console.log('⏳ Waiting for library statistics to load...');
      const statsLoaded = page.locator('.stats-bar .stat-value').first();
      await expect(statsLoaded).not.toHaveText('0', { timeout: 30000 });
      console.log('✅ Library statistics loaded');

      // STEP 2: Apply filters and wait for clusters to load
      console.log('\n📍 STEP 2: Applying filters and waiting for clusters...');
      
      // Apply year filter - select 2023 if available
      const yearButtons = page.locator('.year-btn');
      const yearCount = await yearButtons.count();
      console.log(`Found ${yearCount} year filter buttons`);
      
      if (yearCount > 0) {
        // Try to find 2023, or use the first available year
        const year2023 = page.locator('.year-btn').filter({ hasText: '2023' });
        if (await year2023.count() > 0) {
          await year2023.click();
          console.log('✅ Applied year filter: 2023');
        } else {
          await yearButtons.first().click();
          const selectedYear = await yearButtons.first().textContent();
          console.log(`✅ Applied year filter: ${selectedYear}`);
        }
        await page.waitForTimeout(2000); // Wait for filter to apply
      }

      // Apply file type filter - select JPEG
      const jpegButton = page.locator('.type-btn').filter({ hasText: 'JPEG' });
      if (await jpegButton.count() > 0) {
        await jpegButton.click();
        console.log('✅ Applied file type filter: JPEG');
        await page.waitForTimeout(2000);
      }

      // Apply size filter - select a medium size range
      const sizeButtons = page.locator('.size-btn');
      if (await sizeButtons.count() > 0) {
        const mediumSizeButton = sizeButtons.nth(1); // Usually second button is a medium size
        if (await mediumSizeButton.count() > 0) {
          await mediumSizeButton.click();
          const selectedSize = await mediumSizeButton.textContent();
          console.log(`✅ Applied size filter: ${selectedSize}`);
          await page.waitForTimeout(2000);
        }
      }

      // Wait for clusters to load after filters are applied
      console.log('⏳ Waiting for filtered clusters to load...');
      await page.waitForSelector('.cluster-grid', { timeout: 30000 });
      
      // Check if clusters are actually displayed
      const clusterCards = page.locator('.cluster-card');
      const clusterCount = await clusterCards.count();
      console.log(`📊 Found ${clusterCount} clusters after filtering`);
      
      if (clusterCount === 0) {
        console.log('⚠️ No clusters found after filtering - this might be the issue!');
        await page.screenshot({ path: '/Users/urikogan/code/dedup/test-results/no-clusters-after-filter.png', fullPage: true });
      } else {
        console.log('✅ Clusters loaded successfully after filtering');
        await page.screenshot({ path: '/Users/urikogan/code/dedup/test-results/clusters-after-filter.png', fullPage: true });
      }

      // Check the filtered stats display
      const filteredStats = page.locator('.filtered-stats');
      if (await filteredStats.count() > 0) {
        const filteredStatsText = await filteredStats.textContent();
        console.log(`📈 Filtered stats: ${filteredStatsText}`);
      }

      // STEP 3: Click "Analyze Selected" button
      console.log('\n📍 STEP 3: Clicking "Analyze Selected" button...');
      
      const analyzeButton = page.locator('button').filter({ hasText: 'Analyze Selected' });
      await expect(analyzeButton).toBeVisible({ timeout: 10000 });
      await expect(analyzeButton).toBeEnabled();
      
      console.log('🎯 "Analyze Selected" button is visible and enabled');
      await page.screenshot({ path: '/Users/urikogan/code/dedup/test-results/analyze-button-ready.png', fullPage: true });
      
      // Monitor network requests during the save operation
      const saveRequestPromise = page.waitForResponse(response => 
        response.url().includes('/api/save-filter-session') && response.request().method() === 'POST'
      );
      
      await analyzeButton.click();
      console.log('✅ Clicked "Analyze Selected" button');

      // Wait for the save-filter-session request and check its response
      try {
        const saveResponse = await saveRequestPromise;
        const saveStatus = saveResponse.status();
        console.log(`📡 Save filter session response: ${saveStatus}`);
        
        if (saveStatus === 200) {
          const saveData = await saveResponse.json();
          console.log(`✅ Filter session saved successfully: ${JSON.stringify(saveData)}`);
        } else {
          console.log(`❌ Filter session save failed with status: ${saveStatus}`);
          const saveError = await saveResponse.text();
          console.log(`Error response: ${saveError}`);
        }
      } catch (error) {
        console.log(`❌ Error waiting for save-filter-session response: ${error.message}`);
      }

      // Wait for redirect to dashboard
      console.log('⏳ Waiting for redirect to dashboard...');
      await page.waitForURL('**/dashboard**', { timeout: 15000 });
      console.log('✅ Successfully redirected to dashboard');

      // STEP 4: Verify dashboard detects filtered mode
      console.log('\n📍 STEP 4: Verifying dashboard filtered mode detection...');
      await page.waitForLoadState('networkidle');
      await page.screenshot({ path: '/Users/urikogan/code/dedup/test-results/dashboard-filtered-mode.png', fullPage: true });

      // Check for filtered mode indicators
      const filteredModeIndicator = page.locator('.filtered-mode, .filter-active, [data-filtered="true"]');
      const filteredStatsSection = page.locator('.stats-overview, .filtered-stats');
      
      if (await filteredModeIndicator.count() > 0) {
        console.log('✅ Dashboard detected filtered mode (UI indicator found)');
        const indicatorText = await filteredModeIndicator.textContent();
        console.log(`Filtered mode indicator: ${indicatorText}`);
      } else {
        console.log('⚠️ No explicit filtered mode UI indicator found');
      }

      // Check if stats show filtered data
      if (await filteredStatsSection.count() > 0) {
        const statsText = await filteredStatsSection.textContent();
        console.log(`📊 Dashboard stats: ${statsText.substring(0, 200)}...`);
        
        // Look for keywords that indicate filtered mode
        if (statsText.toLowerCase().includes('filter') || statsText.toLowerCase().includes('selected')) {
          console.log('✅ Dashboard stats appear to show filtered data');
        } else {
          console.log('⚠️ Dashboard stats may not be showing filtered data');
        }
      }

      // STEP 5: Click "Start Smart Analysis" and monitor for failures
      console.log('\n📍 STEP 5: Testing "Start Smart Analysis" in filtered mode...');
      
      const smartAnalysisButton = page.locator('button').filter({ hasText: /Start Smart Analysis|Begin Analysis/ });
      await expect(smartAnalysisButton).toBeVisible({ timeout: 15000 });
      await expect(smartAnalysisButton).toBeEnabled();
      
      console.log('🎯 "Start Smart Analysis" button found and enabled');
      await page.screenshot({ path: '/Users/urikogan/code/dedup/test-results/smart-analysis-button-ready.png', fullPage: true });

      // Monitor the smart analysis API request
      const analysisRequestPromise = page.waitForResponse(response => 
        response.url().includes('/api/smart-analysis') && response.request().method() === 'POST'
      );

      await smartAnalysisButton.click();
      console.log('✅ Clicked "Start Smart Analysis" button');

      // Wait for and analyze the smart analysis response
      try {
        const analysisResponse = await analysisRequestPromise;
        const analysisStatus = analysisResponse.status();
        console.log(`📡 Smart analysis API response: ${analysisStatus}`);
        
        if (analysisStatus === 200) {
          const analysisData = await analysisResponse.json();
          console.log(`✅ Smart analysis API succeeded`);
          console.log(`Analysis result keys: ${Object.keys(analysisData)}`);
          
          if (analysisData.filtered_mode) {
            console.log('✅ Analysis confirmed it was running in filtered mode');
          } else {
            console.log('⚠️ Analysis did not indicate filtered mode');
          }
          
          if (analysisData.groups) {
            console.log(`📊 Analysis returned ${analysisData.groups.length} groups`);
          }
          
          if (analysisData.clusters) {
            console.log(`📊 Analysis returned ${analysisData.clusters.length} clusters`);
          }
          
        } else {
          console.log(`❌ Smart analysis API failed with status: ${analysisStatus}`);
          const errorText = await analysisResponse.text();
          console.log(`Error response: ${errorText}`);
        }
      } catch (error) {
        console.log(`❌ Error with smart analysis API: ${error.message}`);
      }

      // Wait for analysis to complete and check results
      console.log('⏳ Waiting for analysis to complete...');
      await page.waitForTimeout(10000); // Give analysis time to process
      
      // Check for success or failure indicators
      const successIndicator = page.locator('.alert-success, .success-message, [data-analysis="complete"]');
      const errorIndicator = page.locator('.alert-error, .error-message, .alert-danger');
      
      if (await successIndicator.count() > 0) {
        console.log('✅ Analysis appears to have completed successfully');
        const successText = await successIndicator.textContent();
        console.log(`Success message: ${successText}`);
        await page.screenshot({ path: '/Users/urikogan/code/dedup/test-results/analysis-success.png', fullPage: true });
      } else if (await errorIndicator.count() > 0) {
        console.log('❌ Analysis appears to have failed');
        const errorText = await errorIndicator.textContent();
        console.log(`Error message: ${errorText}`);
        await page.screenshot({ path: '/Users/urikogan/code/dedup/test-results/analysis-error.png', fullPage: true });
      } else {
        console.log('⚠️ No clear success/failure indicator found');
        await page.screenshot({ path: '/Users/urikogan/code/dedup/test-results/analysis-unclear.png', fullPage: true });
      }

      // Final screenshot of the dashboard state
      await page.screenshot({ path: '/Users/urikogan/code/dedup/test-results/final-dashboard-state.png', fullPage: true });

    } catch (error) {
      console.log(`❌ Test failed with error: ${error.message}`);
      await page.screenshot({ path: '/Users/urikogan/code/dedup/test-results/test-failure.png', fullPage: true });
      throw error;
    }

    // COMPREHENSIVE DIAGNOSTIC REPORT
    console.log('\n📊 COMPREHENSIVE DIAGNOSTIC REPORT\n');
    console.log('='.repeat(60));
    
    console.log('\n🌐 NETWORK REQUESTS SUMMARY:');
    console.log(`Total requests made: ${requests.length}`);
    requests.forEach((req, idx) => {
      if (req.url.includes('api') || req.url.includes('filter') || req.url.includes('analysis')) {
        console.log(`${idx + 1}. ${req.method} ${req.url} (${req.timestamp})`);
      }
    });
    
    console.log('\n📡 RESPONSE STATUS SUMMARY:');
    responses.forEach((res, idx) => {
      if (res.url.includes('api') || res.url.includes('filter') || res.url.includes('analysis')) {
        console.log(`${idx + 1}. ${res.status} ${res.statusText} - ${res.url} (${res.timestamp})`);
      }
    });
    
    if (networkErrors.length > 0) {
      console.log('\n❌ NETWORK ERRORS:');
      networkErrors.forEach((err, idx) => {
        console.log(`${idx + 1}. ${err.url} - ${err.failure} (${err.timestamp})`);
      });
    } else {
      console.log('\n✅ No network errors detected');
    }
    
    if (consoleErrors.length > 0) {
      console.log('\n🔥 CONSOLE ERRORS:');
      consoleErrors.forEach((err, idx) => {
        console.log(`${idx + 1}. ${err}`);
      });
    } else {
      console.log('\n✅ No console errors detected');
    }
    
    console.log('\n' + '='.repeat(60));
    console.log('🎯 TEST COMPLETED - Check screenshots in test-results/ directory');
  });

  test('Isolated filter session save test', async ({ page }) => {
    console.log('\n🔧 Running isolated filter session save test...\n');
    
    // Navigate to filter interface
    await page.goto('http://127.0.0.1:5003/filters');
    await page.waitForLoadState('networkidle');
    
    // Wait for stats to load
    await page.waitForSelector('.stats-bar .stat-value', { timeout: 30000 });
    
    // Apply a simple filter
    const yearButtons = page.locator('.year-btn');
    if (await yearButtons.count() > 0) {
      await yearButtons.first().click();
      await page.waitForTimeout(2000);
    }
    
    // Monitor the save request specifically
    let saveRequestData = null;
    let saveResponseData = null;
    
    page.on('request', async request => {
      if (request.url().includes('/api/save-filter-session')) {
        try {
          const postData = request.postData();
          saveRequestData = postData;
          console.log(`📤 Save request payload: ${postData}`);
        } catch (error) {
          console.log(`❌ Could not capture request payload: ${error.message}`);
        }
      }
    });
    
    page.on('response', async response => {
      if (response.url().includes('/api/save-filter-session')) {
        try {
          const responseText = await response.text();
          saveResponseData = responseText;
          console.log(`📥 Save response: ${response.status()} - ${responseText}`);
        } catch (error) {
          console.log(`❌ Could not capture response: ${error.message}`);
        }
      }
    });
    
    // Click analyze button
    const analyzeButton = page.locator('button').filter({ hasText: 'Analyze Selected' });
    if (await analyzeButton.count() > 0) {
      await analyzeButton.click();
      await page.waitForTimeout(5000); // Wait for save operation
    }
    
    console.log('\n📊 FILTER SESSION SAVE DIAGNOSTIC:');
    console.log(`Request payload: ${saveRequestData || 'Not captured'}`);
    console.log(`Response data: ${saveResponseData || 'Not captured'}`);
  });

  test('Dashboard filtered mode detection test', async ({ page, context }) => {
    console.log('\n🎛️ Testing dashboard filtered mode detection...\n');
    
    // Create a mock filter session in browser storage/cookie to simulate the saved session
    await page.goto('http://127.0.0.1:5003/dashboard');
    
    // Check if dashboard can detect existing filter sessions
    const sessionCheckResponse = await page.evaluate(async () => {
      try {
        const response = await fetch('/api/get-filter-session');
        const data = await response.json();
        return { status: response.status, data: data };
      } catch (error) {
        return { error: error.message };
      }
    });
    
    console.log(`📊 Filter session check result: ${JSON.stringify(sessionCheckResponse)}`);
    
    // Test dashboard's ability to handle filtered vs non-filtered modes
    await page.waitForLoadState('networkidle');
    await page.screenshot({ path: '/Users/urikogan/code/dedup/test-results/dashboard-mode-detection.png', fullPage: true });
    
    const dashboardContent = await page.content();
    const hasFilteredIndicators = dashboardContent.includes('filter') || 
                                  dashboardContent.includes('selected') || 
                                  dashboardContent.includes('filtered');
    
    console.log(`Dashboard contains filtered mode indicators: ${hasFilteredIndicators}`);
  });
});