"""
Comprehensive Photo Selection Diagnosis Test
============================================

This test diagnoses the specific issue: "it's still not possible to select individual photos 1 by 1 for deletion."
Uses the pre-analyzed photo groups to focus on selection functionality.
"""

import pytest
from playwright.sync_api import Page, expect
import time
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "http://127.0.0.1:5003"

class TestPhotoSelectionDiagnosis:
    """Comprehensive diagnosis of photo selection functionality."""
    
    def test_end_to_end_photo_selection_diagnosis(self, page: Page):
        """Complete end-to-end diagnosis of photo selection functionality."""
        logger.info("=== STARTING COMPREHENSIVE PHOTO SELECTION DIAGNOSIS ===")
        
        # Initialize results dictionary
        diagnosis_results = {
            "page_load": {"success": False, "details": []},
            "photo_groups": {"success": False, "details": []},
            "clickable_elements": {"success": False, "details": []},
            "click_functionality": {"success": False, "details": []},
            "visual_feedback": {"success": False, "details": []},
            "selection_summary": {"success": False, "details": []},
            "javascript_errors": [],
            "recommendations": []
        }
        
        # Capture all console messages
        console_messages = []
        def handle_console(msg):
            console_messages.append({
                "type": msg.type,
                "text": msg.text,
                "timestamp": time.time()
            })
            if msg.type == "error":
                logger.error(f"Console error: {msg.text}")
                diagnosis_results["javascript_errors"].append(msg.text)
        
        page.on("console", handle_console)
        
        # ==== PHASE 1: PAGE LOADING ====
        logger.info("Phase 1: Testing page loading")
        try:
            page.goto(f"{BASE_URL}/legacy?priority=P4&limit=10")
            page.wait_for_load_state("networkidle", timeout=15000)
            
            # Check basic page elements
            header = page.locator("h1")
            expect(header).to_contain_text("Photo Deduplication Tool")
            
            analyze_btn = page.locator("#loadGroupsBtn")
            expect(analyze_btn).to_be_visible()
            
            diagnosis_results["page_load"]["success"] = True
            diagnosis_results["page_load"]["details"].append("✅ Page loaded successfully")
            diagnosis_results["page_load"]["details"].append("✅ Header and analyze button present")
            
            logger.info("✅ Page loading: SUCCESS")
            
        except Exception as e:
            diagnosis_results["page_load"]["details"].append(f"❌ Page loading failed: {e}")
            logger.error(f"❌ Page loading: FAILED - {e}")
        
        # ==== PHASE 2: PHOTO GROUPS LOADING ====
        logger.info("Phase 2: Testing photo groups loading")
        try:
            # Click analyze button
            analyze_btn = page.locator("#loadGroupsBtn")
            analyze_btn.click()
            
            # Wait for analysis with progress monitoring
            logger.info("Monitoring analysis progress...")
            max_wait_time = 90  # seconds
            start_time = time.time()
            
            while time.time() - start_time < max_wait_time:
                try:
                    # Check if photos loaded
                    photo_cards = page.locator(".photo-card").all()
                    if len(photo_cards) > 0:
                        diagnosis_results["photo_groups"]["success"] = True
                        diagnosis_results["photo_groups"]["details"].append(f"✅ Found {len(photo_cards)} photo cards")
                        logger.info(f"✅ Photo groups: SUCCESS - {len(photo_cards)} photos loaded")
                        break
                    
                    # Check for completion without results
                    status_element = page.locator("#groupStatus")
                    if status_element.is_visible():
                        status_text = status_element.inner_text()
                        if "Complete" in status_text or "No duplicate photo groups found" in status_text:
                            diagnosis_results["photo_groups"]["success"] = False
                            diagnosis_results["photo_groups"]["details"].append(f"⚠️ Analysis completed but no photos found: {status_text}")
                            logger.warning(f"⚠️ Photo groups: NO PHOTOS - {status_text}")
                            break
                    
                    time.sleep(2)
                    
                except Exception:
                    time.sleep(2)
                    continue
            else:
                # Timeout reached
                status_element = page.locator("#groupStatus")
                current_status = "Unknown"
                if status_element.is_visible():
                    current_status = status_element.inner_text()
                
                diagnosis_results["photo_groups"]["details"].append(f"❌ Analysis timeout after {max_wait_time}s. Status: {current_status}")
                logger.error(f"❌ Photo groups: TIMEOUT - Status: {current_status}")
                
        except Exception as e:
            diagnosis_results["photo_groups"]["details"].append(f"❌ Photo groups loading failed: {e}")
            logger.error(f"❌ Photo groups: FAILED - {e}")
        
        # ==== PHASE 3: CLICKABLE ELEMENTS ANALYSIS ====
        logger.info("Phase 3: Analyzing clickable elements")
        try:
            photo_cards = page.locator(".photo-card").all()
            
            if len(photo_cards) == 0:
                diagnosis_results["clickable_elements"]["details"].append("❌ No photo cards found to analyze")
                logger.error("❌ Clickable elements: NO CARDS")
            else:
                # Analyze first photo card structure
                first_card = photo_cards[0]
                
                # Get card attributes
                card_attributes = {
                    "class": first_card.get_attribute("class") or "",
                    "data-group": first_card.get_attribute("data-group"),
                    "data-photo": first_card.get_attribute("data-photo"),
                    "onclick": first_card.get_attribute("onclick")
                }
                
                diagnosis_results["clickable_elements"]["details"].append(f"📋 Card attributes: {card_attributes}")
                
                # Check for selection area
                selection_areas = first_card.locator(".photo-selection-area").all()
                diagnosis_results["clickable_elements"]["details"].append(f"📋 Selection areas found: {len(selection_areas)}")
                
                # Check HTML structure
                card_html = first_card.inner_html()[:500]  # First 500 chars
                diagnosis_results["clickable_elements"]["details"].append(f"📋 Card HTML structure: {card_html}...")
                
                diagnosis_results["clickable_elements"]["success"] = True
                logger.info(f"✅ Clickable elements: SUCCESS - Analyzed {len(photo_cards)} cards")
                
        except Exception as e:
            diagnosis_results["clickable_elements"]["details"].append(f"❌ Clickable elements analysis failed: {e}")
            logger.error(f"❌ Clickable elements: FAILED - {e}")
        
        # ==== PHASE 4: CLICK FUNCTIONALITY TESTING ====
        logger.info("Phase 4: Testing click functionality")
        try:
            photo_cards = page.locator(".photo-card").all()
            
            if len(photo_cards) == 0:
                diagnosis_results["click_functionality"]["details"].append("❌ No photo cards available for click testing")
            else:
                first_card = photo_cards[0]
                
                # Test Method 1: Direct card click
                logger.info("Testing direct card click...")
                initial_classes = first_card.get_attribute("class") or ""
                
                try:
                    first_card.click()
                    time.sleep(1)
                    
                    new_classes = first_card.get_attribute("class") or ""
                    
                    if initial_classes != new_classes:
                        diagnosis_results["click_functionality"]["details"].append("✅ Direct card click: Classes changed")
                        diagnosis_results["click_functionality"]["success"] = True
                    else:
                        diagnosis_results["click_functionality"]["details"].append("⚠️ Direct card click: No class changes")
                    
                except Exception as e:
                    diagnosis_results["click_functionality"]["details"].append(f"❌ Direct card click failed: {e}")
                
                # Test Method 2: Selection area click
                logger.info("Testing selection area click...")
                selection_areas = first_card.locator(".photo-selection-area").all()
                
                if len(selection_areas) > 0:
                    try:
                        pre_click_classes = first_card.get_attribute("class") or ""
                        selection_areas[0].click()
                        time.sleep(1)
                        
                        post_click_classes = first_card.get_attribute("class") or ""
                        
                        if pre_click_classes != post_click_classes:
                            diagnosis_results["click_functionality"]["details"].append("✅ Selection area click: Classes changed")
                            diagnosis_results["click_functionality"]["success"] = True
                        else:
                            diagnosis_results["click_functionality"]["details"].append("⚠️ Selection area click: No class changes")
                        
                    except Exception as e:
                        diagnosis_results["click_functionality"]["details"].append(f"❌ Selection area click failed: {e}")
                else:
                    diagnosis_results["click_functionality"]["details"].append("ℹ️ No selection areas found to test")
                
                # Test Method 3: JavaScript function call
                logger.info("Testing JavaScript function call...")
                group_id = first_card.get_attribute("data-group")
                photo_id = first_card.get_attribute("data-photo")
                
                if group_id and photo_id:
                    try:
                        # Check if function exists
                        function_exists = page.evaluate("typeof togglePhotoSelection === 'function'")
                        
                        if function_exists:
                            pre_js_classes = first_card.get_attribute("class") or ""
                            
                            # Call the JavaScript function
                            page.evaluate(f"togglePhotoSelection('{group_id}', '{photo_id}')")
                            time.sleep(1)
                            
                            post_js_classes = first_card.get_attribute("class") or ""
                            
                            if pre_js_classes != post_js_classes:
                                diagnosis_results["click_functionality"]["details"].append("✅ JavaScript function: Classes changed")
                                diagnosis_results["click_functionality"]["success"] = True
                            else:
                                diagnosis_results["click_functionality"]["details"].append("⚠️ JavaScript function: No class changes")
                        else:
                            diagnosis_results["click_functionality"]["details"].append("❌ togglePhotoSelection function not found")
                        
                    except Exception as e:
                        diagnosis_results["click_functionality"]["details"].append(f"❌ JavaScript function call failed: {e}")
                else:
                    diagnosis_results["click_functionality"]["details"].append("❌ Missing data-group or data-photo attributes")
                
                logger.info("✅ Click functionality testing completed")
                
        except Exception as e:
            diagnosis_results["click_functionality"]["details"].append(f"❌ Click functionality testing failed: {e}")
            logger.error(f"❌ Click functionality: FAILED - {e}")
        
        # ==== PHASE 5: VISUAL FEEDBACK TESTING ====
        logger.info("Phase 5: Testing visual feedback")
        try:
            photo_cards = page.locator(".photo-card").all()
            
            if len(photo_cards) > 0:
                first_card = photo_cards[0]
                
                # Check current visual state
                current_classes = first_card.get_attribute("class") or ""
                is_selected = "selected" in current_classes
                
                # Check for visual indicators
                computed_styles = first_card.evaluate("""
                    (element) => {
                        const styles = window.getComputedStyle(element);
                        return {
                            borderColor: styles.borderColor,
                            backgroundColor: styles.backgroundColor,
                            opacity: styles.opacity
                        };
                    }
                """)
                
                diagnosis_results["visual_feedback"]["details"].append(f"📋 Current state: {'SELECTED (DELETE)' if is_selected else 'UNSELECTED (KEEP)'}")
                diagnosis_results["visual_feedback"]["details"].append(f"📋 Visual styles: {computed_styles}")
                
                # Check for pseudo-elements (badges)
                has_keep_badge = "not(.selected)" in page.evaluate("""
                    () => {
                        const styles = getComputedStyle(document.querySelector('.photo-card:not(.selected)'), '::after');
                        return styles ? styles.content : '';
                    }
                """) if not is_selected else False
                
                diagnosis_results["visual_feedback"]["details"].append(f"📋 Keep badge visible: {has_keep_badge}")
                diagnosis_results["visual_feedback"]["success"] = True
                
                logger.info("✅ Visual feedback: SUCCESS")
                
        except Exception as e:
            diagnosis_results["visual_feedback"]["details"].append(f"❌ Visual feedback testing failed: {e}")
            logger.error(f"❌ Visual feedback: FAILED - {e}")
        
        # ==== PHASE 6: SELECTION SUMMARY TESTING ====
        logger.info("Phase 6: Testing selection summary")
        try:
            # Check if selection summary exists
            summary_element = page.locator("#selectionSummary")
            
            if summary_element.is_visible():
                summary_text = summary_element.inner_text()
                diagnosis_results["selection_summary"]["details"].append(f"✅ Selection summary visible: {summary_text[:200]}...")
                diagnosis_results["selection_summary"]["success"] = True
            else:
                diagnosis_results["selection_summary"]["details"].append("ℹ️ Selection summary not visible (may appear after selections)")
            
            logger.info("✅ Selection summary: CHECKED")
            
        except Exception as e:
            diagnosis_results["selection_summary"]["details"].append(f"❌ Selection summary testing failed: {e}")
            logger.error(f"❌ Selection summary: FAILED - {e}")
        
        # ==== PHASE 7: GENERATE RECOMMENDATIONS ====
        logger.info("Phase 7: Generating recommendations")
        
        # Analyze results and generate recommendations
        if not diagnosis_results["photo_groups"]["success"]:
            diagnosis_results["recommendations"].append("🔧 CRITICAL: Photo groups are not loading properly. Check backend analysis process.")
        
        if not diagnosis_results["click_functionality"]["success"]:
            diagnosis_results["recommendations"].append("🔧 HIGH: Photo click functionality is not working. Check JavaScript event handlers.")
        
        if len(diagnosis_results["javascript_errors"]) > 0:
            diagnosis_results["recommendations"].append(f"🔧 HIGH: {len(diagnosis_results['javascript_errors'])} JavaScript errors found. Fix console errors.")
        
        if diagnosis_results["clickable_elements"]["success"] and not diagnosis_results["click_functionality"]["success"]:
            diagnosis_results["recommendations"].append("🔧 MEDIUM: Elements exist but clicks don't work. Check event binding and CSS pointer-events.")
        
        # ==== FINAL REPORT ====
        logger.info("=== PHOTO SELECTION DIAGNOSIS COMPLETE ===")
        logger.info("RESULTS SUMMARY:")
        for phase, result in diagnosis_results.items():
            if isinstance(result, dict) and "success" in result:
                status = "✅ PASS" if result["success"] else "❌ FAIL"
                logger.info(f"  {phase}: {status}")
        
        logger.info("DETAILED FINDINGS:")
        for phase, result in diagnosis_results.items():
            if isinstance(result, dict) and "details" in result:
                for detail in result["details"]:
                    logger.info(f"  {detail}")
        
        if diagnosis_results["javascript_errors"]:
            logger.info("JAVASCRIPT ERRORS:")
            for error in diagnosis_results["javascript_errors"]:
                logger.info(f"  ❌ {error}")
        
        logger.info("RECOMMENDATIONS:")
        for rec in diagnosis_results["recommendations"]:
            logger.info(f"  {rec}")
        
        # Save detailed report
        report_data = {
            "timestamp": time.time(),
            "diagnosis_results": diagnosis_results,
            "console_messages": console_messages
        }
        
        # Assert overall success for pytest
        critical_phases = ["page_load", "photo_groups", "clickable_elements"]
        critical_success = all(diagnosis_results[phase]["success"] for phase in critical_phases)
        
        if not critical_success:
            pytest.fail(f"Critical diagnosis phases failed. See detailed report above.")
        
        logger.info("=== DIAGNOSIS TEST COMPLETED SUCCESSFULLY ===")


# Configuration for this test file
@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {
        **browser_context_args,
        "viewport": {"width": 1280, "height": 800},
        "ignore_https_errors": True,
        "record_video_dir": "tests/videos"  # Record video for diagnosis
    }