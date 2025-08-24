#!/usr/bin/env python3
"""
Photo Deduplication Tool - Flask Backend
Stage 2: Core photo analysis with grouping and similarity detection
"""

from flask import Flask, render_template_string, jsonify, request, send_file
from flask_cors import CORS
from datetime import datetime
import traceback
from photo_scanner import PhotoScanner
from library_analyzer import LibraryAnalyzer
from photo_tagger import PhotoTagger
import json
import os
import tempfile
from PIL import Image
import hashlib

# Enable HEIC/HEIF support
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
    print("✅ HEIC/HEIF support enabled")
except ImportError:
    print("⚠️ pillow-heif not available - HEIC files may not work")

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Global instances
scanner = PhotoScanner()
analyzer = LibraryAnalyzer()
tagger = PhotoTagger()
cached_groups = None
cached_timestamp = None
cached_library_stats = None
cached_clusters = None
cached_library_timestamp = None

# Progress tracking for long-running operations
progress_status = {
    'active': False,
    'step': '',
    'progress': 0,
    'total': 0,
    'estimated_time': 0,
    'elapsed_time': 0,
    'start_time': None,
    'detail_log': [],
    'current_operation': '',
    'current_item': '',
    'items_processed': 0,
    'total_items': 0,
    'sub_progress': 0,
    'sub_total': 0
}

@app.route('/api/progress')
def api_progress():
    """API endpoint returning progress status for long-running operations."""
    global progress_status
    
    if progress_status['active'] and progress_status['start_time']:
        import time
        elapsed = time.time() - progress_status['start_time']
        progress_status['elapsed_time'] = elapsed
        
        # Estimate remaining time based on current progress
        if progress_status['progress'] > 0:
            rate = progress_status['progress'] / elapsed
            remaining_items = progress_status['total'] - progress_status['progress']
            estimated_remaining = remaining_items / rate if rate > 0 else 0
            progress_status['estimated_time'] = estimated_remaining
    
    return jsonify(progress_status)

def update_progress(step, progress=0, total=0, tooltip="", current_operation="", current_item="", items_processed=0, total_items=0):
    """Update progress status for long-running operations with detailed logging."""
    global progress_status
    import time
    
    if not progress_status['active']:
        progress_status['start_time'] = time.time()
        progress_status['active'] = True
        progress_status['detail_log'] = []  # Clear previous logs
    
    # Add to detail log
    timestamp = time.strftime("%H:%M:%S")
    if current_item:
        log_entry = f"{timestamp} - {current_operation}: {current_item} ({items_processed}/{total_items})"
    else:
        log_entry = f"{timestamp} - {step}: {tooltip}"
    
    progress_status['detail_log'].append(log_entry)
    # Keep only last 50 log entries to prevent memory issues
    if len(progress_status['detail_log']) > 50:
        progress_status['detail_log'] = progress_status['detail_log'][-50:]
    
    progress_status.update({
        'step': step,
        'progress': progress,
        'total': total,
        'tooltip': tooltip,
        'current_operation': current_operation,
        'current_item': current_item,
        'items_processed': items_processed,
        'total_items': total_items,
        'sub_progress': items_processed,
        'sub_total': total_items
    })
    
    if current_item:
        print(f"📊 Progress: {step} ({progress}/{total}) - {current_operation}: {current_item} ({items_processed}/{total_items})")
    else:
        print(f"📊 Progress: {step} ({progress}/{total}) - {tooltip}")

def complete_progress():
    """Mark progress as complete."""
    global progress_status
    progress_status.update({
        'active': False,
        'step': 'Complete',
        'progress': 0,
        'total': 0,
        'estimated_time': 0,
        'elapsed_time': 0,
        'start_time': None,
        'tooltip': ''
    })

@app.route('/api/clear-cache')
def clear_cache():
    """Clear all cached data to ensure unified data consistency."""
    global cached_groups, cached_timestamp, cached_library_stats, cached_clusters, cached_library_timestamp
    cached_groups = None
    cached_timestamp = None
    cached_library_stats = None
    cached_clusters = None
    cached_library_timestamp = None
    return jsonify({'success': True, 'message': 'All caches cleared for unified data consistency'})

# Thumbnail cache directory
THUMBNAIL_DIR = os.path.join(tempfile.gettempdir(), 'photo_dedup_thumbnails')
os.makedirs(THUMBNAIL_DIR, exist_ok=True)

@app.route('/')
def index():
    """Main dashboard page with library overview and priority targeting."""
    with open('/Users/urikogan/code/dedup/dashboard.html', 'r') as f:
        return f.read()

