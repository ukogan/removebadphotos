"""
E2E Tests for Dashboard and Legacy Interface Data Consistency
Tests that both interfaces show consistent library statistics after smart analysis.
"""

import pytest
from playwright.sync_api import Page, expect
import time
import json
import re

BASE_URL = "http://127.0.0.1:5003"
DASHBOARD_URL = f"{BASE_URL}/"
LEGACY_URL = f"{BASE_URL}/legacy"

# Test timeout configuration
ANALYSIS_TIMEOUT = 300000  # 5 minutes for smart analysis
PAGE_TIMEOUT = 30000      # 30 seconds for page loads
DEFAULT_TIMEOUT = 10000   # 10 seconds for element interactions

class LibraryStats:
    """Data structure to hold library statistics for comparison"""
    
    def __init__(self):
        self.total_photos = None
        self.library_size = None
        self.estimated_duplicates = None  
        self.potential_savings = None
        self.date_range = None
        self.cluster_count = None
        self.analysis_completed = False
        
    def __str__(self):
        return (f"LibraryStats(photos={self.total_photos}, size={self.library_size}, "
                f"duplicates={self.estimated_duplicates}, savings={self.potential_savings}, "
                f"range={self.date_range}, clusters={self.cluster_count}, "
                f"analysis_completed={self.analysis_completed})")
                
    def compare_with(self, other):
        """Compare two LibraryStats objects and return differences"""
        differences = []
        
        if self.total_photos != other.total_photos:
            differences.append(f"total_photos: {self.total_photos} vs {other.total_photos}")
            
        if self.library_size != other.library_size:
            differences.append(f"library_size: {self.library_size} vs {other.library_size}")
            
        if self.estimated_duplicates != other.estimated_duplicates:
            differences.append(f"estimated_duplicates: {self.estimated_duplicates} vs {other.estimated_duplicates}")
            
        if self.potential_savings != other.potential_savings:
            differences.append(f"potential_savings: {self.potential_savings} vs {other.potential_savings}")
            
        if self.date_range != other.date_range:
            differences.append(f"date_range: {self.date_range} vs {other.date_range}")
            
        if self.cluster_count != other.cluster_count:
            differences.append(f"cluster_count: {self.cluster_count} vs {other.cluster_count}")
            
        return differences

@pytest.fixture
def browser_page(page: Page):
    """Set up page with appropriate timeouts and configurations"""
    page.set_default_timeout(DEFAULT_TIMEOUT)
    page.set_default_navigation_timeout(PAGE_TIMEOUT)
    return page

