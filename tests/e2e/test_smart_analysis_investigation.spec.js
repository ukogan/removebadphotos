// Smart Analysis Bug Investigation Test
// Comprehensive test to identify exact failure points in smart analysis workflow

import { test, expect } from '@playwright/test';

class SmartAnalysisInvestigator {
    constructor(page) {
        this.page = page;
        this.networkLogs = [];
        this.consoleLogs = [];
        this.errors = [];
    }

    async setupMonitoring() {
        // Monitor network requests
        this.page.on('request', request => {
            this.networkLogs.push({
                type: 'request',
                url: request.url(),
                method: request.method(),
                headers: request.headers(),
                postData: request.postData(),
                timestamp: new Date().toISOString()
            });
        });

        this.page.on('response', response => {
            this.networkLogs.push({
                type: 'response',
                url: response.url(),
                status: response.status(),
                statusText: response.statusText(),
                headers: response.headers(),
                timestamp: new Date().toISOString()
            });
        });

        // Monitor console messages
        this.page.on('console', msg => {
            this.consoleLogs.push({
                type: msg.type(),
                text: msg.text(),
                location: msg.location(),
                timestamp: new Date().toISOString()
            });
            
            if (msg.type() === 'error') {
                this.errors.push({
                    text: msg.text(),
                    location: msg.location(),
                    timestamp: new Date().toISOString()
                });
            }
        });

        // Monitor page errors
        this.page.on('pageerror', error => {
            this.errors.push({
                text: error.toString(),
                stack: error.stack,
                timestamp: new Date().toISOString()
            });
        });
    }

    async navigateToDashboard() {
        console.log('🚀 Navigating to dashboard...');
        await this.page.goto('/');
        await this.page.waitForLoadState('networkidle');
    }

    async waitForDashboardLoad() {
        console.log('⏳ Waiting for dashboard to load...');
        
        // Wait for loading indicator to disappear
        await this.page.waitForFunction(() => {
            const loading = document.querySelector('.loading');
            return !loading || loading.style.display === 'none';
        }, { timeout: 30000 });

        // Wait for stats to load
        await this.page.waitForSelector('.stats-overview', { timeout: 30000 });
        console.log('✅ Dashboard loaded successfully');
    }

    async checkModeDetection() {
        console.log('🔍 Checking mode detection...');
        
        // Check for any mode indicators in the DOM
        const modeIndicators = await this.page.$$eval('*', elements => {
            return elements
                .filter(el => el.textContent && (
                    el.textContent.includes('filter') ||
                    el.textContent.includes('overview') ||
                    el.textContent.includes('selected') ||
                    el.textContent.includes('cluster')
                ))
                .map(el => ({
                    tag: el.tagName,
                    text: el.textContent.trim(),
                    className: el.className
                }));
        });

        console.log('Mode indicators found:', modeIndicators);
        return modeIndicators;
    }

    async findSmartAnalysisButton() {
        console.log('🔍 Looking for Smart Analysis button...');
        
        // Wait for the button to appear
        await this.page.waitForSelector('button:has-text("Start Smart Analysis")', { timeout: 10000 });
        
        const button = this.page.locator('button:has-text("Start Smart Analysis")');
        const isVisible = await button.isVisible();
        const isEnabled = await button.isEnabled();
        
        console.log(`Smart Analysis button - Visible: ${isVisible}, Enabled: ${isEnabled}`);
        
        return { button, isVisible, isEnabled };
    }

    async clickSmartAnalysisButton() {
        console.log('🎯 Clicking Smart Analysis button...');
        
        const { button } = await this.findSmartAnalysisButton();
        
        // Record pre-click state
        const preClickNetworkCount = this.networkLogs.length;
        
        // Click the button
        await button.click();
        console.log('✅ Button clicked');
        
        // Wait a moment for any immediate effects
        await this.page.waitForTimeout(1000);
        
        // Check if button text changed (indicates processing started)
        const buttonText = await button.textContent();
        console.log(`Button text after click: "${buttonText}"`);
        
        return { preClickNetworkCount, buttonText };
    }

