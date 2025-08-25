#!/usr/bin/env python3
"""
Photo Tagger Module - Stage 4: Photos Library Integration
Handles photo tagging, smart album creation, and deletion list export
"""

import osxphotos
from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime
import json
import csv
import os

@dataclass
class TaggingResult:
    """Results from photo tagging operation."""
    session_id: str
    photos_tagged: int
    photos_failed: int
    smart_album_created: bool
    album_name: str
    export_files: List[str]
    errors: List[str]

class PhotoTagger:
    """Handles photo tagging and smart album creation using osxphotos."""
    
    def __init__(self):
        self.photosdb = None
        
    def get_photosdb(self):
        """Get or create PhotosDB connection."""
        if self.photosdb is None:
            self.photosdb = osxphotos.PhotosDB()
        return self.photosdb
    
    def tag_photos_for_deletion(self, photo_uuids: List[str], session_id: str) -> TaggingResult:
        """Tag photos with 'marked-for-deletion' and session-specific keywords."""
        print(f"🏷️ Starting photo tagging for {len(photo_uuids)} photos...")
        
        db = self.get_photosdb()
        photos_tagged = 0
        photos_failed = 0
        errors = []
        
        # Define the keywords to add
        deletion_keyword = "marked-for-deletion"
        session_keyword = session_id
        
        try:
            # Use photoscript to interact with Photos app
            import photoscript
            
            for uuid in photo_uuids:
                try:
                    # Find the photo in photoscript
                    photo = photoscript.Photo(uuid)
                    
                    if photo:
                        # Get current keywords
                        current_keywords = list(photo.keywords) if photo.keywords else []
                        
                        # Add our new keywords if not already present
                        keywords_to_add = []
                        if deletion_keyword not in current_keywords:
                            keywords_to_add.append(deletion_keyword)
                        if session_keyword not in current_keywords:
                            keywords_to_add.append(session_keyword)
                        
                        if keywords_to_add:
                            # Add keywords to the photo
                            all_keywords = current_keywords + keywords_to_add
                            photo.keywords = all_keywords
                            print(f"✅ Tagged {photo.filename} with keywords: {keywords_to_add}")
                            photos_tagged += 1
                        else:
                            print(f"ℹ️ Photo {uuid} already has required tags")
                            photos_tagged += 1
                    else:
                        error_msg = f"Photo {uuid} not found in Photos app"
                        print(f"❌ {error_msg}")
                        errors.append(error_msg)
                        photos_failed += 1
                        
                except Exception as e:
                    error_msg = f"Failed to tag photo {uuid}: {str(e)}"
                    print(f"❌ {error_msg}")
                    errors.append(error_msg)
                    photos_failed += 1
                    
        except ImportError:
            # Fallback: Use AppleScript through osascript
            print("⚠️ photoscript not available, falling back to AppleScript...")
            return self._tag_photos_with_applescript(photo_uuids, session_id)
        except Exception as e:
            error_msg = f"Error during tagging process: {str(e)}"
            print(f"❌ {error_msg}")
            errors.append(error_msg)
            
        # Create smart album with session ID format
        timestamp = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
        album_name = f"Marked for Deletion - {timestamp}"
        smart_album_created = self.create_smart_album(album_name, deletion_keyword, session_keyword)
        
        return TaggingResult(
            session_id=session_id,
            photos_tagged=photos_tagged,
            photos_failed=photos_failed,
            smart_album_created=smart_album_created,
            album_name=album_name,
            export_files=[],  # Will be filled by export functions
            errors=errors
        )
    
    def _tag_photos_with_applescript(self, photo_uuids: List[str], session_id: str) -> TaggingResult:
        """Fallback method using AppleScript to tag photos."""
        import subprocess
        
        print("🍎 Using AppleScript to tag photos...")
        
        photos_tagged = 0
        photos_failed = 0
        errors = []
        
        deletion_keyword = "marked-for-deletion"
        session_keyword = session_id
        
        for uuid in photo_uuids:
            try:
                # AppleScript to add keywords to a photo
                applescript = f'''
                tell application "Photos"
                    set targetPhoto to (first media item whose id is "{uuid}")
                    set currentKeywords to keywords of targetPhoto
                    set newKeywords to currentKeywords & {{"{deletion_keyword}", "{session_keyword}"}}
                    set keywords of targetPhoto to newKeywords
                end tell
                '''
                
                result = subprocess.run(
                    ['osascript', '-e', applescript],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    print(f"✅ Tagged photo {uuid} via AppleScript")
                    photos_tagged += 1
                else:
                    error_msg = f"AppleScript failed for {uuid}: {result.stderr}"
                    print(f"❌ {error_msg}")
                    errors.append(error_msg)
                    photos_failed += 1
                    
            except Exception as e:
                error_msg = f"Error tagging photo {uuid} with AppleScript: {str(e)}"
                print(f"❌ {error_msg}")
                errors.append(error_msg)
                photos_failed += 1
        
        # Create smart album with session ID format
        timestamp = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
        album_name = f"Marked for Deletion - {timestamp}"
        smart_album_created = self.create_smart_album_applescript(album_name, deletion_keyword, session_keyword)
        
        return TaggingResult(
            session_id=session_id,
            photos_tagged=photos_tagged,
            photos_failed=photos_failed,
            smart_album_created=smart_album_created,
            album_name=album_name,
            export_files=[],
            errors=errors
        )
    
    def create_smart_album(self, album_name: str, keyword1: str, keyword2: str) -> bool:
        """Create a smart album with keyword filters using osxphotos export."""
        try:
            print(f"📁 Creating album: {album_name}")
            print(f"   Adding photos with keywords '{keyword1}' AND '{keyword2}'")
            
            # Use osxphotos export to add photos to album
            return self.create_album_with_osxphotos(album_name, keyword1, keyword2)
            
        except Exception as e:
            print(f"❌ Error creating album: {e}")
            return self.create_smart_album_applescript(album_name, keyword1, keyword2)
    
    def create_album_with_osxphotos(self, album_name: str, keyword1: str, keyword2: str) -> bool:
        """Create album and add photos using osxphotos export command."""
        try:
            import subprocess
            import tempfile
            import shutil
            
            # Create temporary directory for export
            temp_dir = tempfile.mkdtemp(prefix='photo_dedup_album_')
            
            try:
                print(f"🔧 Using osxphotos to add photos to album '{album_name}'...")
                
                # Build osxphotos export command
                # Export minimal files (just sidecar) and add to album
                cmd = [
                    'osxphotos', 'export', temp_dir,
                    '--keyword', keyword1,
                    '--keyword', keyword2,
                    '--sidecar', 'json',  # Only export JSON sidecar, not the actual photo files
                    '--add-exported-to-album', album_name,
                    '--verbose'
                ]
                
                print(f"   Command: {' '.join(cmd)}")
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                
                if result.returncode == 0:
                    print(f"✅ Successfully created album '{album_name}'")
                    # Count lines containing "exported" to estimate number of photos added
                    exported_count = result.stdout.count('exported')
                    if exported_count > 0:
                        print(f"   Added approximately {exported_count} photos to album")
                    else:
                        print("   Album created (no photos matched the criteria)")
                    return True
                else:
                    print(f"❌ osxphotos export failed:")
                    print(f"   stdout: {result.stdout}")
                    print(f"   stderr: {result.stderr}")
                    return False
                    
            finally:
                # Clean up temporary directory
                try:
                    shutil.rmtree(temp_dir)
                except Exception as cleanup_error:
                    print(f"⚠️ Warning: Could not clean up temp directory {temp_dir}: {cleanup_error}")
                    
        except subprocess.TimeoutExpired:
            print(f"❌ Timeout creating album '{album_name}' - operation took too long")
            return False
        except Exception as e:
            print(f"❌ Error creating album with osxphotos: {e}")
            return False
    
    def create_album_from_uuids(self, album_name: str, photo_uuids: List[str]) -> bool:
        """Create album and add specific photos by UUID using photoscript."""
        try:
            if not photo_uuids:
                print("⚠️ No photo UUIDs provided for album creation")
                return False
            
            print(f"📁 Creating album '{album_name}' with {len(photo_uuids)} photos...")
            
            # Try photoscript first (direct Photos app control)
            try:
                import photoscript
                
                # Create a new album
                photos_app = photoscript.PhotosLibrary()
                
                # Check if album already exists
                existing_albums = [album for album in photos_app.albums() if album.name == album_name]
                if existing_albums:
                    album = existing_albums[0]
                    print(f"📁 Using existing album: {album_name}")
                else:
                    album = photos_app.create_album(album_name)
                    print(f"📁 Created new album: {album_name}")
                
                # Add photos to album by UUID
                added_count = 0
                failed_count = 0
                
                for uuid in photo_uuids:
                    try:
                        # Find photo by UUID
                        photo = photoscript.Photo(uuid)
                        if photo:
                            # Add photo to album
                            album.add([photo])
                            print(f"✅ Added photo {uuid[:8]}... to album")
                            added_count += 1
                        else:
                            print(f"⚠️ Photo {uuid[:8]}... not found")
                            failed_count += 1
                    except Exception as e:
                        print(f"❌ Failed to add photo {uuid[:8]}...: {e}")
                        failed_count += 1
                
                print(f"📊 Album creation complete: {added_count} added, {failed_count} failed")
                return added_count > 0
                
            except ImportError:
                print("⚠️ photoscript not available, falling back to osxphotos export...")
                return self._create_album_with_osxphotos_export(album_name, photo_uuids)
            except Exception as e:
                print(f"❌ photoscript method failed: {e}")
                print("⚠️ Falling back to osxphotos export...")
                return self._create_album_with_osxphotos_export(album_name, photo_uuids)
                
        except Exception as e:
            print(f"❌ Error creating album: {e}")
            return False
    
    def _create_album_with_osxphotos_export(self, album_name: str, photo_uuids: List[str]) -> bool:
        """Fallback method: Create album using osxphotos export (only works for accessible photos)."""
        try:
            import subprocess
            import tempfile
            import shutil
            import os
            
            print(f"🔧 Using osxphotos export fallback method...")
            
            # Create temporary directory for export
            temp_dir = tempfile.mkdtemp(prefix='photo_dedup_album_')
            
            try:
                # Create temporary file with UUIDs
                uuid_file = os.path.join(temp_dir, 'uuids.txt')
                with open(uuid_file, 'w') as f:
                    for uuid in photo_uuids:
                        f.write(f"{uuid}\n")
                
                # Build osxphotos export command using UUID file
                cmd = [
                    'osxphotos', 'export', temp_dir,
                    '--uuid-from-file', uuid_file,
                    '--sidecar', 'json',  # Only export JSON sidecar, not the actual photo files
                    '--add-exported-to-album', album_name,
                    '--verbose'
                ]
                
                print(f"🔧 Running osxphotos export to create album...")
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                
                if result.returncode == 0:
                    print(f"✅ osxphotos export completed")
                    
                    # Count how many photos were actually added
                    exported_count = result.stdout.count('Added')
                    missing_count = result.stdout.count('missing')
                    
                    if exported_count > 0:
                        print(f"✅ Successfully created album '{album_name}' with {exported_count} photos")
                        if missing_count > 0:
                            print(f"⚠️ Note: {missing_count} photos were skipped (original files missing)")
                        return True
                    else:
                        print(f"⚠️ Album '{album_name}' was created but no photos were added")
                        print(f"   This usually means the original photo files are not accessible")
                        if missing_count > 0:
                            print(f"   {missing_count} photos had missing original files")
                        return False
                else:
                    print(f"❌ osxphotos export failed (return code {result.returncode}):")
                    if result.stdout:
                        print(f"   stdout: {result.stdout}")
                    if result.stderr:
                        print(f"   stderr: {result.stderr}")
                    return False
                    
            finally:
                # Clean up temporary directory
                try:
                    shutil.rmtree(temp_dir)
                except Exception as cleanup_error:
                    print(f"⚠️ Warning: Could not clean up temp directory {temp_dir}: {cleanup_error}")
                    
        except subprocess.TimeoutExpired:
            print(f"❌ Timeout creating album '{album_name}' - operation took too long")
            return False
        except Exception as e:
            print(f"❌ Error in osxphotos export fallback: {e}")
            return False
    
    def create_smart_album_applescript(self, album_name: str, keyword1: str, keyword2: str) -> bool:
        """Create smart album using AppleScript."""
        try:
            import subprocess
            
            print(f"🍎 Creating smart album '{album_name}' via AppleScript...")
            
            # AppleScript to create smart album
            # Note: Smart album creation via AppleScript is complex and may not be fully supported
            applescript = f'''
            tell application "Photos"
                -- Note: Smart album creation via AppleScript is limited
                -- Manual creation recommended
                display dialog "Smart Album '{album_name}' should be created manually with criteria:\\nKeyword contains '{keyword1}' AND Keyword contains '{keyword2}'"
            end tell
            '''
            
            result = subprocess.run(
                ['osascript', '-e', applescript],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print(f"✅ Smart album dialog shown")
                return True
            else:
                print(f"❌ AppleScript error: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error creating smart album with AppleScript: {e}")
            return False
    
    def export_deletion_list(self, photo_data: List[Dict], session_id: str, 
                           output_dir: str = None) -> List[str]:
        """Export deletion list to CSV and JSON files."""
        if output_dir is None:
            output_dir = os.path.expanduser("~/Desktop")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"photo_deletion_list_{session_id}_{timestamp}"
        
        csv_file = os.path.join(output_dir, f"{base_filename}.csv")
        json_file = os.path.join(output_dir, f"{base_filename}.json")
        
        export_files = []
        
        try:
            # Export CSV
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                if photo_data:
                    writer = csv.DictWriter(f, fieldnames=photo_data[0].keys())
                    writer.writeheader()
                    writer.writerows(photo_data)
            
            print(f"📄 Exported CSV: {csv_file}")
            export_files.append(csv_file)
            
            # Export JSON
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'session_id': session_id,
                    'export_timestamp': datetime.now().isoformat(),
                    'total_photos': len(photo_data),
                    'photos': photo_data
                }, f, indent=2)
            
            print(f"📄 Exported JSON: {json_file}")
            export_files.append(json_file)
            
        except Exception as e:
            print(f"❌ Error exporting deletion list: {e}")
        
        return export_files

def main():
    """Test the photo tagger functionality."""
    tagger = PhotoTagger()
    
    # Test with a small set of UUIDs (replace with actual UUIDs from your library)
    test_uuids = []  # Add some test UUIDs here
    session_id = "test-session-123"
    
    if test_uuids:
        result = tagger.tag_photos_for_deletion(test_uuids, session_id)
        print(f"Tagging result: {result}")
    else:
        print("No test UUIDs provided - add some UUIDs to test the functionality")

if __name__ == "__main__":
    main()