const { test, expect } = require('@playwright/test');

/**
 * Simplified Debug Test for Streamlined Workflow Issues
 * Identifies why the main tests are failing
 */

const BASE_URL = 'http://127.0.0.1:5003';

test.describe('Streamlined Workflow Debug', () => {
  
  test('Debug: Page Structure Analysis', async ({ page }) => {
    console.log('\n🔍 Analyzing page structure and available elements...');
    
    // Load /filters page
    await page.goto(`${BASE_URL}/filters`);
    await page.waitForLoadState('networkidle');
    
    console.log('✅ /filters page loaded');
    
    // Take screenshot for manual inspection
    await page.screenshot({ 
      path: 'debug_filters_page.png', 
      fullPage: true 
    });
    
    // Check page title
    const title = await page.title();
    console.log(`Page title: ${title}`);
    
    // Find all buttons on the page
    const allButtons = await page.locator('button').all();
    console.log(`Found ${allButtons.length} buttons on page:`);
    
    for (let i = 0; i < allButtons.length; i++) {
      const button = allButtons[i];
      const text = await button.textContent();
      const id = await button.getAttribute('id');
      const classes = await button.getAttribute('class');
      console.log(`  Button ${i+1}: text="${text}", id="${id}", classes="${classes}"`);
    }
    
    // Check for analyze-related buttons with various selectors
    const analyzeSelectors = [
      'button:has-text("Analyze")',
      'button:has-text("Duplicates")', 
      '#analyzeButton',
      '.analyze-button',
      'button[onclick*="analyze"]',
      'input[type="submit"]',
      'input[type="button"]'
    ];
    
    for (const selector of analyzeSelectors) {
      const elements = await page.locator(selector).all();
      if (elements.length > 0) {
        console.log(`✅ Found ${elements.length} elements with selector: ${selector}`);
        for (let i = 0; i < elements.length; i++) {
          const text = await elements[i].textContent();
          console.log(`  Element ${i+1}: "${text}"`);
        }
      } else {
        console.log(`❌ No elements found with selector: ${selector}`);
      }
    }
    
    // Check for form elements
    const forms = await page.locator('form').all();
    console.log(`Found ${forms.length} forms on page`);
    
    // Check for any JavaScript errors
    const consoleLogs = [];
    page.on('console', msg => {
      consoleLogs.push(`${msg.type()}: ${msg.text()}`);
    });
    
    // Wait a bit to catch any delayed JS
    await page.waitForTimeout(2000);
    
    if (consoleLogs.length > 0) {
      console.log('\n📝 Console messages:');
      consoleLogs.forEach(log => console.log(`  ${log}`));
    }
    
    console.log('\n✅ Page structure analysis complete');
  });

  test('Debug: API Endpoints Status', async ({ page }) => {
    console.log('\n🔍 Testing API endpoint availability...');
    
    const endpoints = [
      { path: '/api/library-stats', method: 'GET' },
      { path: '/api/filter-distributions', method: 'GET' },
      { path: '/api/filter-clusters?preview=true', method: 'GET' },
      { path: '/api/analyze-duplicates', method: 'POST' },
      { path: '/api/load-more-duplicates', method: 'GET' }
    ];
    
    for (const endpoint of endpoints) {
      try {
        let response;
        if (endpoint.method === 'GET') {
          response = await page.request.get(`${BASE_URL}${endpoint.path}`);
        } else if (endpoint.method === 'POST') {
          response = await page.request.post(`${BASE_URL}${endpoint.path}`, {
            data: { filters: {} }
          });
        }
        
        const status = response.status();
        const statusText = response.statusText();
        
        if (status >= 200 && status < 300) {
          console.log(`✅ ${endpoint.method} ${endpoint.path}: ${status} ${statusText}`);
        } else if (status >= 400) {
          console.log(`❌ ${endpoint.method} ${endpoint.path}: ${status} ${statusText}`);
        } else {
          console.log(`⚠️ ${endpoint.method} ${endpoint.path}: ${status} ${statusText}`);
        }
        
        // Try to get response body for error analysis
        if (status >= 400) {
          try {
            const body = await response.text();
            console.log(`   Response body: ${body.slice(0, 200)}...`);
          } catch (e) {
            console.log(`   Could not read response body: ${e.message}`);
          }
        }
        
      } catch (error) {
        console.log(`❌ ${endpoint.method} ${endpoint.path}: Network error - ${error.message}`);
      }
    }
  });

  test('Debug: Manual Button Click Test', async ({ page }) => {
    console.log('\n🔍 Manual button click test...');
    
    await page.goto(`${BASE_URL}/filters`);
    await page.waitForLoadState('networkidle');
    
    // Try to find and click any button that might be the analyze button
    const potentialButtons = [
      'button:has-text("Analyze")',
      'button:has-text("Start")',
      'button:has-text("Begin")', 
      'button:has-text("Process")',
      'button[type="submit"]',
      'input[type="submit"]'
    ];
    
    let buttonFound = false;
    
    for (const selector of potentialButtons) {
      const button = page.locator(selector).first();
      if (await button.isVisible()) {
        console.log(`✅ Found clickable button: ${selector}`);
        const text = await button.textContent();
        console.log(`   Button text: "${text}"`);
        
        try {
          await button.click();
          console.log(`✅ Successfully clicked button`);
          buttonFound = true;
          
          // Wait to see what happens
          await page.waitForTimeout(3000);
          
          const currentURL = page.url();
          console.log(`   Current URL after click: ${currentURL}`);
          
          break;
        } catch (error) {
          console.log(`❌ Failed to click button: ${error.message}`);
        }
      }
    }
    
    if (!buttonFound) {
      console.log('❌ No clickable analyze button found');
      
      // Check if there's any form to submit
      const forms = await page.locator('form').all();
      if (forms.length > 0) {
        console.log(`⚠️ Found ${forms.length} forms - might need form submission instead`);
        try {
          await forms[0].press('Enter');
          console.log('✅ Attempted form submission with Enter key');
          await page.waitForTimeout(3000);
          console.log(`   Current URL after form submit: ${page.url()}`);
        } catch (error) {
          console.log(`❌ Form submission failed: ${error.message}`);
        }
      }
    }
  });

  test('Debug: Check Duplicates Page Direct Access', async ({ page }) => {
    console.log('\n🔍 Testing direct access to /duplicates page...');
    
    await page.goto(`${BASE_URL}/duplicates`);
    await page.waitForLoadState('networkidle');
    
    const title = await page.title();
    console.log(`Duplicates page title: ${title}`);
    
    // Take screenshot
    await page.screenshot({ 
      path: 'debug_duplicates_page.png', 
      fullPage: true 
    });
    
    // Check for duplicate groups or content
    const duplicateGroups = await page.locator('.duplicate-group, .group, .photo-group').all();
    console.log(`Found ${duplicateGroups.length} potential duplicate groups`);
    
    // Check for photos/thumbnails
    const photos = await page.locator('img, .photo, .thumbnail').all();
    console.log(`Found ${photos.length} potential photo elements`);
    
    // Check for "Load More" button
    const loadMoreButtons = await page.locator('button:has-text("Load More"), button:has-text("Show More"), #loadMoreButton').all();
    console.log(`Found ${loadMoreButtons.length} potential "Load More" buttons`);
    
    // Check for any error messages
    const errorMessages = await page.locator('.error, .alert-error, [class*="error"]').all();
    if (errorMessages.length > 0) {
      console.log(`⚠️ Found ${errorMessages.length} error messages on duplicates page`);
      for (let i = 0; i < errorMessages.length; i++) {
        const text = await errorMessages[i].textContent();
        console.log(`   Error ${i+1}: "${text}"`);
      }
    }
    
    console.log('✅ Duplicates page analysis complete');
  });

});