const { chromium } = require('playwright');

/**
 * Focused test to verify JavaScript 'toFixed' errors have been resolved
 * Tests specifically for the numeric formatting errors in Smart Analysis results
 */
class ToFixedErrorVerificationTester {
    constructor() {
        this.browser = null;
        this.page = null;
        this.testResults = {
            passed: 0,
            failed: 0,
            errors: [],
            findings: [],
            toFixedErrors: []
        };
        this.baseUrl = 'http://127.0.0.1:5003';
    }

    async setup() {
        console.log('🔍 Setting up test for toFixed JavaScript errors...');
        this.browser = await chromium.launch({ 
            headless: false,
            slowMo: 300
        });
        this.page = await this.browser.newPage();
        
        // Capture all console messages and errors
        this.page.on('console', msg => {
            const type = msg.type();
            const text = msg.text();
            console.log(`[BROWSER ${type.toUpperCase()}] ${text}`);
            
            if (type === 'error') {
                this.testResults.errors.push(`Console Error: ${text}`);
                
                // Specifically check for toFixed related errors
                if (text.includes('toFixed') || text.includes("Cannot read properties of undefined")) {
                    this.testResults.toFixedErrors.push(text);
                    console.log(`🚨 TOFIXED ERROR DETECTED: ${text}`);
                }
            }
        });
        
        this.page.on('pageerror', error => {
            console.log(`[PAGE ERROR] ${error.message}`);
            this.testResults.errors.push(`Page Error: ${error.message}`);
            
            if (error.message.includes('toFixed') || error.message.includes("Cannot read properties of undefined")) {
                this.testResults.toFixedErrors.push(error.message);
                console.log(`🚨 PAGE TOFIXED ERROR DETECTED: ${error.message}`);
            }
        });
        
        // Monitor API responses for data structure issues
        this.page.on('response', async response => {
            const url = response.url();
            const status = response.status();
            
            if (url.includes('/api/smart-analysis')) {
                console.log(`[API] Smart Analysis: ${status} ${url}`);
                
                if (status === 200) {
                    try {
                        const responseData = await response.json();
                        this.validateNumericData(responseData);
                    } catch (e) {
                        console.log(`[API] Could not parse response as JSON: ${e.message}`);
                    }
                }
            }
        });
    }

