const { chromium } = require('playwright');

/**
 * Comprehensive E2E Test Suite for Smart Analysis Controls
 * Testing the photo deduplication application's dashboard functionality
 */
class SmartAnalysisE2ETester {
    constructor() {
        this.browser = null;
        this.page = null;
        this.testResults = {
            passed: 0,
            failed: 0,
            errors: [],
            warnings: [],
            findings: []
        };
        this.baseUrl = 'http://127.0.0.1:5003';
    }

    async setup() {
        console.log('🚀 Setting up browser for Smart Analysis E2E testing...');
        this.browser = await chromium.launch({ 
            headless: false, // Show browser for debugging
            slowMo: 500 // Slow down actions for observation
        });
        this.page = await this.browser.newPage();
        
        // Enable console logging and error capture
        this.page.on('console', msg => {
            const type = msg.type();
            const text = msg.text();
            console.log(`[BROWSER ${type.toUpperCase()}] ${text}`);
            
            if (type === 'error') {
                this.testResults.errors.push(`Console Error: ${text}`);
            }
        });
        
        this.page.on('pageerror', error => {
            console.log(`[PAGE ERROR] ${error.message}`);
            this.testResults.errors.push(`Page Error: ${error.message}`);
        });
        
        // Monitor network requests for API failures
        this.page.on('response', response => {
            const url = response.url();
            const status = response.status();
            
            if (status >= 400) {
                console.log(`[NETWORK ERROR] ${status} ${url}`);
                this.testResults.errors.push(`Network Error: ${status} ${url}`);
            }
        });
    }

    async teardown() {
        if (this.browser) {
            await this.browser.close();
        }
    }

    logTest(testName, passed, message = '') {
        const status = passed ? '✅ PASS' : '❌ FAIL';
        console.log(`${status} ${testName} ${message}`);
        
        if (passed) {
            this.testResults.passed++;
        } else {
            this.testResults.failed++;
            this.testResults.errors.push(`${testName}: ${message}`);
        }
    }

    logFinding(finding) {
        console.log(`🔍 FINDING: ${finding}`);
        this.testResults.findings.push(finding);
    }

    logWarning(warning) {
        console.log(`⚠️ WARNING: ${warning}`);
        this.testResults.warnings.push(warning);
    }

    async waitForSelector(selector, timeout = 10000) {
        try {
            await this.page.waitForSelector(selector, { timeout });
            return true;
        } catch (error) {
            this.logTest(`Selector Wait: ${selector}`, false, `Timeout after ${timeout}ms`);
            return false;
        }
    }

    async testDashboardLoading() {
        console.log('\n📊 Testing Dashboard Loading...');
        
        try {
            // Navigate to dashboard
            await this.page.goto(this.baseUrl, { waitUntil: 'networkidle' });
            this.logTest('Dashboard Navigation', true, 'Page loaded successfully');
            
            // Check if loading screen appears first
            const loadingVisible = await this.page.isVisible('#loading');
            this.logTest('Loading Screen Display', loadingVisible, 'Loading spinner should be visible initially');
            
            // Wait for dashboard content to appear (max 30 seconds for osxphotos)
            const dashboardVisible = await this.waitForSelector('#dashboard-content', 30000);
            this.logTest('Dashboard Content Loaded', dashboardVisible, 'Main dashboard content should appear');
            
            if (dashboardVisible) {
                // Check if loading screen is hidden
                const loadingHidden = !(await this.page.isVisible('#loading'));
                this.logTest('Loading Screen Hidden', loadingHidden, 'Loading screen should disappear');
                
                // Verify essential stats are populated
                const totalPhotos = await this.page.textContent('#total-photos');
                const librarySize = await this.page.textContent('#library-size');
                const estimatedDuplicates = await this.page.textContent('#estimated-duplicates');
                
                this.logTest('Total Photos Populated', totalPhotos !== '-', `Found: ${totalPhotos}`);
                this.logTest('Library Size Populated', librarySize !== '-', `Found: ${librarySize}`);
                this.logTest('Estimated Duplicates Populated', estimatedDuplicates !== '-', `Found: ${estimatedDuplicates}`);
                
                // Check for error messages
                const errorVisible = await this.page.isVisible('#error-message');
                this.logTest('No Error Messages', !errorVisible, 'Error message should not be visible');
            }
            
        } catch (error) {
            this.logTest('Dashboard Loading', false, `Exception: ${error.message}`);
        }
    }

