const { chromium } = require('playwright');

async function checkAppVersion() {
  console.log('🚀 Starting RemoveBadPhotos Version Check');
  
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();

  // Enable console logging
  const consoleMessages = [];
  page.on('console', msg => {
    consoleMessages.push({
      type: msg.type(),
      text: msg.text()
    });
  });

  try {
    console.log('\n1. 🔍 Testing ROOT URL: http://127.0.0.1:5003');
    console.log('=' .repeat(50));
    
    await page.goto('http://127.0.0.1:5003', { 
      waitUntil: 'networkidle',
      timeout: 30000 
    });

    // Basic page information
    const title = await page.title();
    const url = page.url();
    
    console.log('📄 Page Title:', title);
    console.log('🔗 Current URL:', url);

    // Take screenshot
    await page.screenshot({ 
      path: '/Users/urikogan/code/removebadphotos/test-screenshots/root-page.png',
      fullPage: true 
    });

    // Get page content analysis
    const bodyText = await page.textContent('body');
    
    // Check for key indicators
    const indicators = {
      hasBlur: bodyText.toLowerCase().includes('blur'),
      hasDuplicate: bodyText.toLowerCase().includes('duplicate'),
      hasRemoveBadPhotos: bodyText.toLowerCase().includes('removebadphotos'),
      hasTidyLib: bodyText.toLowerCase().includes('tidylib'),
      hasFilter: bodyText.toLowerCase().includes('filter'),
      hasThreshold: bodyText.toLowerCase().includes('threshold')
    };

    console.log('\n📊 CONTENT ANALYSIS:');
    Object.entries(indicators).forEach(([key, value]) => {
      console.log(`  ${value ? '✅' : '❌'} ${key}: ${value}`);
    });

    // Check for specific UI elements
    const headerCount = await page.locator('h1, h2, h3').count();
    const buttonCount = await page.locator('button').count();
    const formCount = await page.locator('form').count();
    const imageCount = await page.locator('img').count();

    console.log('\n🧮 UI ELEMENTS COUNT:');
    console.log(`  Headers (h1-h3): ${headerCount}`);
    console.log(`  Buttons: ${buttonCount}`);
    console.log(`  Forms: ${formCount}`);
    console.log(`  Images: ${imageCount}`);

    // Get header texts
    const headers = await page.locator('h1, h2, h3').allTextContents();
    console.log('\n📝 HEADER TEXTS:');
    headers.forEach((header, i) => {
      console.log(`  ${i + 1}. "${header}"`);
    });

    console.log('\n2. 🔍 Testing /filters URL');
    console.log('=' .repeat(50));
    
    await page.goto('http://127.0.0.1:5003/filters', { 
      waitUntil: 'networkidle',
      timeout: 30000 
    });

    const filtersTitle = await page.title();
    const filtersBodyText = await page.textContent('body');
    
    console.log('📄 /filters Page Title:', filtersTitle);
    
    await page.screenshot({ 
      path: '/Users/urikogan/code/removebadphotos/test-screenshots/filters-page.png',
      fullPage: true 
    });

    const filtersIndicators = {
      hasBlur: filtersBodyText.toLowerCase().includes('blur'),
      hasDuplicate: filtersBodyText.toLowerCase().includes('duplicate'),
      hasRemoveBadPhotos: filtersBodyText.toLowerCase().includes('removebadphotos'),
      hasTidyLib: filtersBodyText.toLowerCase().includes('tidylib')
    };

    console.log('\n📊 /filters CONTENT ANALYSIS:');
    Object.entries(filtersIndicators).forEach(([key, value]) => {
      console.log(`  ${value ? '✅' : '❌'} ${key}: ${value}`);
    });

    // Console messages
    if (consoleMessages.length > 0) {
      console.log('\n🚨 CONSOLE MESSAGES:');
      consoleMessages.forEach(msg => {
        console.log(`  [${msg.type.toUpperCase()}] ${msg.text}`);
      });
    }

    console.log('\n🏁 VERSION CHECK COMPLETE');
    console.log('Screenshots saved to test-screenshots/ directory');

  } catch (error) {
    console.error('❌ Error during version check:', error.message);
    await page.screenshot({ 
      path: '/Users/urikogan/code/removebadphotos/test-screenshots/error.png',
      fullPage: true 
    });
  } finally {
    await browser.close();
  }
}

checkAppVersion().catch(console.error);