"""
Current State Analysis Test
==========================

This test examines the current state of the photo deduplication application
to understand exactly what's available and why individual photo selection may not be working.
"""

import pytest
from playwright.sync_api import Page, expect
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "http://127.0.0.1:5003"

class TestCurrentStateAnalysis:
    """Analyze the current state of the application."""
    
    def test_examine_application_current_state(self, page: Page):
        """Examine what's actually present in the application right now."""
        logger.info("=== EXAMINING CURRENT APPLICATION STATE ===")
        
        # Navigate to application
        page.goto(f"{BASE_URL}/legacy")
        page.wait_for_load_state("networkidle", timeout=10000)
        
        logger.info("📋 Page loaded - examining current state...")
        
        # ==== CHECK WHAT'S CURRENTLY VISIBLE ====
        
        # 1. Check if there are any photo groups already loaded
        existing_groups = page.locator(".group-card").all()
        logger.info(f"📊 Existing groups found: {len(existing_groups)}")
        
        existing_photos = page.locator(".photo-card").all()
        logger.info(f"📊 Existing photo cards found: {len(existing_photos)}")
        
        # 2. Check current status
        status_element = page.locator("#status")
        if status_element.is_visible():
            status_text = status_element.inner_text()
            logger.info(f"📊 Current status: {status_text}")
        
        # 3. Check group status
        group_status = page.locator("#groupStatus")
        if group_status.is_visible():
            group_status_text = group_status.inner_text()
            logger.info(f"📊 Group status: {group_status_text}")
        
        # 4. Check if analyze button is ready
        analyze_btn = page.locator("#loadGroupsBtn")
        if analyze_btn.is_visible():
            btn_text = analyze_btn.inner_text()
            btn_disabled = analyze_btn.is_disabled()
            logger.info(f"📊 Analyze button: '{btn_text}' (disabled: {btn_disabled})")
        
        # ==== IF NO PHOTOS, TRY TO LOAD SOME QUICKLY ====
        
        if len(existing_photos) == 0:
            logger.info("🔄 No photos visible - attempting quick load...")
            
            # Try clicking analyze
            if analyze_btn.is_visible() and not analyze_btn.is_disabled():
                analyze_btn.click()
                logger.info("✅ Clicked analyze button")
                
                # Wait a short time to see if anything appears
                time.sleep(5)
                
                # Check again
                quick_photos = page.locator(".photo-card").all()
                logger.info(f"📊 Photos after quick attempt: {len(quick_photos)}")
                
                if len(quick_photos) == 0:
                    # Check if analysis is in progress
                    current_status = ""
                    if group_status.is_visible():
                        current_status = group_status.inner_text()
                    logger.info(f"📊 Analysis status: {current_status}")
                    
                    if "analyzing" in current_status.lower() or "progress" in current_status.lower():
                        logger.info("⏳ Analysis in progress - waiting a bit longer...")
                        time.sleep(10)
                        
                        final_photos = page.locator(".photo-card").all()
                        logger.info(f"📊 Photos after extended wait: {len(final_photos)}")
        
        # ==== EXAMINE WHATEVER PHOTOS ARE AVAILABLE ====
        
        current_photos = page.locator(".photo-card").all()
        
        if len(current_photos) > 0:
            logger.info(f"🎯 ANALYZING {len(current_photos)} AVAILABLE PHOTO CARDS")
            
            # Examine first photo card in detail
            first_photo = current_photos[0]
            
            # Get all attributes
            card_attributes = {
                "class": first_photo.get_attribute("class"),
                "data-group": first_photo.get_attribute("data-group"), 
                "data-photo": first_photo.get_attribute("data-photo"),
                "onclick": first_photo.get_attribute("onclick"),
                "style": first_photo.get_attribute("style")
            }
            
            logger.info(f"📋 First card attributes: {card_attributes}")
            
            # Get HTML structure
            card_html = first_photo.inner_html()
            logger.info(f"📋 First card HTML (first 300 chars): {card_html[:300]}...")
            
            # Check for clickable sub-elements
            selection_areas = first_photo.locator(".photo-selection-area").all()
            thumbnails = first_photo.locator(".photo-thumbnail").all()
            filenames = first_photo.locator(".photo-filename").all()
            
            logger.info(f"📋 Sub-elements: selection_areas={len(selection_areas)}, thumbnails={len(thumbnails)}, filenames={len(filenames)}")
            
            # ==== TEST CLICK BEHAVIORS ====
            
            logger.info("🧪 TESTING CLICK BEHAVIORS...")
            
            # Store initial state
            initial_classes = first_photo.get_attribute("class") or ""
            logger.info(f"📋 Initial classes: {initial_classes}")
            
            # Test 1: Direct card click
            try:
                logger.info("🧪 Test 1: Direct card click")
                first_photo.click()
                time.sleep(1)
                
                new_classes = first_photo.get_attribute("class") or ""
                logger.info(f"📋 After direct click: {new_classes}")
                
                if initial_classes != new_classes:
                    logger.info("✅ Direct click: SUCCESS - classes changed")
                else:
                    logger.info("❌ Direct click: FAILED - no change")
                
            except Exception as e:
                logger.error(f"❌ Direct click: ERROR - {e}")
            
            # Test 2: Selection area click (if exists)
            if len(selection_areas) > 0:
                try:
                    logger.info("🧪 Test 2: Selection area click")
                    pre_click_classes = first_photo.get_attribute("class") or ""
                    selection_areas[0].click()
                    time.sleep(1)
                    
                    post_click_classes = first_photo.get_attribute("class") or ""
                    logger.info(f"📋 After selection area click: {post_click_classes}")
                    
                    if pre_click_classes != post_click_classes:
                        logger.info("✅ Selection area click: SUCCESS - classes changed")
                    else:
                        logger.info("❌ Selection area click: FAILED - no change")
                    
                except Exception as e:
                    logger.error(f"❌ Selection area click: ERROR - {e}")
            
            # Test 3: JavaScript function call
            group_id = first_photo.get_attribute("data-group")
            photo_id = first_photo.get_attribute("data-photo")
            
            if group_id and photo_id:
                try:
                    logger.info("🧪 Test 3: JavaScript function call")
                    
                    # Check if function exists
                    func_exists = page.evaluate("typeof togglePhotoSelection === 'function'")
                    logger.info(f"📋 togglePhotoSelection function exists: {func_exists}")
                    
                    if func_exists:
                        pre_js_classes = first_photo.get_attribute("class") or ""
                        
                        # Call function
                        page.evaluate(f"togglePhotoSelection('{group_id}', '{photo_id}')")
                        time.sleep(1)
                        
                        post_js_classes = first_photo.get_attribute("class") or ""
                        logger.info(f"📋 After JS function call: {post_js_classes}")
                        
                        if pre_js_classes != post_js_classes:
                            logger.info("✅ JS function call: SUCCESS - classes changed")
                        else:
                            logger.info("❌ JS function call: FAILED - no change")
                    else:
                        logger.info("❌ JS function call: FAILED - function not found")
                        
                        # List available functions
                        available_functions = page.evaluate("""
                            Object.getOwnPropertyNames(window).filter(name => 
                                typeof window[name] === 'function' && name.includes('Photo')
                            )
                        """)
                        logger.info(f"📋 Available photo-related functions: {available_functions}")
                    
                except Exception as e:
                    logger.error(f"❌ JS function call: ERROR - {e}")
            
            # ==== CHECK SELECTION SUMMARY ====
            
            logger.info("🧪 CHECKING SELECTION SUMMARY...")
            
            summary_element = page.locator("#selectionSummary")
            if summary_element.is_visible():
                summary_text = summary_element.inner_text()
                logger.info(f"📋 Selection summary visible: {summary_text[:200]}...")
            else:
                logger.info("📋 Selection summary not visible")
            
            # ==== CHECK FOR JAVASCRIPT ERRORS ====
            
            logger.info("🧪 CHECKING FOR JAVASCRIPT ERRORS...")
            
            # Monitor console for a moment
            console_errors = []
            def handle_console(msg):
                if msg.type == "error":
                    console_errors.append(msg.text)
                    logger.error(f"🚨 Console error: {msg.text}")
            
            page.on("console", handle_console)
            
            # Try another click to trigger any errors
            try:
                first_photo.click()
                time.sleep(2)
            except:
                pass
            
            logger.info(f"📋 Total console errors detected: {len(console_errors)}")
            
        else:
            logger.info("❌ NO PHOTO CARDS AVAILABLE FOR ANALYSIS")
            
            # Check what's preventing photos from loading
            final_status = ""
            if group_status.is_visible():
                final_status = group_status.inner_text()
            
            container_content = page.locator("#groupsContainer").inner_text() if page.locator("#groupsContainer").is_visible() else ""
            
            logger.info(f"📋 Final group status: {final_status}")
            logger.info(f"📋 Groups container content: {container_content[:200]}...")
        
        logger.info("=== CURRENT STATE ANALYSIS COMPLETE ===")
        
        # Always pass this test since it's just for analysis
        assert True, "Analysis complete"