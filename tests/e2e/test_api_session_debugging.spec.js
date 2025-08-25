const { test, expect } = require('@playwright/test');

test.describe('API Session Debugging', () => {
  test('Direct API testing for session save/retrieve issue', async ({ page, request }) => {
    console.log('\n🔧 DIRECT API SESSION DEBUGGING\n');
    console.log('=' .repeat(50));

    // First, navigate to the application to establish session context
    await page.goto('http://127.0.0.1:5003/filters');
    await page.waitForLoadState('networkidle');

    // Test 1: Check current session state
    console.log('\n📍 TEST 1: Current session state check');
    const sessionCheck1 = await page.evaluate(async () => {
      try {
        const response = await fetch('/api/get-filter-session');
        const data = await response.json();
        return { status: response.status, data: data };
      } catch (error) {
        return { error: error.message };
      }
    });
    console.log(`Initial session state: ${JSON.stringify(sessionCheck1, null, 2)}`);

    // Test 2: Test the save-filter-session endpoint directly with minimal data
    console.log('\n📍 TEST 2: Testing save-filter-session endpoint with minimal data');
    
    const testSessionData = {
      session_id: 'test-session-' + Date.now(),
      filter_criteria: {
        year: 2025,
        max_size_mb: 100
      },
      total_clusters_in_filter: 5,
      total_photos_in_filter: 10,
      selected_clusters: [
        {
          cluster_id: 'test_cluster_1',
          photos: ['photo1.jpg', 'photo2.jpg']
        }
      ],
      timestamp: new Date().toISOString()
    };

    const saveTest = await page.evaluate(async (sessionData) => {
      try {
        const response = await fetch('/api/save-filter-session', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(sessionData)
        });
        
        console.log(`Save response status: ${response.status}`);
        console.log(`Save response headers:`, Object.fromEntries(response.headers));
        
        // Try to read the response text first, then parse as JSON
        const responseText = await response.text();
        console.log(`Save response text: "${responseText}"`);
        
        let parsedData;
        try {
          parsedData = JSON.parse(responseText);
        } catch (parseError) {
          return {
            status: response.status,
            responseText: responseText,
            parseError: parseError.message,
            success: false
          };
        }
        
        return {
          status: response.status,
          data: parsedData,
          responseText: responseText,
          success: true
        };
      } catch (error) {
        return { 
          error: error.message,
          success: false
        };
      }
    }, testSessionData);

    console.log(`Save test result: ${JSON.stringify(saveTest, null, 2)}`);

    // Test 3: Check if session was saved after the test save
    console.log('\n📍 TEST 3: Check session state after test save');
    const sessionCheck2 = await page.evaluate(async () => {
      try {
        const response = await fetch('/api/get-filter-session');
        const text = await response.text();
        console.log(`Get session response text: "${text}"`);
        
        const data = JSON.parse(text);
        return { status: response.status, data: data };
      } catch (error) {
        return { error: error.message };
      }
    });
    console.log(`Session state after save: ${JSON.stringify(sessionCheck2, null, 2)}`);

    // Test 4: Simulate the actual filter interface save process
    console.log('\n📍 TEST 4: Simulate actual filter interface save process');
    
    // Apply a filter first to get actual cluster data
    const filterButton = page.locator('.year-btn').nth(1); // Select first year filter
    if (await filterButton.count() > 0) {
      await filterButton.click();
      await page.waitForTimeout(2000);
    }

    // Click Apply Filters
    const applyButton = page.locator('button').filter({ hasText: 'Apply Filters' });
    if (await applyButton.count() > 0) {
      await applyButton.click();
      await page.waitForTimeout(3000);
    }

    // Now try the actual save process that the UI uses
    const actualSaveTest = await page.evaluate(async () => {
      // Check if analyzeSelected function exists
      if (typeof window.analyzeSelected === 'function') {
        console.log('analyzeSelected function found');
        
        // Try to get the current filter state
        let currentFilters = {};
        let selectedClusters = [];
        
        // Try to get selected year
        const selectedYearBtn = document.querySelector('.year-btn.selected, .year-btn.active');
        if (selectedYearBtn) {
          const yearMatch = selectedYearBtn.textContent.match(/(\d{4})/);
          if (yearMatch) {
            currentFilters.year = parseInt(yearMatch[1]);
          }
        }
        
        // Try to get cluster data from the page
        const clusterCards = document.querySelectorAll('.cluster-card');
        console.log(`Found ${clusterCards.length} cluster cards on page`);
        
        clusterCards.forEach((card, index) => {
          if (index < 3) { // Just take first 3 for testing
            const clusterIdElement = card.querySelector('[data-cluster-id]');
            const clusterId = clusterIdElement ? clusterIdElement.dataset.clusterId : `cluster_${index}`;
            selectedClusters.push({
              cluster_id: clusterId,
              photos: [] // Will be populated by backend
            });
          }
        });
        
        console.log(`Extracted filters: ${JSON.stringify(currentFilters)}`);
        console.log(`Extracted clusters: ${selectedClusters.length}`);
        
        // Create session data similar to what the UI would create
        const sessionData = {
          session_id: 'ui-simulation-' + Date.now(),
          filter_criteria: currentFilters,
          total_clusters_in_filter: clusterCards.length,
          total_photos_in_filter: 0, // Would be calculated by backend
          selected_clusters: selectedClusters,
          timestamp: new Date().toISOString()
        };
        
        // Make the save request
        try {
          const response = await fetch('/api/save-filter-session', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json'
            },
            body: JSON.stringify(sessionData)
          });
          
          const responseText = await response.text();
          console.log(`UI simulation save response: ${response.status} - "${responseText}"`);
          
          return {
            status: response.status,
            responseText: responseText,
            sessionData: sessionData,
            success: response.status === 200
          };
        } catch (error) {
          return {
            error: error.message,
            sessionData: sessionData,
            success: false
          };
        }
      } else {
        return { error: 'analyzeSelected function not found' };
      }
    });

    console.log(`UI simulation result: ${JSON.stringify(actualSaveTest, null, 2)}`);

    // Test 5: Final session check
    console.log('\n📍 TEST 5: Final session state check');
    const sessionCheck3 = await page.evaluate(async () => {
      try {
        const response = await fetch('/api/get-filter-session');
        const data = await response.json();
        return { status: response.status, data: data };
      } catch (error) {
        return { error: error.message };
      }
    });
    console.log(`Final session state: ${JSON.stringify(sessionCheck3, null, 2)}`);

    // Test 6: Check browser cookies/local storage for session data
    console.log('\n📍 TEST 6: Browser session storage check');
    const browserSession = await page.evaluate(() => {
      return {
        cookies: document.cookie,
        localStorage: Object.keys(localStorage).length > 0 ? Object.fromEntries(Object.entries(localStorage)) : {},
        sessionStorage: Object.keys(sessionStorage).length > 0 ? Object.fromEntries(Object.entries(sessionStorage)) : {}
      };
    });
    console.log(`Browser session data: ${JSON.stringify(browserSession, null, 2)}`);

    // Summary
    console.log('\n📊 API SESSION DEBUGGING SUMMARY');
    console.log('=' .repeat(50));
    console.log(`Test 1 - Initial session: ${sessionCheck1.data?.has_session || 'failed'}`);
    console.log(`Test 2 - Manual save: ${saveTest.success ? 'success' : 'failed'}`);
    console.log(`Test 3 - Post-save session: ${sessionCheck2.data?.has_session || 'failed'}`);
    console.log(`Test 4 - UI simulation: ${actualSaveTest.success ? 'success' : 'failed'}`);
    console.log(`Test 5 - Final session: ${sessionCheck3.data?.has_session || 'failed'}`);
    console.log(`Browser storage: ${Object.keys(browserSession.localStorage).length + Object.keys(browserSession.sessionStorage).length} items`);

    // Take a screenshot of the final state
    await page.screenshot({ path: '/Users/urikogan/code/dedup/test-results/api-session-debug.png', fullPage: true });
  });
});