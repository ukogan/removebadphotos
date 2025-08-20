#!/usr/bin/env python3
"""
Test thumbnail generation for accessible photos
"""

import osxphotos
import os
from PIL import Image

def find_accessible_photo():
    """Find a photo (not video) that we can access."""
    db = osxphotos.PhotosDB()
    photos = db.photos()
    
    print("🔍 Looking for accessible photo files...")
    
    for i, photo in enumerate(photos):
        # Skip videos
        if photo.filename.lower().endswith(('.mov', '.mp4', '.avi')):
            continue
            
        # Check if we can access this photo
        if photo.path and os.path.exists(photo.path):
            file_size = os.path.getsize(photo.path)
            print(f"✅ Found accessible photo:")
            print(f"   UUID: {photo.uuid}")
            print(f"   Filename: {photo.filename}")
            print(f"   Path: {photo.path}")
            print(f"   Size: {file_size:,} bytes")
            
            # Test if we can open it with PIL
            try:
                with Image.open(photo.path) as img:
                    print(f"   Format: {img.format}")
                    print(f"   Size: {img.size}")
                    print(f"   Mode: {img.mode}")
                return photo
            except Exception as e:
                print(f"   ❌ Cannot open with PIL: {e}")
                continue
        
        if i > 100:  # Don't search forever
            break
    
    print("❌ No accessible photo files found")
    return None

def test_thumbnail_generation(photo):
    """Test generating a thumbnail for the given photo."""
    if not photo:
        return False
        
    print(f"\n🖼️ Testing thumbnail generation for {photo.filename}...")
    
    try:
        thumbnail_path = f"/tmp/test_thumbnail_{photo.uuid}.jpg"
        
        with Image.open(photo.path) as img:
            print(f"✅ Successfully opened image: {img.size} {img.mode}")
            
            # Convert to RGB if needed
            if img.mode in ('RGBA', 'P', 'LA'):
                img = img.convert('RGB')
                print(f"✅ Converted to RGB")
            
            # Create thumbnail
            img.thumbnail((300, 300), Image.Resampling.LANCZOS)
            print(f"✅ Thumbnail created: {img.size}")
            
            # Save thumbnail
            img.save(thumbnail_path, 'JPEG', quality=85, optimize=True)
            print(f"✅ Thumbnail saved to: {thumbnail_path}")
            
            # Verify saved file
            if os.path.exists(thumbnail_path):
                size = os.path.getsize(thumbnail_path)
                print(f"✅ Thumbnail file exists: {size:,} bytes")
                
                # Clean up
                os.remove(thumbnail_path)
                print(f"✅ Thumbnail test successful!")
                return True
            else:
                print(f"❌ Thumbnail file was not created")
                return False
                
    except Exception as e:
        print(f"❌ Thumbnail generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Testing Thumbnail Generation")
    print("=" * 40)
    
    photo = find_accessible_photo()
    success = test_thumbnail_generation(photo)
    
    if success:
        print(f"\n🎉 SUCCESS! Thumbnails can be generated.")
        print(f"   Photo UUID to test: {photo.uuid}")
        print(f"   Test URL: http://127.0.0.1:5002/api/thumbnail/{photo.uuid}")
    else:
        print(f"\n❌ FAILURE: Cannot generate thumbnails.")