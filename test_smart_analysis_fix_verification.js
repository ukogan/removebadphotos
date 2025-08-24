const { chromium } = require('playwright');

/**
 * Focused test to verify Smart Analysis Controls fix for timestamp AttributeError
 * Tests specifically for the JSON serialization error that replaced the original timestamp error
 */
class SmartAnalysisFixVerificationTester {
    constructor() {
        this.browser = null;
        this.page = null;
        this.testResults = {
            passed: 0,
            failed: 0,
            errors: [],
            findings: []
        };
        this.baseUrl = 'http://127.0.0.1:5003';
    }

    async setup() {
        console.log('🔍 Setting up focused test for Smart Analysis fix verification...');
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
            }
        });
        
        this.page.on('pageerror', error => {
            console.log(`[PAGE ERROR] ${error.message}`);
            this.testResults.errors.push(`Page Error: ${error.message}`);
        });
        
        // Monitor specific API requests
        this.page.on('response', response => {
            const url = response.url();
            const status = response.status();
            
            if (url.includes('/api/smart-analysis')) {
                console.log(`[API] Smart Analysis: ${status} ${url}`);
            }
            
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

    async testSpecificAnalysisWorkflow() {
        console.log('\n🎯 Testing Specific Analysis Workflow for Fix Verification...');
        
        try {
            // Navigate to dashboard
            await this.page.goto(this.baseUrl, { waitUntil: 'networkidle' });
            
            // Wait for dashboard to load
            await this.page.waitForSelector('#dashboard-content', { timeout: 30000 });
            this.logTest('Dashboard Loaded', true, 'Ready for analysis');
            
            // Set up test parameters
            await this.page.fill('#size-slider', '5');
            await this.page.waitForTimeout(1000);
            
            // Test both analysis types to isolate the issue
            for (const analysisType of ['metadata', 'smart']) {
                console.log(`\n📊 Testing ${analysisType} analysis...`);
                
                // Select analysis type
                await this.page.click(`button[data-type="${analysisType}"]`);
                await this.page.waitForTimeout(500);
                
                // Track API calls
                let apiRequestMade = false;
                let apiResponseStatus = null;
                let apiResponseBody = null;
                
                this.page.on('response', async (response) => {
                    if (response.url().includes('/api/smart-analysis')) {
                        apiRequestMade = true;
                        apiResponseStatus = response.status();
                        try {
                            apiResponseBody = await response.json();
                        } catch (e) {
                            console.log('Could not parse API response as JSON');
                        }
                    }
                });
                
                // Start analysis
                await this.page.click('#start-analysis');
                
                // Monitor for specific error patterns
                let timestampErrorFound = false;
                let jsonSerializationErrorFound = false;
                let otherErrorFound = false;
                let errorMessage = '';
                
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
                        errorMessage = await this.page.textContent('#error-message');
                        console.log(`❌ Error detected: ${errorMessage}`);
                        
                        // Classify the error type
                        if (errorMessage.includes('timestamp') || errorMessage.includes('PhotoInfo')) {
                            timestampErrorFound = true;
                            this.logFinding(`TIMESTAMP ERROR STILL PRESENT: ${errorMessage}`);
                        } else if (errorMessage.includes('JSON serializable') || errorMessage.includes('Stats')) {
                            jsonSerializationErrorFound = true;
                            this.logFinding(`JSON SERIALIZATION ERROR: ${errorMessage}`);
                        } else {
                            otherErrorFound = true;
                            this.logFinding(`OTHER ERROR: ${errorMessage}`);
                        }
                        
                        analysisComplete = true;
                    }
                    
                    // Check for successful completion
                    const priorityVisible = await this.page.isVisible('#priority-results');
                    if (priorityVisible) {
                        console.log('✅ Analysis completed successfully');
                        analysisComplete = true;
                        this.logTest(`${analysisType} Analysis Success`, true, 'Priority results displayed');
                    }
                    
                    // Check button state for silent failures
                    const buttonText = await this.page.textContent('#start-analysis');
                    if (!buttonText.includes('Analyzing') && !priorityVisible && !errorVisible) {
                        // Silent failure - button returned to normal without results
                        console.log('⚠️ Silent failure detected - button returned to normal state');
                        analysisComplete = true;
                        this.logTest(`${analysisType} Analysis Silent Failure`, false, 'No results or error shown');
                    }
                }
                
                // Report findings for this analysis type
                this.logTest(`${analysisType} API Request Made`, apiRequestMade, `Request was ${apiRequestMade ? '' : 'not '}made`);
                
                if (apiResponseStatus) {
                    this.logTest(`${analysisType} API Response Status`, apiResponseStatus === 200, `Status: ${apiResponseStatus}`);
                }
                
                if (timestampErrorFound) {
                    this.logTest(`${analysisType} Timestamp Fix`, false, 'Original timestamp error still present');
                } else if (jsonSerializationErrorFound) {
                    this.logTest(`${analysisType} Timestamp Fix`, true, 'Original timestamp error is fixed');
                    this.logTest(`${analysisType} New Serialization Issue`, false, 'JSON serialization error introduced');
                } else if (otherErrorFound) {
                    this.logTest(`${analysisType} Analysis Result`, false, `Different error: ${errorMessage}`);
                } else if (analysisComplete) {
                    this.logTest(`${analysisType} Complete Success`, true, 'Analysis completed without errors');
                }
                
                // Wait a bit before next test
                await this.page.waitForTimeout(2000);
            }
            
        } catch (error) {
            this.logTest('Analysis Workflow Test', false, `Exception: ${error.message}`);
        }
    }

    async generateReport() {
        console.log('\n📋 SMART ANALYSIS FIX VERIFICATION REPORT');
        console.log('==========================================');
        console.log(`✅ Tests Passed: ${this.testResults.passed}`);
        console.log(`❌ Tests Failed: ${this.testResults.failed}`);
        console.log(`🔍 Key Findings: ${this.testResults.findings.length}`);
        console.log(`🚨 Errors Found: ${this.testResults.errors.length}`);
        
        if (this.testResults.findings.length > 0) {
            console.log('\n🔍 KEY FINDINGS:');
            this.testResults.findings.forEach((finding, index) => {
                console.log(`${index + 1}. ${finding}`);
            });
        }
        
        if (this.testResults.errors.length > 0) {
            console.log('\n🚨 ERRORS:');
            this.testResults.errors.forEach((error, index) => {
                console.log(`${index + 1}. ${error}`);
            });
        }
        
        // Generate conclusion
        console.log('\n📊 CONCLUSION:');
        const hasTimestampErrors = this.testResults.findings.some(f => f.includes('TIMESTAMP ERROR'));
        const hasJsonErrors = this.testResults.findings.some(f => f.includes('JSON SERIALIZATION ERROR'));
        
        if (hasTimestampErrors) {
            console.log('❌ The original timestamp AttributeError fix is NOT working');
            console.log('   The PhotoInfo -> PhotoData conversion is still failing');
        } else if (hasJsonErrors) {
            console.log('✅ The original timestamp AttributeError has been successfully fixed');
            console.log('❌ However, a new JSON serialization error has been introduced');
            console.log('   The Stats object is not JSON serializable and needs to be converted to a dictionary');
        } else if (this.testResults.passed > this.testResults.failed) {
            console.log('✅ Smart Analysis workflow is working correctly');
            console.log('   Both the timestamp fix and JSON serialization are working');
        } else {
            console.log('❌ Smart Analysis workflow has other issues that need investigation');
        }
        
        const successRate = ((this.testResults.passed / (this.testResults.passed + this.testResults.failed)) * 100).toFixed(1);
        console.log(`\n📈 Test Success Rate: ${successRate}%`);
    }

    async runFocusedTest() {
        console.log('🔍 Starting Focused Smart Analysis Fix Verification');
        console.log('=================================================');
        
        try {
            await this.setup();
            await this.testSpecificAnalysisWorkflow();
        } catch (error) {
            console.log(`❌ Test failed with error: ${error.message}`);
            this.testResults.errors.push(`Test Suite Error: ${error.message}`);
        } finally {
            await this.teardown();
            await this.generateReport();
        }
    }
}

// Run the focused test
const tester = new SmartAnalysisFixVerificationTester();
tester.runFocusedTest().catch(console.error);