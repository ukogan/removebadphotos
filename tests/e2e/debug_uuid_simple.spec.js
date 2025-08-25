const { test, expect } = require('@playwright/test');

test.describe('UUID Extraction Simple Debug', () => {
  test('Manual UUID extraction workflow analysis', async ({ page }) => {
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
      console.log(`[CONSOLE ${message.type().toUpperCase()}] ${message.text()}`);
    });

    // Capture network activity
    page.on('request', request => {
      if (request.url().includes('/api/')) {
        networkRequests.push({
          url: request.url(),
          method: request.method(),
          postData: request.postData(),
          timestamp: new Date().toISOString()
        });
        console.log(`[REQUEST] ${request.method()} ${request.url()}`);
        if (request.postData()) {
          console.log(`[POST DATA] ${request.postData()}`);
        }
      }
    });

    page.on('response', response => {
      if (response.url().includes('/api/')) {
        console.log(`[RESPONSE] ${response.status()} ${response.url()}`);
        networkResponses.push({
          url: response.url(),
          status: response.status(),
          timestamp: new Date().toISOString()
        });
      }
    });

    console.log('\n=== STEP 1: Navigate to filters page ===');
    await page.goto('http://127.0.0.1:5003/filters');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);

    console.log('\n=== STEP 2: Check UI elements present ===');
    
    // Check for different possible filter elements
    const analyzeButton = page.locator('button:has-text("Analyze")').first();
    const yearButtons = page.locator('button:contains("2024")').first();
    const resetButton = page.locator('button:has-text("Reset")');

    console.log('Analyze button visible:', await analyzeButton.isVisible());
    console.log('Year 2024 button visible:', await yearButtons.isVisible());
    console.log('Reset button visible:', await resetButton.isVisible());

    console.log('\n=== STEP 3: Apply filter by clicking 2024 year ===');
    if (await yearButtons.isVisible()) {
      await yearButtons.click();
      await page.waitForTimeout(2000);
      console.log('Clicked 2024 year filter');
    } else {
      console.log('2024 year button not found, proceeding without filter');
    }

    console.log('\n=== STEP 4: Check current state before analyze ===');
    const preAnalyzeState = await page.evaluate(() => {
      return {
        hasCurrentFilteredData: typeof window.currentFilteredData !== 'undefined',
        currentFilteredDataLength: window.currentFilteredData ? window.currentFilteredData.length : 0,
        hasCurrentFilters: typeof window.currentFilters !== 'undefined',
        currentFilters: window.currentFilters || null,
        analyzeButtonExists: !!document.querySelector('button[onclick*="analyzeSelected"]') || !!document.getElementById('analyze-selected-btn')
      };
    });
    
    console.log('Pre-analyze state:', JSON.stringify(preAnalyzeState, null, 2));

    console.log('\n=== STEP 5: Execute JavaScript to manually trigger analyze ===');
    
    // Try to find and click the analyze button through various methods
    try {
      // Method 1: Look for analyzeSelected function
      const hasAnalyzeFunction = await page.evaluate(() => {
        return typeof window.analyzeSelected === 'function';
      });
      
      if (hasAnalyzeFunction) {
        console.log('Found analyzeSelected function, calling it...');
        await page.evaluate(() => {
          window.analyzeSelected();
        });
        await page.waitForTimeout(3000);
      } else {
        console.log('analyzeSelected function not found');
        
        // Method 2: Try to click any analyze button
        const buttons = page.locator('button');
        const count = await buttons.count();
        console.log(`Found ${count} buttons on page`);
        
        for (let i = 0; i < count; i++) {
          const buttonText = await buttons.nth(i).textContent();
          console.log(`Button ${i}: "${buttonText}"`);
          if (buttonText && buttonText.toLowerCase().includes('analyze')) {
            console.log(`Clicking analyze button: "${buttonText}"`);
            await buttons.nth(i).click();
            await page.waitForTimeout(3000);
            break;
          }
        }
      }
    } catch (error) {
      console.log('Error executing analyze:', error.message);
    }

    console.log('\n=== STEP 6: Check what network requests were made ===');
    
    // Filter relevant requests
    const filterClustersRequests = networkRequests.filter(req => 
      req.url.includes('/api/filter-clusters') && req.url.includes('include_photos=true')
    );
    
    const saveSessionRequests = networkRequests.filter(req => 
      req.url.includes('/api/save-filter-session') || req.url.includes('/api/session/save')
    );

    console.log(`Filter clusters requests with include_photos=true: ${filterClustersRequests.length}`);
    filterClustersRequests.forEach((req, index) => {
      console.log(`  ${index + 1}. ${req.method} ${req.url}`);
    });

    console.log(`Save session requests: ${saveSessionRequests.length}`);
    saveSessionRequests.forEach((req, index) => {
      console.log(`  ${index + 1}. ${req.method} ${req.url}`);
      if (req.postData) {
        console.log(`     POST DATA: ${req.postData}`);
      }
    });

    console.log('\n=== STEP 7: Check for UUID extraction messages ===');
    const uuidMessages = consoleMessages.filter(msg => 
      msg.text.includes('Extracted') && msg.text.includes('photo UUIDs')
    );
    
    const errorMessages = consoleMessages.filter(msg => 
      msg.type === 'error' || msg.text.includes('Error') || msg.text.includes('Failed')
    );

    console.log(`UUID extraction messages: ${uuidMessages.length}`);
    uuidMessages.forEach(msg => console.log(`  - ${msg.text}`));

    console.log(`Error messages: ${errorMessages.length}`);
    errorMessages.forEach(msg => console.log(`  - [${msg.type}] ${msg.text}`));

    console.log('\n=== STEP 8: Manual API test ===');
    
    // Make the API call manually to see what we get
    try {
      const response = await page.request.get('http://127.0.0.1:5003/api/filter-clusters?min_size_mb=1&include_photos=true');
      const data = await response.json();
      
      console.log(`Manual API call status: ${response.status()}`);
      if (response.ok()) {
        console.log(`Response contains ${data.clusters ? data.clusters.length : 0} clusters`);
        
        if (data.clusters && data.clusters.length > 0) {
          const sampleCluster = data.clusters[0];
          console.log('Sample cluster structure:', JSON.stringify(sampleCluster, null, 2));
          
          // Check for photo UUIDs in the response
          let totalUUIDs = 0;
          data.clusters.forEach(cluster => {
            if (cluster.photos && Array.isArray(cluster.photos)) {
              totalUUIDs += cluster.photos.length;
            }
          });
          console.log(`Total photo UUIDs available in API response: ${totalUUIDs}`);
        }
      } else {
        console.log(`API call failed with status ${response.status()}`);
      }
    } catch (error) {
      console.log('Manual API call failed:', error.message);
    }

    console.log('\n=== DIAGNOSTIC SUMMARY ===');
    console.log(`Total network requests: ${networkRequests.length}`);
    console.log(`Total console messages: ${consoleMessages.length}`);
    console.log(`Filter clusters requests: ${filterClustersRequests.length}`);
    console.log(`Save session requests: ${saveSessionRequests.length}`);
    console.log(`UUID extraction messages: ${uuidMessages.length}`);
    console.log(`Error messages: ${errorMessages.length}`);

    // Final state check
    const finalState = await page.evaluate(() => {
      return {
        currentURL: window.location.href,
        redirected: window.location.href.includes('dashboard')
      };
    });
    
    console.log('Final state:', JSON.stringify(finalState, null, 2));
  });
});