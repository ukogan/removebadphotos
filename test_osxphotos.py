#!/usr/bin/env python3
"""
Test script to verify osxphotos can access macOS Photos library.
This is the highest risk item that could kill the entire project.
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

try:
    import osxphotos
    print("✅ osxphotos library imported successfully")
except ImportError as e:
    print(f"❌ Failed to import osxphotos: {e}")
    sys.exit(1)

def test_photos_access():
    """Test basic access to Photos library."""
    print("\n🔍 Testing Photos library access...")
    
    try:
        # Initialize PhotosDB
        photosdb = osxphotos.PhotosDB()
        print("✅ Successfully connected to Photos library")
        
        # Get basic stats
        total_photos = len(photosdb.photos())
        print(f"📊 Total photos found: {total_photos}")
        
        if total_photos == 0:
            print("⚠️ No photos found - this might be expected if Photos library is empty")
            return True
            
        # Test accessing a few photos
        photos = photosdb.photos()[:5]  # Get first 5 photos
        print(f"🖼️ Testing access to first {len(photos)} photos:")
        
        for i, photo in enumerate(photos, 1):
            try:
                print(f"  {i}. UUID: {photo.uuid[:8]}... | Date: {photo.date} | Filename: {photo.filename}")
            except Exception as e:
                print(f"  {i}. ❌ Error accessing photo data: {e}")
                
        return True
        
    except Exception as e:
        print(f"❌ Failed to access Photos library: {e}")
        return False

def test_photo_metadata():
    """Test accessing detailed photo metadata."""
    print("\n🔍 Testing photo metadata access...")
    
    try:
        photosdb = osxphotos.PhotosDB()
        photos = photosdb.photos()
        
        if not photos:
            print("ℹ️ No photos available for metadata testing")
            return True
            
        # Test first photo's metadata
        photo = photos[0]
        print("📋 Sample photo metadata:")
        print(f"  UUID: {photo.uuid}")
        print(f"  Filename: {photo.filename}")
        print(f"  Date: {photo.date}")
        print(f"  Path: {photo.path}")
        print(f"  Camera make: {getattr(photo.exif_info, 'camera_make', 'Unknown') if photo.exif_info else 'No EXIF'}")
        print(f"  Camera model: {getattr(photo.exif_info, 'camera_model', 'Unknown') if photo.exif_info else 'No EXIF'}")
        print(f"  Original filename: {photo.original_filename}")
        print(f"  Has adjustments: {photo.hasadjustments}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to access photo metadata: {e}")
        return False

def test_time_grouping():
    """Test if we can group photos by time windows."""
    print("\n🔍 Testing time-based photo grouping...")
    
    try:
        photosdb = osxphotos.PhotosDB()
        photos = photosdb.photos()
        
        if len(photos) < 2:
            print("ℹ️ Need at least 2 photos for grouping test")
            return True
        
        # Find photos taken within 10 seconds of each other
        similar_groups = []
        
        for i, photo1 in enumerate(photos):
            if not photo1.date:
                continue
                
            group = [photo1]
            
            for j, photo2 in enumerate(photos[i+1:], i+1):
                if not photo2.date:
                    continue
                    
                time_diff = abs((photo1.date - photo2.date).total_seconds())
                if time_diff <= 10:  # Within 10 seconds
                    group.append(photo2)
                    
            if len(group) > 1:
                similar_groups.append(group)
                if len(similar_groups) >= 3:  # Just test first few groups
                    break
        
        print(f"🎯 Found {len(similar_groups)} potential photo groups (taken within 10 seconds):")
        for i, group in enumerate(similar_groups, 1):
            print(f"  Group {i}: {len(group)} photos")
            for photo in group:
                print(f"    - {photo.filename} at {photo.date}")
                
        return True
        
    except Exception as e:
        print(f"❌ Failed to test photo grouping: {e}")
        return False

def main():
    """Run all tests to verify osxphotos functionality."""
    print("🚀 Testing osxphotos library for photo deduplication project")
    print("=" * 60)
    
    tests = [
        ("Photos Library Access", test_photos_access),
        ("Photo Metadata", test_photo_metadata), 
        ("Time-based Grouping", test_time_grouping)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📝 Running: {test_name}")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY:")
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}: {test_name}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED! osxphotos is working correctly.")
        print("✅ Safe to proceed with Stage 1 development.")
    else:
        print("\n❌ SOME TESTS FAILED!")
        print("🔴 Need to resolve osxphotos issues before proceeding.")
        print("💡 Check macOS permissions for Photos access.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)