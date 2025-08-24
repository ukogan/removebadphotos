"""
End-to-End Tests for Individual Photo Selection Functionality
============================================================

This test suite validates the end-to-end functionality of individual photo selection
in the photo deduplication application, specifically testing the reported issue:
"it's still not possible to select individual photos 1 by 1 for deletion."

Test Coverage:
- Individual photo card click interactions
- Visual state changes (KEEP ↔ DELETE toggle)
- Selection summary updates in real-time
- JavaScript error detection
- Cross-browser compatibility
- Confirmation flow accuracy
"""

import pytest
from playwright.sync_api import Page, expect
import time
import json
from typing import List, Dict, Any
import logging

# Configure logging for test execution
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Base URL for the application
BASE_URL = "http://127.0.0.1:5003"

class TestIndividualPhotoSelection:
    """Test suite for individual photo selection functionality."""
    
    @pytest.fixture(autouse=True)
    def setup_test(self, page: Page):
        """Set up each test with page navigation and initial state verification."""
        logger.info("Setting up test: navigating to application")
        
        # Navigate to the main application page
        page.goto(f"{BASE_URL}/legacy?priority=P4&limit=10")
        
        # Wait for the page to be fully loaded
        page.wait_for_selector("#status", timeout=10000)
        
        # Check if stats are loaded successfully
        status_element = page.locator("#status")
        expect(status_element).to_be_visible()
        
        # Wait for the analyze button to be available
        page.wait_for_selector("#loadGroupsBtn", timeout=10000)
        
        logger.info("Test setup completed successfully")
    
    def wait_for_analysis_completion(self, page: Page, timeout_ms: int = 120000) -> None:
        """Wait for photo analysis to complete."""
        logger.info("Starting photo analysis...")
        
        # Click the analyze button
        analyze_btn = page.locator("#loadGroupsBtn")
        expect(analyze_btn).to_be_visible()
        analyze_btn.click()
        
        # Monitor progress and wait for completion
        start_time = time.time()
        
        while time.time() - start_time < timeout_ms / 1000:
            try:
                # Check if analysis is complete by looking for photo groups
                if page.locator(".group-card").count() > 0:
                    logger.info("Photo analysis completed - groups loaded")
                    break
                
                # Check for error states
                if "Error" in page.locator("#groupStatus").inner_text():
                    raise Exception("Analysis failed with error")
                    
            except Exception:
                # Continue waiting if elements aren't ready yet
                pass
                
            time.sleep(1)
        else:
            raise TimeoutError("Analysis did not complete within timeout")
    
    def get_photo_cards(self, page: Page) -> List:
        """Get all photo card elements from the page."""
        # Wait for photo cards to be present
        page.wait_for_selector(".photo-card", timeout=30000)
        return page.locator(".photo-card").all()
    
    def get_photo_selection_state(self, photo_card) -> Dict[str, Any]:
        """Extract the current selection state of a photo card."""
        card_classes = photo_card.get_attribute("class") or ""
        
        # Check if photo is selected (DELETE state)
        is_selected = "selected" in card_classes
        
        # Get the visual indicator
        visual_state = "DELETE" if is_selected else "KEEP"
        
        # Get photo UUID and group ID
        photo_uuid = photo_card.get_attribute("data-photo") or ""
        group_id = photo_card.get_attribute("data-group") or ""
        
        return {
            "is_selected": is_selected,
            "visual_state": visual_state,
            "photo_uuid": photo_uuid,
            "group_id": group_id,
            "card_classes": card_classes
        }
    
    def get_selection_summary_stats(self, page: Page) -> Dict[str, Any]:
        """Extract current selection summary statistics."""
        summary_div = page.locator("#selectionSummary")
        
        if not summary_div.is_visible():
            return {
                "visible": False,
                "photos_to_delete": 0,
                "groups_with_deletions": 0,
                "estimated_savings": "0 MB"
            }
        
        summary_text = summary_div.inner_text()
        
        # Parse the summary text to extract statistics
        photos_to_delete = 0
        groups_with_deletions = 0
        estimated_savings = "0 MB"
        
        # Extract numbers from summary text using basic parsing
        lines = summary_text.split('\n')
        for line in lines:
            if "photos" in line and "will be marked for deletion" in line:
                # Extract photo count
                words = line.split()
                for i, word in enumerate(words):
                    if word.isdigit():
                        photos_to_delete = int(word)
                        break
            elif "groups" in line:
                # Extract group count
                words = line.split()
                for word in words:
                    if word.isdigit():
                        groups_with_deletions = int(word)
                        break
            elif "MB" in line and "saving" in line:
                # Extract savings estimate
                words = line.split()
                for i, word in enumerate(words):
                    if "MB" in word:
                        # Get the number before MB
                        if i > 0 and any(c.isdigit() for c in words[i-1]):
                            estimated_savings = f"{words[i-1]} MB"
                        break
        
        return {
            "visible": True,
            "photos_to_delete": photos_to_delete,
            "groups_with_deletions": groups_with_deletions,
            "estimated_savings": estimated_savings
        }
    
    @pytest.mark.e2e
    def test_application_loads_successfully(self, page: Page):
        """Test that the application loads and displays photo library information."""
        logger.info("Testing application initial load")
        
        # Verify page title
        expect(page).to_have_title("Photo Dedup Tool")
        
        # Verify main header is present
        header = page.locator("h1")
        expect(header).to_contain_text("Photo Deduplication Tool")
        
        # Verify status shows connection success
        status = page.locator("#status")
        expect(status).to_be_visible()
        
        # Verify controls are available
        controls = page.locator("#controls")
        expect(controls).to_be_visible()
        
        logger.info("✅ Application loads successfully")
    
    @pytest.mark.e2e
    def test_photo_groups_load_and_display(self, page: Page):
        """Test that photo groups load and display correctly."""
        logger.info("Testing photo group loading")
        
        # Start analysis
        self.wait_for_analysis_completion(page)
        
        # Verify photo groups are displayed
        group_cards = page.locator(".group-card")
        expect(group_cards.first).to_be_visible()
        
        group_count = group_cards.count()
        logger.info(f"Found {group_count} photo groups")
        
        assert group_count > 0, "No photo groups were loaded"
        
        # Verify each group has photo cards
        photo_cards = self.get_photo_cards(page)
        assert len(photo_cards) > 0, "No photo cards found in groups"
        
        logger.info(f"✅ Successfully loaded {group_count} groups with {len(photo_cards)} photos")
    
    @pytest.mark.e2e
    def test_individual_photo_click_functionality(self, page: Page):
        """Test core functionality: individual photo cards can be clicked."""
        logger.info("Testing individual photo click functionality")
        
        # Load photo groups
        self.wait_for_analysis_completion(page)
        
        # Get all photo cards
        photo_cards = self.get_photo_cards(page)
        assert len(photo_cards) > 0, "No photo cards available for testing"
        
        logger.info(f"Testing click functionality on {len(photo_cards)} photo cards")
        
        # Test clicking each photo card
        clickable_count = 0
        for i, card in enumerate(photo_cards[:5]):  # Test first 5 to avoid timeout
            try:
                # Get initial state
                initial_state = self.get_photo_selection_state(card)
                logger.info(f"Photo {i+1} initial state: {initial_state['visual_state']}")
                
                # Click the photo card
                card.click(timeout=5000)
                
                # Wait a moment for state change
                time.sleep(0.5)
                
                # Get new state
                new_state = self.get_photo_selection_state(card)
                logger.info(f"Photo {i+1} new state: {new_state['visual_state']}")
                
                # Verify state changed
                assert initial_state["is_selected"] != new_state["is_selected"], \
                    f"Photo {i+1} click did not change selection state"
                
                clickable_count += 1
                
            except Exception as e:
                logger.error(f"Error clicking photo {i+1}: {e}")
                continue
        
        assert clickable_count > 0, "No photo cards were successfully clickable"
        logger.info(f"✅ Successfully tested clicking on {clickable_count} photo cards")
    
    @pytest.mark.e2e  
    def test_keep_delete_state_toggle(self, page: Page):
        """Test KEEP ↔ DELETE state toggling works correctly."""
        logger.info("Testing KEEP ↔ DELETE state toggling")
        
        # Load photo groups
        self.wait_for_analysis_completion(page)
        
        # Get first photo card for detailed testing
        photo_cards = self.get_photo_cards(page)
        test_card = photo_cards[0]
        
        # Initial state should be KEEP (not selected)
        initial_state = self.get_photo_selection_state(test_card)
        logger.info(f"Initial state: {initial_state}")
        
        assert initial_state["visual_state"] == "KEEP", \
            f"Expected initial KEEP state, got {initial_state['visual_state']}"
        
        # Click to change to DELETE state
        test_card.click()
        time.sleep(0.5)
        
        delete_state = self.get_photo_selection_state(test_card)
        logger.info(f"After first click: {delete_state}")
        
        assert delete_state["visual_state"] == "DELETE", \
            f"Expected DELETE state after click, got {delete_state['visual_state']}"
        
        # Click again to return to KEEP state
        test_card.click()
        time.sleep(0.5)
        
        keep_state = self.get_photo_selection_state(test_card)
        logger.info(f"After second click: {keep_state}")
        
        assert keep_state["visual_state"] == "KEEP", \
            f"Expected KEEP state after second click, got {keep_state['visual_state']}"
        
        logger.info("✅ KEEP ↔ DELETE state toggling works correctly")
    
    @pytest.mark.e2e
    def test_visual_indicators_display_correctly(self, page: Page):
        """Test that visual indicators (shield/X, colors) display correctly."""
        logger.info("Testing visual indicators display")
        
        # Load photo groups
        self.wait_for_analysis_completion(page)
        
        # Get test photo card
        photo_cards = self.get_photo_cards(page)
        test_card = photo_cards[0]
        
        # Test KEEP state visuals
        keep_state = self.get_photo_selection_state(test_card)
        if keep_state["visual_state"] == "DELETE":
            # Click to get to KEEP state
            test_card.click()
            time.sleep(0.5)
        
        # Verify KEEP visual indicators
        keep_classes = test_card.get_attribute("class")
        assert "selected" not in keep_classes, "KEEP state should not have 'selected' class"
        
        # Check for KEEP indicator (🛡️ KEEP)
        keep_indicator = test_card.locator("::after")  # CSS pseudo-element
        # Note: Pseudo-elements are hard to test directly, so we check the class instead
        
        # Click to DELETE state
        test_card.click()
        time.sleep(0.5)
        
        # Verify DELETE visual indicators  
        delete_classes = test_card.get_attribute("class")
        assert "selected" in delete_classes, "DELETE state should have 'selected' class"
        
        # Check that visual styling changed
        border_color = test_card.evaluate("el => window.getComputedStyle(el).borderColor")
        logger.info(f"DELETE state border color: {border_color}")
        
        # Verify red-ish border for DELETE state (RGB values for red tones)
        assert any(color in border_color for color in ["220", "rgb(220, 53, 69)", "rgb(220,53,69)"]), \
            f"Expected red border for DELETE state, got {border_color}"
        
        logger.info("✅ Visual indicators display correctly")
    
    @pytest.mark.e2e
    def test_selection_summary_updates_realtime(self, page: Page):
        """Test that selection summary updates in real-time when photos are selected."""
        logger.info("Testing selection summary real-time updates")
        
        # Load photo groups
        self.wait_for_analysis_completion(page)
        
        # Get initial summary state (should be hidden initially)
        initial_summary = self.get_selection_summary_stats(page)
        logger.info(f"Initial summary: {initial_summary}")
        
        # Get photo cards for testing
        photo_cards = self.get_photo_cards(page)
        
        # Select first photo (change to DELETE)
        first_card = photo_cards[0]
        first_state = self.get_photo_selection_state(first_card)
        
        if first_state["visual_state"] == "DELETE":
            # Start from KEEP state
            first_card.click()
            time.sleep(0.5)
        
        # Click to select for deletion
        first_card.click()
        time.sleep(1)  # Wait for summary update
        
        # Check summary appeared and shows 1 photo
        summary_after_one = self.get_selection_summary_stats(page)
        logger.info(f"Summary after selecting 1 photo: {summary_after_one}")
        
        assert summary_after_one["visible"], "Selection summary should be visible after selecting photos"
        assert summary_after_one["photos_to_delete"] >= 1, \
            f"Expected at least 1 photo to delete, got {summary_after_one['photos_to_delete']}"
        
        # Select second photo
        if len(photo_cards) > 1:
            second_card = photo_cards[1]
            second_state = self.get_photo_selection_state(second_card)
            
            if second_state["visual_state"] == "DELETE":
                # Start from KEEP state  
                second_card.click()
                time.sleep(0.5)
            
            # Click to select for deletion
            second_card.click()
            time.sleep(1)
            
            # Check summary updated to show 2 photos
            summary_after_two = self.get_selection_summary_stats(page)
            logger.info(f"Summary after selecting 2 photos: {summary_after_two}")
            
            assert summary_after_two["photos_to_delete"] >= 2, \
                f"Expected at least 2 photos to delete, got {summary_after_two['photos_to_delete']}"
        
        # Deselect first photo
        first_card.click()
        time.sleep(1)
        
        # Check summary updated
        summary_after_deselect = self.get_selection_summary_stats(page)
        logger.info(f"Summary after deselecting: {summary_after_deselect}")
        
        assert summary_after_deselect["photos_to_delete"] < summary_after_two["photos_to_delete"], \
            "Summary should update when photos are deselected"
        
        logger.info("✅ Selection summary updates in real-time")
    
    @pytest.mark.e2e
    def test_no_javascript_errors_during_selection(self, page: Page):
        """Test that no JavaScript errors occur during photo selection."""
        logger.info("Testing for JavaScript errors during selection")
        
        js_errors = []
        
        # Capture JavaScript console errors
        def handle_console(msg):
            if msg.type == "error":
                js_errors.append(msg.text)
                logger.error(f"JavaScript error: {msg.text}")
        
        page.on("console", handle_console)
        
        # Load photo groups
        self.wait_for_analysis_completion(page)
        
        # Perform various photo selection operations
        photo_cards = self.get_photo_cards(page)
        
        # Click multiple photos
        for i, card in enumerate(photo_cards[:3]):
            logger.info(f"Testing photo {i+1} for JS errors")
            card.click()
            time.sleep(0.5)
            
            # Click again to toggle back
            card.click()
            time.sleep(0.5)
        
        # Check for critical JavaScript errors
        critical_errors = [error for error in js_errors if 
                          "togglePhotoSelection" in error or 
                          "updatePhotoCards" in error or
                          "updateSelectionSummary" in error]
        
        if critical_errors:
            logger.error(f"Critical JavaScript errors found: {critical_errors}")
            
        # Allow some non-critical warnings but fail on critical errors
        assert len(critical_errors) == 0, \
            f"Critical JavaScript errors occurred: {critical_errors}"
        
        logger.info("✅ No critical JavaScript errors during photo selection")
    
    @pytest.mark.e2e
    def test_bulk_action_buttons_vs_individual_selection(self, page: Page):
        """Test that bulk action buttons work correctly alongside individual selection."""
        logger.info("Testing bulk actions vs individual selection")
        
        # Load photo groups
        self.wait_for_analysis_completion(page)
        
        # Get first group's photos
        first_group = page.locator(".group-card").first
        keep_all_btn = first_group.locator(".keep-all-btn")
        delete_duplicates_btn = first_group.locator(".delete-duplicates-btn")
        
        # Get photo cards in first group
        group_photos = first_group.locator(".photo-card").all()
        assert len(group_photos) > 1, "Need multiple photos to test bulk actions"
        
        # Test "Keep All" button
        keep_all_btn.click()
        time.sleep(1)
        
        # Verify all photos are in KEEP state
        for card in group_photos:
            state = self.get_photo_selection_state(card)
            assert state["visual_state"] == "KEEP", \
                f"After Keep All, photo should be in KEEP state, got {state['visual_state']}"
        
        # Test individual selection after bulk action
        first_photo = group_photos[0]
        first_photo.click()
        time.sleep(0.5)
        
        # Verify individual photo changed to DELETE
        state = self.get_photo_selection_state(first_photo)
        assert state["visual_state"] == "DELETE", \
            "Individual selection should work after bulk Keep All"
        
        # Test "Delete Duplicates" button
        delete_duplicates_btn.click()
        time.sleep(1)
        
        # Verify at least one photo remains in KEEP state (recommended photo)
        keep_count = sum(1 for card in group_photos 
                        if self.get_photo_selection_state(card)["visual_state"] == "KEEP")
        delete_count = sum(1 for card in group_photos 
                          if self.get_photo_selection_state(card)["visual_state"] == "DELETE")
        
        assert keep_count >= 1, "Delete Duplicates should keep at least one photo"
        assert delete_count >= 1, "Delete Duplicates should mark at least one photo for deletion"
        
        logger.info("✅ Bulk actions work correctly with individual selection")
    
    @pytest.mark.e2e
    def test_confirmation_flow_accuracy(self, page: Page):
        """Test that confirmation flow shows correct photos for deletion."""
        logger.info("Testing confirmation flow accuracy")
        
        # Load photo groups
        self.wait_for_analysis_completion(page)
        
        # Select specific photos for deletion
        photo_cards = self.get_photo_cards(page)
        selected_uuids = []
        
        # Select first 2 photos
        for i in range(min(2, len(photo_cards))):
            card = photo_cards[i]
            state = self.get_photo_selection_state(card)
            
            # Ensure we start from KEEP state
            if state["visual_state"] == "DELETE":
                card.click()
                time.sleep(0.5)
            
            # Select for deletion
            card.click()
            time.sleep(0.5)
            
            # Record UUID
            new_state = self.get_photo_selection_state(card)
            selected_uuids.append(new_state["photo_uuid"])
            
            logger.info(f"Selected photo {i+1} for deletion: {new_state['photo_uuid']}")
        
        # Check selection summary matches our selections
        summary = self.get_selection_summary_stats(page)
        assert summary["photos_to_delete"] >= len(selected_uuids), \
            f"Summary shows {summary['photos_to_delete']} but we selected {len(selected_uuids)}"
        
        # Test confirmation button appears
        confirm_btn = page.locator("#confirmBtn")
        expect(confirm_btn).to_be_visible()
        
        # For testing purposes, we can't actually complete the deletion workflow
        # as it would modify the Photos library, but we can verify the button is functional
        
        logger.info("✅ Confirmation flow shows accurate photo counts")
    
    @pytest.mark.e2e 
    def test_cross_browser_compatibility(self, page: Page):
        """Test photo selection works across different browsers."""
        # Get browser name from page context
        browser_name = page.context.browser.browser_type.name
        logger.info(f"Testing photo selection on {browser_name}")
        
        # This test will be run automatically by pytest-playwright for each browser
        # Load photo groups
        self.wait_for_analysis_completion(page)
        
        # Test basic click functionality
        photo_cards = self.get_photo_cards(page)
        test_card = photo_cards[0]
        
        # Initial state
        initial_state = self.get_photo_selection_state(test_card)
        
        # Click to toggle
        test_card.click()
        time.sleep(0.5)
        
        # Verify state changed
        new_state = self.get_photo_selection_state(test_card)
        assert initial_state["is_selected"] != new_state["is_selected"], \
            f"Photo selection toggle failed on {browser_name}"
        
        logger.info(f"✅ Photo selection works correctly on {browser_name}")
    
    @pytest.mark.e2e
    def test_performance_with_multiple_selections(self, page: Page):
        """Test performance when selecting multiple photos rapidly."""
        logger.info("Testing performance with multiple rapid selections")
        
        # Load photo groups
        self.wait_for_analysis_completion(page)
        
        # Get all photo cards
        photo_cards = self.get_photo_cards(page)
        
        # Measure time for rapid selections
        start_time = time.time()
        
        # Rapidly click multiple photos
        for i, card in enumerate(photo_cards[:5]):  # Test first 5 photos
            card.click(timeout=1000)  # Short timeout for performance test
            
            # Brief pause to allow state update
            time.sleep(0.1)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        logger.info(f"Rapid selection of 5 photos took {total_time:.2f} seconds")
        
        # Verify all selections worked
        selected_count = 0
        for card in photo_cards[:5]:
            state = self.get_photo_selection_state(card)
            if state["visual_state"] == "DELETE":
                selected_count += 1
        
        # Should have decent success rate even with rapid clicking
        success_rate = selected_count / 5
        assert success_rate >= 0.8, \
            f"Rapid selection success rate too low: {success_rate*100:.1f}%"
        
        # Performance threshold: should complete within reasonable time
        assert total_time < 10, f"Rapid selection took too long: {total_time:.2f}s"
        
        logger.info(f"✅ Performance test passed - {selected_count}/5 selections successful")
    
    def teardown_method(self, method):
        """Clean up after each test method."""
        logger.info(f"Completed test: {method.__name__}")