    async testSmartAnalysisControls() {
        console.log('\n🎯 Testing Smart Analysis Controls...');
        
        try {
            // Check if Smart Analysis Controls section is visible
            const controlsVisible = await this.page.isVisible('.analysis-controls');
            this.logTest('Smart Analysis Controls Visible', controlsVisible, 'Controls section should be displayed');
            
            if (controlsVisible) {
                // Test size slider
                const sizeSlider = await this.page.isVisible('#size-slider');
                this.logTest('Size Slider Present', sizeSlider, 'Size filter slider should be visible');
                
                // Test analysis type buttons
                const fastBtn = await this.page.isVisible('button[data-type="metadata"]');
                const smartBtn = await this.page.isVisible('button[data-type="smart"]');
                this.logTest('Analysis Type Buttons Present', fastBtn && smartBtn, 'Both Fast and Smart buttons should be visible');
                
                // Test start analysis button
                const startBtn = await this.page.isVisible('#start-analysis');
                this.logTest('Start Analysis Button Present', startBtn, 'Start analysis button should be visible');
            }
            
        } catch (error) {
            this.logTest('Smart Analysis Controls', false, `Exception: ${error.message}`);
        }
    }

    async testSizeFilterFunctionality() {
        console.log('\n💾 Testing Size Filter Functionality...');
        
        try {
            // Get initial slider value
            const initialValue = await this.page.inputValue('#size-slider');
            this.logTest('Size Slider Initial Value', initialValue === '5', `Expected: 5, Got: ${initialValue}`);
            
            // Test slider movement
            await this.page.fill('#size-slider', '10');
            await this.page.waitForTimeout(1000); // Wait for preview update
            
            const updatedValue = await this.page.inputValue('#size-slider');
            const sizeValueText = await this.page.textContent('#size-value');
            
            this.logTest('Size Slider Value Update', updatedValue === '10', `Slider value: ${updatedValue}`);
            this.logTest('Size Value Display Update', sizeValueText === '10 MB', `Display: ${sizeValueText}`);
            
            // Check if filter preview updates
            const filterPreview = await this.page.textContent('#filter-preview');
            this.logTest('Filter Preview Updates', filterPreview.includes('≥10MB'), `Preview: ${filterPreview}`);
            
            // Test edge cases
            await this.page.fill('#size-slider', '0');
            await this.page.waitForTimeout(1000);
            const zeroValue = await this.page.textContent('#size-value');
            this.logTest('Zero MB Filter', zeroValue === '0 MB', `Zero filter: ${zeroValue}`);
            
            await this.page.fill('#size-slider', '20');
            await this.page.waitForTimeout(1000);
            const maxValue = await this.page.textContent('#size-value');
            this.logTest('Max MB Filter (20MB)', maxValue === '20 MB', `Max filter: ${maxValue}`);
            
            // Reset to middle value for further tests
            await this.page.fill('#size-slider', '5');
            await this.page.waitForTimeout(1000);
            
        } catch (error) {
            this.logTest('Size Filter Functionality', false, `Exception: ${error.message}`);
        }
    }

    async testAnalysisTypeToggle() {
        console.log('\n🔍 Testing Analysis Type Toggle...');
        
        try {
            // Click Fast (metadata) button
            await this.page.click('button[data-type="metadata"]');
            await this.page.waitForTimeout(500);
            
            const metadataSelected = await this.page.evaluate(() => {
                const btn = document.querySelector('button[data-type="metadata"]');
                return btn && btn.style.background === 'rgb(40, 167, 69)'; // #28a745
            });
            this.logTest('Fast Analysis Selection', metadataSelected, 'Fast button should be highlighted');
            
            const description = await this.page.textContent('#analysis-description');
            this.logTest('Fast Analysis Description', description.includes('Fast grouping'), `Description: ${description}`);
            
            // Click Smart button
            await this.page.click('button[data-type="smart"]');
            await this.page.waitForTimeout(500);
            
            const smartSelected = await this.page.evaluate(() => {
                const btn = document.querySelector('button[data-type="smart"]');
                return btn && btn.style.background === 'rgb(102, 126, 234)'; // #667eea
            });
            this.logTest('Smart Analysis Selection', smartSelected, 'Smart button should be highlighted');
            
            const smartDescription = await this.page.textContent('#analysis-description');
            this.logTest('Smart Analysis Description', smartDescription.includes('Smart grouping'), `Description: ${smartDescription}`);
            
        } catch (error) {
            this.logTest('Analysis Type Toggle', false, `Exception: ${error.message}`);
        }
    }