    async monitorAnalysisProgress() {
        console.log('📊 Monitoring analysis progress...');
        
        // Wait for either success or failure indicators
        let progressDetected = false;
        let completed = false;
        let failed = false;
        
        const timeout = 60000; // 60 seconds
        const startTime = Date.now();
        
        while (!completed && !failed && (Date.now() - startTime) < timeout) {
            // Check for progress indicators
            const progressElement = await this.page.$('.progress-bar, .progress-indicator, .loading-spinner');
            if (progressElement) {
                progressDetected = true;
                console.log('📈 Progress indicator detected');
            }
            
            // Check for error messages
            const errorElement = await this.page.$('.error, .alert-danger, [class*="error"]');
            if (errorElement) {
                const errorText = await errorElement.textContent();
                console.log('❌ Error detected:', errorText);
                failed = true;
            }
            
            // Check for completion indicators
            const completeElement = await this.page.$('.analysis-results, .results-container, [class*="result"]');
            if (completeElement) {
                console.log('✅ Results detected');
                completed = true;
            }
            
            // Check button state
            const button = this.page.locator('button:has-text("Start Smart Analysis"), button:has-text("Processing"), button:has-text("Analyzing")');
            const buttonText = await button.first().textContent();
            
            if (buttonText && buttonText.includes('Start Smart Analysis')) {
                // Button returned to original state - either completed or failed
                break;
            }
            
            await this.page.waitForTimeout(1000);
        }
        
        return { progressDetected, completed, failed, timedOut: (Date.now() - startTime) >= timeout };
    }

    async captureSmartAnalysisApiCalls() {
        console.log('🔍 Analyzing API calls...');
        
        const apiCalls = this.networkLogs.filter(log => 
            log.url.includes('/api/smart-analysis') || 
            log.url.includes('/api/progress')
        );
        
        console.log(`Found ${apiCalls.length} relevant API calls`);
        
        for (const call of apiCalls) {
            console.log(`${call.type.toUpperCase()}: ${call.method || 'N/A'} ${call.url}`);
            if (call.status) {
                console.log(`  Status: ${call.status} ${call.statusText}`);
            }
            if (call.postData) {
                console.log(`  Data: ${call.postData}`);
            }
        }
        
        return apiCalls;
    }

    async getDetailedErrorReport() {
        console.log('📋 Generating detailed error report...');
        
        const report = {
            timestamp: new Date().toISOString(),
            errors: this.errors,
            consoleWarnings: this.consoleLogs.filter(log => log.type === 'warning'),
            networkFailures: this.networkLogs.filter(log => 
                log.type === 'response' && 
                (log.status >= 400 || log.status === 0)
            ),
            allApiCalls: this.networkLogs.filter(log => log.url.includes('/api/')),
            pageState: {}
        };
        
        // Capture current page state
        try {
            report.pageState.title = await this.page.title();
            report.pageState.url = this.page.url();
            report.pageState.buttonStates = await this.page.$$eval('button', buttons => 
                buttons.map(btn => ({
                    text: btn.textContent.trim(),
                    disabled: btn.disabled,
                    className: btn.className
                }))
            );
        } catch (e) {
            report.pageState.error = e.toString();
        }
        
        return report;
    }
}

