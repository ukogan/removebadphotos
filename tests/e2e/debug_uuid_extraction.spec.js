const { test, expect } = require('@playwright/test');

test.describe('UUID Extraction Debugging', () => {
  test('Debug step-by-step photo UUID extraction workflow', async ({ page }) => {
    const consoleMessages = [];
    const networkRequests = [];
    const networkResponses = [];

    // Capture console messages
    page.on('console', message => {
      consoleMessages.push({
        type: message.type(),
        text: message.text(),
        timestamp: new Date().toISOString()
      });
      console.log(`[BROWSER CONSOLE ${message.type().toUpperCase()}] ${message.text()}`);
    });

    // Capture network activity
    page.on('request', request => {
      if (request.url().includes('/api/')) {
        networkRequests.push({
          url: request.url(),
          method: request.method(),
          headers: request.headers(),
          postData: request.postData(),
          timestamp: new Date().toISOString()
        });
        console.log(`[NETWORK REQUEST] ${request.method()} ${request.url()}`);
        if (request.postData()) {
          console.log(`[REQUEST BODY] ${request.postData()}`);
        }
      }
    });

    page.on('response', response => {
      if (response.url().includes('/api/')) {
        networkResponses.push({
          url: response.url(),
          status: response.status(),
          headers: response.headers(),
          timestamp: new Date().toISOString()
        });
        console.log(`[NETWORK RESPONSE] ${response.status()} ${response.url()}`);
      }
    });

    // Step 1: Navigate to filters page
    console.log('\n=== STEP 1: Navigate to filters page ===');
    await page.goto('http://127.0.0.1:5003/filters');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000); // Allow time for initial data loading

    // Step 2: Check what data is currently loaded BEFORE applying any filters
    console.log('\n=== STEP 2: Check initial data state ===');
    const initialData = await page.evaluate(() => {
      return {
        currentFilteredDataExists: typeof window.currentFilteredData !== 'undefined',
        currentFilteredDataLength: window.currentFilteredData ? window.currentFilteredData.length : 0,
        currentFiltersExists: typeof window.currentFilters !== 'undefined',
        currentFilters: window.currentFilters || null,
        hasAnalyzeButton: !!document.getElementById('analyze-selected-btn')
      };
    });
    console.log('Initial data state:', JSON.stringify(initialData, null, 2));

    // Step 3: Apply Min size 1MB filter
    console.log('\n=== STEP 3: Apply Min size 1MB filter ===');
    await page.fill('#min-size-mb', '1');
    await page.waitForTimeout(1000); // Allow filter to apply
    
    // Check data after applying filter
    const afterFilterData = await page.evaluate(() => {
      return {
        currentFilteredDataLength: window.currentFilteredData ? window.currentFilteredData.length : 0,
        currentFilters: window.currentFilters || null
      };
    });
    console.log('After filter data:', JSON.stringify(afterFilterData, null, 2));

    // Step 4: Before clicking "Analyze Selected", check current data
    console.log('\n=== STEP 4: Check data before clicking Analyze Selected ===');
    const preAnalyzeData = await page.evaluate(() => {
      console.log('Current filtered data:', window.currentFilteredData);
      console.log('Current filters:', window.currentFilters);
      
      return {
        currentFilteredDataLength: window.currentFilteredData ? window.currentFilteredData.length : 0,
        currentFilters: window.currentFilters || null,
        sampleCluster: window.currentFilteredData && window.currentFilteredData.length > 0 ? window.currentFilteredData[0] : null
      };
    });
    console.log('Pre-analyze data:', JSON.stringify(preAnalyzeData, null, 2));

    // Step 5: Click "Analyze Selected" and monitor the entire process
    console.log('\n=== STEP 5: Click Analyze Selected and monitor process ===');
    
    // Clear previous network data to focus on analyze button click
    networkRequests.length = 0;
    networkResponses.length = 0;
    consoleMessages.length = 0;

    const analyzeButton = await page.locator('#analyze-selected-btn');
    await expect(analyzeButton).toBeVisible();
    
    // Click and wait for network activity
    await Promise.all([
      analyzeButton.click(),
      page.waitForTimeout(5000) // Give time for all requests to complete
    ]);

    // Step 6: Capture the exact sequence of events
    console.log('\n=== STEP 6: Analyze the complete workflow ===');

    // Find the specific API calls we're interested in
    const filterClustersRequests = networkRequests.filter(req => 
      req.url.includes('/api/filter-clusters') && req.url.includes('include_photos=true')
    );
    
    const saveSessionRequests = networkRequests.filter(req => 
      req.url.includes('/api/save-filter-session') || req.url.includes('/api/session/save')
    );

    console.log(`Found ${filterClustersRequests.length} filter-clusters requests with include_photos=true`);
    console.log(`Found ${saveSessionRequests.length} save session requests`);

    // Get API responses for the key calls
    for (const request of filterClustersRequests) {
      console.log(`\n--- FILTER CLUSTERS REQUEST ---`);
      console.log(`URL: ${request.url}`);
      console.log(`Method: ${request.method}`);
      
      const response = networkResponses.find(resp => resp.url === request.url);
      if (response) {
        console.log(`Response Status: ${response.status}`);
      }
    }

    for (const request of saveSessionRequests) {
      console.log(`\n--- SAVE SESSION REQUEST ---`);
      console.log(`URL: ${request.url}`);
      console.log(`Method: ${request.method}`);
      console.log(`Request Body: ${request.postData}`);
      
      const response = networkResponses.find(resp => resp.url === request.url);
      if (response) {
        console.log(`Response Status: ${response.status}`);
      }
    }

    // Step 7: Check what happened to UUID extraction
    console.log('\n=== STEP 7: Check UUID extraction results ===');
    const uuidExtractionMessages = consoleMessages.filter(msg => 
      msg.text.includes('Extracted') && msg.text.includes('photo UUIDs')
    );
    
    const errorMessages = consoleMessages.filter(msg => 
      msg.type === 'error' || msg.text.includes('Error') || msg.text.includes('Failed')
    );

    console.log(`Found ${uuidExtractionMessages.length} UUID extraction messages:`);
    uuidExtractionMessages.forEach(msg => {
      console.log(`- ${msg.timestamp}: ${msg.text}`);
    });

    console.log(`Found ${errorMessages.length} error messages:`);
    errorMessages.forEach(msg => {
      console.log(`- ${msg.timestamp} [${msg.type}]: ${msg.text}`);
    });

    // Step 8: Get final state after analyze button click
    const finalState = await page.evaluate(() => {
      return {
        currentURL: window.location.href,
        hasRedirected: window.location.href.includes('dashboard'),
        finalFilteredDataLength: window.currentFilteredData ? window.currentFilteredData.length : 0
      };
    });
    
    console.log('\nFinal state:', JSON.stringify(finalState, null, 2));

    // Detailed analysis of the workflow
    console.log('\n=== DIAGNOSTIC SUMMARY ===');
    console.log('Total network requests captured:', networkRequests.length);
    console.log('Total network responses captured:', networkResponses.length);
    console.log('Total console messages captured:', consoleMessages.length);
    
    // Check for specific failure points
    const hasFilterClustersCall = filterClustersRequests.length > 0;
    const hasSaveSessionCall = saveSessionRequests.length > 0;
    const hasUUIDExtraction = uuidExtractionMessages.length > 0;
    const hasErrors = errorMessages.length > 0;
    
    console.log('\nWorkflow Analysis:');
    console.log(`✓ Filter clusters API call made: ${hasFilterClustersCall}`);
    console.log(`✓ Save session API call made: ${hasSaveSessionCall}`);
    console.log(`✓ UUID extraction message logged: ${hasUUIDExtraction}`);
    console.log(`⚠ Errors detected: ${hasErrors}`);

    if (!hasFilterClustersCall) {
      console.log('❌ ISSUE: No filter-clusters API call with include_photos=true was made');
    }
    
    if (!hasSaveSessionCall) {
      console.log('❌ ISSUE: No save session API call was made');
    }
    
    if (!hasUUIDExtraction) {
      console.log('❌ ISSUE: No UUID extraction message was logged');
    }

    // Look for the specific issue
    const badRequestResponses = networkResponses.filter(resp => resp.status === 400);
    if (badRequestResponses.length > 0) {
      console.log('\n❌ Found 400 Bad Request responses:');
      badRequestResponses.forEach(resp => {
        console.log(`- ${resp.url}: Status ${resp.status}`);
      });
    }

    // Final assertions to verify the test captured useful data
    expect(networkRequests.length).toBeGreaterThan(0);
    expect(analyzeButton).toHaveBeenClicked();
  });
});