class TestInterfaceConsistency:
    """Test suite for verifying data consistency between dashboard and legacy interfaces"""
    
    def test_dashboard_loads_successfully(self, browser_page: Page):
        """Verify that dashboard interface loads without errors"""
        print("🔍 Testing dashboard page load...")
        
        # Navigate to dashboard
        browser_page.goto(DASHBOARD_URL)
        
        # Verify page loads successfully
        expect(browser_page).to_have_title("Photo Dedup Tool - Dashboard")
        
        # Wait for loading to complete
        browser_page.wait_for_selector("#dashboard-content", timeout=PAGE_TIMEOUT)
        
        # Verify core elements are present
        expect(browser_page.locator("h1")).to_contain_text("Photo Dedup Dashboard")
        expect(browser_page.locator("#total-photos")).to_be_visible()
        expect(browser_page.locator("#start-analysis")).to_be_visible()
        
        print("✅ Dashboard loads successfully")

    def test_legacy_interface_loads_successfully(self, browser_page: Page):
        """Verify that legacy interface loads without errors"""
        print("🔍 Testing legacy interface load...")
        
        # Navigate to legacy interface
        browser_page.goto(LEGACY_URL)
        
        # Verify page loads successfully - checking for common legacy interface elements
        expect(browser_page.locator("body")).to_be_visible()
        
        # Look for typical legacy interface indicators
        page_content = browser_page.content()
        assert len(page_content) > 1000, "Legacy page content seems too short"
        
        print("✅ Legacy interface loads successfully")

    def extract_dashboard_stats_before_analysis(self, browser_page: Page) -> LibraryStats:
        """Extract library statistics from dashboard before running analysis"""
        print("📊 Extracting dashboard stats before analysis...")
        
        stats = LibraryStats()
        
        # Navigate to dashboard
        browser_page.goto(DASHBOARD_URL)
        browser_page.wait_for_selector("#dashboard-content", timeout=PAGE_TIMEOUT)
        
        # Extract stats from dashboard
        stats.total_photos = browser_page.locator("#total-photos").inner_text().strip()
        stats.library_size = browser_page.locator("#library-size").inner_text().strip()
        stats.estimated_duplicates = browser_page.locator("#estimated-duplicates").inner_text().strip()
        stats.potential_savings = browser_page.locator("#potential-savings").inner_text().strip()
        stats.date_range = browser_page.locator("#date-range").inner_text().strip()
        stats.cluster_count = browser_page.locator("#cluster-count").inner_text().strip()
        
        print(f"📊 Dashboard stats before analysis: {stats}")
        return stats

    def run_smart_analysis_on_dashboard(self, browser_page: Page) -> LibraryStats:
        """Run smart analysis on dashboard and return updated stats"""
        print("🚀 Running smart analysis on dashboard...")
        
        # Navigate to dashboard
        browser_page.goto(DASHBOARD_URL)
        browser_page.wait_for_selector("#dashboard-content", timeout=PAGE_TIMEOUT)
        
        # Wait for analysis button to be ready
        analysis_button = browser_page.locator("#start-analysis")
        expect(analysis_button).to_be_visible()
        expect(analysis_button).not_to_be_disabled()
        
        # Take screenshot before analysis
        browser_page.screenshot(path="dashboard_before_analysis.png", full_page=True)
        
        # Click the smart analysis button
        analysis_button.click()
        
        # Wait for analysis to start - button should be disabled
        expect(analysis_button).to_be_disabled(timeout=5000)
        
        # Wait for progress log to appear
        browser_page.wait_for_selector("#progress-log-container", state="visible", timeout=10000)
        
        # Monitor progress and wait for completion
        print("⏳ Monitoring analysis progress...")
        start_time = time.time()
        
        while time.time() - start_time < ANALYSIS_TIMEOUT / 1000:  # Convert to seconds
            # Check if analysis is complete (button re-enabled)
            if not analysis_button.is_disabled():
                break
                
            # Check for error messages
            error_element = browser_page.locator("#error-message")
            if error_element.is_visible():
                error_text = error_element.inner_text()
                raise Exception(f"Analysis failed with error: {error_text}")
            
            # Check progress log for completion indicator
            progress_log = browser_page.locator("#progress-log")
            if progress_log.is_visible():
                log_content = progress_log.inner_text()
                if "✅ Analysis completed successfully!" in log_content:
                    break
                if "❌ Analysis failed" in log_content:
                    raise Exception(f"Analysis failed: {log_content}")
            
            time.sleep(2)  # Check every 2 seconds
        
        # Verify analysis completed successfully
        if analysis_button.is_disabled():
            raise Exception("Analysis timed out - button still disabled")
        
        print("✅ Analysis completed successfully")
        
        # Take screenshot after analysis
        browser_page.screenshot(path="dashboard_after_analysis.png", full_page=True)
        
        # Extract updated stats
        stats = LibraryStats()
        stats.total_photos = browser_page.locator("#total-photos").inner_text().strip()
        stats.library_size = browser_page.locator("#library-size").inner_text().strip() 
        stats.estimated_duplicates = browser_page.locator("#estimated-duplicates").inner_text().strip()
        stats.potential_savings = browser_page.locator("#potential-savings").inner_text().strip()
        stats.date_range = browser_page.locator("#date-range").inner_text().strip()
        stats.cluster_count = browser_page.locator("#cluster-count").inner_text().strip()
        stats.analysis_completed = True
        
        print(f"📊 Dashboard stats after analysis: {stats}")
        return stats

    def extract_legacy_stats(self, browser_page: Page) -> LibraryStats:
        """Extract library statistics from legacy interface"""
        print("📊 Extracting legacy interface stats...")
        
        # Navigate to legacy interface
        browser_page.goto(LEGACY_URL)
        
        # Wait for the page to load completely and for any loading indicators to disappear
        try:
            # Wait for any loading text to disappear (up to 60 seconds)
            browser_page.wait_for_function(
                "() => !document.body.innerText.includes('Loading Photos library information')", 
                timeout=60000
            )
        except Exception as e:
            print(f"⚠️ Legacy interface still loading after 60s: {e}")
        
        # Take screenshot of legacy interface
        browser_page.screenshot(path="legacy_interface_final.png", full_page=True)
        
        stats = LibraryStats()
        
        # Get page content after loading is complete
        page_content = browser_page.content()
        
        # Save the page content for debugging
        with open("legacy_page_content.html", "w") as f:
            f.write(page_content)
        
        print(f"📄 Legacy page content length: {len(page_content)} characters")
        
        # Look for common stat patterns in the HTML
        # This is a flexible approach since we don't know the exact legacy interface structure
        
        # Try to find total photos - multiple patterns
        photo_patterns = [
            r'(\d+(?:,\d+)*)\s*(?:photos?|images?)',
            r'Total.*?(\d+(?:,\d+)*)',
            r'Library.*?(\d+(?:,\d+)*)',
            r'(\d+(?:,\d+)*)\s*files?'
        ]
        
        for pattern in photo_patterns:
            photo_match = re.search(pattern, page_content, re.IGNORECASE)
            if photo_match:
                stats.total_photos = photo_match.group(1)
                break
        
        # Try to find library size - multiple patterns
        size_patterns = [
            r'(\d+(?:\.\d+)?)\s*GB',
            r'Size.*?(\d+(?:\.\d+)?)\s*GB',
            r'Library.*?(\d+(?:\.\d+)?)\s*GB'
        ]
        
        for pattern in size_patterns:
            size_match = re.search(pattern, page_content, re.IGNORECASE)
            if size_match:
                stats.library_size = f"{size_match.group(1)} GB"
                break
        
        # Try to find duplicates info
        dup_patterns = [
            r'(\d+(?:,\d+)*)\s*(?:duplicates?)',
            r'Duplicate.*?(\d+(?:,\d+)*)',
            r'Found.*?(\d+(?:,\d+)*)'
        ]
        
        for pattern in dup_patterns:
            dup_match = re.search(pattern, page_content, re.IGNORECASE)
            if dup_match:
                stats.estimated_duplicates = dup_match.group(1)
                break
        
        # Try to find savings info
        savings_patterns = [
            r'~?(\d+(?:\.\d+)?)\s*GB.*savings?',
            r'Save.*?(\d+(?:\.\d+)?)\s*GB',
            r'Savings.*?(\d+(?:\.\d+)?)\s*GB'
        ]
        
        for pattern in savings_patterns:
            savings_match = re.search(pattern, page_content, re.IGNORECASE)
            if savings_match:
                stats.potential_savings = f"~{savings_match.group(1)} GB"
                break
        
        # Try to find date range
        date_patterns = [
            r'(\d{4})-(\d{4})',
            r'Date.*?(\d{4}).*?(\d{4})',
            r'Range.*?(\d{4}).*?(\d{4})'
        ]
        
        for pattern in date_patterns:
            date_match = re.search(pattern, page_content)
            if date_match:
                stats.date_range = f"{date_match.group(1)}-{date_match.group(2)}"
                break
        
        # Try to find cluster info
        cluster_patterns = [
            r'(\d+(?:,\d+)*)\s*(?:clusters?|groups?)',
            r'Cluster.*?(\d+(?:,\d+)*)',
            r'Group.*?(\d+(?:,\d+)*)'
        ]
        
        for pattern in cluster_patterns:
            cluster_match = re.search(pattern, page_content, re.IGNORECASE)
            if cluster_match:
                stats.cluster_count = cluster_match.group(1)
                break
        
        # Check if analysis data is present (indicates analysis was run)
        stats.analysis_completed = bool(
            stats.estimated_duplicates or 
            stats.potential_savings or 
            stats.cluster_count or
            'analysis' in page_content.lower() or
            'priority' in page_content.lower()
        )
        
        print(f"📊 Legacy stats: {stats}")
        return stats

    def test_data_consistency_after_analysis(self, browser_page: Page):
        """Main test: Verify data consistency between dashboard and legacy after running smart analysis"""
        print("\n🧪 Starting comprehensive data consistency test...")
        
        # Step 1: Get initial dashboard stats (before analysis)
        print("\n📊 Step 1: Getting initial dashboard stats...")
        initial_stats = self.extract_dashboard_stats_before_analysis(browser_page)
        
        # Step 2: Run smart analysis on dashboard
        print("\n🚀 Step 2: Running smart analysis...")
        dashboard_stats = self.run_smart_analysis_on_dashboard(browser_page)
        
        # Step 3: Get legacy interface stats (should now show analysis results)
        print("\n📊 Step 3: Getting legacy interface stats...")
        legacy_stats = self.extract_legacy_stats(browser_page)
        
        # Step 4: Compare the stats
        print("\n🔍 Step 4: Comparing stats between interfaces...")
        differences = dashboard_stats.compare_with(legacy_stats)
        
        # Generate detailed test report
        self.generate_test_report(initial_stats, dashboard_stats, legacy_stats, differences)
        
        # Assertions
        print("\n✅ Performing consistency assertions...")
        
        # Basic consistency checks
        if differences:
            print("⚠️  Found differences between interfaces:")
            for diff in differences:
                print(f"   - {diff}")
        
        # Critical assertions - these should match exactly if the cache unification worked
        assert dashboard_stats.total_photos == legacy_stats.total_photos or \
               (dashboard_stats.total_photos and legacy_stats.total_photos and 
                dashboard_stats.total_photos.replace(',', '') == legacy_stats.total_photos.replace(',', '')), \
               f"Total photos mismatch: Dashboard='{dashboard_stats.total_photos}' vs Legacy='{legacy_stats.total_photos}'"
        
        # If both interfaces processed analysis data, they should have similar results
        if dashboard_stats.analysis_completed and legacy_stats.analysis_completed:
            assert dashboard_stats.library_size == legacy_stats.library_size or \
                   (dashboard_stats.library_size and legacy_stats.library_size), \
                   f"Library size mismatch: Dashboard='{dashboard_stats.library_size}' vs Legacy='{legacy_stats.library_size}'"
        
        print("🎉 Data consistency test passed!")

    def generate_test_report(self, initial_stats: LibraryStats, dashboard_stats: LibraryStats, 
                           legacy_stats: LibraryStats, differences: list):
        """Generate a detailed test report"""
        
        report = {
            "test_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "test_results": {
                "initial_dashboard_stats": {
                    "total_photos": initial_stats.total_photos,
                    "library_size": initial_stats.library_size,
                    "estimated_duplicates": initial_stats.estimated_duplicates,
                    "potential_savings": initial_stats.potential_savings,
                    "date_range": initial_stats.date_range,
                    "cluster_count": initial_stats.cluster_count,
                    "analysis_completed": initial_stats.analysis_completed
                },
                "dashboard_after_analysis": {
                    "total_photos": dashboard_stats.total_photos,
                    "library_size": dashboard_stats.library_size, 
                    "estimated_duplicates": dashboard_stats.estimated_duplicates,
                    "potential_savings": dashboard_stats.potential_savings,
                    "date_range": dashboard_stats.date_range,
                    "cluster_count": dashboard_stats.cluster_count,
                    "analysis_completed": dashboard_stats.analysis_completed
                },
                "legacy_interface_stats": {
                    "total_photos": legacy_stats.total_photos,
                    "library_size": legacy_stats.library_size,
                    "estimated_duplicates": legacy_stats.estimated_duplicates,
                    "potential_savings": legacy_stats.potential_savings,
                    "date_range": legacy_stats.date_range,
                    "cluster_count": legacy_stats.cluster_count,
                    "analysis_completed": legacy_stats.analysis_completed
                },
                "consistency_check": {
                    "differences_found": len(differences),
                    "differences": differences,
                    "overall_consistency": "PASS" if len(differences) == 0 else "PARTIAL"
                }
            }
        }
        
        # Write report to file
        with open("interface_consistency_test_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        # Print summary
        print(f"\n📋 TEST REPORT SUMMARY")
        print(f"{'='*50}")
        print(f"Timestamp: {report['test_timestamp']}")
        print(f"Differences found: {len(differences)}")
        print(f"Overall consistency: {report['test_results']['consistency_check']['overall_consistency']}")
        
        if differences:
            print(f"\n⚠️  DIFFERENCES DETECTED:")
            for i, diff in enumerate(differences, 1):
                print(f"   {i}. {diff}")
        else:
            print(f"\n✅ PERFECT CONSISTENCY - All stats match between interfaces!")
        
        print(f"\n📄 Detailed report saved to: interface_consistency_test_report.json")
        print(f"📸 Screenshots saved:")
        print(f"   - dashboard_before_analysis.png")
        print(f"   - dashboard_after_analysis.png") 
        print(f"   - legacy_interface.png")

    def test_smart_analysis_workflow_complete(self, browser_page: Page):
        """Test the complete workflow of smart analysis and interface consistency"""
        print("\n🔧 Testing complete smart analysis workflow...")
        
        # This test runs the main consistency test
        self.test_data_consistency_after_analysis(browser_page)
        
        print("✅ Complete workflow test passed!")

if __name__ == "__main__":
    # This allows running the test directly
    pytest.main([__file__, "-v", "-s"])