    async testSmartAnalysisExecution() {
        console.log('\n🚀 Testing Smart Analysis Execution...');
        
        try {
            // Ensure we're using Fast analysis for quicker test
            await this.page.click('button[data-type="metadata"]');
            await this.page.waitForTimeout(500);
            
            // Set a reasonable filter size (5MB)
            await this.page.fill('#size-slider', '5');
            await this.page.waitForTimeout(1000);
            
            // Monitor network requests specifically for the analysis API
            let analysisRequestMade = false;
            let analysisResponse = null;
            
            this.page.on('response', response => {
                if (response.url().includes('/api/smart-analysis')) {
                    analysisRequestMade = true;
                    analysisResponse = response;
                }
            });
            
            // Click Start Analysis button
            const startBtn = '#start-analysis';
            await this.page.click(startBtn);
            
            // Check button state changes to loading
            await this.page.waitForTimeout(500);
            const buttonText = await this.page.textContent(startBtn);
            this.logTest('Analysis Button Loading State', buttonText.includes('Analyzing'), `Button text: ${buttonText}`);
            
            // Wait for analysis to complete (up to 60 seconds for osxphotos)
            console.log('⏳ Waiting for analysis to complete...');
            
            let analysisCompleted = false;
            let attempts = 0;
            const maxAttempts = 120; // 2 minutes
            
            while (attempts < maxAttempts && !analysisCompleted) {
                await this.page.waitForTimeout(1000);
                attempts++;
                
                const currentButtonText = await this.page.textContent(startBtn);
                const priorityResultsVisible = await this.page.isVisible('#priority-results');
                const errorVisible = await this.page.isVisible('#error-message');
                
                if (priorityResultsVisible) {
                    analysisCompleted = true;
                    this.logTest('Analysis Completion', true, `Completed in ${attempts} seconds`);
                } else if (errorVisible) {
                    const errorText = await this.page.textContent('#error-message');
                    this.logTest('Analysis Completion', false, `Error: ${errorText}`);
                    
                    // Check for specific osxphotos timestamp error
                    if (errorText.includes('timestamp') || errorText.includes('PhotoInfo')) {
                        this.logFinding('OSXPHOTOS ATTRIBUTE ERROR: ' + errorText);
                    }
                    
                    break;
                } else if (!currentButtonText.includes('Analyzing')) {
                    // Button returned to normal state - check for silent failure
                    analysisCompleted = true;
                    this.logTest('Analysis Silent Return', false, 'Analysis returned without results or error');
                }
                
                // Log progress every 10 seconds
                if (attempts % 10 === 0) {
                    console.log(`⏳ Still waiting... ${attempts}s elapsed`);
                }
            }
            
            if (attempts >= maxAttempts) {
                this.logTest('Analysis Timeout', false, 'Analysis did not complete within 2 minutes');
            }
            
            // Check if network request was made
            this.logTest('Analysis API Request', analysisRequestMade, 'API request to /api/smart-analysis should be made');
            
            if (analysisResponse) {
                this.logTest('Analysis API Response Status', analysisResponse.status() < 400, `Status: ${analysisResponse.status()}`);
            }
            
        } catch (error) {
            this.logTest('Smart Analysis Execution', false, `Exception: ${error.message}`);
        }
    }

    async testPriorityResultsDisplay() {
        console.log('\n🎯 Testing Priority Results Display...');
        
        try {
            // Check if priority results section is visible
            const priorityVisible = await this.page.isVisible('#priority-results');
            
            if (priorityVisible) {
                this.logTest('Priority Results Visible', true, 'Priority results section is displayed');
                
                // Check for priority grid
                const gridVisible = await this.page.isVisible('#priority-grid');
                this.logTest('Priority Grid Present', gridVisible, 'Priority grid should be visible');
                
                if (gridVisible) {
                    // Check for P1-P10 buckets
                    const priorityLevels = ['P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8', 'P9', 'P10'];
                    let bucketsFound = 0;
                    
                    for (const priority of priorityLevels) {
                        const bucketExists = await this.page.isVisible(`[data-priority="${priority}"]`);
                        if (bucketExists) {
                            bucketsFound++;
                            
                            // Check bucket content
                            const bucketStats = await this.page.textContent(`[data-priority="${priority}"] .priority-stats`);
                            this.logTest(`${priority} Bucket Content`, bucketStats.length > 0, `Stats: ${bucketStats.substring(0, 50)}...`);
                            
                            // Check if analyze button is present and enabled/disabled appropriately
                            const analyzeBtn = await this.page.isVisible(`[data-priority="${priority}"] .analyze-btn`);
                            this.logTest(`${priority} Analyze Button`, analyzeBtn, 'Analyze button should be present');
                        }
                    }
                    
                    this.logTest('Priority Buckets Count', bucketsFound === 10, `Found ${bucketsFound} out of 10 priority buckets`);
                }
            } else {
                this.logTest('Priority Results Visible', false, 'Priority results not displayed - analysis may have failed');
            }
            
        } catch (error) {
            this.logTest('Priority Results Display', false, `Exception: ${error.message}`);
        }
    }

