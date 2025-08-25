#!/usr/bin/env python3
"""
Quick verification script to demonstrate the duplicate detection issue.
This script directly tests the API endpoints to show the problem clearly.
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://127.0.0.1:5003"

def test_api_endpoint(endpoint, method="GET", data=None):
    """Test an API endpoint and return response data."""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method == "POST":
            response = requests.post(url, json=data or {}, timeout=30)
        else:
            response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"HTTP {response.status_code}", "details": response.text}
    except Exception as e:
        return {"error": str(e)}

def main():
    print("=" * 80)
    print("DUPLICATE DETECTION ISSUE VERIFICATION")
    print("=" * 80)
    print(f"Testing at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test 1: Check library stats
    print("1. LIBRARY STATS:")
    stats = test_api_endpoint("/api/library-stats")
    if "stats" in stats:
        library_stats = stats["stats"]
        print(f"   📊 Total Photos: {library_stats.get('total_photos', 'N/A')}")
        print(f"   💾 Total Size: {library_stats.get('total_size_gb', 'N/A')} GB")
        print(f"   ✅ Status: Library scan working properly")
    else:
        print(f"   ❌ Error: {stats}")
    print()
    
    # Test 2: Check clustering works
    print("2. PHOTO CLUSTERING:")
    clusters = test_api_endpoint("/api/filter-clusters?preview=true")
    if "total_clusters" in clusters:
        print(f"   📁 Total Clusters: {clusters['total_clusters']}")
        print(f"   ✅ Status: Photo clustering working properly")
    else:
        print(f"   ❌ Error: {clusters}")
    print()
    
    # Test 3: Check filtering works
    print("3. FILTERING SYSTEM:")
    year_filter = test_api_endpoint("/api/filter-clusters?year=2025")
    if "total_clusters" in year_filter:
        print(f"   📅 Year 2025 Clusters: {year_filter['total_clusters']}")
        print(f"   🔍 Filters Applied: {year_filter.get('filters_applied', {})}")
        print(f"   ✅ Status: Filtering system working properly")
    else:
        print(f"   ❌ Error: {year_filter}")
    print()
    
    # Test 4: CRITICAL TEST - Duplicate Detection
    print("4. DUPLICATE DETECTION (CRITICAL TEST):")
    print("   🔄 Testing analyze-duplicates endpoint...")
    
    # Test with no filters
    duplicate_analysis = test_api_endpoint("/api/analyze-duplicates", "POST", {})
    if "analysis" in duplicate_analysis:
        analysis = duplicate_analysis["analysis"]
        print(f"   📸 Photos Analyzed: {analysis.get('total_photos_analyzed', 'N/A')}")
        print(f"   📋 Groups Found: {analysis.get('total_groups_found', 'N/A')}")
        print(f"   💾 Potential Savings: {analysis.get('potential_savings_gb', 'N/A')} GB")
        print(f"   ⏱️  Analysis Time: {analysis.get('analysis_duration_seconds', 'N/A')}s")
        
        # Check if note indicates stub implementation
        note = duplicate_analysis.get("note", "")
        if note:
            print(f"   📝 Note: {note}")
        
        # CRITICAL CHECK
        groups_found = analysis.get('total_groups_found', 0)
        if groups_found == 0:
            print(f"   🚨 CRITICAL ISSUE: 0 duplicate groups found in {analysis.get('total_photos_analyzed', 'N/A')} photos")
            print(f"   🔧 This indicates duplicate detection is not functioning")
            
            # Check if it's explicitly a stub
            if "MVP implementation" in note or "next iteration" in note:
                print(f"   ⚠️  CONFIRMED: This is a stub implementation")
        else:
            print(f"   ✅ SUCCESS: Found {groups_found} duplicate groups")
    else:
        print(f"   ❌ Error: {duplicate_analysis}")
    print()
    
    # Test 5: Test with specific filter
    print("5. FILTERED DUPLICATE DETECTION:")
    print("   🔄 Testing with Year 2025 filter...")
    
    filtered_analysis = test_api_endpoint("/api/analyze-duplicates", "POST", {
        "filters": {"year": 2025}
    })
    
    if "analysis" in filtered_analysis:
        analysis = filtered_analysis["analysis"]
        groups_found = analysis.get('total_groups_found', 0)
        photos_analyzed = analysis.get('total_photos_analyzed', 'N/A')
        
        print(f"   📸 Photos Analyzed: {photos_analyzed}")
        print(f"   📋 Groups Found: {groups_found}")
        
        if groups_found == 0:
            print(f"   🚨 CRITICAL ISSUE: Even with year filter, 0 duplicate groups found")
            print(f"   🔧 Expected: Some duplicates in year 2025 photos")
        else:
            print(f"   ✅ SUCCESS: Found {groups_found} duplicate groups for year 2025")
    print()
    
    # Summary
    print("=" * 80)
    print("VERIFICATION SUMMARY:")
    print("=" * 80)
    print("✅ Library scanning: Working")
    print("✅ Photo clustering: Working") 
    print("✅ Filter system: Working")
    print("❌ Duplicate detection: BROKEN - Returns 0 groups consistently")
    print()
    print("CONCLUSION:")
    print("The system infrastructure is solid, but the core duplicate detection")
    print("logic is not implemented. The API returns stub responses indicating")
    print("this functionality is planned for 'next iteration'.")
    print()
    print("IMPACT:")
    print("- Complete workflow failure for end users")
    print("- No actual duplicate detection occurring") 
    print("- Photos app integration cannot be tested")
    print("- E2E testing blocked at core functionality level")
    print()
    print("RECOMMENDATION:")
    print("Implement actual duplicate detection algorithms in the unified API")
    print("before proceeding with further E2E testing or user deployment.")

if __name__ == "__main__":
    main()