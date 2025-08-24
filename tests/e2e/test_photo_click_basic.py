"""
Focused Test for Individual Photo Click Issues
==============================================

This test suite specifically targets the reported issue:
"it's still not possible to select individual photos 1 by 1 for deletion."

Simplified test approach to identify root cause.
"""

import pytest
from playwright.sync_api import Page, expect
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "http://127.0.0.1:5003"

class TestPhotoClickBasic:
    """Basic tests focused on photo clicking functionality."""
    
    @pytest.fixture(autouse=True)
    def setup_test(self, page: Page):
        """Navigate to application and wait for basic loading."""
        logger.info("Setting up basic test")
        page.goto(f"{BASE_URL}/legacy?priority=P4&limit=10")
        page.wait_for_load_state("networkidle", timeout=10000)
        logger.info("Page loaded")
    
    def test_page_loads_with_analyze_button(self, page: Page):
        """Verify the page loads and analyze button is available."""
        logger.info("Testing page loads with analyze button")
        
        # Check analyze button exists
        analyze_btn = page.locator("#loadGroupsBtn")
        expect(analyze_btn).to_be_visible()
        
        button_text = analyze_btn.inner_text()
        logger.info(f"Analyze button text: {button_text}")
        
        assert "Analyze" in button_text
        logger.info("✅ Page loads with analyze button")
    
    def test_analyze_button_triggers_loading(self, page: Page):
        """Test that clicking analyze button triggers photo loading."""
        logger.info("Testing analyze button functionality")
        
        # Click analyze button
        analyze_btn = page.locator("#loadGroupsBtn")
        analyze_btn.click()
        
        # Wait a bit for loading to start
        time.sleep(2)
        
        # Check status changed to indicate loading
        status = page.locator("#groupStatus")
        expect(status).to_be_visible()
        
        status_text = status.inner_text()
        logger.info(f"Status after clicking analyze: {status_text}")
        
        # Should show some loading indication
        assert any(word in status_text.lower() for word in ["analyzing", "loading", "progress", "complete"]), \
            f"Expected loading status, got: {status_text}"
        
        logger.info("✅ Analyze button triggers loading")
    
    def test_wait_for_photo_groups_minimal(self, page: Page):
        """Wait for photo groups to load (with reasonable timeout)."""
        logger.info("Testing photo groups loading (minimal wait)")
        
        # Click analyze
        analyze_btn = page.locator("#loadGroupsBtn")
        analyze_btn.click()
        
        # Wait for either photo groups OR error message (up to 60 seconds)
        logger.info("Waiting for photo groups or error...")
        
        try:
            # Wait for either photo cards or error message
            page.wait_for_function("""
                () => {
                    // Check if photo cards loaded
                    const photoCards = document.querySelectorAll('.photo-card');
                    if (photoCards.length > 0) return true;
                    
                    // Check if there's an error message
                    const status = document.getElementById('groupStatus');
                    if (status && status.innerText.includes('Error')) return true;
                    
                    // Check if analysis completed without results
                    if (status && status.innerText.includes('Analysis Complete')) return true;
                    
                    return false;
                }
            """, timeout=60000)
            
            logger.info("Photo analysis completed (success or error)")
            
        except Exception as e:
            logger.error(f"Timeout waiting for analysis: {e}")
            
            # Get current status for debugging
            status = page.locator("#groupStatus")
            if status.is_visible():
                current_status = status.inner_text()
                logger.error(f"Current status: {current_status}")
            
            raise
        
        logger.info("✅ Photo analysis completed (within timeout)")
    
    def test_identify_clickable_elements(self, page: Page):
        """Identify what elements are actually clickable for photo selection."""
        logger.info("Identifying clickable elements for photo selection")
        
        # Load groups first
        analyze_btn = page.locator("#loadGroupsBtn")
        analyze_btn.click()
        
        # Wait for some content
        time.sleep(10)  # Fixed wait to see what loads
        
        # Check what photo-related elements exist
        photo_cards = page.locator(".photo-card").all()
        logger.info(f"Found {len(photo_cards)} photo cards")
        
        # Check for selection areas
        selection_areas = page.locator(".photo-selection-area").all()
        logger.info(f"Found {len(selection_areas)} selection areas")
        
        # Check for any clickable photo elements
        clickable_photos = page.locator(".photo-card[onclick], .photo-card .photo-selection-area, .photo-thumbnail[onclick]").all()
        logger.info(f"Found {len(clickable_photos)} elements with click handlers")
        
        if len(photo_cards) > 0:
            # Examine first photo card structure
            first_card = photo_cards[0]
            card_html = first_card.inner_html()
            logger.info(f"First photo card HTML structure: {card_html[:200]}...")
            
            # Check attributes
            card_attrs = {
                "class": first_card.get_attribute("class"),
                "data-group": first_card.get_attribute("data-group"),
                "data-photo": first_card.get_attribute("data-photo"),
                "onclick": first_card.get_attribute("onclick")
            }
            logger.info(f"First card attributes: {card_attrs}")
            
        logger.info("✅ Identified clickable elements")
    
    def test_attempt_photo_click_different_methods(self, page: Page):
        """Try different methods to click on photos and observe behavior."""
        logger.info("Testing different photo click methods")
        
        # Load groups
        analyze_btn = page.locator("#loadGroupsBtn")
        analyze_btn.click()
        time.sleep(10)
        
        photo_cards = page.locator(".photo-card").all()
        
        if len(photo_cards) == 0:
            logger.warning("No photo cards found - skipping click tests")
            return
        
        logger.info(f"Testing clicks on {len(photo_cards)} photo cards")
        
        first_card = photo_cards[0]
        
        # Method 1: Direct card click
        logger.info("Method 1: Clicking photo card directly")
        try:
            # Get initial classes
            initial_classes = first_card.get_attribute("class") or ""
            logger.info(f"Initial classes: {initial_classes}")
            
            # Click the card
            first_card.click()
            time.sleep(1)
            
            # Check for changes
            new_classes = first_card.get_attribute("class") or ""
            logger.info(f"After click classes: {new_classes}")
            
            if initial_classes != new_classes:
                logger.info("✅ Direct card click changed classes")
            else:
                logger.warning("⚠️ Direct card click did not change classes")
                
        except Exception as e:
            logger.error(f"Direct card click failed: {e}")
        
        # Method 2: Click selection area
        logger.info("Method 2: Clicking photo selection area")
        try:
            selection_area = first_card.locator(".photo-selection-area")
            if selection_area.count() > 0:
                initial_classes = first_card.get_attribute("class") or ""
                selection_area.click()
                time.sleep(1)
                new_classes = first_card.get_attribute("class") or ""
                
                if initial_classes != new_classes:
                    logger.info("✅ Selection area click changed classes")
                else:
                    logger.warning("⚠️ Selection area click did not change classes")
            else:
                logger.info("No selection area found")
                
        except Exception as e:
            logger.error(f"Selection area click failed: {e}")
        
        # Method 3: JavaScript click
        logger.info("Method 3: Attempting JavaScript-based click")
        try:
            # Get photo and group IDs
            group_id = first_card.get_attribute("data-group")
            photo_id = first_card.get_attribute("data-photo")
            
            if group_id and photo_id:
                logger.info(f"Calling togglePhotoSelection('{group_id}', '{photo_id}')")
                
                # Call the JavaScript function directly
                result = page.evaluate(f"togglePhotoSelection('{group_id}', '{photo_id}')")
                logger.info(f"JavaScript function result: {result}")
                
                time.sleep(1)
                final_classes = first_card.get_attribute("class") or ""
                logger.info(f"After JS click classes: {final_classes}")
                
            else:
                logger.warning("Missing group_id or photo_id attributes")
                
        except Exception as e:
            logger.error(f"JavaScript click failed: {e}")
        
        logger.info("✅ Completed different click method tests")
    
    def test_console_errors_during_interaction(self, page: Page):
        """Monitor console for errors during photo interactions."""
        logger.info("Monitoring console errors during photo interaction")
        
        console_messages = []
        
        def handle_console(msg):
            console_messages.append({
                "type": msg.type,
                "text": msg.text,
                "location": msg.location
            })
            if msg.type == "error":
                logger.error(f"Console error: {msg.text}")
        
        page.on("console", handle_console)
        
        # Load groups and try interactions
        analyze_btn = page.locator("#loadGroupsBtn")
        analyze_btn.click()
        time.sleep(10)
        
        # Try clicking photos
        photo_cards = page.locator(".photo-card").all()
        
        if len(photo_cards) > 0:
            try:
                first_card = photo_cards[0]
                first_card.click()
                time.sleep(1)
            except Exception as e:
                logger.error(f"Click failed with exception: {e}")
        
        # Report console messages
        error_messages = [msg for msg in console_messages if msg["type"] == "error"]
        warning_messages = [msg for msg in console_messages if msg["type"] == "warning"]
        
        logger.info(f"Found {len(error_messages)} console errors")
        logger.info(f"Found {len(warning_messages)} console warnings")
        
        for error in error_messages:
            logger.error(f"Console error: {error['text']}")
        
        logger.info("✅ Console monitoring completed")
        
        # Return results for analysis
        return {
            "error_count": len(error_messages),
            "warning_count": len(warning_messages),
            "errors": error_messages
        }