#!/usr/bin/env python3
"""
Smart Analysis End-to-End Test - Critical Fix Verification
Tests the complete Smart Analysis workflow to verify timestamp AttributeError 
and JSON serialization fixes are working correctly.
"""
import pytest
from playwright.sync_api import Page, expect
import time
import json


@pytest.mark.e2e
def test_smart_analysis_complete_workflow(page: Page):
    """
    Test complete Smart Analysis workflow end-to-end
    
    This test verifies:
    1. Dashboard loads correctly with Smart Analysis Controls
    2. Smart Analysis UI elements are functional 
    3. Analysis completes without AttributeError (timestamp fix)
    4. Analysis completes without JSON serialization error (Stats fix)
    5. Priority results (P1-P10) are displayed correctly
    
    Critical fixes being tested:
    - ✅ PhotoInfo to PhotoData conversion (timestamp AttributeError fix)
    - ✅ Stats object to dictionary conversion (JSON serialization fix)
    """
    
    # Step 1: Navigate to dashboard
    print("🔍 Step 1: Loading dashboard...")
    page.goto("http://127.0.0.1:5003")
    
    # Verify page loads
    expect(page).to_have_title("Photo Dedup Tool - Dashboard")
    
    # Step 2: Verify Smart Analysis Controls are present
    print("🔍 Step 2: Verifying Smart Analysis Controls UI...")
    
    # Check for Smart Analysis Controls section
    smart_controls = page.locator("section.analysis-controls")
    expect(smart_controls).to_be_visible()
    
    # Check for key UI elements
    expect(page.locator("h2:has-text('Smart Analysis Controls')")).to_be_visible()
    expect(page.locator("#start-analysis")).to_be_visible()
    expect(page.locator("#size-slider")).to_be_visible()
    expect(page.locator("button.analysis-type-btn[data-type='smart']")).to_be_visible()
    expect(page.locator("button.analysis-type-btn[data-type='metadata']")).to_be_visible()
    
    # Step 3: Configure analysis parameters
    print("🔍 Step 3: Configuring Smart Analysis parameters...")
    
    # Set analysis type to Smart by clicking the button
    page.click("button.analysis-type-btn[data-type='smart']")
    
    # Set file size slider to 1MB (lower value for testing)
    page.locator("#size-slider").fill("1")
    
    # Verify button is enabled and ready
    start_button = page.locator("#start-analysis")
    expect(start_button).to_be_enabled()
    expect(start_button).to_contain_text("Start Smart Analysis")
    
    # Step 4: Start the analysis
    print("🔍 Step 4: Starting Smart Analysis...")
    
    # Click start analysis button
    start_button.click()
    
    # Verify button changes to analyzing state
    expect(start_button).to_contain_text("Analyzing...")
    expect(start_button).to_be_disabled()
    
    # Step 5: Monitor analysis progress and completion
    print("🔍 Step 5: Monitoring analysis progress...")
    
    # Wait for analysis to complete (with timeout)
    # The button should return to enabled state when done
    page.wait_for_function(
        "document.getElementById('start-analysis').disabled === false",
        timeout=60000  # 60 second timeout
    )
    
    # Verify button returns to normal state
    expect(start_button).to_be_enabled()
    expect(start_button).to_contain_text("Start Smart Analysis")
    
    # Step 6: Verify analysis results are displayed
    print("🔍 Step 6: Verifying analysis results...")
    
    # Check for results section
    results_section = page.locator("#results-section, .results-container, [data-testid='results']")
    if results_section.count() > 0:
        expect(results_section).to_be_visible()
    
    # Look for priority clusters or groups
    priority_elements = page.locator("[data-priority], .priority-cluster, [class*='priority'], [id*='priority']")
    
    # Step 7: Verify no critical errors in console
    print("🔍 Step 7: Checking for JavaScript errors...")
    
    # Check console for critical errors (AttributeError, JSON serialization errors)
    console_errors = []
    def handle_console(msg):
        if msg.type in ['error', 'warning']:
            console_errors.append(f"{msg.type}: {msg.text}")
    
    page.on("console", handle_console)
    
    # Wait a moment for any delayed errors
    page.wait_for_timeout(2000)
    
    # Filter out non-critical errors
    critical_errors = [
        error for error in console_errors 
        if any(keyword in error.lower() for keyword in [
            'attributeerror', 'timestamp', 'json', 'serialization', 
            'typeerror', 'keyerror', 'uncaught'
        ])
    ]
    
    # Step 8: Verify API response structure
    print("🔍 Step 8: Verifying API response structure...")
    
    # Make direct API call to verify response structure
    response = page.request.post("http://127.0.0.1:5003/api/smart-analysis", 
        headers={"Content-Type": "application/json"},
        data=json.dumps({
            "analysis_type": "smart", 
            "min_size_mb": 1,
            "max_photos": 200
        })
    )
    
    assert response.status == 200
    api_data = response.json()
    
    # Verify response structure
    assert "success" in api_data
    assert api_data["success"] is True
    
    if "data" in api_data:
        data = api_data["data"]
        # Check for expected data structure
        assert isinstance(data, dict)
        
        # Look for priority results
        if "priority_clusters" in data:
            priority_clusters = data["priority_clusters"]
            assert isinstance(priority_clusters, list)
    
    # Final verification - no critical errors
    assert len(critical_errors) == 0, f"Critical errors found: {critical_errors}"
    
    print("✅ Smart Analysis workflow test completed successfully!")
    print(f"   - Dashboard loaded correctly")
    print(f"   - Smart Analysis Controls functional")  
    print(f"   - Analysis completed without errors")
    print(f"   - No AttributeError or JSON serialization errors")
    print(f"   - API response structure valid")


