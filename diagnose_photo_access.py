#!/usr/bin/env python3
"""
Photo Access Diagnostics - Determine why we can't access photos
"""

import os
import sys
from pathlib import Path

try:
    import osxphotos
    print("✅ osxphotos library imported successfully")
except ImportError as e:
    print(f"❌ Failed to import osxphotos: {e}")
    sys.exit(1)

def diagnose_photo_access():
    """Comprehensive photo access diagnostics."""
    print("\n🔍 PHOTO ACCESS DIAGNOSTICS")
    print("=" * 50)
    
    try:
        # Initialize PhotosDB
        db = osxphotos.PhotosDB()
        photos = db.photos()
        print(f"📊 Total photos found: {len(photos)}")
        
        if not photos:
            print("❌ No photos found - cannot continue diagnostics")
            return
        
        # Test first few photos
        test_photos = photos[:10]
        print(f"\n🧪 Testing access to first {len(test_photos)} photos:")
        
        accessible_photos = 0
        path_none_count = 0
        path_exists_count = 0
        export_success_count = 0
        
        for i, photo in enumerate(test_photos, 1):
            print(f"\n📸 Photo {i}: {photo.uuid[:8]}... ({photo.filename})")
            
            # Test direct path access
            photo_path = photo.path
            if photo_path is None:
                print("   ❌ photo.path = None")
                path_none_count += 1
            else:
                print(f"   📁 photo.path = {photo_path}")
                if os.path.exists(photo_path):
                    print("   ✅ Path exists and accessible")
                    accessible_photos += 1
                    path_exists_count += 1
                else:
                    print("   ❌ Path does not exist or not accessible")
            
            # Test export functionality
            try:
                temp_dir = "/tmp/osxphotos_test"
                os.makedirs(temp_dir, exist_ok=True)
                
                # Try different export approaches
                try:
                    # Method 1: Basic export
                    exported_paths = photo.export(temp_dir)
                except Exception as e1:
                    try:
                        # Method 2: Export with overwrite
                        exported_paths = photo.export(temp_dir, overwrite=True)
                    except Exception as e2:
                        print(f"   ❌ Export method 1 failed: {e1}")
                        print(f"   ❌ Export method 2 failed: {e2}")
                        exported_paths = []
                
                if exported_paths:
                    print(f"   ✅ Export successful: {len(exported_paths)} file(s)")
                    export_success_count += 1
                    
                    # Check if exported file exists
                    exported_path = exported_paths[0]
                    if os.path.exists(exported_path):
                        file_size = os.path.getsize(exported_path)
                        print(f"   📦 Exported file size: {file_size:,} bytes")
                        
                        # Clean up
                        try:
                            os.remove(exported_path)
                        except:
                            pass
                    else:
                        print("   ⚠️ Export reported success but file not found")
                else:
                    print("   ❌ Export returned empty list")
                    
            except Exception as e:
                print(f"   ❌ Export failed: {e}")
        
        # Summary
        print(f"\n📊 DIAGNOSTIC SUMMARY:")
        print(f"   Photos with path=None: {path_none_count}/{len(test_photos)}")
        print(f"   Photos with accessible paths: {path_exists_count}/{len(test_photos)}")
        print(f"   Photos successfully exported: {export_success_count}/{len(test_photos)}")
        
        if accessible_photos > 0:
            print("✅ SOLUTION: Direct path access working")
            return "direct_path"
        elif export_success_count > 0:
            print("✅ SOLUTION: Export functionality working")
            return "export"
        else:
            print("❌ PROBLEM: No photo access method working")
            return None
            
    except Exception as e:
        print(f"❌ Failed to diagnose photo access: {e}")
        import traceback
        traceback.print_exc()
        return None

def check_permissions():
    """Check macOS permissions and suggest solutions."""
    print(f"\n🔐 PERMISSION ANALYSIS:")
    print("=" * 50)
    
    # Check if we're running in a restricted environment
    try:
        photos_library_path = Path.home() / "Pictures" / "Photos Library.photoslibrary"
        print(f"📁 Photos library path: {photos_library_path}")
        print(f"📍 Library exists: {photos_library_path.exists()}")
        
        if photos_library_path.exists():
            # Try to list contents
            try:
                contents = list(photos_library_path.iterdir())
                print(f"📂 Can list library contents: {len(contents)} items")
            except PermissionError:
                print("❌ Permission denied accessing Photos library")
                print("💡 SOLUTION NEEDED: Full Disk Access permission")
            except Exception as e:
                print(f"⚠️ Error accessing library: {e}")
    
    except Exception as e:
        print(f"❌ Error checking permissions: {e}")

def suggest_solutions(access_method):
    """Suggest solutions based on diagnostic results."""
    print(f"\n💡 RECOMMENDED SOLUTIONS:")
    print("=" * 50)
    
    if access_method == "direct_path":
        print("✅ Direct path access working - no changes needed")
        
    elif access_method == "export":
        print("📋 Use export-based thumbnail generation:")
        print("   1. Modify thumbnail endpoint to use photo.export()")
        print("   2. Cache exported files in temp directory")
        print("   3. Clean up exported files after thumbnail generation")
        
    else:
        print("🚨 CRITICAL: No photo access working. Try these solutions:")
        print("\n📋 SOLUTION 1: Enable Full Disk Access")
        print("   1. Open System Settings > Privacy & Security")
        print("   2. Click 'Full Disk Access'")
        print("   3. Add Terminal (or your Python executable)")
        print("   4. Restart terminal and retry")
        
        print("\n📋 SOLUTION 2: Grant Photos Access")
        print("   1. Open System Settings > Privacy & Security")
        print("   2. Click 'Photos'")
        print("   3. Add Terminal (or your Python executable)")
        print("   4. Restart terminal and retry")
        
        print("\n📋 SOLUTION 3: Run from Different Environment")
        print("   1. Try running from macOS Terminal app directly")
        print("   2. Try running from Finder (double-click script)")
        print("   3. Try running with sudo (not recommended)")

def main():
    """Run comprehensive photo access diagnostics."""
    print("🩺 macOS Photo Access Diagnostics")
    print("Diagnosing why thumbnail generation is failing...")
    
    check_permissions()
    access_method = diagnose_photo_access()
    suggest_solutions(access_method)
    
    if access_method:
        print(f"\n🎉 SUCCESS: Found working access method: {access_method}")
        return True
    else:
        print(f"\n❌ FAILURE: No working photo access method found")
        print("   Please follow the suggested solutions above")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)