    async testErrorHandlingAndEdgeCases() {
        console.log('\n⚠️ Testing Error Handling and Edge Cases...');
        
        try {
            // Test invalid API endpoints
            await this.page.goto(`${this.baseUrl}/api/invalid-endpoint`);
            const response404 = this.page.url().includes('invalid-endpoint');
            this.logTest('Invalid API Endpoint', response404, 'Should handle invalid endpoints gracefully');
            
            // Go back to main dashboard
            await this.page.goto(this.baseUrl);
            await this.page.waitForSelector('#dashboard-content', { timeout: 10000 });
            
            // Test extreme filter values
            await this.page.fill('#size-slider', '0');
            await this.page.waitForTimeout(1000);
            const zeroFilterPreview = await this.page.textContent('#filter-preview');
            this.logTest('Zero MB Filter Handling', zeroFilterPreview.includes('≥0MB'), `Preview: ${zeroFilterPreview}`);
            
            await this.page.fill('#size-slider', '20');
            await this.page.waitForTimeout(1000);
            const maxFilterPreview = await this.page.textContent('#filter-preview');
            this.logTest('Max MB Filter Handling', maxFilterPreview.includes('≥20MB'), `Preview: ${maxFilterPreview}`);
            
        } catch (error) {
            this.logTest('Error Handling', false, `Exception: ${error.message}`);
        }
    }

    async runFullTestSuite() {
        console.log('🔍 Starting Comprehensive Smart Analysis E2E Test Suite');
        console.log('==================================================');
        
        try {
            await this.setup();
            
            // Run all test modules
            await this.testDashboardLoading();
            await this.testSmartAnalysisControls();
            await this.testSizeFilterFunctionality();
            await this.testAnalysisTypeToggle();
            await this.testSmartAnalysisExecution();
            await this.testPriorityResultsDisplay();
            await this.testErrorHandlingAndEdgeCases();
            
        } catch (error) {
            console.log(`❌ Test suite failed with error: ${error.message}`);
            this.testResults.errors.push(`Test Suite Error: ${error.message}`);
        } finally {
            await this.teardown();
            this.generateTestReport();
        }
    }

    generateTestReport() {
        console.log('\n📋 COMPREHENSIVE TEST REPORT');
        console.log('============================');
        console.log(`✅ Tests Passed: ${this.testResults.passed}`);
        console.log(`❌ Tests Failed: ${this.testResults.failed}`);
        console.log(`🔍 Findings: ${this.testResults.findings.length}`);
        console.log(`⚠️ Warnings: ${this.testResults.warnings.length}`);
        console.log(`🚨 Errors: ${this.testResults.errors.length}`);
        
        if (this.testResults.errors.length > 0) {
            console.log('\n🚨 ERRORS FOUND:');
            this.testResults.errors.forEach((error, index) => {
                console.log(`${index + 1}. ${error}`);
            });
        }
        
        if (this.testResults.findings.length > 0) {
            console.log('\n🔍 KEY FINDINGS:');
            this.testResults.findings.forEach((finding, index) => {
                console.log(`${index + 1}. ${finding}`);
            });
        }
        
        if (this.testResults.warnings.length > 0) {
            console.log('\n⚠️ WARNINGS:');
            this.testResults.warnings.forEach((warning, index) => {
                console.log(`${index + 1}. ${warning}`);
            });
        }
        
        const successRate = ((this.testResults.passed / (this.testResults.passed + this.testResults.failed)) * 100).toFixed(1);
        console.log(`\n📊 Overall Success Rate: ${successRate}%`);
        
        if (this.testResults.failed === 0 && this.testResults.errors.length === 0) {
            console.log('🎉 ALL TESTS PASSED! Smart Analysis Controls are working correctly.');
        } else {
            console.log('❌ Issues found in Smart Analysis Controls. Review errors and findings above.');
        }
    }
}

// Run the test suite
const tester = new SmartAnalysisE2ETester();
tester.runFullTestSuite().catch(console.error);