test.describe('Smart Analysis Bug Investigation', () => {
    let investigator;

    test.beforeEach(async ({ page }) => {
        investigator = new SmartAnalysisInvestigator(page);
        await investigator.setupMonitoring();
    });

    test('Investigate smart analysis failure in overview mode', async ({ page }) => {
        console.log('\n🔍 STARTING SMART ANALYSIS INVESTIGATION - OVERVIEW MODE\n');
        
        // Step 1: Navigate and wait for dashboard
        await investigator.navigateToDashboard();
        await investigator.waitForDashboardLoad();
        
        // Step 2: Check mode detection
        const modeIndicators = await investigator.checkModeDetection();
        console.log('\n📊 MODE DETECTION RESULTS:', modeIndicators);
        
        // Step 3: Find and analyze the Smart Analysis button
        const buttonInfo = await investigator.findSmartAnalysisButton();
        expect(buttonInfo.isVisible).toBe(true);
        
        // Step 4: Click the button and monitor response
        const clickResult = await investigator.clickSmartAnalysisButton();
        
        // Step 5: Monitor progress and capture results
        const progressResult = await investigator.monitorAnalysisProgress();
        console.log('\n📈 PROGRESS MONITORING RESULTS:', progressResult);
        
        // Step 6: Capture API calls
        const apiCalls = await investigator.captureSmartAnalysisApiCalls();
        
        // Step 7: Generate comprehensive error report
        const errorReport = await investigator.getDetailedErrorReport();
        
        // Step 8: Take screenshot for visual debugging
        await page.screenshot({ 
            path: '/Users/urikogan/code/dedup/smart_analysis_failure_screenshot.png',
            fullPage: true 
        });
        
        // Final analysis and reporting
        console.log('\n🔍 FINAL INVESTIGATION RESULTS:');
        console.log('================================');
        console.log('Button Click Success:', clickResult.buttonText !== '🚀 Start Smart Analysis');
        console.log('Progress Detected:', progressResult.progressDetected);
        console.log('Analysis Completed:', progressResult.completed);
        console.log('Analysis Failed:', progressResult.failed);
        console.log('Timed Out:', progressResult.timedOut);
        console.log('API Calls Made:', apiCalls.length);
        console.log('JavaScript Errors:', errorReport.errors.length);
        console.log('Network Failures:', errorReport.networkFailures.length);
        
        // Output detailed logs
        console.log('\n📋 DETAILED ERROR REPORT:');
        console.log(JSON.stringify(errorReport, null, 2));
        
        // Assert that we can identify the failure point
        if (progressResult.failed || errorReport.errors.length > 0 || errorReport.networkFailures.length > 0) {
            console.log('\n❌ FAILURE CONFIRMED - See detailed logs above');
        } else if (progressResult.timedOut) {
            console.log('\n⏰ TIMEOUT - Analysis took too long or hung');
        } else {
            console.log('\n✅ No obvious failures detected - May be a subtle issue');
        }
    });

    test('Test smart analysis with simulated filtered mode', async ({ page }) => {
        console.log('\n🔍 TESTING FILTERED MODE SIMULATION\n');
        
        // Navigate to dashboard
        await investigator.navigateToDashboard();
        
        // Simulate filtered mode by setting session data
        await page.evaluate(() => {
            // Simulate having filter session data
            const mockFilterSession = {
                selected_clusters: ['cluster1', 'cluster2'],
                total_clusters_in_filter: 2,
                filter_criteria: { min_size_mb: 5 }
            };
            
            // Try to set session storage or trigger filtered mode
            sessionStorage.setItem('filter_session', JSON.stringify(mockFilterSession));
            
            // Also try posting to set session on backend
            fetch('/api/set-filter-session', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(mockFilterSession)
            }).catch(e => console.log('Filter session setup failed:', e));
        });
        
        await investigator.waitForDashboardLoad();
        
        // Check if filtered mode is detected
        const modeIndicators = await investigator.checkModeDetection();
        console.log('Filtered mode indicators:', modeIndicators);
        
        // Try smart analysis in this mode
        const buttonInfo = await investigator.findSmartAnalysisButton();
        if (buttonInfo.isVisible && buttonInfo.isEnabled) {
            await investigator.clickSmartAnalysisButton();
            const progressResult = await investigator.monitorAnalysisProgress();
            
            console.log('Filtered mode analysis result:', progressResult);
        }
        
        const errorReport = await investigator.getDetailedErrorReport();
        console.log('\nFiltered mode error report:', JSON.stringify(errorReport, null, 2));
    });
});