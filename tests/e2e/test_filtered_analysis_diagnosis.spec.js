const { test, expect } = require('@playwright/test');

test.describe('Filtered Analysis Diagnosis - Focused Investigation', () => {
  test.setTimeout(90000); // 1.5 minutes

  test('Step-by-step filtered analysis workflow diagnosis', async ({ page }) => {
    console.log('\n🔍 FOCUSED FILTERED ANALYSIS DIAGNOSIS\n');
    console.log('=' .repeat(50));
    
    // Track network requests and console messages
    const apiRequests = [];
    const consoleErrors = [];
    
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
        console.log(`❌ [CONSOLE ERROR] ${msg.text()}`);
      }
    });
    
    page.on('request', request => {
      if (request.url().includes('/api/')) {
        apiRequests.push({
          method: request.method(),
          url: request.url(),
          timestamp: new Date().toISOString()
        });
        console.log(`📡 API Request: ${request.method()} ${request.url()}`);
      }
    });
    
    page.on('response', async response => {
      if (response.url().includes('/api/')) {
        console.log(`📡 API Response: ${response.status()} ${response.url()}`);
        if (response.status() !== 200) {
          try {
            const errorText = await response.text();
            console.log(`❌ Error Response: ${errorText}`);
          } catch (e) {
            console.log(`❌ Could not read error response: ${e.message}`);
          }
        }
      }
    });

    try {
      // STEP 1: Load filter interface and verify basic functionality
      console.log('\n📍 STEP 1: Loading filter interface...');
      await page.goto('http://127.0.0.1:5003/filters');
      await page.waitForLoadState('networkidle');
      
      // Check page title/heading (corrected based on earlier test failure)
      const heading = page.locator('h1').first();
      const headingText = await heading.textContent();
      console.log(`📄 Page heading: "${headingText}"`);
      
      // Wait for statistics to load
      console.log('⏳ Waiting for statistics to load...');
      const statsValues = page.locator('.stat-value');
      await expect(statsValues.first()).not.toHaveText('0', { timeout: 30000 });
      
      const totalPhotos = await statsValues.nth(0).textContent();
      const duplicateClusters = await statsValues.nth(1).textContent();
      console.log(`📊 Library stats loaded: ${totalPhotos} photos, ${duplicateClusters} clusters`);
      
      await page.screenshot({ path: '/Users/urikogan/code/dedup/test-results/step1-interface-loaded.png', fullPage: true });

      // STEP 2: Apply filters systematically
      console.log('\n📍 STEP 2: Applying filters systematically...');
      
      // Apply year filter
      console.log('🗓️ Applying year filter...');
      const yearButtons = page.locator('.year-btn');
      const yearCount = await yearButtons.count();
      console.log(`Found ${yearCount} year filter buttons`);
      
      if (yearCount > 1) {
        // Click the second year button (skip "All Years")
        await yearButtons.nth(1).click();
        const selectedYear = await yearButtons.nth(1).textContent();
        console.log(`✅ Applied year filter: ${selectedYear}`);
        await page.waitForTimeout(1000);
      }
      
      // Apply file type filter
      console.log('📁 Applying file type filter...');
      const jpegButton = page.locator('.type-btn').filter({ hasText: 'JPG' });
      if (await jpegButton.count() > 0) {
        await jpegButton.click();
        console.log('✅ Applied JPG file type filter');
        await page.waitForTimeout(1000);
      }
      
      await page.screenshot({ path: '/Users/urikogan/code/dedup/test-results/step2-filters-applied.png', fullPage: true });

      // STEP 3: Click Apply Filters and wait for results
      console.log('\n📍 STEP 3: Applying filters and loading clusters...');
      const applyFiltersButton = page.locator('button').filter({ hasText: 'Apply Filters' });
      if (await applyFiltersButton.count() > 0) {
        console.log('🎯 Clicking Apply Filters button...');
        await applyFiltersButton.click();
        await page.waitForTimeout(3000); // Give time for filtering
      }
      
      // Wait for cluster loading
      console.log('⏳ Waiting for clusters to load...');
      try {
        await page.waitForSelector('.cluster-grid', { timeout: 20000 });
        console.log('✅ Cluster grid appeared');
      } catch (error) {
        console.log('⚠️ Cluster grid did not appear - checking for loading state');
      }
      
      // Check for cluster results
      const clusterCards = page.locator('.cluster-card');
      const clusterCount = await clusterCards.count();
      console.log(`📊 Found ${clusterCount} clusters in filtered results`);
      
      if (clusterCount === 0) {
        console.log('❌ CRITICAL ISSUE: No clusters found after filtering!');
        
        // Check for loading indicators
        const loadingIndicator = page.locator('.loading, .spinner, [data-loading="true"]');
        const isLoading = await loadingIndicator.count() > 0;
        console.log(`Loading state: ${isLoading ? 'Still loading' : 'Not loading'}`);
        
        // Check filter results section
        const filterResultsSection = page.locator('.filter-results, #filterResults');
        const resultsText = await filterResultsSection.textContent();
        console.log(`Filter results section: "${resultsText.substring(0, 100)}..."`);
        
        await page.screenshot({ path: '/Users/urikogan/code/dedup/test-results/step3-no-clusters-error.png', fullPage: true });
        
        // This is likely the core issue - no clusters loaded after filtering
        console.log('\n🚨 ROOT CAUSE IDENTIFIED: Filter operation not returning clusters');
        console.log('This will cause the "Analyze Selected" button to be invisible/disabled');
        return; // Stop here to focus on this issue
      }
      
      await page.screenshot({ path: '/Users/urikogan/code/dedup/test-results/step3-clusters-loaded.png', fullPage: true });

      // STEP 4: Verify Analyze Selected button visibility and functionality
      console.log('\n📍 STEP 4: Testing Analyze Selected button...');
      
      // Scroll down to find the Analyze Selected button
      await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
      await page.waitForTimeout(500);
      
      const analyzeButton = page.locator('button').filter({ hasText: 'Analyze Selected' });
      const analyzeButtonCount = await analyzeButton.count();
      console.log(`🔍 Found ${analyzeButtonCount} "Analyze Selected" button(s)`);
      
      if (analyzeButtonCount === 0) {
        console.log('❌ CRITICAL ISSUE: "Analyze Selected" button not found!');
        
        // Look for the button container/section
        const analyzeSection = page.locator('.analyze-section, #analyzeSection, [class*="analyze"]');
        const analyzeSectionCount = await analyzeSection.count();
        console.log(`Found ${analyzeSectionCount} analyze sections`);
        
        if (analyzeSectionCount > 0) {
          const sectionText = await analyzeSection.first().textContent();
          console.log(`Analyze section content: "${sectionText.substring(0, 100)}..."`);
        }
        
        await page.screenshot({ path: '/Users/urikogan/code/dedup/test-results/step4-no-analyze-button.png', fullPage: true });
        console.log('\n🚨 ROOT CAUSE: "Analyze Selected" button not visible - likely due to no clusters');
        return;
      }
      
      // Check button visibility and state
      const isVisible = await analyzeButton.isVisible();
      const isEnabled = await analyzeButton.isEnabled();
      console.log(`📍 Analyze button - Visible: ${isVisible}, Enabled: ${isEnabled}`);
      
      if (!isVisible) {
        console.log('❌ CRITICAL ISSUE: "Analyze Selected" button exists but is not visible!');
        
        // Get the button's computed styles to understand why it's hidden
        const buttonStyle = await analyzeButton.first().evaluate(el => {
          const styles = window.getComputedStyle(el);
          return {
            display: styles.display,
            visibility: styles.visibility,
            opacity: styles.opacity,
            height: styles.height,
            overflow: styles.overflow
          };
        });
        console.log(`Button styles: ${JSON.stringify(buttonStyle)}`);
        
        await page.screenshot({ path: '/Users/urikogan/code/dedup/test-results/step4-button-hidden.png', fullPage: true });
        return;
      }

      // STEP 5: Test the save filter session functionality
      console.log('\n📍 STEP 5: Testing save filter session...');
      
      // Monitor the save request
      const saveRequestPromise = page.waitForResponse(
        response => response.url().includes('/api/save-filter-session') && response.request().method() === 'POST',
        { timeout: 10000 }
      );
      
      console.log('🎯 Clicking "Analyze Selected" button...');
      await analyzeButton.click();
      
      try {
        const saveResponse = await saveRequestPromise;
        const saveStatus = saveResponse.status();
        console.log(`📡 Save filter session response: ${saveStatus}`);
        
        if (saveStatus === 200) {
          const saveData = await saveResponse.json();
          console.log(`✅ Filter session saved: ${JSON.stringify(saveData, null, 2)}`);
          
          // Check the session data structure
          if (saveData.session_id) {
            console.log(`📋 Session ID: ${saveData.session_id}`);
          }
          if (saveData.message) {
            console.log(`💬 Message: ${saveData.message}`);
          }
          
        } else {
          console.log(`❌ Save failed with status: ${saveStatus}`);
          const errorText = await saveResponse.text();
          console.log(`Error: ${errorText}`);
          
          await page.screenshot({ path: '/Users/urikogan/code/dedup/test-results/step5-save-failed.png', fullPage: true });
          return;
        }
      } catch (error) {
        console.log(`❌ Save request failed or timed out: ${error.message}`);
        await page.screenshot({ path: '/Users/urikogan/code/dedup/test-results/step5-save-timeout.png', fullPage: true });
        return;
      }
      
      // Wait for redirect
      console.log('⏳ Waiting for redirect to dashboard...');
      try {
        await page.waitForURL('**/dashboard**', { timeout: 10000 });
        console.log('✅ Successfully redirected to dashboard');
      } catch (error) {
        console.log(`❌ Redirect failed: ${error.message}`);
        const currentUrl = page.url();
        console.log(`Current URL: ${currentUrl}`);
        return;
      }

      // STEP 6: Test dashboard filtered mode detection
      console.log('\n📍 STEP 6: Testing dashboard filtered mode detection...');
      await page.waitForLoadState('networkidle');
      
      // Check for session data via API
      const sessionCheckResponse = await page.evaluate(async () => {
        try {
          const response = await fetch('/api/get-filter-session');
          const data = await response.json();
          return { status: response.status, data: data };
        } catch (error) {
          return { error: error.message };
        }
      });
      
      console.log(`📊 Session check result: ${JSON.stringify(sessionCheckResponse, null, 2)}`);
      
      if (sessionCheckResponse.status === 200 && sessionCheckResponse.data.has_session) {
        console.log('✅ Dashboard detected filter session');
        console.log(`📋 Session mode: ${sessionCheckResponse.data.mode}`);
        
        if (sessionCheckResponse.data.filter_session) {
          const filterSession = sessionCheckResponse.data.filter_session;
          console.log(`📊 Filter session data:`);
          console.log(`  - Total clusters: ${filterSession.total_clusters_in_filter}`);
          console.log(`  - Total photos: ${filterSession.total_photos_in_filter}`);
          console.log(`  - Session ID: ${filterSession.session_id}`);
        }
      } else {
        console.log('❌ Dashboard did not detect filter session');
      }
      
      await page.screenshot({ path: '/Users/urikogan/code/dedup/test-results/step6-dashboard-filtered.png', fullPage: true });

      // STEP 7: Test smart analysis in filtered mode
      console.log('\n📍 STEP 7: Testing smart analysis in filtered mode...');
      
      const smartAnalysisButton = page.locator('button').filter({ hasText: /Start Smart Analysis|Begin Analysis/ });
      const smartButtonCount = await smartAnalysisButton.count();
      console.log(`🔍 Found ${smartButtonCount} smart analysis button(s)`);
      
      if (smartButtonCount === 0) {
        console.log('❌ Smart analysis button not found');
        await page.screenshot({ path: '/Users/urikogan/code/dedup/test-results/step7-no-smart-button.png', fullPage: true });
        return;
      }
      
      // Monitor the smart analysis request
      const analysisRequestPromise = page.waitForResponse(
        response => response.url().includes('/api/smart-analysis') && response.request().method() === 'POST',
        { timeout: 30000 }
      );
      
      console.log('🎯 Clicking "Start Smart Analysis" button...');
      await smartAnalysisButton.first().click();
      
      try {
        const analysisResponse = await analysisRequestPromise;
        const analysisStatus = analysisResponse.status();
        console.log(`📡 Smart analysis response: ${analysisStatus}`);
        
        if (analysisStatus === 200) {
          const analysisData = await analysisResponse.json();
          console.log(`✅ Smart analysis succeeded`);
          
          // Check key response properties
          console.log(`📊 Analysis results:`);
          console.log(`  - Filtered mode: ${analysisData.filtered_mode}`);
          console.log(`  - Groups: ${analysisData.groups ? analysisData.groups.length : 'N/A'}`);
          console.log(`  - Clusters: ${analysisData.clusters ? analysisData.clusters.length : 'N/A'}`);
          console.log(`  - Success: ${analysisData.success}`);
          
          if (analysisData.error) {
            console.log(`❌ Analysis error: ${analysisData.error}`);
          }
          
        } else {
          console.log(`❌ Smart analysis failed with status: ${analysisStatus}`);
          const errorText = await analysisResponse.text();
          console.log(`Error response: ${errorText}`);
          
          await page.screenshot({ path: '/Users/urikogan/code/dedup/test-results/step7-analysis-failed.png', fullPage: true });
        }
        
      } catch (error) {
        console.log(`❌ Smart analysis request failed: ${error.message}`);
        await page.screenshot({ path: '/Users/urikogan/code/dedup/test-results/step7-analysis-timeout.png', fullPage: true });
      }
      
      // Final state screenshot
      await page.waitForTimeout(5000);
      await page.screenshot({ path: '/Users/urikogan/code/dedup/test-results/step7-final-state.png', fullPage: true });
      
    } catch (error) {
      console.log(`❌ Test failed with error: ${error.message}`);
      await page.screenshot({ path: '/Users/urikogan/code/dedup/test-results/test-error-state.png', fullPage: true });
      throw error;
    }
    
    // FINAL SUMMARY
    console.log('\n📊 DIAGNOSTIC SUMMARY');
    console.log('=' .repeat(50));
    console.log(`Total API requests: ${apiRequests.length}`);
    apiRequests.forEach((req, idx) => {
      console.log(`${idx + 1}. ${req.method} ${req.url}`);
    });
    
    if (consoleErrors.length > 0) {
      console.log(`\nConsole errors encountered: ${consoleErrors.length}`);
      consoleErrors.forEach((err, idx) => {
        console.log(`${idx + 1}. ${err}`);
      });
    } else {
      console.log('\nNo console errors detected');
    }
    
    console.log('\n🎯 Check test-results/ directory for detailed screenshots');
  });
});