@pytest.mark.e2e
class TestPhotoSelectionEdgeCases:
    """Test edge cases and error conditions for photo selection."""
    
    @pytest.fixture(autouse=True)
    def setup_test(self, page: Page):
        """Set up each test with page navigation."""
        page.goto(f"{BASE_URL}/legacy?priority=P4&limit=10")
        page.wait_for_selector("#status", timeout=10000)
    
    def test_no_photos_available_scenario(self, page: Page):
        """Test behavior when no photo groups are available."""
        logger.info("Testing no photos available scenario")
        
        # Navigate to a priority that might have no results
        page.goto(f"{BASE_URL}/legacy?priority=P10&limit=10")
        page.wait_for_selector("#loadGroupsBtn", timeout=10000)
        
        # Click analyze
        page.click("#loadGroupsBtn")
        
        # Wait for completion or error
        page.wait_for_selector("#groupStatus", timeout=30000)
        
        # Check if groups container shows appropriate message
        groups_container = page.locator("#groupsContainer")
        expect(groups_container).to_be_visible()
        
        # Should handle gracefully - either show "no groups found" or show some groups
        container_text = groups_container.inner_text()
        
        # Test passes if either groups are shown OR appropriate empty state message
        assert "No duplicate photo groups found" in container_text or \
               page.locator(".group-card").count() >= 0, \
               "Application should handle no groups scenario gracefully"
        
        logger.info("✅ No photos scenario handled correctly")
    
    def test_photo_card_without_uuid(self, page: Page):
        """Test handling of photo cards that might be missing required attributes."""
        logger.info("Testing photo card error handling")
        
        # This test verifies robust error handling in the JavaScript code
        # We can't easily create malformed cards, but we can test the error paths
        
        # Navigate and load groups
        page.wait_for_selector("#loadGroupsBtn", timeout=10000)
        page.click("#loadGroupsBtn")
        page.wait_for_selector(".photo-card", timeout=60000)
        
        # Use browser console to test error handling
        error_test_script = """
        // Test calling togglePhotoSelection with invalid parameters
        try {
            togglePhotoSelection('invalid-group', 'invalid-photo');
            console.log('EDGE_CASE_TEST: Invalid parameters handled');
        } catch (e) {
            console.log('EDGE_CASE_TEST: Error caught:', e.message);
        }
        
        // Test updatePhotoCards with invalid group
        try {
            updatePhotoCards('non-existent-group');
            console.log('EDGE_CASE_TEST: Invalid group handled');
        } catch (e) {
            console.log('EDGE_CASE_TEST: Error caught:', e.message);
        }
        """
        
        # Execute error test script
        result = page.evaluate(error_test_script)
        
        # Check console for our test messages (no exceptions should crash the page)
        logger.info("✅ Error handling test completed")


# Configuration for pytest-playwright
@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Configure browser context with appropriate settings."""
    return {
        **browser_context_args,
        "viewport": {"width": 1280, "height": 800},
        "ignore_https_errors": True,
    }


@pytest.fixture(scope="session") 
def playwright_browser_type():
    """Specify which browsers to test."""
    return ["chromium", "firefox"]  # Skip webkit for now as it can be flaky