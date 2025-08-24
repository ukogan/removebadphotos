"""
Quick verification test to check current interface states
"""

import pytest
from playwright.sync_api import Page

BASE_URL = "http://127.0.0.1:5003"

@pytest.fixture
def browser_page(page: Page):
    page.set_default_timeout(10000)
    return page

class TestQuickVerification:
    """Quick tests to verify current interface states"""
    
    def test_dashboard_shows_basic_stats(self, browser_page: Page):
        """Verify dashboard shows basic library statistics"""
        browser_page.goto(f"{BASE_URL}/")
        browser_page.wait_for_selector("#dashboard-content")
        
        # Check basic stats are displayed
        total_photos = browser_page.locator("#total-photos").inner_text()
        library_size = browser_page.locator("#library-size").inner_text()
        
        print(f"Dashboard - Total Photos: {total_photos}")
        print(f"Dashboard - Library Size: {library_size}")
        
        assert total_photos != "-", "Dashboard should show total photos"
        assert library_size != "-", "Dashboard should show library size"
        
    def test_legacy_shows_after_analysis(self, browser_page: Page):
        """Verify legacy interface shows analysis results"""
        browser_page.goto(f"{BASE_URL}/legacy")
        
        # Wait for loading to complete
        browser_page.wait_for_function(
            "() => !document.body.innerText.includes('Loading Photos library information')", 
            timeout=30000
        )
        
        # Check if analysis results are shown
        content = browser_page.content()
        
        has_photos_count = "14,638" in content
        has_duplicates = "duplicates" in content.lower() or "groups" in content.lower()
        
        print(f"Legacy - Has photo count: {has_photos_count}")
        print(f"Legacy - Has duplicate info: {has_duplicates}")
        
        assert has_photos_count or has_duplicates, "Legacy should show some analysis data"
        
    def test_interfaces_both_accessible(self, browser_page: Page):
        """Verify both interfaces are accessible and load"""
        
        # Test dashboard
        browser_page.goto(f"{BASE_URL}/")
        assert "Photo Dedup Dashboard" in browser_page.content()
        
        # Test legacy  
        browser_page.goto(f"{BASE_URL}/legacy")
        assert "Photo Deduplication Tool" in browser_page.content()
        
        print("✅ Both interfaces are accessible and loading correctly")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])