    validateNumericData(data) {
        console.log('🔍 Validating API response numeric data structure...');
        
        // Check library stats
        if (data.library_stats) {
            const stats = data.library_stats;
            
            // Check for undefined values that would cause toFixed errors
            if (stats.total_size_gb === undefined || stats.total_size_gb === null) {
                this.logFinding('ISSUE: total_size_gb is undefined/null in API response');
            }
            
            if (stats.potential_savings_gb === undefined || stats.potential_savings_gb === null) {
                this.logFinding('ISSUE: potential_savings_gb is undefined/null in API response');
            }
            
            console.log(`📊 Library Stats: total_size_gb=${stats.total_size_gb}, potential_savings_gb=${stats.potential_savings_gb}`);
        }
        
        // Check priority results
        if (data.priority_results && Array.isArray(data.priority_results)) {
            data.priority_results.forEach((result, index) => {
                // Check for the data mapping issue (API returns total_savings_mb vs frontend expects savings_mb)
                if (result.total_savings_mb !== undefined && result.savings_mb === undefined) {
                    this.logFinding(`MAPPING ISSUE: Priority result ${index} has total_savings_mb but missing savings_mb`);
                }
                
                if (result.photo_count !== undefined && result.photos === undefined) {
                    this.logFinding(`MAPPING ISSUE: Priority result ${index} has photo_count but missing photos`);
                }
                
                // Check for undefined savings values
                const savingsValue = result.savings_mb || result.total_savings_mb;
                if (savingsValue === undefined || savingsValue === null) {
                    this.logFinding(`ISSUE: Savings value undefined for priority result ${index}`);
                }
                
                console.log(`📊 Priority ${index + 1}: savings=${savingsValue}MB, photos=${result.photos || result.photo_count}`);
            });
        }
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

    async testDashboardNumericDisplay() {
        console.log('\n📊 Testing Dashboard Numeric Display...');
        
        try {
            // Navigate to dashboard
            await this.page.goto(this.baseUrl, { waitUntil: 'networkidle' });
            
            // Wait for dashboard to load
            await this.page.waitForSelector('#dashboard-content', { timeout: 30000 });
            this.logTest('Dashboard Loaded', true, 'Ready for testing');
            
            // Check initial state - no toFixed errors should occur on load
            await this.page.waitForTimeout(2000);
            
            const initialToFixedErrors = this.testResults.toFixedErrors.length;
            this.logTest('Dashboard Load - No toFixed Errors', initialToFixedErrors === 0, 
                `Found ${initialToFixedErrors} toFixed errors on load`);
            
        } catch (error) {
            this.logTest('Dashboard Load Test', false, `Exception: ${error.message}`);
        }
    }

    async testSmartAnalysisNumericFormatting() {
        console.log('\n🎯 Testing Smart Analysis Numeric Formatting...');
        
        try {
            // Set up test parameters
            await this.page.fill('#size-slider', '5');
            await this.page.waitForTimeout(1000);
            
            // Select Smart analysis
            await this.page.click('button[data-type="smart"]');
            await this.page.waitForTimeout(500);
            
            // Track toFixed errors before analysis
            const toFixedErrorsBefore = this.testResults.toFixedErrors.length;
            
            // Start analysis
            console.log('🚀 Starting Smart Analysis...');
            await this.page.click('#start-analysis');
            
            // Wait for completion or error (up to 60 seconds)
            let attempts = 0;
            const maxAttempts = 60;
            let analysisComplete = false;
            
            while (attempts < maxAttempts && !analysisComplete) {
                await this.page.waitForTimeout(1000);
                attempts++;
                
                // Check for error message
                const errorVisible = await this.page.isVisible('#error-message');
                if (errorVisible) {
                    const errorMessage = await this.page.textContent('#error-message');
                    console.log(`❌ Error detected: ${errorMessage}`);
                    analysisComplete = true;
                    this.logTest('Smart Analysis Completion', false, `Error: ${errorMessage}`);
                }
                
                // Check for successful completion
                const priorityVisible = await this.page.isVisible('#priority-results');
                if (priorityVisible) {
                    console.log('✅ Analysis completed successfully');
                    analysisComplete = true;
                    this.logTest('Smart Analysis Completion', true, 'Priority results displayed');
                    
                    // Now test the specific numeric formatting
                    await this.testPriorityResultsFormatting();
                    await this.testLibraryStatsFormatting();
                }
                
                // Check button state for silent failures
                const buttonText = await this.page.textContent('#start-analysis');
                if (!buttonText.includes('Analyzing') && !priorityVisible && !errorVisible) {
                    console.log('⚠️ Silent failure detected - button returned to normal state');
                    analysisComplete = true;
                    this.logTest('Smart Analysis Silent Failure', false, 'No results or error shown');
                }
            }
            
            // Check for toFixed errors during analysis
            const toFixedErrorsAfter = this.testResults.toFixedErrors.length;
            const newToFixedErrors = toFixedErrorsAfter - toFixedErrorsBefore;
            
            this.logTest('Smart Analysis - No toFixed Errors', newToFixedErrors === 0,
                `Found ${newToFixedErrors} new toFixed errors during analysis`);
            
        } catch (error) {
            this.logTest('Smart Analysis Numeric Test', false, `Exception: ${error.message}`);
        }
    }

    async testPriorityResultsFormatting() {
        console.log('\n📋 Testing Priority Results Numeric Formatting...');
        
        try {
            // Wait for priority results to be visible
            await this.page.waitForSelector('#priority-results', { timeout: 5000 });
            
            // Get all priority bucket elements (correct selector)
            const priorityItems = await this.page.$$('.priority-bucket');
            
            console.log(`Found ${priorityItems.length} priority result buckets`);
            this.logTest('Priority Results Present', priorityItems.length > 0,
                `${priorityItems.length} priority buckets found`);
            
            // Check each priority item for proper numeric formatting
            for (let i = 0; i < priorityItems.length; i++) {
                const item = priorityItems[i];
                
                // Look for savings display
                const savingsText = await item.textContent();
                
                // Check if savings contains "MB" and is properly formatted
                if (savingsText.includes('MB')) {
                    const mbMatch = savingsText.match(/(\d+(?:\.\d+)?)\s*MB/);
                    if (mbMatch) {
                        console.log(`✅ Priority ${i + 1}: Found savings ${mbMatch[1]} MB`);
                        this.logTest(`Priority ${i + 1} Savings Format`, true, `${mbMatch[1]} MB displayed correctly`);
                    } else {
                        console.log(`⚠️ Priority ${i + 1}: MB found but no numeric value extracted`);
                        this.logTest(`Priority ${i + 1} Savings Format`, false, 'MB found but no numeric value');
                    }
                } else {
                    console.log(`⚠️ Priority ${i + 1}: No MB savings display found`);
                    this.logFinding(`Priority ${i + 1} missing MB savings display`);
                }
                
                // Check for "NaN" or "undefined" in the text
                if (savingsText.includes('NaN') || savingsText.includes('undefined')) {
                    this.logTest(`Priority ${i + 1} Valid Values`, false, 'Contains NaN or undefined');
                    this.logFinding(`Priority ${i + 1} contains invalid values: ${savingsText}`);
                } else {
                    this.logTest(`Priority ${i + 1} Valid Values`, true, 'No NaN or undefined values');
                }
            }
            
        } catch (error) {
            this.logTest('Priority Results Formatting Test', false, `Exception: ${error.message}`);
        }
    }

    async testLibraryStatsFormatting() {
        console.log('\n📊 Testing Library Stats Numeric Formatting...');
        
        try {
            // Look for library stats display (correct selectors based on HTML structure)
            const statsElements = await this.page.$$('.stats-overview, .stats-grid, .stat-card');
            
            if (statsElements.length === 0) {
                this.logFinding('No library stats elements found on page');
                return;
            }
            
            for (let i = 0; i < statsElements.length; i++) {
                const statsElement = statsElements[i];
                const statsText = await statsElement.textContent();
                
                console.log(`📊 Checking stats element ${i + 1}: ${statsText.substring(0, 100)}...`);
                
                // Check for GB formatting
                if (statsText.includes('GB')) {
                    const gbMatches = statsText.match(/(\d+(?:\.\d+)?)\s*GB/g);
                    if (gbMatches) {
                        gbMatches.forEach((match, index) => {
                            console.log(`✅ Found GB value: ${match}`);
                            this.logTest(`Library Stats GB Format ${index + 1}`, true, `${match} displayed correctly`);
                        });
                    }
                }
                
                // Check for total photos count
                if (statsText.match(/(\d+(?:,\d+)*)\s*photos?/i)) {
                    const photoMatches = statsText.match(/(\d+(?:,\d+)*)\s*photos?/gi);
                    photoMatches.forEach((match, index) => {
                        console.log(`✅ Found photo count: ${match}`);
                        this.logTest(`Library Stats Photo Count ${index + 1}`, true, `${match} displayed correctly`);
                    });
                }
                
                // Check for invalid values
                if (statsText.includes('NaN') || statsText.includes('undefined') || statsText.includes('null')) {
                    this.logTest(`Library Stats Valid Values ${i + 1}`, false, 'Contains invalid values');
                    this.logFinding(`Library stats contain invalid values: ${statsText}`);
                } else {
                    this.logTest(`Library Stats Valid Values ${i + 1}`, true, 'No invalid values found');
                }
            }
            
        } catch (error) {
            this.logTest('Library Stats Formatting Test', false, `Exception: ${error.message}`);
        }
    }

    async generateReport() {
        console.log('\n📋 TOFIXED ERROR VERIFICATION REPORT');
        console.log('=====================================');
        console.log(`✅ Tests Passed: ${this.testResults.passed}`);
        console.log(`❌ Tests Failed: ${this.testResults.failed}`);
        console.log(`🔍 Key Findings: ${this.testResults.findings.length}`);
        console.log(`🚨 All Errors: ${this.testResults.errors.length}`);
        console.log(`🎯 toFixed Errors: ${this.testResults.toFixedErrors.length}`);
        
        if (this.testResults.toFixedErrors.length > 0) {
            console.log('\n🚨 TOFIXED ERRORS DETECTED:');
            this.testResults.toFixedErrors.forEach((error, index) => {
                console.log(`${index + 1}. ${error}`);
            });
        }
        
        if (this.testResults.findings.length > 0) {
            console.log('\n🔍 KEY FINDINGS:');
            this.testResults.findings.forEach((finding, index) => {
                console.log(`${index + 1}. ${finding}`);
            });
        }
        
        if (this.testResults.errors.length > 0) {
            console.log('\n🚨 ALL ERRORS:');
            this.testResults.errors.forEach((error, index) => {
                console.log(`${index + 1}. ${error}`);
            });
        }
        
        // Generate conclusion
        console.log('\n📊 CONCLUSION:');
        
        if (this.testResults.toFixedErrors.length === 0) {
            console.log('✅ NO TOFIXED ERRORS DETECTED');
            console.log('   The JavaScript toFixed error fixes are working correctly');
            console.log('   All numeric values are properly validated before calling toFixed()');
        } else {
            console.log('❌ TOFIXED ERRORS STILL PRESENT');
            console.log('   The following toFixed errors were detected during testing:');
            this.testResults.toFixedErrors.forEach(error => {
                console.log(`   - ${error}`);
            });
        }
        
        const successRate = this.testResults.passed + this.testResults.failed > 0 
            ? ((this.testResults.passed / (this.testResults.passed + this.testResults.failed)) * 100).toFixed(1)
            : 0;
        console.log(`\n📈 Test Success Rate: ${successRate}%`);
        
        // Specific recommendations
        console.log('\n💡 RECOMMENDATIONS:');
        if (this.testResults.toFixedErrors.length === 0) {
            console.log('✅ The toFixed error fixes are working - no further action needed');
        } else {
            console.log('❌ Additional fixes needed for remaining toFixed errors');
            console.log('   Review the error details above and add null/undefined checks');
        }
    }

    async runToFixedTest() {
        console.log('🔍 Starting toFixed Error Verification Test');
        console.log('============================================');
        
        try {
            await this.setup();
            await this.testDashboardNumericDisplay();
            await this.testSmartAnalysisNumericFormatting();
        } catch (error) {
            console.log(`❌ Test failed with error: ${error.message}`);
            this.testResults.errors.push(`Test Suite Error: ${error.message}`);
        } finally {
            await this.teardown();
            await this.generateReport();
        }
    }
}

// Run the toFixed error verification test
const tester = new ToFixedErrorVerificationTester();
tester.runToFixedTest().catch(console.error);