#!/usr/bin/env python3
"""
Photo Deduplication Tool - Flask Backend
Stage 2: Core photo analysis with grouping and similarity detection
"""

from flask import Flask, render_template_string, jsonify, request, send_file
from datetime import datetime
import traceback
from photo_scanner import PhotoScanner
import json
import os
import tempfile
from PIL import Image
import hashlib

app = Flask(__name__)

# Global scanner instance
scanner = PhotoScanner()
cached_groups = None
cached_timestamp = None

@app.route('/api/clear-cache')
def clear_cache():
    """Clear cached groups to force fresh analysis."""
    global cached_groups, cached_timestamp
    cached_groups = None
    cached_timestamp = None
    return jsonify({'success': True, 'message': 'Cache cleared'})

# Thumbnail cache directory
THUMBNAIL_DIR = os.path.join(tempfile.gettempdir(), 'photo_dedup_thumbnails')
os.makedirs(THUMBNAIL_DIR, exist_ok=True)

@app.route('/')
def index():
    """Main page displaying basic photo information."""
    html_template = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Photo Dedup Tool</title>
        <style>
            body { 
                font-family: Arial, sans-serif; 
                max-width: 1200px; 
                margin: 0 auto; 
                padding: 20px;
                background-color: #f5f5f5;
            }
            .header {
                background-color: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                margin-bottom: 20px;
            }
            .stats {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
                margin-top: 20px;
            }
            .stat-card {
                background-color: white;
                padding: 15px;
                border-radius: 8px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                text-align: center;
            }
            .stat-number {
                font-size: 2em;
                font-weight: bold;
                color: #2196F3;
            }
            .stat-label {
                color: #666;
                margin-top: 5px;
            }
            .status {
                margin-top: 20px;
                padding: 15px;
                border-radius: 8px;
                text-align: center;
            }
            .success { background-color: #dff0d8; color: #3c763d; border: 1px solid #d6e9c6; }
            .error { background-color: #f2dede; color: #a94442; border: 1px solid #ebccd1; }
            .loading { background-color: #d9edf7; color: #31708f; border: 1px solid #bce8f1; }
            
            .controls {
                background-color: white;
                padding: 15px;
                border-radius: 8px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                margin-top: 20px;
                text-align: center;
            }
            
            .btn {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                cursor: pointer;
                margin: 5px;
                font-size: 16px;
            }
            .btn:hover { background-color: #1976D2; }
            .btn:disabled { background-color: #ccc; cursor: not-allowed; }
            
            .groups-container {
                margin-top: 20px;
            }
            
            .group-card {
                background-color: white;
                border-radius: 10px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                margin-bottom: 20px;
                overflow: hidden;
            }
            
            .group-header {
                background-color: #f8f9fa;
                padding: 15px;
                border-bottom: 1px solid #dee2e6;
            }
            
            .group-title {
                font-size: 18px;
                font-weight: bold;
                color: #333;
                margin-bottom: 5px;
            }
            
            .group-meta {
                font-size: 14px;
                color: #666;
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 10px;
                margin-top: 10px;
            }
            
            .photos-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 15px;
                padding: 20px;
            }
            
            .photo-card {
                border: 3px solid #ddd;
                border-radius: 12px;
                padding: 10px;
                transition: all 0.3s ease;
                cursor: pointer;
                background-color: white;
            }
            
            .photo-card:hover {
                transform: translateY(-3px);
                box-shadow: 0 8px 16px rgba(0,0,0,0.15);
            }
            
            .photo-card.recommended {
                border-color: #4CAF50;
                background-color: #f8fff8;
                box-shadow: 0 4px 8px rgba(76, 175, 80, 0.2);
            }
            
            .photo-card.selected {
                border-color: #2196F3;
                background-color: #f3f8ff;
                box-shadow: 0 4px 8px rgba(33, 150, 243, 0.3);
            }
            
            .photo-thumbnail {
                width: 100%;
                max-width: 250px;
                height: 200px;
                object-fit: cover;
                border-radius: 8px;
                margin-bottom: 10px;
                background-color: #f5f5f5;
            }
            
            .photo-loading {
                width: 100%;
                height: 200px;
                background-color: #f0f0f0;
                border-radius: 8px;
                display: flex;
                align-items: center;
                justify-content: center;
                color: #666;
                margin-bottom: 10px;
            }
            
            .photo-info {
                font-size: 12px;
                color: #666;
                margin-top: 5px;
            }
            
            .photo-filename {
                font-weight: bold;
                color: #333;
                margin-bottom: 5px;
                font-size: 14px;
            }
            
            .recommended-badge {
                display: inline-block;
                background-color: #4CAF50;
                color: white;
                padding: 2px 6px;
                border-radius: 3px;
                font-size: 10px;
                margin-bottom: 5px;
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🖼️ Photo Deduplication Tool</h1>
            <p>Stage 3: Visual Interface</p>
            <p><strong>Status:</strong> Interactive photo selection with thumbnails - click photos to select/deselect for keeping</p>
        </div>

        <div id="status" class="status loading">
            📡 Loading Photos library information...
        </div>

        <div id="stats" class="stats" style="display: none;">
            <!-- Stats will be populated by JavaScript -->
        </div>

        <div class="controls" style="display: none;" id="controls">
            <button class="btn" onclick="loadGroups()" id="loadGroupsBtn">🔍 Analyze Photo Groups</button>
            <span id="groupStatus" style="margin-left: 15px;"></span>
        </div>

        <div class="controls" style="display: none;" id="selectionSummary">
            <h3>📊 Selection Summary</h3>
            <div id="summaryStats"></div>
            <button class="btn" onclick="confirmDeletions()" id="confirmBtn" style="background-color: #FF5722;">🗑️ Confirm Deletions</button>
        </div>

        <div id="groupsContainer" class="groups-container">
            <!-- Photo groups will be populated here -->
        </div>

        <script>
            let groupsLoaded = false;
            let photoSelections = {}; // Track user selections by group_id

            // Load photo stats via API
            fetch('/api/stats')
                .then(response => response.json())
                .then(data => {
                    const statusDiv = document.getElementById('status');
                    const statsDiv = document.getElementById('stats');
                    const controlsDiv = document.getElementById('controls');
                    
                    if (data.success) {
                        statusDiv.className = 'status success';
                        statusDiv.innerHTML = '✅ Successfully connected to macOS Photos library';
                        
                        // Show stats
                        statsDiv.style.display = 'grid';
                        statsDiv.innerHTML = `
                            <div class="stat-card">
                                <div class="stat-number">${data.total_photos.toLocaleString()}</div>
                                <div class="stat-label">Total Photos</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-number">${data.sample_groups || 0}</div>
                                <div class="stat-label">Sample Groups Found</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-number">${data.estimated_savings}</div>
                                <div class="stat-label">Estimated Savings</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-number">${data.sample_photos || 0}</div>
                                <div class="stat-label">Photos Analyzed</div>
                            </div>
                        `;
                        
                        // Show controls
                        controlsDiv.style.display = 'block';
                    } else {
                        statusDiv.className = 'status error';
                        statusDiv.innerHTML = `❌ Error: ${data.error}`;
                    }
                })
                .catch(error => {
                    const statusDiv = document.getElementById('status');
                    statusDiv.className = 'status error';
                    statusDiv.innerHTML = `❌ Failed to connect: ${error}`;
                });

            function loadGroups() {
                if (groupsLoaded) return;
                
                const btn = document.getElementById('loadGroupsBtn');
                const status = document.getElementById('groupStatus');
                
                btn.disabled = true;
                btn.innerHTML = '⏳ Analyzing...';
                status.innerHTML = 'Finding similar photo groups...';
                
                fetch('/api/groups?limit=200')
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            allGroups = data.groups; // Store for calculations
                            displayGroups(data.groups);
                            status.innerHTML = `✅ Found ${data.total_groups} groups`;
                            btn.innerHTML = '✅ Analysis Complete';
                            groupsLoaded = true;
                        } else {
                            status.innerHTML = `❌ Error: ${data.error}`;
                            btn.disabled = false;
                            btn.innerHTML = '🔍 Analyze Photo Groups';
                        }
                    })
                    .catch(error => {
                        status.innerHTML = `❌ Failed to load: ${error}`;
                        btn.disabled = false;
                        btn.innerHTML = '🔍 Analyze Photo Groups';
                    });
            }

            function displayGroups(groups) {
                const container = document.getElementById('groupsContainer');
                
                if (groups.length === 0) {
                    container.innerHTML = '<div class="status">ℹ️ No duplicate photo groups found in sample</div>';
                    return;
                }
                
                let html = '';
                
                groups.forEach(group => {
                    const timeSpan = new Date(group.time_window_start).toLocaleString() + 
                                   ' - ' + new Date(group.time_window_end).toLocaleString();
                    
                    // Initialize selections for this group with recommended photo
                    if (!photoSelections[group.group_id]) {
                        const recommendedPhoto = group.photos.find(p => p.recommended);
                        photoSelections[group.group_id] = recommendedPhoto ? [recommendedPhoto.uuid] : [];
                    }
                    
                    html += `
                        <div class="group-card">
                            <div class="group-header">
                                <div class="group-title">📁 ${group.group_id}</div>
                                <div class="group-meta">
                                    <div>📅 <strong>Time:</strong> ${timeSpan}</div>
                                    <div>📷 <strong>Camera:</strong> ${group.camera_model}</div>
                                    <div>📸 <strong>Photos:</strong> ${group.photo_count}</div>
                                    <div>💾 <strong>Total Size:</strong> ${group.total_size_mb} MB</div>
                                    <div>💰 <strong>Potential Savings:</strong> ${group.potential_savings_mb} MB</div>
                                </div>
                            </div>
                            <div class="photos-grid">
                    `;
                    
                    group.photos.forEach(photo => {
                        const timestamp = photo.timestamp ? new Date(photo.timestamp).toLocaleString() : 'Unknown';
                        const resolution = photo.width && photo.height ? `${photo.width}×${photo.height}` : 'Unknown';
                        const fileSize = photo.file_size > 0 ? `${(photo.file_size / (1024*1024)).toFixed(1)} MB` : 'Unknown';
                        
                        const isSelected = photoSelections[group.group_id].includes(photo.uuid);
                        const cardClasses = ['photo-card'];
                        if (photo.recommended && isSelected) cardClasses.push('recommended');
                        else if (isSelected) cardClasses.push('selected');
                        
                        html += `
                            <div class="${cardClasses.join(' ')}" onclick="togglePhotoSelection('${group.group_id}', '${photo.uuid}')" data-group="${group.group_id}" data-photo="${photo.uuid}">
                                ${photo.recommended ? '<div class="recommended-badge">⭐ RECOMMENDED</div>' : ''}
                                <div class="photo-loading" id="loading_${photo.uuid}">📷 Loading...</div>
                                <img class="photo-thumbnail" 
                                     src="/api/thumbnail/${photo.uuid}" 
                                     alt="${photo.filename}"
                                     style="display: none;"
                                     onload="this.style.display='block'; document.getElementById('loading_${photo.uuid}').style.display='none';"
                                     onerror="this.style.display='none'; document.getElementById('loading_${photo.uuid}').innerHTML='❌ Could not load image';">
                                <div class="photo-filename">${photo.filename}</div>
                                <div class="photo-info">
                                    <div>📅 ${timestamp}</div>
                                    <div>📐 ${resolution}</div>
                                    <div>💾 ${fileSize}</div>
                                    <div>🎯 Quality: ${photo.quality_score.toFixed(1)}/100</div>
                                </div>
                            </div>
                        `;
                    });
                    
                    html += '</div></div>';
                });
                
                container.innerHTML = html;
                updateSelectionSummary();
            }

            function togglePhotoSelection(groupId, photoUuid) {
                const selections = photoSelections[groupId] || [];
                const index = selections.indexOf(photoUuid);
                
                if (index === -1) {
                    // Add to selection
                    selections.push(photoUuid);
                } else {
                    // Remove from selection (but ensure at least one photo remains selected)
                    if (selections.length > 1) {
                        selections.splice(index, 1);
                    }
                }
                
                photoSelections[groupId] = selections;
                updatePhotoCards(groupId);
                updateSelectionSummary();
            }

            function updatePhotoCards(groupId) {
                const cards = document.querySelectorAll(`[data-group="${groupId}"]`);
                
                cards.forEach(card => {
                    const photoUuid = card.getAttribute('data-photo');
                    const isSelected = photoSelections[groupId].includes(photoUuid);
                    const isRecommended = card.querySelector('.recommended-badge') !== null;
                    
                    // Update card classes
                    card.className = 'photo-card';
                    if (isRecommended && isSelected) {
                        card.className += ' recommended';
                    } else if (isSelected) {
                        card.className += ' selected';
                    }
                });
            }

            let allGroups = []; // Store groups for calculations

            function updateSelectionSummary() {
                if (allGroups.length === 0) return;
                
                let totalPhotosToDelete = 0;
                let totalSavingsMB = 0;
                let groupsWithDeletions = 0;
                
                allGroups.forEach(group => {
                    const selectedPhotos = photoSelections[group.group_id] || [];
                    const photosToDelete = group.photos.filter(photo => !selectedPhotos.includes(photo.uuid));
                    
                    if (photosToDelete.length > 0) {
                        groupsWithDeletions++;
                        totalPhotosToDelete += photosToDelete.length;
                        
                        // Calculate savings for this group
                        const deletionSizeMB = photosToDelete.reduce((sum, photo) => {
                            return sum + (photo.file_size / (1024 * 1024));
                        }, 0);
                        totalSavingsMB += deletionSizeMB;
                    }
                });
                
                const summaryDiv = document.getElementById('selectionSummary');
                const statsDiv = document.getElementById('summaryStats');
                
                if (totalPhotosToDelete > 0) {
                    summaryDiv.style.display = 'block';
                    statsDiv.innerHTML = `
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 15px;">
                            <div class="stat-card">
                                <div class="stat-number">${totalPhotosToDelete}</div>
                                <div class="stat-label">Photos to Delete</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-number">${groupsWithDeletions}</div>
                                <div class="stat-label">Groups with Deletions</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-number">${totalSavingsMB.toFixed(1)} MB</div>
                                <div class="stat-label">Estimated Savings</div>
                            </div>
                        </div>
                    `;
                } else {
                    summaryDiv.style.display = 'none';
                }
            }

            function confirmDeletions() {
                let totalPhotosToDelete = 0;
                let deletionList = [];
                
                allGroups.forEach(group => {
                    const selectedPhotos = photoSelections[group.group_id] || [];
                    const photosToDelete = group.photos.filter(photo => !selectedPhotos.includes(photo.uuid));
                    
                    photosToDelete.forEach(photo => {
                        deletionList.push({
                            group_id: group.group_id,
                            uuid: photo.uuid,
                            filename: photo.filename,
                            timestamp: photo.timestamp,
                            file_size: photo.file_size
                        });
                    });
                    
                    totalPhotosToDelete += photosToDelete.length;
                });
                
                if (totalPhotosToDelete === 0) {
                    alert('No photos selected for deletion.');
                    return;
                }
                
                const confirmMsg = `⚠️ CONFIRMATION REQUIRED ⚠️

You are about to mark ${totalPhotosToDelete} photos for deletion.

This action will:
1. Tag these photos as "marked-for-deletion" in your Photos library
2. Create a smart album for easy review
3. Generate a deletion list for your records

The photos will NOT be permanently deleted - you will need to manually delete them from the smart album.

Do you want to proceed?`;
                
                if (confirm(confirmMsg)) {
                    // In a real implementation, this would send the deletion list to the server
                    alert(`✅ SUCCESS!

${totalPhotosToDelete} photos have been marked for deletion.

Next steps:
1. A smart album "Photo Dedup - ${new Date().toLocaleDateString()}" would be created
2. Tagged photos would appear in this album
3. You can manually delete them from Photos app
4. A deletion list would be saved for your records

(This is a demonstration - actual tagging not implemented yet)`);
                    
                    console.log('Photos marked for deletion:', deletionList);
                }
            }
        </script>
    </body>
    </html>
    '''
    return render_template_string(html_template)

@app.route('/api/stats')
def api_stats():
    """API endpoint returning Photos library statistics with real group analysis."""
    try:
        print("📊 Computing photo library statistics...")
        
        # Scan photos (limited for initial testing)
        photos = scanner.scan_photos(limit=200)  # Increased from 100 for better stats
        total_photos = len(photos)
        
        if total_photos == 0:
            return jsonify({
                'success': True,
                'total_photos': 0,
                'potential_groups': 0,
                'estimated_savings': "No photos found",
                'timestamp': datetime.now().isoformat()
            })
        
        # Group photos by time and camera
        groups = scanner.group_photos_by_time_and_camera(photos)
        potential_groups = len(groups)
        
        # Calculate savings
        total_savings_bytes = sum(group.potential_savings_bytes for group in groups)
        total_savings_mb = total_savings_bytes / (1024 * 1024)
        
        # Estimate full library stats
        db = scanner.get_photosdb()
        full_photo_count = len(db.photos())
        
        # Scale up estimates based on sample
        if total_photos > 0:
            scale_factor = full_photo_count / total_photos
            estimated_full_groups = int(potential_groups * scale_factor)
            estimated_full_savings = total_savings_mb * scale_factor
        else:
            estimated_full_groups = 0
            estimated_full_savings = 0
        
        return jsonify({
            'success': True,
            'total_photos': full_photo_count,
            'sample_photos': total_photos,
            'sample_groups': potential_groups,
            'potential_groups': estimated_full_groups,
            'estimated_savings': f"~{estimated_full_savings:.1f} MB" if estimated_full_savings > 0 else "TBD",
            'sample_savings_mb': round(total_savings_mb, 1),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        error_msg = str(e)
        print(f"Error in api_stats: {error_msg}")
        print(traceback.format_exc())
        
        return jsonify({
            'success': False,
            'error': error_msg,
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/groups')
def api_groups():
    """API endpoint returning photo groups for review."""
    global cached_groups, cached_timestamp
    
    try:
        # Check if we have cached results (valid for 5 minutes)
        now = datetime.now()
        if (cached_groups is not None and cached_timestamp is not None and 
            (now - cached_timestamp).total_seconds() < 300):
            print("📋 Using cached photo groups")
            groups = cached_groups
        else:
            print("🔄 Computing fresh photo groups...")
            
            # Get limit from query parameter
            limit = request.args.get('limit', 100, type=int)
            limit = min(limit, 1000)  # Cap at 1000 for performance
            
            # Scan photos
            photos = scanner.scan_photos(limit=limit)
            
            if not photos:
                return jsonify({
                    'success': True,
                    'groups': [],
                    'total_groups': 0,
                    'message': 'No photos found'
                })
            
            # Group photos
            groups = scanner.group_photos_by_time_and_camera(photos)
            
            # Cache results
            cached_groups = groups
            cached_timestamp = now
        
        # Convert groups to JSON-serializable format
        groups_data = []
        for group in groups:
            group_data = {
                'group_id': group.group_id,
                'photos': [
                    {
                        'uuid': photo.uuid,
                        'filename': photo.filename,
                        'timestamp': photo.timestamp.isoformat() if photo.timestamp else None,
                        'camera_model': photo.camera_model,
                        'file_size': photo.file_size,
                        'width': photo.width,
                        'height': photo.height,
                        'format': photo.format,
                        'quality_score': photo.quality_score,
                        'recommended': photo.uuid == group.recommended_photo_uuid
                    }
                    for photo in group.photos
                ],
                'time_window_start': group.time_window_start.isoformat(),
                'time_window_end': group.time_window_end.isoformat(), 
                'camera_model': group.camera_model,
                'total_size_bytes': group.total_size_bytes,
                'total_size_mb': round(group.total_size_bytes / (1024 * 1024), 2),
                'potential_savings_bytes': group.potential_savings_bytes,
                'potential_savings_mb': round(group.potential_savings_bytes / (1024 * 1024), 2),
                'photo_count': len(group.photos)
            }
            groups_data.append(group_data)
        
        return jsonify({
            'success': True,
            'groups': groups_data,
            'total_groups': len(groups_data),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        error_msg = str(e)
        print(f"Error in api_groups: {error_msg}")
        print(traceback.format_exc())
        
        return jsonify({
            'success': False,
            'error': error_msg,
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/thumbnail/<photo_uuid>')
def api_thumbnail(photo_uuid):
    """Serve photo thumbnail by UUID."""
    try:
        # Generate thumbnail cache filename
        thumbnail_filename = f"{photo_uuid}_thumb.jpg"
        thumbnail_path = os.path.join(THUMBNAIL_DIR, thumbnail_filename)
        
        # Check if thumbnail already exists
        if os.path.exists(thumbnail_path):
            return send_file(thumbnail_path, mimetype='image/jpeg')
        
        # Find the photo in our database using the photos list
        db = scanner.get_photosdb()
        photos = db.photos()
        photo = None
        
        for p in photos:
            if p.uuid == photo_uuid:
                photo = p
                break
        
        if not photo:
            print(f"Photo {photo_uuid} not found in database")
            return jsonify({'error': 'Photo not found'}), 404
        
        # Try multiple approaches to get photo path
        photo_path = None
        
        # Method 1: Direct path access
        if photo.path and os.path.exists(photo.path):
            photo_path = photo.path
            print(f"Using direct path for {photo_uuid}: {photo_path}")
        else:
            # Method 2: Try export functionality
            try:
                temp_export_path = os.path.join(THUMBNAIL_DIR, f"{photo_uuid}_export")
                os.makedirs(temp_export_path, exist_ok=True)
                
                exported_paths = photo.export(temp_export_path, overwrite=True)
                if exported_paths and os.path.exists(exported_paths[0]):
                    photo_path = exported_paths[0]
                    print(f"Using exported path for {photo_uuid}: {photo_path}")
                else:
                    print(f"Export returned empty or invalid path for {photo_uuid}")
                    
            except Exception as e:
                print(f"Export failed for {photo_uuid}: {e}")
        
        if not photo_path:
            print(f"No accessible path found for {photo_uuid}")
            return jsonify({'error': 'Photo file not accessible - may be cloud-only or restricted'}), 404
        
        # Check if this is a video file
        if photo_path.lower().endswith(('.mov', '.mp4', '.avi', '.m4v')):
            print(f"Skipping video file for {photo_uuid}: {photo_path}")
            return jsonify({'error': 'Thumbnail not available for video files'}), 404
        
        # Generate thumbnail
        try:
            with Image.open(photo_path) as img:
                print(f"Successfully opened image for {photo_uuid}: {img.size} {img.mode}")
                
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'P', 'LA'):
                    img = img.convert('RGB')
                    print(f"Converted {photo_uuid} to RGB mode")
                
                # Calculate thumbnail size maintaining aspect ratio
                original_size = img.size
                img.thumbnail((300, 300), Image.Resampling.LANCZOS)
                print(f"Thumbnail for {photo_uuid}: {original_size} -> {img.size}")
                
                # Save thumbnail to cache
                img.save(thumbnail_path, 'JPEG', quality=85, optimize=True)
                print(f"Thumbnail saved for {photo_uuid}: {thumbnail_path}")
                
                return send_file(thumbnail_path, mimetype='image/jpeg')
                
        except Exception as e:
            print(f"Error generating thumbnail for {photo_uuid}: {e}")
            print(f"Photo path was: {photo_path}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': 'Could not generate thumbnail'}), 500
            
    except Exception as e:
        print(f"Error in thumbnail endpoint: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/health')
def api_health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'stage': 'Stage 3: Visual Interface'
    })

if __name__ == '__main__':
    print("🚀 Starting Photo Dedup Tool - Stage 3 FINAL")
    print("🖼️ WORKING: Visual interface with actual photo thumbnails!")
    print("🌐 Open http://127.0.0.1:5003 in your browser")
    print(f"📁 Thumbnails cached in: {THUMBNAIL_DIR}")
    print("=" * 60)
    
    # Run Flask app
    app.run(host='127.0.0.1', port=5003, debug=True)