@app.route('/legacy')
def legacy():
    """Legacy interface for detailed photo analysis."""
    html_template = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Photo Dedup Tool</title>
        <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect x='3' y='5' width='18' height='14' rx='2' fill='%23e0e0e0' stroke='%23999' stroke-width='1'/%3E%3Crect x='3' y='5' width='18' height='2' fill='%23999'/%3E%3Crect x='5' y='8' width='3' height='2' rx='1' fill='%23666'/%3E%3Ccircle cx='16' cy='12' r='2' fill='%23666'/%3E%3Crect x='11' y='13' width='18' height='14' rx='2' fill='%23fff' stroke='%23666' stroke-width='1'/%3E%3Crect x='11' y='13' width='18' height='2' fill='%23666'/%3E%3Crect x='13' y='16' width='3' height='2' rx='1' fill='%23333'/%3E%3Ccircle cx='24' cy='20' r='2' fill='%23333'/%3E%3C/svg%3E">
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
                grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
                gap: 20px;
                padding: 20px;
            }
            
            .photo-card {
                border: 2px solid #dee2e6;
                border-radius: 8px;
                padding: 16px;
                margin: 8px;
                text-align: center;
                cursor: pointer;
                transition: all 0.2s ease;
                background-color: #f8f9fa;
                position: relative;
                opacity: 0.8;
            }
            
            .photo-card:not(.selected)::after {
                content: "🛡️ KEEP";
                position: absolute;
                top: 8px;
                right: 8px;
                background: #28a745;
                color: white;
                padding: 6px 12px;
                border-radius: 6px;
                font-size: 0.8rem;
                font-weight: bold;
                z-index: 2;
                box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            }
            
            .photo-card:hover {
                transform: translateY(-3px);
                box-shadow: 0 8px 16px rgba(0,0,0,0.15);
            }
            
            .photo-card.recommended {
                border-color: #ffc107;
                background-color: #fff9e6;
                box-shadow: 0 4px 8px rgba(255, 193, 7, 0.3);
                position: relative;
            }
            
            .photo-card.recommended::after {
                content: "⭐ RECOMMENDED";
                position: absolute;
                top: 8px;
                left: 8px;
                background: #ffc107;
                color: #212529;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 0.75rem;
                font-weight: bold;
                z-index: 2;
            }
            
            .photo-card.selected {
                border-color: #dc3545;
                background-color: white;
                box-shadow: 0 4px 12px rgba(220, 53, 69, 0.4);
                position: relative;
                opacity: 1;
                transform: translateY(-1px);
            }
            
            .photo-card.selected::before {
                content: "❌ DELETE";
                position: absolute;
                top: 8px;
                right: 8px;
                background: #dc3545;
                color: white;
                padding: 6px 12px;
                border-radius: 6px;
                font-size: 0.8rem;
                font-weight: bold;
                z-index: 2;
                box-shadow: 0 2px 4px rgba(0,0,0,0.3);
            }
            
            .photo-card.selected::after {
                content: "";
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(220, 53, 69, 0.15);
                border-radius: 8px;
                z-index: 1;
            }
            
            .photo-thumbnail {
                width: 100%;
                max-width: 500px;
                height: 400px;
                object-fit: contain;
                border-radius: 8px;
                margin-bottom: 10px;
                background-color: #f5f5f5;
            }
            
            .photo-loading {
                width: 100%;
                height: 400px;
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
            
            
            .photo-filename {
                cursor: pointer;
                color: #2196F3;
                text-decoration: underline;
            }
            
            .photo-filename:hover {
                color: #1976D2;
            }
            
            .photo-thumbnail {
                cursor: pointer;
            }
            
            /* Full-screen preview modal */
            .preview-modal {
                display: none;
                position: fixed;
                top: 0;
                left: 0;
                width: 100vw;
                height: 100vh;
                background-color: rgba(0, 0, 0, 0.95);
                z-index: 10000;
                cursor: pointer;
            }
            
            .preview-content {
                position: relative;
                width: 100%;
                height: 100%;
                display: flex;
                align-items: center;
                justify-content: center;
                flex-direction: column;
            }
            
            .preview-image {
                max-width: 95vw;
                max-height: 90vh;
                width: auto;
                height: auto;
                object-fit: contain;
                border: 2px solid #fff;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.8);
                /* Ensure minimum size for tiny images */
                min-width: 400px;
                min-height: 300px;
            }
            
            .preview-info {
                color: white;
                text-align: center;
                margin-top: 20px;
                font-size: 16px;
            }
            
            .preview-controls {
                position: absolute;
                bottom: 30px;
                left: 50%;
                transform: translateX(-50%);
                color: white;
                text-align: center;
                font-size: 14px;
                opacity: 0.8;
            }
            
            .preview-nav {
                position: absolute;
                top: 50%;
                transform: translateY(-50%);
                font-size: 40px;
                color: white;
                cursor: pointer;
                user-select: none;
                opacity: 0.6;
                transition: opacity 0.3s;
                width: 60px;
                height: 60px;
                display: flex;
                align-items: center;
                justify-content: center;
                background: rgba(0, 0, 0, 0.5);
                border-radius: 50%;
            }
            
            .preview-nav:hover {
                opacity: 1;
            }
            
            .preview-nav.prev {
                left: 30px;
            }
            
            .preview-nav.next {
                right: 30px;
            }
            
            .preview-close {
                position: absolute;
                top: 20px;
                right: 30px;
                font-size: 40px;
                color: white;
                cursor: pointer;
                opacity: 0.6;
                transition: opacity 0.3s;
            }
            
            .preview-close:hover {
                opacity: 1;
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

        <!-- Full-screen preview modal -->
        <div id="previewModal" class="preview-modal" onclick="closePreview()">
            <div class="preview-content" onclick="event.stopPropagation()">
                <div class="preview-close" onclick="closePreview()">&times;</div>
                <div class="preview-nav prev" id="prevPhoto" onclick="navigatePhoto(-1)">&#8249;</div>
                <div class="preview-nav next" id="nextPhoto" onclick="navigatePhoto(1)">&#8250;</div>
                <img id="previewImage" class="preview-image" src="" alt="">
                <div class="preview-info">
                    <div id="previewFilename" style="font-weight: bold; margin-bottom: 10px;"></div>
                    <div id="previewMetadata"></div>
                </div>
                <div class="preview-controls">
                    Press ESC to close • Use arrow keys to navigate
                </div>
            </div>
        </div>

        <script>
            let groupsLoaded = false;
            let photoSelections = {}; // Track user selections by group_id

            // Load stats immediately (working approach)
            console.log('Script starting...');
            
            setTimeout(function() {
                console.log('About to fetch stats...');
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
                                <div class="stat-number">${data.total_size_gb ? data.total_size_gb.toFixed(1) + ' GB' : 'TBD'}</div>
                                <div class="stat-label">Library Size</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-number">${data.sample_groups || 0}</div>
                                <div class="stat-label">Sample Groups Found</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-number">${data.estimated_savings}</div>
                                <div class="stat-label">Est. Savings</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-number">${data.sample_photos || 0}</div>
                                <div class="stat-label">Photos Analyzed</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-number">${data.date_range_start && data.date_range_end ? 
                                    new Date(data.date_range_start).getFullYear() + '-' + new Date(data.date_range_end).getFullYear() 
                                    : 'TBD'}</div>
                                <div class="stat-label">Date Range</div>
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
            }, 1000); // End setTimeout

            // Global functions accessible to HTML onclick handlers
            let progressInterval = null;
            
            function formatTime(seconds) {
                if (seconds < 60) return `${Math.round(seconds)}s`;
                if (seconds < 3600) return `${Math.round(seconds / 60)}m ${Math.round(seconds % 60)}s`;
                return `${Math.round(seconds / 3600)}h ${Math.round((seconds % 3600) / 60)}m`;
            }
            
            function updateProgress() {
                fetch('/api/progress')
                    .then(response => response.json())
                    .then(progress => {
                        const status = document.getElementById('groupStatus');
                        
                        if (progress.active) {
                            const percentage = progress.total > 0 ? Math.round((progress.progress / progress.total) * 100) : 0;
                            const elapsed = formatTime(progress.elapsed_time);
                            const remaining = progress.estimated_time > 0 ? formatTime(progress.estimated_time) : '';
                            
                            let statusText = `🔄 ${progress.step} (${percentage}%)`;
                            if (elapsed) statusText += ` • ${elapsed} elapsed`;
                            if (remaining) statusText += ` • ~${remaining} remaining`;
                            
                            status.innerHTML = statusText;
                            status.title = progress.tooltip || '';
                        }
                    })
                    .catch(error => {
                        console.log('Progress polling error:', error);
                    });
            }

            function loadGroups() {
                if (groupsLoaded) return;
                
                const btn = document.getElementById('loadGroupsBtn');
                const status = document.getElementById('groupStatus');
                
                btn.disabled = true;
                btn.innerHTML = '⏳ Analyzing...';
                status.innerHTML = '🔄 Starting analysis...';
                status.title = 'Preparing to analyze your photo library for duplicates';
                
                // Start progress polling
                progressInterval = setInterval(updateProgress, 1000);
                
                // Check for priority and limit parameters from URL
                const urlParams = new URLSearchParams(window.location.search);
                const priority = urlParams.get('priority');
                const limit = urlParams.get('limit') || '10';
                
                let apiUrl;
                if (priority) {
                    // Use priority-filtered API endpoint (already analyzed)
                    apiUrl = `/api/groups?priority=${priority}&limit=${limit}`;
                } else {
                    // Use full analysis API endpoint
                    apiUrl = `/api/groups?limit=${limit}`;
                }
                
                fetch(apiUrl)
                    .then(response => response.json())
                    .then(data => {
                        // Stop progress polling
                        if (progressInterval) {
                            clearInterval(progressInterval);
                            progressInterval = null;
                        }
                        
                        if (data.success) {
                            allGroups = data.groups; // Store for calculations
                            displayGroups(data.groups);
                            status.innerHTML = `✅ Analysis Complete • Found ${data.total_groups} groups`;
                            status.title = 'Photo analysis completed successfully';
                            btn.innerHTML = '✅ Analysis Complete';
                            groupsLoaded = true;
                        } else {
                            status.innerHTML = `❌ Error: ${data.error}`;
                            status.title = '';
                            btn.disabled = false;
                            btn.innerHTML = '🔍 Analyze Photo Groups';
                        }
                    })
                    .catch(error => {
                        // Stop progress polling
                        if (progressInterval) {
                            clearInterval(progressInterval);
                            progressInterval = null;
                        }
                        
                        status.innerHTML = `❌ Failed to load: ${error}`;
                        status.title = '';
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
                    
                    // Initialize selections for this group with NO photos selected (require explicit user action)
                    if (!photoSelections[group.group_id]) {
                        photoSelections[group.group_id] = [];
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
                                    <div>💰 <strong>Est. Savings:</strong> ~${group.potential_savings_mb} MB</div>
                                </div>
                            </div>
                            <div class="group-actions" style="margin: 16px 0; display: flex; justify-content: space-between; align-items: center;">
                                <div class="primary-actions">
                                    <button class="action-btn keep-all-btn" onclick="keepAllPhotos('${group.group_id}')" style="background: #28a745; color: white; border: none; padding: 10px 16px; margin-right: 8px; border-radius: 6px; cursor: pointer; font-weight: 600;">🛡️ Keep All Photos</button>
                                    <button class="action-btn delete-duplicates-btn" onclick="deleteAllButOne('${group.group_id}')" style="background: #dc3545; color: white; border: none; padding: 10px 16px; margin-right: 8px; border-radius: 6px; cursor: pointer; font-weight: 600;">❌ Delete Duplicates</button>
                                    <button class="action-btn delete-all-btn" onclick="deleteAllPhotos('${group.group_id}')" style="background: #721c24; color: white; border: none; padding: 10px 16px; margin-right: 8px; border-radius: 6px; cursor: pointer; font-weight: bold;">❌ Delete All Photos</button>
                                </div>
                                <div class="secondary-actions">
                                    <button class="action-btn why-grouped-btn" onclick="showWhyGrouped('${group.group_id}')" style="background: #6c757d; color: white; border: none; padding: 8px 12px; border-radius: 6px; cursor: pointer; font-size: 0.9rem;">ℹ️ Grouping Info</button>
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
                        if (isSelected) cardClasses.push('selected'); // Selected = DELETE target
                        
                        html += `
                            <div class="${cardClasses.join(' ')}" data-group="${group.group_id}" data-photo="${photo.uuid}" data-photo-index="${group.photos.indexOf(photo)}">
                                <div class="photo-loading" id="loading_${photo.uuid}">📷 Loading...</div>
                                <img class="photo-thumbnail" 
                                     src="/api/thumbnail/${photo.uuid}" 
                                     alt="${photo.filename}"
                                     style="display: none;"
                                     onload="this.style.display='block'; document.getElementById('loading_${photo.uuid}').style.display='none';"
                                     onerror="this.style.display='none'; document.getElementById('loading_${photo.uuid}').innerHTML='❌ Could not load image';"
                                     onclick="event.stopPropagation(); openPreview('${group.group_id}', ${group.photos.indexOf(photo)});">
                                <div class="photo-filename" onclick="event.stopPropagation(); openInPhotos('${photo.uuid}')">${photo.filename}</div>
                                <div class="photo-info">
                                    <div>📅 ${timestamp}</div>
                                    <div>📐 ${resolution}</div>
                                    <div>💾 ${fileSize}</div>
                                    <div>🎯 Quality: ${photo.quality_score.toFixed(1)}/100</div>
                                </div>
                                <div class="photo-selection-area" onclick="togglePhotoSelection('${group.group_id}', '${photo.uuid}')" style="position: absolute; bottom: 0; right: 0; width: 30px; height: 30px; background: ${isSelected ? 'rgba(220,53,69,0.8)' : 'rgba(40,167,69,0.8)'}; border-radius: 50%; margin: 5px; display: flex; align-items: center; justify-content: center; font-size: 14px; cursor: pointer; color: white; font-weight: bold;">
                                    ${isSelected ? '❌' : '🛡️'}
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
                    // Add to deletion selection (mark for DELETE)
                    selections.push(photoUuid);
                } else {
                    // Remove from deletion selection (mark for KEEP)
                    selections.splice(index, 1);
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
                    // Update card classes based on selection state only
                    card.className = 'photo-card';
                    if (isSelected) {
                        card.className += ' selected'; // Selected = DELETE target
                    }
                });
            }

            function keepAllPhotos(groupId) {
                // Keep all photos (select NONE for deletion)
                const group = allGroups.find(g => g.group_id === groupId);
                if (group) {
                    photoSelections[groupId] = [];
                    updatePhotoCards(groupId);
                    updateSelectionSummary();
                }
            }

            function deleteAllButOne(groupId) {
                // Delete all except recommended photo (select all EXCEPT recommended for deletion)
                const group = allGroups.find(g => g.group_id === groupId);
                if (group) {
                    const recommendedPhoto = group.photos.find(photo => photo.recommended);
                    const photoToKeep = recommendedPhoto || group.photos[0];
                    
                    // Select all photos EXCEPT the one to keep
                    photoSelections[groupId] = group.photos
                        .filter(photo => photo.uuid !== photoToKeep.uuid)
                        .map(photo => photo.uuid);
                    
                    updatePhotoCards(groupId);
                    updateSelectionSummary();
                }
            }

            function deleteAllPhotos(groupId) {
                // Delete all photos in the group (select ALL for deletion)
                if (confirm('⚠️ Are you sure you want to delete ALL photos in this group? This will mark all photos for deletion.')) {
                    const group = allGroups.find(g => g.group_id === groupId);
                    if (group) {
                        photoSelections[groupId] = group.photos.map(photo => photo.uuid);
                        updatePhotoCards(groupId);
                        updateSelectionSummary();
                    }
                }
            }

            function showWhyGrouped(groupId) {
                const group = allGroups.find(g => g.group_id === groupId);
                if (!group) return;
                
                // Analyze why these photos were grouped
                const photos = group.photos;
                const timeSpan = new Date(group.time_window_end) - new Date(group.time_window_start);
                const timeSpanSeconds = Math.round(timeSpan / 1000);
                
                // Analyze timestamps
                const timestamps = photos.map(p => new Date(p.timestamp)).sort((a, b) => a - b);
                const firstPhoto = timestamps[0];
                const lastPhoto = timestamps[timestamps.length - 1];
                const totalSpan = Math.round((lastPhoto - firstPhoto) / 1000);
                
                // Analyze cameras
                const cameras = [...new Set(photos.map(p => p.camera_model).filter(c => c))];
                
                // Analyze file formats
                const formats = [...new Set(photos.map(p => p.format))];
                
                // Analyze resolutions
                const resolutions = [...new Set(photos.map(p => p.width && p.height ? `${p.width}×${p.height}` : 'Unknown'))];
                
                const explanation = `🔍 WHY THESE PHOTOS WERE GROUPED TOGETHER

📊 Current Grouping Algorithm:
• Time Window: Photos taken within 10 seconds
• Camera Match: Same camera model
• No Visual Similarity: Not yet implemented

📅 Time Analysis:
• First photo: ${firstPhoto.toLocaleString()}
• Last photo: ${lastPhoto.toLocaleString()}
• Total time span: ${totalSpan} seconds
• Within 10-second window: ${timeSpanSeconds <= 10 ? '✅ Yes' : '❌ No - this may be a grouping error'}

📷 Camera Analysis:
• Camera models: ${cameras.length > 0 ? cameras.join(', ') : 'Unknown'}
• Same camera: ${cameras.length <= 1 ? '✅ Yes' : '❌ No - this may be a grouping error'}

🖼️ Technical Details:
• File formats: ${formats.join(', ')}
• Resolutions: ${resolutions.join(', ')}
• Photo count: ${photos.length}

⚠️ KNOWN LIMITATIONS:
• No visual similarity analysis (coming in Stage 5)
• May group different subjects taken quickly
• Videos should be filtered out but some may slip through
• Time-based grouping can be too broad

💡 RECOMMENDATIONS:
• Use "Keep All" if photos are different subjects
• Use "Delete All But Best" if photos are truly similar
• Manual review is always recommended`;
                
                alert(explanation);
            }

            let allGroups = []; // Store groups for calculations

            function updateSelectionSummary() {
                if (allGroups.length === 0) return;
                
                let totalPhotosToDelete = 0;
                let totalSavingsMB = 0;
                let groupsWithDeletions = 0;
                
                allGroups.forEach(group => {
                    const selectedPhotos = photoSelections[group.group_id] || [];
                    const photosToDelete = group.photos.filter(photo => selectedPhotos.includes(photo.uuid));
                    
                    if (photosToDelete.length > 0) {
                        groupsWithDeletions++;
                        totalPhotosToDelete += photosToDelete.length;
                        
                        // Calculate estimated savings for this group
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
                        <div class="deletion-warning" style="background: #fff3cd; border: 2px solid #ffc107; border-radius: 8px; padding: 16px; margin-bottom: 16px;">
                            <div style="display: flex; align-items: center; margin-bottom: 8px;">
                                <span style="font-size: 1.5rem; margin-right: 8px;">⚠️</span>
                                <strong style="color: #856404;">DELETION SUMMARY</strong>
                            </div>
                            <div style="color: #856404;">
                                <strong>${totalPhotosToDelete} photos</strong> from <strong>${groupsWithDeletions} groups</strong> will be marked for deletion, saving approximately <strong>~${totalSavingsMB.toFixed(1)} MB</strong>
                            </div>
                        </div>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 15px;">
                            <div class="stat-card" style="background: #f8d7da; border: 1px solid #dc3545;">
                                <div class="stat-number" style="color: #dc3545;">❌ ${totalPhotosToDelete}</div>
                                <div class="stat-label">Photos to Delete</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-number">${groupsWithDeletions}</div>
                                <div class="stat-label">Groups with Deletions</div>
                            </div>
                            <div class="stat-card" style="background: #d4edda; border: 1px solid #28a745;">
                                <div class="stat-number" style="color: #28a745;">💾 ~${totalSavingsMB.toFixed(1)} MB</div>
                                <div class="stat-label">Est. Storage Savings</div>
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
                    // FIXED: In inverted model, selected photos = photos to DELETE
                    const photosToDelete = group.photos.filter(photo => selectedPhotos.includes(photo.uuid));
                    
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
                    // Execute the real workflow
                    executeWorkflow(deletionList, totalPhotosToDelete);
                }
            }

            function executeWorkflow(deletionList, totalPhotosToDelete) {
                // Calculate estimated savings
                const totalSavingsMB = deletionList.reduce((sum, photo) => {
                    return sum + (photo.file_size / (1024 * 1024));
                }, 0);
                
                // Extract just the UUIDs
                const photoUuids = deletionList.map(photo => photo.uuid);
                
                // Show loading state
                const confirmBtn = document.getElementById('confirmBtn');
                const originalText = confirmBtn.textContent;
                confirmBtn.textContent = '🔄 Processing...';
                confirmBtn.disabled = true;
                
                // Call the workflow API
                fetch('/api/complete-workflow', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        photo_uuids: photoUuids,
                        estimated_savings_mb: totalSavingsMB
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showWorkflowSuccess(data);
                    } else {
                        alert('❌ Error: ' + (data.error || 'Unknown error occurred'));
                    }
                })
                .catch(error => {
                    console.error('Error executing workflow:', error);
                    alert('❌ Network error: ' + error.message);
                })
                .finally(() => {
                    // Restore button
                    confirmBtn.textContent = originalText;
                    confirmBtn.disabled = false;
                });
            }

            function showWorkflowSuccess(data) {
                const summary = data.summary;
                const guidance = data.workflow_guidance;
                
                // Create a detailed success modal/alert
                const nextSteps = summary.next_steps.map(step => '• ' + step).join('\\n');
                const successMsg = `✅ WORKFLOW COMPLETED SUCCESSFULLY!

📊 Summary:
• ${summary.photos_processed} photos processed
• ~${summary.estimated_savings_mb.toFixed(1)} MB estimated savings
• Session ID: ${summary.session_id}
• Album name: "${summary.album_name}"

📋 Next Steps:
${nextSteps}

🔧 Manual Instructions:
📋 Tagging: ${guidance.tagging_instructions}

📁 Smart Album: ${guidance.album_instructions}

⚠️ ${guidance.safety_reminder}

📄 Deletion list has been generated and is available in the browser console.`;

                alert(successMsg);
                
                // Log detailed data to console
                console.log('=== DELETION WORKFLOW COMPLETED ===');
                console.log('Summary:', summary);
                console.log('Export Data:', data.export_data);
                console.log('Guidance:', guidance);
                
                // Optionally download the deletion list
                downloadDeletionList(data.export_data, summary.session_id);
            }

            function downloadDeletionList(exportData, sessionId) {
                // Create CSV content
                const headers = ['UUID', 'Filename', 'Timestamp', 'Size (MB)', 'Camera', 'Width', 'Height', 'Format', 'Quality Score'];
                const csvContent = [
                    headers.join(','),
                    ...exportData.map(photo => [
                        photo.uuid,
                        `"${photo.filename}"`,
                        photo.timestamp,
                        photo.file_size_mb,
                        `"${photo.camera_model || ''}"`,
                        photo.width || '',
                        photo.height || '',
                        photo.format || '',
                        photo.quality_score || ''
                    ].join(','))
                ].join('\\n');
                
                // Create download link
                const blob = new Blob([csvContent], { type: 'text/csv' });
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `deletion_list_${sessionId}.csv`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
                
                console.log('📄 Deletion list CSV downloaded:', `deletion_list_${sessionId}.csv`);
            }

            // Preview functionality
            let currentPreviewGroup = null;
            let currentPreviewIndex = 0;

            function openPreview(groupId, photoIndex) {
                const group = allGroups.find(g => g.group_id === groupId);
                if (!group || !group.photos[photoIndex]) return;

                currentPreviewGroup = group;
                currentPreviewIndex = photoIndex;
                
                const photo = group.photos[photoIndex];
                const modal = document.getElementById('previewModal');
                const image = document.getElementById('previewImage');
                const filename = document.getElementById('previewFilename');
                const metadata = document.getElementById('previewMetadata');
                
                // Set image source to full-resolution image
                image.src = `/api/full-image/${photo.uuid}`;
                image.onerror = function() {
                    // Fallback to thumbnail if full image fails
                    console.log('Full image failed, falling back to thumbnail');
                    image.src = `/api/thumbnail/${photo.uuid}`;
                    image.onerror = function() {
                        image.style.display = 'none';
                        image.nextElementSibling.innerHTML = '❌ Image not available for preview';
                    };
                };
                
                // Set metadata
                filename.textContent = photo.filename;
                const timestamp = photo.timestamp ? new Date(photo.timestamp).toLocaleString() : 'Unknown';
                const resolution = photo.width && photo.height ? `${photo.width}×${photo.height}` : 'Unknown';
                const fileSize = photo.file_size > 0 ? `${(photo.file_size / (1024*1024)).toFixed(1)} MB` : 'Unknown';
                
                metadata.innerHTML = `
                    📅 ${timestamp}<br>
                    📐 ${resolution}<br>
                    💾 ${fileSize}<br>
                    🎯 Quality: ${photo.quality_score.toFixed(1)}/100<br>
                    📷 ${photo.camera_model || 'Unknown camera'}
                `;
                
                // Show modal
                modal.style.display = 'block';
                document.body.style.overflow = 'hidden';
                
                // Update navigation buttons
                updatePreviewNavigation();
            }

            function closePreview() {
                const modal = document.getElementById('previewModal');
                modal.style.display = 'none';
                document.body.style.overflow = '';
                currentPreviewGroup = null;
                currentPreviewIndex = 0;
            }

            function navigatePhoto(direction) {
                if (!currentPreviewGroup) return;
                
                const newIndex = currentPreviewIndex + direction;
                if (newIndex >= 0 && newIndex < currentPreviewGroup.photos.length) {
                    currentPreviewIndex = newIndex;
                    const photo = currentPreviewGroup.photos[currentPreviewIndex];
                    
                    const image = document.getElementById('previewImage');
                    const filename = document.getElementById('previewFilename');
                    const metadata = document.getElementById('previewMetadata');
                    
                    // Set image source to full-resolution image
                    image.src = `/api/full-image/${photo.uuid}`;
                    image.onerror = function() {
                        // Fallback to thumbnail if full image fails
                        console.log('Full image failed, falling back to thumbnail');
                        image.src = `/api/thumbnail/${photo.uuid}`;
                        image.onerror = function() {
                            image.style.display = 'none';
                            image.nextElementSibling.innerHTML = '❌ Image not available for preview';
                        };
                    };
                    filename.textContent = photo.filename;
                    
                    const timestamp = photo.timestamp ? new Date(photo.timestamp).toLocaleString() : 'Unknown';
                    const resolution = photo.width && photo.height ? `${photo.width}×${photo.height}` : 'Unknown';
                    const fileSize = photo.file_size > 0 ? `${(photo.file_size / (1024*1024)).toFixed(1)} MB` : 'Unknown';
                    
                    metadata.innerHTML = `
                        📅 ${timestamp}<br>
                        📐 ${resolution}<br>
                        💾 ${fileSize}<br>
                        🎯 Quality: ${photo.quality_score.toFixed(1)}/100<br>
                        📷 ${photo.camera_model || 'Unknown camera'}
                    `;
                    
                    updatePreviewNavigation();
                }
            }

            function updatePreviewNavigation() {
                const prevBtn = document.getElementById('prevPhoto');
                const nextBtn = document.getElementById('nextPhoto');
                
                if (currentPreviewGroup) {
                    prevBtn.style.display = currentPreviewIndex > 0 ? 'flex' : 'none';
                    nextBtn.style.display = currentPreviewIndex < currentPreviewGroup.photos.length - 1 ? 'flex' : 'none';
                }
            }

            function openInPhotos(photoUuid) {
                // Show visual feedback
                const filenameElement = event.target;
                const originalText = filenameElement.textContent;
                filenameElement.textContent = '🔄 Opening in Photos...';
                filenameElement.style.color = '#FF9800';
                
                // Call backend endpoint to open specific photo in Photos app
                fetch(`/api/open-photo/${photoUuid}`, { method: 'POST' })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            filenameElement.textContent = '✅ Opened in Photos!';
                            filenameElement.style.color = '#4CAF50';
                            setTimeout(() => {
                                filenameElement.textContent = originalText;
                                filenameElement.style.color = '#2196F3';
                            }, 2000);
                        } else {
                            console.error('Failed to open photo in Photos app:', data.error);
                            if (data.search_term) {
                                filenameElement.textContent = `🔍 Search for: ${data.search_term}`;
                                filenameElement.style.color = '#FF9800';
                            } else {
                                filenameElement.textContent = '❌ Failed to open';
                                filenameElement.style.color = '#f44336';
                            }
                            setTimeout(() => {
                                filenameElement.textContent = originalText;
                                filenameElement.style.color = '#2196F3';
                            }, 3000);
                        }
                    })
                    .catch(error => {
                        console.error('Error opening photo:', error);
                        filenameElement.textContent = '❌ Error occurred';
                        filenameElement.style.color = '#f44336';
                        setTimeout(() => {
                            filenameElement.textContent = originalText;
                            filenameElement.style.color = '#2196F3';
                            // Fallback: just open Photos app
                            window.open('photos://', '_blank');
                        }, 2000);
                    });
            }

            // Keyboard navigation
            document.addEventListener('keydown', function(e) {
                if (document.getElementById('previewModal').style.display === 'block') {
                    switch(e.key) {
                        case 'Escape':
                            closePreview();
                            break;
                        case 'ArrowLeft':
                            navigatePhoto(-1);
                            break;
                        case 'ArrowRight':
                            navigatePhoto(1);
                            break;
                    }
                    e.preventDefault();
                }
            });
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
        full_photo_count = len(db.photos(intrash=False, movies=False))
        
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
            'estimated_savings': f"~{estimated_full_savings:.0f} MB" if estimated_full_savings > 0 else "TBD",
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

@app.route('/api/library-stats')
def api_library_stats():
    """Fast endpoint for basic library statistics without analysis"""
    global cached_library_stats, cached_library_timestamp
    
    try:
        # Check if we have cached stats from smart analysis first (preferred)
        now = datetime.now()
        if (cached_library_stats is not None and cached_library_timestamp is not None and 
            (now - cached_library_timestamp).total_seconds() < 1800):
            print("📋 Using cached library stats from smart analysis")
            stats = cached_library_stats
            return jsonify({
                'success': True,
                'stats': {
                    'total_photos': stats['total_photos'],
                    'total_size_gb': stats['total_size_gb'],
                    'estimated_duplicates': stats['estimated_duplicates'],
                    'potential_savings_gb': stats['potential_savings_gb'],
                    'date_range_start': stats['date_range_start'],
                    'date_range_end': stats['date_range_end'],
                    'potential_groups': stats['potential_groups'],
                    'camera_models': stats['camera_models']
                }
            })
        
        # Fall back to fresh computation if no cached data
        scanner = PhotoScanner()
        db = scanner.get_photosdb()
        
        # Get basic stats without expensive operations
        photos = db.photos(intrash=False, movies=False)
        total_photos = len(photos)
        
        if total_photos == 0:
            return jsonify({
                'success': True,
                'stats': {
                    'total_photos': 0,
                    'total_size_gb': 0,
                    'estimated_duplicates': 'TBD',
                    'potential_savings_gb': None,
                    'date_range_start': None,
                    'date_range_end': None,
                    'potential_groups': 'TBD',
                    'camera_models': []
                }
            })
        
        # Basic calculations
        total_size = sum(p.original_filesize for p in photos if p.original_filesize)
        total_size_gb = total_size / (1024 ** 3)
        
        # Get date range
        dates = [p.date for p in photos if p.date]
        if dates:
            date_range_start = min(dates).isoformat()
            date_range_end = max(dates).isoformat()
        else:
            date_range_start = None
            date_range_end = None
        
        # Get camera models (limit to prevent slowdown)
        camera_models = []
        for p in photos[:1000]:
            if hasattr(p, 'exif_info') and p.exif_info:
                camera_model = getattr(p.exif_info, 'camera_model', None)
                if camera_model:
                    camera_models.append(camera_model)
        camera_models = list(set(camera_models))[:10]
        
        return jsonify({
            'success': True,
            'stats': {
                'total_photos': total_photos,
                'total_size_gb': round(total_size_gb, 1),
                'estimated_duplicates': 'TBD',
                'potential_savings_gb': None,
                'date_range_start': date_range_start,
                'date_range_end': date_range_end,
                'potential_groups': 'TBD',
                'camera_models': camera_models
            }
        })
    
    except Exception as e:
        print(f"❌ Error in library stats: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/filter-preview')
def api_filter_preview():
    """Preview how many photos match the filter criteria"""
    try:
        min_size_mb = float(request.args.get('min_size_mb', 5))
        min_size_bytes = min_size_mb * 1024 * 1024
        
        scanner = PhotoScanner()
        db = scanner.get_photosdb()
        photos = db.photos(intrash=False, movies=False)
        
        total_photos = len(photos)
        if total_photos == 0:
            return jsonify({
                'success': True,
                'filtered_count': 0,
                'percentage': 0,
                'total_photos': 0
            })
        
        # Filter by file size
        filtered_photos = [p for p in photos if p.original_filesize and p.original_filesize >= min_size_bytes]
        filtered_count = len(filtered_photos)
        percentage = (filtered_count / total_photos) * 100 if total_photos > 0 else 0
        
        return jsonify({
            'success': True,
            'filtered_count': filtered_count,
            'percentage': percentage,
            'total_photos': total_photos
        })
    
    except Exception as e:
        print(f"❌ Error in filter preview: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/smart-analysis', methods=['POST'])
def api_smart_analysis():
    """Run focused analysis with user-specified parameters"""
    try:
        data = request.get_json()
        min_size_mb = data.get('min_size_mb', 5)
        analysis_type = data.get('analysis_type', 'metadata')
        max_photos = data.get('max_photos', 500)
        
        min_size_bytes = min_size_mb * 1024 * 1024
        
        print(f"🎯 Starting smart analysis: {analysis_type}, min_size={min_size_mb}MB, max={max_photos}")
        
        scanner = PhotoScanner()
        db = scanner.get_photosdb()
        
        # Get ALL photos first
        all_photos = db.photos(intrash=False)
        print(f"📚 Total library: {len(all_photos)} photos")
        
        # Filter by size across ENTIRE library
        size_filtered = [p for p in all_photos 
                        if p.original_filesize and p.original_filesize >= min_size_bytes]
        print(f"📈 Photos ≥{min_size_mb}MB: {len(size_filtered)} ({len(size_filtered)/len(all_photos)*100:.1f}%)")
        
        # Sort by file size (largest first) to prioritize biggest savings
        size_filtered.sort(key=lambda p: p.original_filesize, reverse=True)
        
        # NOW limit to prevent infinite processing, but from the largest files
        photos = size_filtered[:max_photos]
        print(f"🎯 Analyzing top {len(photos)} largest files")
        
        print(f"📈 Analyzing {len(photos)} photos (filtered from library)")
        
        # Convert PhotoInfo objects to PhotoData objects
        print(f"🔄 Converting {len(photos)} photos to PhotoData format...")
        photo_data_list = []
        for photo in photos:
            photo_data = scanner.extract_photo_metadata(photo)
            photo_data_list.append(photo_data)
        
        if analysis_type == 'metadata':
            # Fast metadata-only grouping
            groups = scanner.group_photos_by_time_and_camera(photo_data_list)
        else:
            # Smart grouping with basic quality hints but no full analysis
            groups = scanner.group_photos_by_time_and_camera(photo_data_list)
        
        # Priority scoring helper functions
        def _calculate_priority_score(group):
            """Calculate real priority score (0-100) based on duplicate confidence indicators"""
            if not group.photos or len(group.photos) < 2:
                return 0
            
            # Factor 1: File size factor (40%) - Larger files = higher priority for savings
            avg_file_size = sum(p.file_size for p in group.photos) / len(group.photos)
            file_size_mb = avg_file_size / (1024 * 1024)
            # Scale: 0MB=0, 10MB=50, 20MB+=100
            file_size_factor = min(100, (file_size_mb / 10.0) * 50)
            
            # Factor 2: Time proximity factor (30%) - Closer timestamps = higher confidence
            timestamps = [p.timestamp for p in group.photos if p.timestamp]
            if len(timestamps) >= 2:
                time_span = max(timestamps) - min(timestamps)
                time_span_seconds = time_span.total_seconds()
                # Scale: 0s=100, 10s=80, 60s=20, 300s+=0
                time_proximity_factor = max(0, 100 - (time_span_seconds / 3.0))
            else:
                time_proximity_factor = 0
                
            # Factor 3: Group confidence factor (20%) - More photos + same camera = higher confidence
            group_size_factor = min(100, (len(group.photos) - 1) * 25)  # 2 photos=25, 3=50, 4+=75-100
            
            # Same camera bonus
            cameras = set(p.camera_model for p in group.photos if p.camera_model)
            camera_factor = 100 if len(cameras) == 1 and list(cameras)[0] else 50
            group_confidence_factor = (group_size_factor + camera_factor) / 2
            
            # Factor 4: Similarity factor (10%) - Quality scores and potential visual similarity  
            quality_scores = [p.quality_score for p in group.photos if p.quality_score > 0]
            if quality_scores:
                # High variation in quality scores suggests one clear best photo
                quality_variation = max(quality_scores) - min(quality_scores) if len(quality_scores) > 1 else 0
                similarity_factor = min(100, quality_variation * 2)  # Higher variation = clearer duplicate
            else:
                similarity_factor = 50  # Neutral if no quality data
            
            # Combine factors with weights
            priority_score = (
                file_size_factor * 0.4 +
                time_proximity_factor * 0.3 + 
                group_confidence_factor * 0.2 +
                similarity_factor * 0.1
            )
            
            priority_score = min(100, max(0, priority_score))
            
            # Debug logging for priority calculation
            print(f"📊 Group {group.group_id}: score={priority_score:.1f} (size={file_size_factor:.1f}, time={time_proximity_factor:.1f}, group={group_confidence_factor:.1f}, sim={similarity_factor:.1f})")
            
            return priority_score
        
        def _score_to_priority_level(score):
            """Convert 0-100 priority score to P1-P10 level"""
            if score >= 90: return "P1"    # Perfect matches - large files, perfect timing  
            elif score >= 80: return "P2"  # Very high confidence - burst photos, large savings
            elif score >= 70: return "P3"  # High confidence - clear duplicates, good savings
            elif score >= 60: return "P4"  # High-medium confidence
            elif score >= 50: return "P5"  # Medium+ confidence  
            elif score >= 40: return "P6"  # Medium confidence
            elif score >= 30: return "P7"  # Medium-low confidence
            elif score >= 20: return "P8"  # Low+ confidence
            elif score >= 10: return "P9"  # Low confidence
            else: return "P10"              # Lowest confidence
        
        # Convert to clusters for dashboard display with real priority scoring
        clusters = []
        for i, group in enumerate(groups[:50]):  # Limit to 50 groups
            # Calculate real priority score based on duplicate confidence
            priority_score = _calculate_priority_score(group)
            priority_level = _score_to_priority_level(priority_score)
            
            cluster = type('Cluster', (), {
                'cluster_id': f"cluster_{i}",  # Fix: use cluster_id instead of group_id
                'group_id': f"cluster_{i}",    # Keep group_id for compatibility
                'photos': group.photos,
                'duplicate_probability_score': priority_score,  # Real confidence score
                'potential_savings_bytes': group.potential_savings_bytes,
                'priority_level': priority_level,  # Real P1-P10 based on confidence
                'recommended_photo': group.photos[0] if group.photos else None,
                'photo_uuids': [p.uuid for p in group.photos]  # Add photo_uuids for legacy compatibility
            })()
            clusters.append(cluster)
        
        # Create dashboard data structure
        priority_summary = {}
        for p_level in [f"P{i}" for i in range(1, 11)]:
            level_clusters = [c for c in clusters if c.priority_level == p_level]
            if level_clusters:
                priority_summary[p_level] = {
                    'count': len(level_clusters),
                    'total_savings_mb': sum(c.potential_savings_bytes for c in level_clusters) / (1024*1024),
                    'photo_count': sum(len(c.photos) for c in level_clusters)
                }
            else:
                priority_summary[p_level] = {
                    'count': 0,
                    'total_savings_mb': 0,
                    'photo_count': 0
                }
        
        # Create stats - use full library counts, not just analyzed subset
        total_savings = sum(g.potential_savings_bytes for g in groups)
        total_library_size = sum(p.original_filesize for p in all_photos if p.original_filesize) / (1024**3)
        
        stats = {
            'total_photos': len(all_photos),  # Show total library count, not just analyzed photos
            'total_size_gb': total_library_size,  # Show total library size, not just analyzed photos  
            'estimated_duplicates': len([g for g in groups if len(g.photos) > 1]),
            'potential_savings_gb': total_savings / (1024**3),
            'potential_groups': len(groups),
            'date_range_start': min(p.date for p in all_photos if p.date).isoformat() if any(p.date for p in all_photos) else None,
            'date_range_end': max(p.date for p in all_photos if p.date).isoformat() if any(p.date for p in all_photos) else None,
            'camera_models': list(set([getattr(p.exif_info, 'camera_model', None) for p in all_photos[:1000] 
                                    if hasattr(p, 'exif_info') and p.exif_info and getattr(p.exif_info, 'camera_model', None)]))[:10],
            'photos_analyzed': len(photo_data_list)  # Add separate field for analyzed count
        }
        
        # Cache results globally so legacy interface can use them
        global cached_library_stats, cached_clusters, cached_library_timestamp, cached_groups, cached_timestamp
        cached_library_stats = stats
        cached_clusters = clusters
        cached_library_timestamp = datetime.now()
        
        # Also update the legacy cache system with the same data
        # This ensures both interfaces use the same analysis results
        cached_groups = groups
        cached_timestamp = datetime.now()
        
        dashboard_data = {
            'library_stats': stats,
            'priority_summary': priority_summary,
            'cluster_count': len(clusters)
        }
        
        # Log priority distribution summary
        priority_distribution = {}
        for cluster in clusters:
            level = cluster.priority_level
            priority_distribution[level] = priority_distribution.get(level, 0) + 1
        
        print(f"✅ Smart analysis complete: {len(groups)} groups, {len(clusters)} clusters")
        print(f"🎯 Real priority distribution: {dict(sorted(priority_distribution.items()))}")
        print(f"🔄 Updated both cache systems for unified data access")
        
        return jsonify({
            'success': True,
            'dashboard': dashboard_data,
            'analysis_type': analysis_type,
            'photos_analyzed': len(photos)
        })
    
    except Exception as e:
        print(f"❌ Error in smart analysis: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/dashboard')
def api_dashboard():
    """API endpoint for dashboard with library overview and cluster analysis."""
    global cached_library_stats, cached_clusters, cached_library_timestamp
    
    try:
        # Check if we have cached results (valid for 30 minutes)
        now = datetime.now()
        if (cached_library_stats is not None and cached_clusters is not None and 
            cached_library_timestamp is not None and 
            (now - cached_library_timestamp).total_seconds() < 1800):
            print("📋 Using cached dashboard data")
            stats = cached_library_stats
            clusters = cached_clusters
        else:
            print("🔄 Computing fresh dashboard data...")
            
            # Fast library scan
            stats, photos = analyzer.quick_scan_library()
            
            # Identify clusters
            clusters = analyzer.identify_clusters(photos)
            
            # Update stats with cluster information
            stats.estimated_duplicates = sum(cluster.photo_count for cluster in clusters)
            stats.potential_savings_bytes = sum(cluster.potential_savings_bytes for cluster in clusters)
            
            # Cache results
            cached_library_stats = stats
            cached_clusters = clusters
            cached_library_timestamp = now
        
        # Generate priority summary
        priority_summary = analyzer.generate_priority_summary(clusters)
        
        # Convert to JSON-serializable format with appropriate rounding for estimates
        dashboard_data = {
            'library_stats': {
                'total_photos': stats.total_photos,
                'date_range_start': stats.date_range_start.isoformat(),
                'date_range_end': stats.date_range_end.isoformat(),
                'total_size_gb': round(stats.total_size_bytes / (1024*1024*1024), 1),
                'estimated_duplicates': stats.estimated_duplicates,
                'potential_savings_gb': round(stats.potential_savings_bytes / (1024*1024*1024), 1),
                'camera_models': stats.camera_models[:10],  # Top 10 cameras
                'has_location_data': stats.has_location_data
            },
            'priority_summary': priority_summary,
            'cluster_count': len(clusters),
            'timestamp': now.isoformat()
        }
        
        return jsonify({
            'success': True,
            'dashboard': dashboard_data
        })
        
    except Exception as e:
        error_msg = str(e)
        print(f"Error in api_dashboard: {error_msg}")
        print(traceback.format_exc())
        
        return jsonify({
            'success': False,
            'error': error_msg,
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/clusters/<priority>')
def api_clusters_by_priority(priority):
    """API endpoint returning clusters filtered by priority level."""
    global cached_clusters
    
    try:
        if cached_clusters is None:
            return jsonify({
                'success': False,
                'error': 'No cluster data available. Please load dashboard first.',
                'clusters': []
            }), 400
        
        # Filter clusters by priority
        valid_priorities = [f'P{i}' for i in range(1, 11)]  # P1-P10
        if priority not in valid_priorities:
            return jsonify({
                'success': False,
                'error': f'Invalid priority. Must be one of: {valid_priorities}',
                'clusters': []
            }), 400
        
        filtered_clusters = [c for c in cached_clusters if c.priority_level == priority]
        
        # Convert to JSON-serializable format
        clusters_data = []
        for cluster in filtered_clusters:
            cluster_data = {
                'cluster_id': cluster.cluster_id,
                'photo_count': cluster.photo_count,
                'time_span_start': cluster.time_span_start.isoformat(),
                'time_span_end': cluster.time_span_end.isoformat(),
                'total_size_mb': cluster.total_size_bytes / (1024*1024),
                'potential_savings_mb': cluster.potential_savings_bytes / (1024*1024),
                'duplicate_probability_score': cluster.duplicate_probability_score,
                'priority_level': cluster.priority_level,
                'camera_model': cluster.camera_model,
                'location_summary': cluster.location_summary,
                'photo_uuids': cluster.photo_uuids
            }
            clusters_data.append(cluster_data)
        
        # Sort by duplicate probability score (highest first)
        clusters_data.sort(key=lambda x: x['duplicate_probability_score'], reverse=True)
        
        return jsonify({
            'success': True,
            'priority': priority,
            'clusters': clusters_data,
            'total_clusters': len(clusters_data)
        })
        
    except Exception as e:
        error_msg = str(e)
        print(f"Error in api_clusters_by_priority: {error_msg}")
        print(traceback.format_exc())
        
        return jsonify({
            'success': False,
            'error': error_msg,
            'clusters': []
        }), 500

@app.route('/api/analyze-cluster/<cluster_id>')
def api_analyze_cluster(cluster_id):
    """Deep analysis of specific photo cluster with full visual similarity analysis."""
    global cached_clusters
    
    try:
        if cached_clusters is None:
            return jsonify({
                'success': False,
                'error': 'No cluster data available. Please load dashboard first.',
                'groups': []
            }), 400
        
        # Find the specific cluster
        target_cluster = None
        for cluster in cached_clusters:
            if cluster.cluster_id == cluster_id:
                target_cluster = cluster
                break
        
        if not target_cluster:
            return jsonify({
                'success': False,
                'error': f'Cluster {cluster_id} not found.',
                'groups': []
            }), 404
        
        print(f"🔍 Deep analysis of cluster {cluster_id} with {target_cluster.photo_count} photos...")
        
        # Get the full photo objects for this cluster
        db = scanner.get_photosdb()
        photos = []
        for uuid in target_cluster.photo_uuids:
            for photo in db.photos(intrash=False):
                if photo.uuid == uuid:
                    photos.append(photo)
                    break
        
        if not photos:
            return jsonify({
                'success': False,
                'error': f'No photos found for cluster {cluster_id}.',
                'groups': []
            }), 404
        
        # Convert to PhotoData objects
        photo_data_list = []
        for photo in photos:
            photo_data = scanner.extract_photo_metadata(photo)
            photo_data_list.append(photo_data)
        
        # Run enhanced grouping with visual similarity for this specific cluster
        initial_groups = scanner.group_photos_by_time_and_camera(photo_data_list, time_window_seconds=30)  # Wider window for cluster analysis
        enhanced_groups = scanner.enhanced_grouping_with_similarity(initial_groups, progress_callback=update_progress)
        final_groups = scanner.filter_groups_by_visual_similarity(enhanced_groups, similarity_threshold=70.0)
        
        # Convert to JSON-serializable format
        groups_data = []
        for group in final_groups:
            group_data = {
                'group_id': f"{cluster_id}_{group.group_id}",
                'photos': [
                    {
                        'uuid': photo.uuid,
                        'filename': photo.original_filename or photo.filename,
                        'original_filename': photo.original_filename,
                        'timestamp': photo.timestamp.isoformat() if photo.timestamp else None,
                        'camera_model': photo.camera_model,
                        'file_size': photo.file_size,
                        'width': photo.width,
                        'height': photo.height,
                        'format': photo.format,
                        'quality_score': photo.quality_score,
                        'organization_score': getattr(photo, 'organization_score', 0.0),
                        'albums': getattr(photo, 'albums', []) or [],
                        'folder_names': getattr(photo, 'folder_names', []) or [],
                        'keywords': getattr(photo, 'keywords', []) or [],
                        'recommended': photo.uuid == group.recommended_photo_uuid
                    }
                    for photo in group.photos
                ],
                'time_window_start': group.time_window_start.isoformat(),
                'time_window_end': group.time_window_end.isoformat(),
                'camera_model': group.camera_model,
                'total_size_bytes': group.total_size_bytes,
                'potential_savings_bytes': group.potential_savings_bytes,
                'cluster_source': cluster_id,
                'original_cluster_score': target_cluster.duplicate_probability_score
            }
            groups_data.append(group_data)
        
        return jsonify({
            'success': True,
            'cluster_id': cluster_id,
            'groups': groups_data,
            'total_groups': len(groups_data),
            'original_cluster_info': {
                'photo_count': target_cluster.photo_count,
                'duplicate_probability_score': target_cluster.duplicate_probability_score,
                'priority_level': target_cluster.priority_level
            }
        })
        
    except Exception as e:
        error_msg = str(e)
        print(f"Error in api_analyze_cluster: {error_msg}")
        print(traceback.format_exc())
        
        return jsonify({
            'success': False,
            'error': error_msg,
            'groups': []
        }), 500

@app.route('/api/groups')
def api_groups():
    """API endpoint returning photo groups for review."""
    global cached_groups, cached_timestamp, cached_clusters
    
    try:
        # Check for priority-based analysis request
        priority = request.args.get('priority')
        limit = request.args.get('limit', 10, type=int)  # Default to 10 for better UX
        
        if priority and cached_clusters is not None:
            print(f"🎯 Priority-based analysis requested: {priority} (limit: {limit})")
            
            # Get clusters for the specified priority
            priority_clusters = [c for c in cached_clusters if c.priority_level == priority]
            
            if not priority_clusters:
                return jsonify({
                    'success': True,
                    'groups': [],
                    'total_groups': 0,
                    'message': f'No {priority} priority clusters found'
                })
            
            # Sort by duplicate probability score and take top clusters
            priority_clusters.sort(key=lambda c: c.duplicate_probability_score, reverse=True)
            selected_clusters = priority_clusters[:limit]
            
            print(f"📊 Analyzing top {len(selected_clusters)} {priority} priority clusters...")
            
            # Analyze each cluster and collect groups
            all_groups = []
            for cluster in selected_clusters:
                print(f"🔍 Analyzing cluster {cluster.cluster_id} (score: {cluster.duplicate_probability_score})")
                
                # Get the full photo objects for this cluster
                db = scanner.get_photosdb()
                photos = []
                for uuid in cluster.photo_uuids:
                    for photo in db.photos(intrash=False):
                        if photo.uuid == uuid:
                            photos.append(photo)
                            break
                
                if photos:
                    # Convert to PhotoData objects
                    photo_data_list = []
                    for photo in photos:
                        photo_data = scanner.extract_photo_metadata(photo)
                        photo_data_list.append(photo_data)
                    
                    # Run enhanced grouping for this cluster
                    cluster_groups = scanner.group_photos_by_time_and_camera(photo_data_list, time_window_seconds=30)
                    enhanced_groups = scanner.enhanced_grouping_with_similarity(cluster_groups, progress_callback=update_progress)
                    final_groups = scanner.filter_groups_by_visual_similarity(enhanced_groups, similarity_threshold=70.0)
                    
                    # Add cluster info to groups
                    for group in final_groups:
                        group.group_id = f"{cluster.cluster_id}_{group.group_id}"
                        all_groups.append(group)
            
            groups = all_groups
            print(f"✅ Priority analysis complete: {len(groups)} groups from {len(selected_clusters)} clusters")
            
            # Sort groups by total size (largest first) and limit to 10
            groups.sort(key=lambda g: g.total_size_bytes, reverse=True)
            if len(groups) > 10:
                groups = groups[:10]
                print(f"📊 Limited to top 10 largest groups for manageable review session")
            
        else:
            # Original behavior for non-priority requests
            # Check if we have cached results from smart analysis first (preferred)
            now = datetime.now()
            if (cached_groups is not None and cached_timestamp is not None and 
                (now - cached_timestamp).total_seconds() < 300):
                print("📋 Using cached photo groups from smart analysis")
                groups = cached_groups
            else:
                print("🔄 Computing fresh photo groups...")
                
                # Start progress tracking
                update_progress("Initializing analysis", 0, 4, "Setting up photo deduplication analysis...")
                
                # For photo scanning, we need a larger sample to find duplicates
                # The limit parameter controls output groups, not input photos
                scan_limit = 5000  # Scan more photos to find duplicates
                
                # Step 1: Scan photos
                update_progress("Scanning Photos library", 1, 4, f"Analyzing up to {scan_limit:,} photos from your library...")
                photos = scanner.scan_photos(limit=scan_limit)
                
                if not photos:
                    complete_progress()
                    return jsonify({
                        'success': True,
                        'groups': [],
                        'total_groups': 0,
                        'message': 'No photos found'
                    })
                
                # Step 2: Group photos by time and camera
                update_progress("Grouping photos", 2, 4, f"Creating groups from {len(photos):,} photos using 10-second windows and camera matching...")
                groups = scanner.group_photos_by_time_and_camera(photos)
                
                # Step 3: Enhanced grouping with quality analysis
                update_progress("Analyzing image quality", 3, 4, f"Computing quality scores for {len(groups):,} photo groups using sharpness and composition analysis...")
                groups = scanner.enhanced_grouping_with_similarity(groups, progress_callback=update_progress)
                
                # Step 4: Visual similarity filtering
                update_progress("Filtering by visual similarity", 4, 4, f"Comparing visual similarity to prevent unrelated photos in same group (70% threshold)...")
                groups = scanner.filter_groups_by_visual_similarity(groups, similarity_threshold=70.0)
                
                # Complete progress tracking
                complete_progress()
                
                # Cache results
                cached_groups = groups
                cached_timestamp = now
        
        # Apply limit for manageable review sessions
        if len(groups) > 10:
            groups = groups[:10]
            print(f"📊 Limited to top 10 groups for manageable review session")
        
        # Convert groups to JSON-serializable format
        groups_data = []
        for group in groups:
            group_data = {
                'group_id': group.group_id,
                'photos': [
                    {
                        'uuid': photo.uuid,
                        'filename': photo.original_filename or photo.filename,
                        'original_filename': photo.original_filename,
                        'timestamp': photo.timestamp.isoformat() if photo.timestamp else None,
                        'camera_model': photo.camera_model,
                        'file_size': photo.file_size,
                        'width': photo.width,
                        'height': photo.height,
                        'format': photo.format,
                        'quality_score': photo.quality_score,
                        'organization_score': getattr(photo, 'organization_score', 0.0),
                        'albums': getattr(photo, 'albums', []) or [],
                        'folder_names': getattr(photo, 'folder_names', []) or [],
                        'keywords': getattr(photo, 'keywords', []) or [],
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
        photos = db.photos(intrash=False, movies=False)
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
            # Method 2: Download iCloud photo if needed
            print(f"Photo {photo_uuid} not locally available, attempting iCloud download...")
            try:
                temp_export_path = os.path.join(THUMBNAIL_DIR, f"{photo_uuid}_export")
                os.makedirs(temp_export_path, exist_ok=True)
                
                # Force download from iCloud with explicit options
                exported_paths = photo.export(
                    temp_export_path, 
                    overwrite=True,
                    use_photos_export=True,  # Use Photos app export API (may download from iCloud)
                    timeout=60  # 60 second timeout for downloads
                )
                
                if exported_paths and len(exported_paths) > 0 and os.path.exists(exported_paths[0]):
                    photo_path = exported_paths[0]
                    print(f"✅ Successfully downloaded and using: {photo_path}")
                    print(f"   File size: {os.path.getsize(photo_path)} bytes")
                else:
                    print(f"❌ Export returned no valid files for {photo_uuid}")
                    print(f"   Exported paths: {exported_paths}")
                    
            except Exception as e:
                print(f"❌ Download/export failed for {photo_uuid}: {e}")
                import traceback
                traceback.print_exc()
        
        if not photo_path:
            print(f"❌ No accessible path found for {photo_uuid} after all attempts")
            return jsonify({'error': 'Photo file not accessible - download failed or restricted'}), 404
        
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
                # Use larger thumbnails for better quality assessment
                original_size = img.size
                img.thumbnail((600, 600), Image.Resampling.LANCZOS)
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

@app.route('/api/full-image/<photo_uuid>')
def api_full_image(photo_uuid):
    """Serve full-resolution photo by UUID for preview modal."""
    try:
        # Find the photo in our database using the photos list
        db = scanner.get_photosdb()
        photos = db.photos(intrash=False, movies=False)
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
            print(f"Using direct path for full image {photo_uuid}: {photo_path}")
        else:
            # Method 2: Check if we already exported this for thumbnails
            temp_export_path = os.path.join(THUMBNAIL_DIR, f"{photo_uuid}_export")
            if os.path.exists(temp_export_path):
                exported_files = os.listdir(temp_export_path)
                if exported_files:
                    photo_path = os.path.join(temp_export_path, exported_files[0])
                    print(f"Using previously exported file for {photo_uuid}: {photo_path}")
            
            # Method 3: Download iCloud photo if needed
            if not photo_path:
                print(f"Photo {photo_uuid} not locally available, attempting iCloud download...")
                try:
                    os.makedirs(temp_export_path, exist_ok=True)
                    
                    # Force download from iCloud with explicit options
                    exported_paths = photo.export(
                        temp_export_path, 
                        overwrite=True,
                        use_photos_export=True,  # Use Photos app export API (may download from iCloud)
                        timeout=60  # 60 second timeout for downloads
                    )
                    
                    if exported_paths and len(exported_paths) > 0 and os.path.exists(exported_paths[0]):
                        photo_path = exported_paths[0]
                        print(f"✅ Successfully downloaded full image: {photo_path}")
                    else:
                        print(f"❌ Export returned no valid files for {photo_uuid}")
                        
                except Exception as e:
                    print(f"❌ Download/export failed for {photo_uuid}: {e}")
        
        if not photo_path or not os.path.exists(photo_path):
            print(f"❌ No accessible path found for full image {photo_uuid}")
            return jsonify({'error': 'Photo file not accessible - download failed or restricted'}), 404
        
        # Check if this is a video file
        if photo_path.lower().endswith(('.mov', '.mp4', '.avi', '.m4v')):
            print(f"Skipping video file for {photo_uuid}: {photo_path}")
            return jsonify({'error': 'Full image not available for video files'}), 404
        
        # Serve the full-resolution image directly
        try:
            # Get the MIME type based on file extension
            file_ext = os.path.splitext(photo_path)[1].lower()
            if file_ext in ['.jpg', '.jpeg']:
                mimetype = 'image/jpeg'
            elif file_ext in ['.png']:
                mimetype = 'image/png'
            elif file_ext in ['.heic', '.heif']:
                # For HEIC files, we might need to convert to JPEG for web display
                mimetype = 'image/heic'
            else:
                mimetype = 'image/jpeg'  # Default fallback
            
            print(f"Serving full image for {photo_uuid}: {photo_path} ({mimetype})")
            return send_file(photo_path, mimetype=mimetype)
            
        except Exception as e:
            print(f"Error serving full image for {photo_uuid}: {e}")
            return jsonify({'error': 'Could not serve full image'}), 500
            
    except Exception as e:
        print(f"Error in full image endpoint: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/open-photo/<photo_uuid>', methods=['POST'])
def api_open_photo(photo_uuid):
    """Open specific photo in Photos app using AppleScript."""
    try:
        # Find the photo in our database
        db = scanner.get_photosdb()
        photos = db.photos(intrash=False, movies=False)
        photo = None
        
        for p in photos:
            if p.uuid == photo_uuid:
                photo = p
                break
        
        if not photo:
            return jsonify({'success': False, 'error': 'Photo not found'}), 404
        
        # For more specific search, combine filename with date information
        search_filename = photo.original_filename or photo.filename
        if '.' in search_filename:
            search_filename = search_filename.rsplit('.', 1)[0]  # Remove extension
        
        # Add date to make search more specific
        date_str = ""
        if photo.date:
            # Format as "Jan 2023" or similar
            date_str = f" {photo.date.strftime('%b %Y')}"
        
        # First try: Open Photos and navigate to the Moment/Day containing this photo
        applescript = f'''
        on run
            tell application "Photos"
                activate
                delay 1
                
                try
                    -- Try to find photo by UUID first (most reliable)
                    set foundPhoto to media item id "{photo_uuid}"
                    if foundPhoto exists then
                        spotlight foundPhoto
                        return "success: found by UUID"
                    end if
                on error
                    -- UUID approach failed, continue to search
                end try
                
                -- Navigate to Library view
                tell application "System Events"
                    tell process "Photos"
                        -- Go to Photos main library
                        try
                            click menu item "Photos" of menu "View" of menu bar 1
                            delay 1
                        end try
                        
                        -- Open search
                        keystroke "f" using command down
                        delay 1
                        
                        -- Clear and search for filename with date
                        keystroke "a" using command down
                        delay 0.3
                        keystroke "{search_filename}{date_str}"
                        delay 2
                        keystroke return
                        delay 2
                        
                        -- If results found, select first result
                        try
                            keystroke return
                            delay 1
                        end try
                    end tell
                end tell
                
                return "success: searched for {search_filename}{date_str}"
            end tell
        end run
        '''
        
        search_term = f"{search_filename}{date_str}"
        print(f"🔍 Searching for photo: {search_term}")
        
        import subprocess
        result = subprocess.run(
            ['osascript', '-e', applescript], 
            capture_output=True, 
            text=True, 
            timeout=20
        )
        
        print(f"📄 AppleScript result: {result.returncode}")
        if result.stderr:
            print(f"⚠️ AppleScript stderr: {result.stderr}")
        if result.stdout:
            print(f"📝 AppleScript stdout: {result.stdout}")
        
        if result.returncode == 0:
            success_msg = "Found and opened specific photo!" if "found by UUID" in str(result.stdout) else f'Searched for "{search_term}" in Photos app'
            return jsonify({
                'success': True, 
                'message': success_msg
            })
        else:
            # If AppleScript fails, try simpler approach - just open Photos
            simple_script = '''
            tell application "Photos"
                activate
                delay 0.5
            end tell
            '''
            
            subprocess.run(['osascript', '-e', simple_script], timeout=5)
            
            return jsonify({
                'success': False, 
                'error': f'Could not search automatically. Photos app opened. Search manually for: {search_term}',
                'search_term': search_term
            })
                
    except subprocess.TimeoutExpired:
        return jsonify({
            'success': False, 
            'error': 'AppleScript timeout - Photos app may be unresponsive'
        }), 500
    except Exception as e:
        return jsonify({
            'success': False, 
            'error': f'Error opening photo: {str(e)}'
        }), 500

# ========================================
# Stage 4: Photos Library Integration
# ========================================

@app.route('/api/complete-workflow', methods=['POST'])
def api_complete_workflow():
    """Complete the full photo tagging and organization workflow."""
    try:
        data = request.json
        photo_uuids = data.get('photo_uuids', [])
        estimated_savings_mb = data.get('estimated_savings_mb', 0)
        
        if not photo_uuids:
            return jsonify({'success': False, 'error': 'No photos provided'}), 400
        
        session_id = f"session-{int(datetime.now().timestamp())}"
        print(f"🚀 Starting complete workflow for {len(photo_uuids)} photos")
        
        # Execute the actual tagging workflow
        tagging_result = tagger.tag_photos_for_deletion(photo_uuids, session_id)
        
        # Get photo details for export
        db = scanner.get_photosdb()
        photos = db.photos(intrash=False, movies=False)
        photo_lookup = {p.uuid: p for p in photos}
        
        export_data = []
        for uuid in photo_uuids:
            if uuid in photo_lookup:
                photo = photo_lookup[uuid]
                # Extract metadata safely with fallbacks
                camera_make = None
                camera_model = None
                if hasattr(photo, 'exif_info') and photo.exif_info:
                    camera_make = getattr(photo.exif_info, 'camera_make', None)
                    camera_model = getattr(photo.exif_info, 'camera_model', None)
                
                export_data.append({
                    'uuid': uuid,
                    'filename': photo.original_filename or photo.filename or f"{uuid}.unknown",
                    'timestamp': photo.date.isoformat() if photo.date else None,
                    'file_size_mb': round((photo.original_filesize or 0) / (1024*1024), 2),
                    'camera_model': camera_model or 'Unknown',
                    'width': photo.width or 0,
                    'height': photo.height or 0,
                    'format': photo.uti.split('.')[-1].upper() if hasattr(photo, 'uti') and photo.uti else 'Unknown',
                    'quality_score': getattr(photo, 'quality_score', 0),
                    'session_id': session_id,
                    'marked_timestamp': datetime.now().isoformat(),
                    'tagged_successfully': uuid in [photo_uuid for photo_uuid in photo_uuids[:tagging_result.photos_tagged]]
                })
        
        # Export deletion list to files
        export_files = tagger.export_deletion_list(export_data, session_id)
        tagging_result.export_files = export_files
        
        # Calculate final stats
        total_size_mb = sum(item['file_size_mb'] for item in export_data)
        
        return jsonify({
            'success': True,
            'tagging_result': {
                'photos_tagged': tagging_result.photos_tagged,
                'photos_failed': tagging_result.photos_failed,
                'smart_album_created': tagging_result.smart_album_created,
                'album_name': tagging_result.album_name,
                'errors': tagging_result.errors,
                'export_files': tagging_result.export_files
            },
            'summary': {
                'session_id': session_id,
                'photos_processed': len(export_data),
                'photos_tagged_successfully': tagging_result.photos_tagged,
                'estimated_savings_mb': estimated_savings_mb,
                'actual_size_mb': total_size_mb,
                'album_name': tagging_result.album_name,
                'timestamp': datetime.now().isoformat(),
                'next_steps': [
                    f"✅ {tagging_result.photos_tagged} photos tagged with 'marked-for-deletion' keyword",
                    f"📁 Check Photos app for smart album: '{tagging_result.album_name}'",
                    "👀 Review photos in the smart album",
                    "🗑️ Manually delete photos you want to remove",
                    f"📄 Deletion lists exported to Desktop: {len(tagging_result.export_files)} files"
                ] if tagging_result.photos_tagged > 0 else [
                    "⚠️ No photos were successfully tagged",
                    "📄 Deletion list still exported for manual processing",
                    "🔧 Check console for error details"
                ]
            },
            'export_data': export_data,
            'workflow_guidance': {
                'tagging_status': f"Tagged {tagging_result.photos_tagged} of {len(photo_uuids)} photos successfully",
                'album_status': f"Smart album {'created' if tagging_result.smart_album_created else 'creation attempted (may require manual setup)'}",
                'export_status': f"Exported {len(tagging_result.export_files)} files to Desktop",
                'safety_reminder': "⚠️ This tool tags photos but does not delete them. You maintain full control over deletions."
            }
        })
        
    except Exception as e:
        print(f"Error in complete workflow endpoint: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/create-album', methods=['POST'])
def api_create_album():
    """Create a Photos album with specified photos marked for deletion."""
    try:
        data = request.get_json()
        
        # Get photo UUIDs that should be marked for deletion
        photo_uuids = data.get('photo_uuids', [])
        album_name = data.get('album_name', '')
        
        if not photo_uuids:
            return jsonify({'error': 'No photo UUIDs provided'}), 400
        
        if not album_name:
            # Generate default album name with timestamp
            from datetime import datetime
            timestamp = datetime.now().strftime("%b-%d at %H:%M")
            album_name = f"Marked for Deletion - {timestamp}"
        
        print(f"🎯 Creating album '{album_name}' with {len(photo_uuids)} photos...")
        
        # Use PhotoTagger to create album
        success = tagger.create_album_from_uuids(album_name, photo_uuids)
        
        if success:
            return jsonify({
                'success': True,
                'album_name': album_name,
                'photos_added': len(photo_uuids),
                'message': f'Successfully created album "{album_name}" with {len(photo_uuids)} photos'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to create album - check server logs for details'
            }), 500
        
    except Exception as e:
        print(f"Error in create album endpoint: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/health')
def api_health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'stage': 'Stage 4: Photos Library Integration'
    })

if __name__ == '__main__':
    print("🚀 Starting Photo Dedup Tool - Stage 5: Heatmap Dashboard")
    print("🏷️ NEW: Smart targeting with priority-based analysis!")
    print("🖼️ WORKING: Interactive dashboard with cluster analysis!")
    print("🔍 ENHANCED: Fast library scan + targeted photo review!")
    print("🌐 Open http://127.0.0.1:5003 in your browser")
    print(f"📁 Thumbnails cached in: {THUMBNAIL_DIR}")
    print("=" * 60)
    
    # Run Flask app
    app.run(host='127.0.0.1', port=5003, debug=True)