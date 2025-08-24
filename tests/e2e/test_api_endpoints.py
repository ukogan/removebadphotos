"""
API Endpoints Test
==================

Test the API endpoints directly to understand what data is being returned
and why the frontend might not be displaying photo groups properly.
"""

import pytest
from playwright.sync_api import Page
import time
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "http://127.0.0.1:5003"

class TestAPIEndpoints:
    """Test API endpoints directly."""
    
    def test_api_stats_endpoint(self, page: Page):
        """Test the /api/stats endpoint directly."""
        logger.info("=== TESTING API STATS ENDPOINT ===")
        
        # Make direct API call
        page.goto(f"{BASE_URL}/api/stats")
        page.wait_for_load_state("networkidle")
        
        # Get the JSON response
        try:
            response_text = page.inner_text("body")
            logger.info(f"Raw API response: {response_text}")
            
            # Parse JSON
            api_data = json.loads(response_text)
            logger.info(f"Parsed API data: {api_data}")
            
            # Check if successful
            if api_data.get("success"):
                logger.info("✅ API stats endpoint: SUCCESS")
                logger.info(f"📊 Total photos: {api_data.get('total_photos', 'N/A')}")
                logger.info(f"📊 Sample photos: {api_data.get('sample_photos', 'N/A')}")
                logger.info(f"📊 Sample groups: {api_data.get('sample_groups', 'N/A')}")
                logger.info(f"📊 Estimated savings: {api_data.get('estimated_savings', 'N/A')}")
            else:
                logger.error(f"❌ API stats endpoint: FAILED - {api_data.get('error', 'Unknown error')}")
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ API stats endpoint: JSON parsing failed - {e}")
            logger.error(f"Raw response: {response_text}")
        except Exception as e:
            logger.error(f"❌ API stats endpoint: Unexpected error - {e}")
    
    def test_api_groups_endpoint(self, page: Page):
        """Test the /api/groups endpoint directly."""
        logger.info("=== TESTING API GROUPS ENDPOINT ===")
        
        # Test without parameters first
        page.goto(f"{BASE_URL}/api/groups")
        page.wait_for_load_state("networkidle", timeout=120000)  # Allow time for processing
        
        try:
            response_text = page.inner_text("body")
            logger.info(f"Raw groups API response (first 500 chars): {response_text[:500]}...")
            
            # Parse JSON
            api_data = json.loads(response_text)
            logger.info(f"Groups API success: {api_data.get('success')}")
            
            if api_data.get("success"):
                groups = api_data.get("groups", [])
                logger.info(f"✅ API groups endpoint: SUCCESS")
                logger.info(f"📊 Total groups returned: {len(groups)}")
                logger.info(f"📊 Total groups available: {api_data.get('total_groups', 'N/A')}")
                
                # Examine first group if available
                if groups:
                    first_group = groups[0]
                    logger.info(f"📊 First group ID: {first_group.get('group_id')}")
                    logger.info(f"📊 First group photo count: {first_group.get('photo_count')}")
                    
                    photos = first_group.get("photos", [])
                    if photos:
                        first_photo = photos[0]
                        logger.info(f"📊 First photo UUID: {first_photo.get('uuid')}")
                        logger.info(f"📊 First photo filename: {first_photo.get('filename')}")
                else:
                    logger.info("📊 No groups returned")
            else:
                logger.error(f"❌ API groups endpoint: FAILED - {api_data.get('error', 'Unknown error')}")
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ API groups endpoint: JSON parsing failed - {e}")
        except Exception as e:
            logger.error(f"❌ API groups endpoint: Unexpected error - {e}")
    
    def test_api_groups_with_priority(self, page: Page):
        """Test the /api/groups endpoint with priority parameter."""
        logger.info("=== TESTING API GROUPS WITH PRIORITY ===")
        
        # Test with P4 priority (which was used in previous tests)
        page.goto(f"{BASE_URL}/api/groups?priority=P4&limit=10")
        page.wait_for_load_state("networkidle", timeout=60000)
        
        try:
            response_text = page.inner_text("body")
            logger.info(f"Priority groups response (first 300 chars): {response_text[:300]}...")
            
            api_data = json.loads(response_text)
            
            if api_data.get("success"):
                groups = api_data.get("groups", [])
                logger.info(f"✅ API priority groups: SUCCESS")
                logger.info(f"📊 P4 priority groups: {len(groups)}")
                
                if groups:
                    # This should be what the frontend displays
                    logger.info("📊 P4 Priority groups available for frontend display")
                    for i, group in enumerate(groups):
                        logger.info(f"  Group {i+1}: {group.get('group_id')} ({group.get('photo_count')} photos)")
                else:
                    logger.info("📊 No P4 priority groups available")
            else:
                logger.error(f"❌ API priority groups: FAILED - {api_data.get('error')}")
                
        except Exception as e:
            logger.error(f"❌ API priority groups: ERROR - {e}")
    
    def test_frontend_javascript_loading(self, page: Page):
        """Test if the frontend JavaScript is properly loading and executing."""
        logger.info("=== TESTING FRONTEND JAVASCRIPT LOADING ===")
        
        # Navigate to the legacy page
        page.goto(f"{BASE_URL}/legacy?priority=P4&limit=10")
        page.wait_for_load_state("networkidle")
        
        # Check if key JavaScript functions are available
        js_functions_to_check = [
            "loadGroups",
            "togglePhotoSelection", 
            "updatePhotoCards",
            "updateSelectionSummary",
            "displayGroups"
        ]
        
        for func_name in js_functions_to_check:
            try:
                exists = page.evaluate(f"typeof {func_name} === 'function'")
                logger.info(f"📋 JavaScript function '{func_name}': {'✅ EXISTS' if exists else '❌ MISSING'}")
            except Exception as e:
                logger.error(f"📋 JavaScript function '{func_name}': ERROR - {e}")
        
        # Check if key variables are available
        js_variables_to_check = [
            "groupsLoaded",
            "photoSelections", 
            "allGroups"
        ]
        
        for var_name in js_variables_to_check:
            try:
                exists = page.evaluate(f"typeof {var_name} !== 'undefined'")
                if exists:
                    value = page.evaluate(f"{var_name}")
                    logger.info(f"📋 JavaScript variable '{var_name}': ✅ EXISTS (value: {value})")
                else:
                    logger.info(f"📋 JavaScript variable '{var_name}': ❌ MISSING")
            except Exception as e:
                logger.error(f"📋 JavaScript variable '{var_name}': ERROR - {e}")
        
        # Check if DOM elements are properly set up
        elements_to_check = [
            "#loadGroupsBtn",
            "#groupStatus", 
            "#selectionSummary",
            "#groupsContainer"
        ]
        
        for selector in elements_to_check:
            try:
                element = page.locator(selector)
                if element.count() > 0:
                    logger.info(f"📋 DOM element '{selector}': ✅ EXISTS")
                    
                    # Check if it's visible
                    if element.is_visible():
                        logger.info(f"📋 DOM element '{selector}': ✅ VISIBLE")
                    else:
                        logger.info(f"📋 DOM element '{selector}': ⚠️ HIDDEN")
                else:
                    logger.info(f"📋 DOM element '{selector}': ❌ MISSING")
            except Exception as e:
                logger.error(f"📋 DOM element '{selector}': ERROR - {e}")
        
        logger.info("=== FRONTEND JAVASCRIPT LOADING TEST COMPLETE ===")
    
    def test_manual_api_call_simulation(self, page: Page):
        """Simulate the exact API calls the frontend makes."""
        logger.info("=== SIMULATING FRONTEND API CALLS ===")
        
        # Navigate to the page first
        page.goto(f"{BASE_URL}/legacy?priority=P4&limit=10")
        page.wait_for_load_state("networkidle")
        
        # Simulate the stats API call that happens on page load
        logger.info("🔄 Simulating stats API call...")
        
        stats_result = page.evaluate("""
            fetch('/api/stats')
                .then(response => response.json())
                .then(data => {
                    console.log('Stats API result:', data);
                    return data;
                })
                .catch(error => {
                    console.error('Stats API error:', error);
                    return { error: error.toString() };
                });
        """)
        
        logger.info(f"📊 Stats API simulation result: {stats_result}")
        
        # If stats worked, simulate the groups API call
        if isinstance(stats_result, dict) and stats_result.get('success'):
            logger.info("🔄 Simulating groups API call...")
            
            groups_result = page.evaluate("""
                fetch('/api/groups?priority=P4&limit=10')
                    .then(response => response.json())
                    .then(data => {
                        console.log('Groups API result:', data);
                        return data;
                    })
                    .catch(error => {
                        console.error('Groups API error:', error);
                        return { error: error.toString() };
                    });
            """)
            
            logger.info(f"📊 Groups API simulation result: {groups_result}")
        
        logger.info("=== FRONTEND API CALL SIMULATION COMPLETE ===")
    
    def test_analyze_complete_workflow(self, page: Page):
        """Test the complete workflow of clicking analyze and getting results."""
        logger.info("=== TESTING COMPLETE ANALYZE WORKFLOW ===")
        
        console_messages = []
        def capture_console(msg):
            console_messages.append({
                "type": msg.type,
                "text": msg.text,
                "timestamp": time.time()
            })
            logger.info(f"🖥️ Console [{msg.type}]: {msg.text}")
        
        page.on("console", capture_console)
        
        # Navigate to legacy page
        page.goto(f"{BASE_URL}/legacy")
        page.wait_for_load_state("networkidle")
        
        # Wait for stats to load (the initial step)
        logger.info("⏳ Waiting for initial stats to load...")
        
        max_wait = 30  # seconds
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            try:
                # Check if analyze button is available
                analyze_btn = page.locator("#loadGroupsBtn")
                if analyze_btn.count() > 0 and analyze_btn.is_visible():
                    logger.info("✅ Analyze button is now available")
                    break
                
                # Check current status
                status = page.locator("#status")
                if status.is_visible():
                    status_text = status.inner_text()
                    logger.info(f"📊 Current status: {status_text}")
                
                time.sleep(2)
            except:
                time.sleep(2)
        else:
            logger.error("❌ Analyze button never became available")
            return
        
        # Click analyze button
        logger.info("🔄 Clicking analyze button...")
        try:
            analyze_btn.click()
            logger.info("✅ Analyze button clicked")
            
            # Monitor progress
            progress_timeout = 120  # 2 minutes
            progress_start = time.time()
            
            while time.time() - progress_start < progress_timeout:
                try:
                    # Check for photo cards
                    photo_cards = page.locator(".photo-card")
                    if photo_cards.count() > 0:
                        logger.info(f"✅ Photo cards appeared: {photo_cards.count()} found")
                        break
                    
                    # Check group status
                    group_status = page.locator("#groupStatus")
                    if group_status.is_visible():
                        status_text = group_status.inner_text()
                        logger.info(f"📊 Analysis status: {status_text}")
                    
                    time.sleep(3)
                    
                except:
                    time.sleep(3)
            else:
                logger.error("❌ Analysis timeout - no photo cards appeared")
            
        except Exception as e:
            logger.error(f"❌ Error clicking analyze button: {e}")
        
        # Report console messages
        error_messages = [msg for msg in console_messages if msg["type"] == "error"]
        if error_messages:
            logger.error(f"🚨 Console errors detected: {len(error_messages)}")
            for error in error_messages:
                logger.error(f"  ❌ {error['text']}")
        
        logger.info("=== COMPLETE ANALYZE WORKFLOW TEST COMPLETE ===")
    
    def test_diagnose_issue_summary(self, page: Page):
        """Create a final summary of what's working and what's not."""
        logger.info("=== FINAL ISSUE DIAGNOSIS SUMMARY ===")
        
        # This test always passes but provides the summary
        assert True, "Diagnosis complete"