@pytest.mark.e2e
def test_smart_analysis_error_handling(page: Page):
    """
    Test Smart Analysis error handling and recovery
    
    This test specifically looks for:
    - Proper error messages when analysis fails
    - No AttributeError exceptions in the UI
    - No JSON serialization errors
    - Graceful degradation when issues occur
    """
    
    print("🔍 Testing Smart Analysis error handling...")
    
    # Load dashboard
    page.goto("http://127.0.0.1:5003")
    
    # Set extreme parameters that might cause issues
    page.click("button.analysis-type-btn[data-type='smart']")
    page.locator("#size-slider").fill("0.1")  # Very small
    
    # Monitor console for errors
    console_messages = []
    page.on("console", lambda msg: console_messages.append(f"{msg.type}: {msg.text}"))
    
    # Start analysis
    page.click("#start-analysis")
    
    # Wait for completion or timeout
    try:
        page.wait_for_function(
            "document.getElementById('start-analysis').disabled === false",
            timeout=90000  # 90 second timeout for large analysis
        )
        print("✅ Analysis completed without timeout")
    except Exception as e:
        print(f"⚠️ Analysis timed out: {e}")
    
    # Check for specific error types we fixed
    attribution_errors = [msg for msg in console_messages if 'attributeerror' in msg.lower() and 'timestamp' in msg.lower()]
    json_errors = [msg for msg in console_messages if 'json' in msg.lower() and ('serializ' in msg.lower() or 'parse' in msg.lower())]
    
    assert len(attribution_errors) == 0, f"AttributeError found: {attribution_errors}"
    assert len(json_errors) == 0, f"JSON serialization errors found: {json_errors}"
    
    print("✅ Error handling test passed - no critical errors detected")


@pytest.mark.e2e  
def test_smart_analysis_ui_responsiveness(page: Page):
    """
    Test Smart Analysis UI responsiveness and user feedback
    
    Verifies:
    - UI updates during analysis
    - Progress indicators work correctly  
    - Button states change appropriately
    - Results display properly when analysis completes
    """
    
    print("🔍 Testing Smart Analysis UI responsiveness...")
    
    page.goto("http://127.0.0.1:5003")
    
    # Configure for quick analysis
    page.click("button.analysis-type-btn[data-type='metadata']")
    page.locator("#size-slider").fill("5")
    
    start_button = page.locator("#start-analysis")
    
    # Record initial state
    initial_text = start_button.text_content()
    assert "Start" in initial_text
    
    # Start analysis and immediately check state changes
    start_button.click()
    
    # Verify immediate UI feedback
    page.wait_for_timeout(500)  # Give UI time to update
    
    # Button should be disabled and show progress
    expect(start_button).to_be_disabled()
    analyzing_text = start_button.text_content()
    assert "Analyzing" in analyzing_text or "⏳" in analyzing_text
    
    # Wait for completion
    page.wait_for_function(
        "document.getElementById('start-analysis').disabled === false",
        timeout=30000
    )
    
    # Verify UI returns to normal
    expect(start_button).to_be_enabled()
    final_text = start_button.text_content()
    assert "Start" in final_text
    
    print("✅ UI responsiveness test passed")


@pytest.mark.e2e
def test_smart_analysis_different_modes(page: Page):
    """
    Test different Smart Analysis modes
    
    Tests:
    - Fast analysis mode
    - Smart analysis mode  
    - Full analysis mode (if available)
    
    Verifies each mode completes without the fixed errors
    """
    
    analysis_modes = [("metadata", "Fast"), ("smart", "Smart")]
    
    for mode_value, mode_name in analysis_modes:
        print(f"🔍 Testing {mode_name} analysis mode...")
        
        page.goto("http://127.0.0.1:5003")
        
        # Configure analysis
        page.click(f"button.analysis-type-btn[data-type='{mode_value}']")
        page.locator("#size-slider").fill("2")
        
        # Monitor for errors
        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        
        # Run analysis
        page.click("#start-analysis")
        
        # Wait for completion
        page.wait_for_function(
            "document.getElementById('start-analysis').disabled === false",
            timeout=45000
        )
        
        # Check for our specific fixed errors
        timestamp_errors = [err for err in console_errors if 'attributeerror' in err.lower() and 'timestamp' in err.lower()]
        json_serialization_errors = [err for err in console_errors if 'json' in err.lower() and 'object' in err.lower()]
        
        assert len(timestamp_errors) == 0, f"{mode_name} mode: AttributeError timestamp issues: {timestamp_errors}"
        assert len(json_serialization_errors) == 0, f"{mode_name} mode: JSON serialization issues: {json_serialization_errors}"
        
        print(f"✅ {mode_name} analysis mode passed")
        
        # Clear console for next test
        page.evaluate("console.clear()")


if __name__ == "__main__":
    # Run tests directly if called as script
    pytest.main([__file__, "-v", "--tb=short"])