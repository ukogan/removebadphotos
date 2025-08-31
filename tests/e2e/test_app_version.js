const { test, expect } = require('@playwright/test');

test.describe('RemoveBadPhotos App Version Verification', () => {
  test('Verify what version is being served at root URL', async ({ page }) => {
    // Enable console logging
    const consoleMessages = [];
    page.on('console', msg => {
      consoleMessages.push({
        type: msg.type(),
        text: msg.text(),
        location: msg.location()
      });
    });

    // Enable network monitoring
    const networkRequests = [];
    page.on('request', request => {
      networkRequests.push({
        url: request.url(),
        method: request.method()
      });
    });

    console.log('🔍 Testing root URL: http://127.0.0.1:5003');
    
    try {
      // Navigate to the root URL
      await page.goto('http://127.0.0.1:5003', { 
        waitUntil: 'networkidle',
        timeout: 30000 
      });

      // Take a screenshot of the initial state
      await page.screenshot({ 
        path: '/Users/urikogan/code/removebadphotos/test-screenshots/root-page-initial.png',
        fullPage: true 
      });

      // Get basic page information
      const title = await page.title();
      const url = page.url();
      
      console.log('📄 Page Title:', title);
      console.log('🔗 Current URL:', url);

      // Check for key indicators of different interfaces
      const pageText = await page.textContent('body');
      const hasBlurDetection = pageText.includes('blur') || pageText.includes('Blur');
      const hasDuplicateDetection = pageText.includes('duplicate') || pageText.includes('Duplicate');
      const hasRemoveBadPhotos = pageText.includes('removebadphotos') || pageText.includes('RemoveBadPhotos');
      const hasTidyLib = pageText.includes('tidylib') || pageText.includes('TidyLib');

      console.log('🔍 Content Analysis:');
      console.log('  - Has Blur Detection references:', hasBlurDetection);
      console.log('  - Has Duplicate Detection references:', hasDuplicateDetection);
      console.log('  - Has RemoveBadPhotos branding:', hasRemoveBadPhotos);
      console.log('  - Has TidyLib branding:', hasTidyLib);

      // Check for specific UI elements
      const headerElements = await page.locator('h1, h2, h3').allTextContents();
      const buttonElements = await page.locator('button').allTextContents();
      
      console.log('📝 Header Elements:', headerElements);
      console.log('🔘 Button Elements:', buttonElements);

      // Check for filter controls
      const hasFilterControls = await page.locator('input[type="range"], .slider, .filter-control').count() > 0;
      const hasThresholdControls = await page.locator('*').filter({ hasText: /threshold/i }).count() > 0;
      
      console.log('⚙️  Has Filter Controls:', hasFilterControls);
      console.log('📊 Has Threshold Controls:', hasThresholdControls);

      // Check for photo grid or similar photo display
      const hasPhotoGrid = await page.locator('.photo-grid, .image-grid, .gallery, img').count() > 0;
      console.log('🖼️  Has Photo Display:', hasPhotoGrid);

      // Output console messages if any
      if (consoleMessages.length > 0) {
        console.log('🚨 Console Messages:');
        consoleMessages.forEach(msg => {
          console.log(`  [${msg.type.toUpperCase()}] ${msg.text}`);
        });
      }

      // Check specific network requests
      const htmlRequest = networkRequests.find(req => req.url === 'http://127.0.0.1:5003/');
      console.log('🌐 HTML Request found:', !!htmlRequest);

    } catch (error) {
      console.error('❌ Error testing root URL:', error.message);
      
      // Take error screenshot
      await page.screenshot({ 
        path: '/Users/urikogan/code/removebadphotos/test-screenshots/root-page-error.png',
        fullPage: true 
      });
      
      throw error;
    }
  });

  test('Verify /filters endpoint', async ({ page }) => {
    console.log('🔍 Testing /filters URL: http://127.0.0.1:5003/filters');
    
    try {
      await page.goto('http://127.0.0.1:5003/filters', { 
        waitUntil: 'networkidle',
        timeout: 30000 
      });

      // Take a screenshot
      await page.screenshot({ 
        path: '/Users/urikogan/code/removebadphotos/test-screenshots/filters-page.png',
        fullPage: true 
      });

      const title = await page.title();
      const pageText = await page.textContent('body');
      
      console.log('📄 /filters Page Title:', title);
      console.log('🔍 Page contains "blur":', pageText.includes('blur'));
      console.log('🔍 Page contains "duplicate":', pageText.includes('duplicate'));
      console.log('🔍 Page contains "removebadphotos":', pageText.includes('removebadphotos'));
      
    } catch (error) {
      console.error('❌ Error testing /filters URL:', error.message);
      await page.screenshot({ 
        path: '/Users/urikogan/code/removebadphotos/test-screenshots/filters-page-error.png',
        fullPage: true 
      });
    }
  });

  test('Test keyboard shortcut functionality', async ({ page }) => {
    console.log('⌨️  Testing keyboard shortcuts');
    
    try {
      await page.goto('http://127.0.0.1:5003', { waitUntil: 'networkidle' });
      
      // Wait for page to be ready
      await page.waitForTimeout(2000);
      
      // Try pressing 'd' key
      await page.keyboard.press('d');
      
      // Take screenshot after keypress
      await page.screenshot({ 
        path: '/Users/urikogan/code/removebadphotos/test-screenshots/after-d-keypress.png',
        fullPage: true 
      });
      
      console.log('SUCCESS: d key pressed successfully');
      
    } catch (error) {
      console.error('❌ Error testing keyboard shortcuts:', error.message);
    }
  });
});