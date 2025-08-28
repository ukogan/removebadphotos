#!/usr/bin/env python3
"""
Photo Deduplication Tool - Flask Backend
Stage 2: Core photo analysis with grouping and similarity detection
"""

from flask import Flask, render_template_string, jsonify, request, send_file, session
from flask_cors import CORS
from datetime import datetime
import traceback
import os
import secrets
from photo_scanner import PhotoScanner
from library_analyzer import LibraryAnalyzer
from photo_tagger import PhotoTagger
from lazy_photo_loader import LazyPhotoLoader
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

# Configure session management for filter-to-dashboard data flow
app.secret_key = secrets.token_hex(32)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True for HTTPS in production
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour session timeout

# Global instances
scanner = PhotoScanner()
analyzer = LibraryAnalyzer()
tagger = PhotoTagger()
lazy_loader = LazyPhotoLoader(analyzer, scanner)
cached_groups = None
cached_timestamp = None
cached_library_stats = None
cached_clusters = None
cached_library_timestamp = None

# Analysis cache for streamlined workflow
analysis_cache = {}
CACHE_EXPIRY_MINUTES = 30
MAX_CACHED_ANALYSES = 10

# Server-side session storage to avoid large cookies
server_side_sessions = {}

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

@app.route('/filters')
def filters():
    """Stage 5B: Smart filter interface for targeted duplicate analysis."""
    try:
        with open('/Users/urikogan/code/dedup/filter_interface.html', 'r') as f:
            return f.read()
    except Exception as e:
        print(f"Error serving filter interface: {e}")
        return f"Error loading filter interface: {e}", 500

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
                border: 1px solid #e2e8f0;
                border-radius: 12px;
                padding: 20px;
                margin: 12px;
                text-align: center;
                transition: all 0.3s ease;
                background-color: white;
                position: relative;
                box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            }
            
            .photo-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 25px rgba(0,0,0,0.12);
            }
            
            .photo-card.recommended {
                border-color: #ffc107;
                background-color: #fff9e6;
                box-shadow: 0 4px 12px rgba(255, 193, 7, 0.2);
            }
            
            .photo-card.recommended::before {
                content: "⭐ RECOMMENDED";
                position: absolute;
                top: 12px;
                left: 12px;
                background: #ffc107;
                color: #212529;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 0.75rem;
                font-weight: bold;
                z-index: 2;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            
            .photo-card.selected {
                border: 3px solid #ef4444;
                background: linear-gradient(rgba(239, 68, 68, 0.03), rgba(239, 68, 68, 0.08));
                box-shadow: 0 4px 16px rgba(239, 68, 68, 0.25);
            }
            
            .photo-card.selected .photo-thumbnail {
                opacity: 0.7;
                position: relative;
            }
            
            .photo-card.selected .photo-thumbnail::after {
                content: "MARKED FOR DELETION";
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                background: rgba(239, 68, 68, 0.9);
                color: white;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: 600;
                font-size: 0.9rem;
                box-shadow: 0 2px 8px rgba(0,0,0,0.3);
            }
            
            .photo-action-button {
                transition: all 0.2s ease;
            }
            
            .photo-action-button:hover {
                transform: scale(1.02);
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            }
            
            .photo-action-button.mark-delete:hover {
                background: #dc2626 !important;
                box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3) !important;
            }
            
            .photo-action-button.remove-mark:hover {
                background: #4b5563 !important;
                box-shadow: 0 4px 12px rgba(107, 114, 128, 0.3) !important;
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
            
            /* Photo interaction improvements - hover to show preview icon */
            .photo-image-container:hover .preview-icon {
                display: flex !important;
            }
            
            .preview-icon:hover {
                background: rgba(0,0,0,0.9) !important;
                transform: scale(1.1);
            }
            
            /* Improved photo card cursor and interaction */
            .photo-thumbnail:hover {
                opacity: 0.9;
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

        <!-- Pagination controls -->
        <div id="paginationControls" class="controls" style="display: none;">
            <button class="btn" onclick="loadMoreGroups()" id="loadMoreBtn">📄 Load More Groups</button>
            <span id="paginationStatus" style="margin-left: 15px;"></span>
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
            
            // Pagination variables
            let currentPage = 1;
            let totalGroupsAvailable = 0;
            let hasMoreGroups = false;
            
            // Toast notification system
            function showToast(message, type = 'info', duration = 3000) {
                const toast = document.createElement('div');
                toast.className = `toast toast-${type}`;
                toast.style.cssText = `
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    z-index: 1000;
                    padding: 12px 16px;
                    border-radius: 8px;
                    color: white;
                    font-weight: 600;
                    max-width: 400px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                    background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#6b7280'};
                    transform: translateX(100%);
                    transition: transform 0.3s ease;
                `;
                toast.textContent = message;
                
                document.body.appendChild(toast);
                
                // Animate in
                setTimeout(() => toast.style.transform = 'translateX(0)', 10);
                
                // Auto dismiss
                setTimeout(() => {
                    toast.style.transform = 'translateX(100%)';
                    setTimeout(() => document.body.removeChild(toast), 300);
                }, duration);
            }

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
                            
                            // Update pagination state
                            totalGroupsAvailable = data.total_groups || data.groups.length;
                            hasMoreGroups = data.has_next || false;
                            
                            status.innerHTML = `✅ Analysis Complete • Found ${data.total_groups} groups`;
                            status.title = 'Photo analysis completed successfully';
                            btn.innerHTML = '✅ Analysis Complete';
                            groupsLoaded = true;
                            
                            // Show pagination controls if there are more groups
                            if (hasMoreGroups) {
                                const paginationControls = document.getElementById('paginationControls');
                                const paginationStatus = document.getElementById('paginationStatus');
                                paginationControls.style.display = 'block';
                                paginationStatus.innerHTML = `Showing ${data.groups.length} of ${totalGroupsAvailable} groups`;
                            }
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
            
            function loadMoreGroups() {
                if (!hasMoreGroups) return;
                
                const btn = document.getElementById('loadMoreBtn');
                const status = document.getElementById('paginationStatus');
                
                btn.disabled = true;
                btn.innerHTML = '⏳ Loading...';
                
                // Get URL parameters
                const urlParams = new URLSearchParams(window.location.search);
                const priority = urlParams.get('priority');
                const limit = urlParams.get('limit') || '10';
                
                // Calculate next page
                const nextPage = currentPage + 1;
                
                let apiUrl;
                if (priority) {
                    // Use priority-filtered API endpoint with pagination
                    apiUrl = `/api/groups?priority=${priority}&limit=${limit}&page=${nextPage}`;
                } else {
                    // Use full analysis API endpoint with pagination
                    apiUrl = `/api/groups?limit=${limit}&page=${nextPage}`;
                }
                
                fetch(apiUrl)
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            // Append new groups to existing ones
                            allGroups = [...allGroups, ...data.groups];
                            appendGroups(data.groups); // Need to create this function
                            
                            // Update pagination state
                            currentPage = nextPage;
                            hasMoreGroups = data.has_next || false;
                            
                            if (hasMoreGroups) {
                                btn.disabled = false;
                                btn.innerHTML = '📄 Load More Groups';
                                status.innerHTML = `Showing ${allGroups.length} of ${totalGroupsAvailable} groups`;
                            } else {
                                btn.style.display = 'none';
                                status.innerHTML = `✅ All ${totalGroupsAvailable} groups loaded`;
                            }
                        } else {
                            status.innerHTML = `❌ Failed to load more groups: ${data.error}`;
                            btn.disabled = false;
                            btn.innerHTML = '📄 Load More Groups';
                        }
                    })
                    .catch(error => {
                        status.innerHTML = `❌ Failed to load more groups: ${error}`;
                        btn.disabled = false;
                        btn.innerHTML = '📄 Load More Groups';
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
                                    <div>📸 <strong>Photos:</strong> ${group.photo_count || 0}</div>
                                    <div>💾 <strong>Total Size:</strong> ${group.total_size_mb ? group.total_size_mb + ' MB' : 'TBD'}</div>
                                    <div>💰 <strong>Est. Savings:</strong> ~${group.potential_savings_mb ? group.potential_savings_mb + ' MB' : 'TBD'}</div>
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
                                <div class="photo-image-container" style="position: relative; cursor: pointer;">
                                    <img class="photo-thumbnail" 
                                         src="/api/thumbnail/${photo.uuid}" 
                                         alt="${photo.filename}"
                                         style="display: none;"
                                         onload="this.style.display='block'; document.getElementById('loading_${photo.uuid}').style.display='none';"
                                         onerror="this.style.display='none'; document.getElementById('loading_${photo.uuid}').innerHTML='❌ Could not load image';"
                                         onclick="togglePhotoSelection('${group.group_id}', '${photo.uuid}')"
                                         ondblclick="event.stopPropagation(); openPreview('${group.group_id}', ${group.photos.indexOf(photo)});">
                                    <div class="preview-icon" onclick="event.stopPropagation(); openPreview('${group.group_id}', ${group.photos.indexOf(photo)});" 
                                         style="position: absolute; top: 8px; right: 8px; background: rgba(0,0,0,0.7); color: white; border-radius: 50%; width: 32px; height: 32px; display: none; align-items: center; justify-content: center; cursor: pointer; font-size: 14px; transition: all 0.2s ease;">🔍</div>
                                </div>
                                <div class="photo-filename" onclick="event.stopPropagation(); openInPhotos('${photo.uuid}')">${photo.filename}</div>
                                <div class="photo-info">
                                    <div>📅 ${timestamp}</div>
                                    <div>💾 ${fileSize}</div>
                                    <div>⭐ ${photo.quality_score ? photo.quality_score.toFixed(1) : '0.0'} ${photo.quality_method === 'favorite' ? '(favorite)' : photo.quality_method === 'quality' ? '(quality)' : photo.quality_method === 'inferred quality' ? '(inferred)' : ''}</div>
                                </div>
                                <button class="photo-action-button ${isSelected ? 'remove-mark' : 'mark-delete'}" onclick="togglePhotoSelection('${group.group_id}', '${photo.uuid}')" style="width: 100%; height: 50px; border-radius: 8px; border: 2px solid ${isSelected ? '#6b7280' : '#dc2626'}; font-size: 16px; font-weight: 600; display: flex; align-items: center; justify-content: center; cursor: pointer; transition: all 0.2s ease; background: ${isSelected ? '#6b7280' : '#ef4444'}; color: white; margin-top: 8px;">
                                    ${isSelected ? 'Remove Mark' : 'Mark for Deletion'}
                                </button>
                            </div>
                        `;
                    });
                    
                    html += '</div></div>';
                });
                
                container.innerHTML = html;
                updateSelectionSummary();
            }
            
            function appendGroups(groups) {
                const container = document.getElementById('groupsContainer');
                
                if (groups.length === 0) return;
                
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
                                    <div>📸 <strong>Photos:</strong> ${group.photo_count || 0}</div>
                                    <div>💾 <strong>Total Size:</strong> ${group.total_size_mb ? group.total_size_mb + ' MB' : 'TBD'}</div>
                                    <div>💰 <strong>Est. Savings:</strong> ~${group.potential_savings_mb ? group.potential_savings_mb + ' MB' : 'TBD'}</div>
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
                        const fileSize = photo.file_size > 0 ? `${(photo.file_size / (1024*1024)).toFixed(1)} MB` : 'Unknown';
                        
                        const isSelected = photoSelections[group.group_id].includes(photo.uuid);
                        
                        html += `
                            <div class="photo-card ${isSelected ? 'selected' : ''}" data-group="${group.group_id}" data-photo="${photo.uuid}" data-photo-index="${group.photos.indexOf(photo)}">
                                <div class="photo-loading" id="loading_${photo.uuid}">📷 Loading...</div>
                                <div class="photo-image-container" style="position: relative; cursor: pointer;">
                                    <img class="photo-thumbnail" 
                                         src="/api/thumbnail/${photo.uuid}" 
                                         alt="${photo.filename}"
                                         style="display: none;" 
                                         onload="this.style.display='block'; document.getElementById('loading_${photo.uuid}').style.display='none';"
                                         onerror="this.style.display='none'; document.getElementById('loading_${photo.uuid}').innerHTML='❌ Could not load image';"
                                         onclick="togglePhotoSelection('${group.group_id}', '${photo.uuid}')"
                                         ondblclick="event.stopPropagation(); openPreview('${group.group_id}', ${group.photos.indexOf(photo)});">
                                    <div class="preview-icon" onclick="event.stopPropagation(); openPreview('${group.group_id}', ${group.photos.indexOf(photo)});" 
                                         style="position: absolute; top: 8px; right: 8px; background: rgba(0,0,0,0.7); color: white; border-radius: 50%; width: 32px; height: 32px; display: none; align-items: center; justify-content: center; cursor: pointer; font-size: 14px; transition: all 0.2s ease;">🔍</div>
                                </div>
                                <div class="photo-filename" onclick="event.stopPropagation(); openInPhotos('${photo.uuid}')">${photo.filename}</div>
                                <div class="photo-info">
                                    <div>📅 ${timestamp}</div>
                                    <div>💾 ${fileSize}</div>
                                    <div>⭐ ${photo.quality_score ? photo.quality_score.toFixed(1) : '0.0'} ${photo.quality_method === 'favorite' ? '(favorite)' : photo.quality_method === 'quality' ? '(quality)' : photo.quality_method === 'inferred quality' ? '(inferred)' : ''}</div>
                                </div>
                                <button class="photo-action-button ${isSelected ? 'remove-mark' : 'mark-delete'}" onclick="togglePhotoSelection('${group.group_id}', '${photo.uuid}')" style="width: 100%; height: 50px; border-radius: 8px; border: 2px solid ${isSelected ? '#6b7280' : '#dc2626'}; font-size: 16px; font-weight: 600; display: flex; align-items: center; justify-content: center; cursor: pointer; transition: all 0.2s ease; background: ${isSelected ? '#6b7280' : '#ef4444'}; color: white; margin-top: 8px;">
                                    ${isSelected ? 'Remove Mark' : 'Mark for Deletion'}
                                </button>
                            </div>
                        `;
                    });
                    
                    html += '</div></div>';
                });
                
                // Append to existing container content
                container.innerHTML += html;
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
                    
                    // Update card classes based on selection state
                    card.className = 'photo-card';
                    if (isSelected) {
                        card.className += ' selected'; // Selected = DELETE target
                    }
                    
                    // Update button appearance and text
                    const button = card.querySelector('.photo-action-button');
                    if (button) {
                        // Update button classes
                        button.className = `photo-action-button ${isSelected ? 'remove-mark' : 'mark-delete'}`;
                        
                        // Update button text
                        button.textContent = isSelected ? 'Remove Mark' : 'Mark for Deletion';
                        
                        // Update button styling
                        if (isSelected) {
                            button.style.background = '#6b7280';
                            button.style.borderColor = '#6b7280';
                        } else {
                            button.style.background = '#ef4444';
                            button.style.borderColor = '#dc2626';
                        }
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
                if (confirm('Mark all photos in this group for deletion?')) {
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
                
                // Show simplified toast notification
                showToast(`✅ ${summary.photos_processed} photos marked for deletion and added to "${summary.album_name}" album for your final review • ${summary.estimated_savings_mb.toFixed(0)} MB freed`, 'success', 4000);
                
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
                    💾 ${fileSize}<br>
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
                        💾 ${fileSize}<br>
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
        
        # Scan photos (limited for performance testing)
        photos = scanner.scan_photos(limit=500)  # Increased from 200 for better sample representation
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
        
        # Get basic stats without expensive operations - excluding marked for deletion
        photos, excluded_count = scanner.get_unprocessed_photos(include_videos=False)
        total_photos = len(photos)
        if excluded_count > 0:
            print(f"📊 Library stats: excluded {excluded_count} photos already marked for deletion")
        
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
        photos, excluded_count = scanner.get_unprocessed_photos(include_videos=False)
        if excluded_count > 0:
            print(f"🗑️ Filter preview: excluded {excluded_count} photos already marked for deletion")
        
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

def run_filtered_analysis(filter_session, min_size_mb, analysis_type, max_photos):
    """Run analysis on only the selected photos from filter interface"""
    try:
        print(f"🎯 Running filtered analysis on {filter_session['total_photos_in_filter']} selected photos")
        
        scanner = PhotoScanner()
        db = scanner.get_photosdb()
        
        # Get the selected photo UUIDs
        selected_photo_uuids = filter_session.get('selected_photo_uuids', [])
        if not selected_photo_uuids:
            return jsonify({
                'success': False,
                'error': 'No selected photos found in filter session'
            })
        
        print(f"📋 Working with {len(selected_photo_uuids)} selected photo UUIDs")
        
        # Get all unprocessed photos from library and filter to only selected ones (excludes marked for deletion)
        all_photos, excluded_count = scanner.get_unprocessed_photos(include_videos=True)
        selected_photos = [p for p in all_photos if p.uuid in selected_photo_uuids]
        print(f"🔄 Excluded {excluded_count} photos already marked for deletion from filter selection")
        
        print(f"✅ Found {len(selected_photos)} photos matching selected UUIDs")
        
        if not selected_photos:
            print(f"❌ CRITICAL: Found {len(selected_photos)} photos out of {len(selected_photo_uuids)} requested UUIDs")
            return jsonify({
                'success': False,
                'error': f'No matching photos found in library for selected UUIDs. Expected {len(selected_photo_uuids)} photos but found 0. This may indicate a database sync issue or that the photos have been moved/deleted.',
                'debug_info': {
                    'requested_uuids': len(selected_photo_uuids),
                    'found_photos': 0,
                    'sample_uuids': selected_photo_uuids[:5]  # First 5 for debugging
                }
            })
        
        # Report UUID resolution success rate
        uuid_success_rate = len(selected_photos) / len(selected_photo_uuids) * 100
        print(f"📊 UUID Resolution: {len(selected_photos)}/{len(selected_photo_uuids)} photos found ({uuid_success_rate:.1f}%)")
        
        if uuid_success_rate < 80:  # Less than 80% found
            print(f"⚠️ WARNING: Low UUID resolution rate ({uuid_success_rate:.1f}%) may indicate data issues")
        
        # Apply size filtering on the selected photos
        min_size_bytes = min_size_mb * 1024 * 1024
        size_filtered_photos = [p for p in selected_photos 
                               if p.original_filesize and p.original_filesize >= min_size_bytes]
        
        print(f"📈 Photos ≥{min_size_mb}MB in selection: {len(size_filtered_photos)}")
        
        # If no photos meet size criteria, use all selected photos
        if not size_filtered_photos:
            print("⚠️ No photos meet size criteria, using all selected photos")
            photos_to_analyze = selected_photos
        else:
            photos_to_analyze = size_filtered_photos
        
        # Sort by file size (largest first) for priority analysis
        photos_to_analyze.sort(key=lambda p: p.original_filesize or 0, reverse=True)
        
        # Limit to max_photos for performance
        if len(photos_to_analyze) > max_photos:
            print(f"🔄 Limiting analysis to top {max_photos} largest photos")
            photos_to_analyze = photos_to_analyze[:max_photos]
        
        print(f"🔍 Converting {len(photos_to_analyze)} photos to PhotoData format...")
        
        # Convert PhotoInfo objects to PhotoData objects
        photo_data_list = []
        for photo in photos_to_analyze:
            try:
                photo_data = scanner.extract_photo_metadata(photo)
                photo_data_list.append(photo_data)
            except Exception as e:
                print(f"⚠️ Error processing photo {photo.uuid}: {e}")
                continue
        
        print(f"✅ Successfully processed {len(photo_data_list)} photos")
        
        if not photo_data_list:
            return jsonify({
                'success': False,
                'error': 'No photos could be processed for analysis'
            })
        
        # Group the selected photos
        if analysis_type == 'metadata':
            groups = scanner.group_photos_by_time_and_camera(photo_data_list)
        else:
            groups = scanner.group_photos_by_time_and_camera(photo_data_list)
        
        print(f"📊 Created {len(groups)} groups from selected photos")
        
        # Apply the same priority scoring from the main analysis function
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
        
        # Convert to clusters for dashboard display
        clusters = []
        for i, group in enumerate(groups):
            priority_score = _calculate_priority_score(group)
            priority_level = _score_to_priority_level(priority_score)
            
            cluster = type('Cluster', (), {
                'cluster_id': f"filtered_cluster_{i}",
                'group_id': f"filtered_cluster_{i}",
                'photos': group.photos,
                'duplicate_probability_score': priority_score,
                'potential_savings_bytes': group.potential_savings_bytes,
                'priority_level': priority_level,
                'recommended_photo': group.photos[0] if group.photos else None,
                'photo_uuids': [p.uuid for p in group.photos]
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
        
        # Get library stats (but keep them as overview stats for context) - excluding marked for deletion
        all_photos, _ = scanner.get_unprocessed_photos(include_videos=True)
        total_savings = sum(g.potential_savings_bytes for g in filtered_groups)
        total_library_size = sum(p.original_filesize for p in all_photos if p.original_filesize) / (1024**3)
        
        stats = {
            'total_photos': len(all_photos),  # Keep full library count for context
            'total_size_gb': total_library_size,  # Keep full library size for context
            'estimated_duplicates': len(filtered_groups),  # But show only filtered duplicates
            'potential_savings_gb': total_savings / (1024**3),  # Only savings from filtered selection
            'potential_groups': len(filtered_groups),  # Only filtered groups
            'date_range_start': min(p.date for p in all_photos if p.date).isoformat() if any(p.date for p in all_photos) else None,
            'date_range_end': max(p.date for p in all_photos if p.date).isoformat() if any(p.date for p in all_photos) else None,
            'camera_models': list(set([getattr(p.exif_info, 'camera_model', None) for p in all_photos[:1000] 
                                    if hasattr(p, 'exif_info') and p.exif_info and getattr(p.exif_info, 'camera_model', None)]))[:10],
            'photos_analyzed': len(all_group_photos),  # Photos in the filtered selection
            'filtered_mode': True  # Flag to indicate this is filtered analysis
        }
        
        # Cache results globally
        global cached_library_stats, cached_clusters, cached_library_timestamp, cached_groups, cached_timestamp
        cached_library_stats = stats
        cached_clusters = clusters
        cached_library_timestamp = datetime.now()
        cached_groups = filtered_groups
        cached_timestamp = datetime.now()
        
        dashboard_data = {
            'library_stats': stats,
            'priority_summary': priority_summary,
            'cluster_count': len(clusters)
        }
        
        print(f"✅ Filtered analysis complete: {len(filtered_groups)} groups, {len(clusters)} clusters")
        print(f"🎯 Analysis focused on {len(all_group_photos)} photos from selected clusters")
        
        return jsonify({
            'success': True,
            'dashboard': dashboard_data,
            'analysis_type': f"{analysis_type}_filtered",
            'photos_analyzed': len(all_group_photos),
            'mode': 'filtered'
        })
        
    except Exception as e:
        print(f"❌ Error in filtered analysis: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        })

def apply_filter_criteria(photos, criteria):
    """Apply filter criteria to photo list"""
    filtered = photos
    
    # Year range filter - support both single year and year range
    if criteria.get('start_year') and criteria.get('end_year'):
        start_year = int(criteria['start_year'])
        end_year = int(criteria['end_year'])
        filtered = [p for p in filtered if p.date and start_year <= p.date.year <= end_year]
    elif criteria.get('year'):
        # Single year support (from filter interface)
        year = int(criteria['year'])
        filtered = [p for p in filtered if p.date and p.date.year == year]
    
    # File type filter  
    if criteria.get('file_types'):
        file_types = [ft.lower() for ft in criteria['file_types']]
        filtered = [p for p in filtered if p.path_edited and any(p.path_edited.lower().endswith(f'.{ft}') for ft in file_types)]
    
    # Size filter
    if criteria.get('min_size_mb'):
        min_size_bytes = criteria['min_size_mb'] * 1024 * 1024
        filtered = [p for p in filtered if p.original_filesize and p.original_filesize >= min_size_bytes]
    
    return filtered

@app.route('/api/smart-analysis', methods=['POST'])
def api_smart_analysis():
    """Run focused analysis with user-specified parameters"""
    try:
        data = request.get_json()
        min_size_mb = data.get('min_size_mb', 5)
        analysis_type = data.get('analysis_type', 'metadata')
        max_photos = data.get('max_photos', 500)
        
        min_size_bytes = min_size_mb * 1024 * 1024
        
        # Check for filter session data
        filter_session = session.get('filter_session')
        if filter_session:
            print(f"🎯 Filtered analysis mode: analyzing {filter_session['total_clusters_in_filter']} selected clusters")
            return run_filtered_analysis(filter_session, min_size_mb, analysis_type, max_photos)
        
        print(f"🎯 Starting overview analysis: {analysis_type}, min_size={min_size_mb}MB, max={max_photos}")
        
        scanner = PhotoScanner()
        
        # Get ALL unprocessed photos first (excludes marked for deletion)
        all_photos, excluded_count = scanner.get_unprocessed_photos(include_videos=True)
        print(f"📚 Total library: {len(all_photos)} photos (excluded {excluded_count} already marked for deletion)")
        
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
                        'quality_method': getattr(photo, 'quality_method', 'unknown'),
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
    """API endpoint returning photo groups for review.
    
    CRITICAL: This endpoint must use ONLY the filtered session data.
    The workflow is: filter → analyze → legacy shows ONLY filtered results.
    """
    global cached_groups, cached_timestamp, scanner
    
    try:
        limit = request.args.get('limit', 10, type=int)
        page = request.args.get('page', 1, type=int)
        priority = request.args.get('priority')
        
        print(f"🎯 api_groups called with limit={limit}, page={page}, priority={priority}")
        print(f"🎯 Session keys: {list(session.keys())}")
        
        # NEW: Check for unified analysis cache first (streamlined workflow)
        if analysis_cache:
            latest_cache_key = max(analysis_cache.keys(), key=lambda k: analysis_cache[k]['timestamp'])
            cached_analysis = analysis_cache[latest_cache_key]
            
            # Check if cache is still valid
            from datetime import timedelta
            if datetime.now() - cached_analysis['timestamp'] <= timedelta(minutes=CACHE_EXPIRY_MINUTES):
                print(f"🚀 Using unified analysis cache: {latest_cache_key} ({len(cached_analysis['all_groups'])} groups)")
                
                all_groups = cached_analysis['all_groups']
                
                # Convert unified format to legacy format
                legacy_groups = []
                for group in all_groups:
                    legacy_group = {
                        'group_id': group['id'],
                        'photos': [
                            {
                                'uuid': photo['uuid'],
                                'filename': photo['filename'],
                                'original_filename': photo.get('original_filename'),
                                'timestamp': photo.get('timestamp'),
                                'camera_model': photo.get('camera_model', 'Unknown'),
                                'file_size': photo.get('file_size_bytes', 0),
                                'width': 0,  # Not available in unified format
                                'height': 0,  # Not available in unified format
                                'format': 'Unknown',  # Not available in unified format
                                'quality_score': photo.get('quality_score', 0.0),
                                'quality_method': photo.get('quality_method', 'unknown'),
                                'organization_score': 0.0,  # Not available in unified format
                                'albums': [],  # Not available in unified format
                                'folder_names': [],  # Not available in unified format
                                'keywords': [],  # Not available in unified format
                                'recommended': photo['uuid'] == group['impact']['best_photo_uuid']
                            }
                            for photo in group['photos']
                        ],
                        'time_window_start': group.get('timestamp', ''),
                        'time_window_end': group.get('timestamp', ''),
                        'camera_model': group.get('camera_model', 'Unknown'),
                        'total_size_bytes': group['impact']['total_savings_bytes'] + max(photo.get('file_size_bytes', 0) for photo in group['photos']),
                        'potential_savings_bytes': group['impact']['total_savings_bytes'],
                        'recommended_photo_uuid': group['impact']['best_photo_uuid']
                    }
                    legacy_groups.append(legacy_group)
                
                # Apply pagination
                start_idx = (page - 1) * limit
                end_idx = start_idx + limit
                paginated_groups = legacy_groups[start_idx:end_idx]
                
                print(f"📄 Returning page {page}: groups {start_idx+1}-{min(end_idx, len(all_groups))} of {len(all_groups)}")
                
                return jsonify({
                    'success': True,
                    'groups': paginated_groups,
                    'total_groups': len(all_groups),
                    'current_page': page,
                    'total_pages': (len(all_groups) + limit - 1) // limit,
                    'has_next': end_idx < len(all_groups),
                    'has_previous': page > 1,
                    'mode': 'unified_analysis',
                    'cache_key': latest_cache_key,
                    'message': f'Showing {len(paginated_groups)} groups from unified analysis (page {page})'
                })
        
        # NEW: Check for streamlined filter criteria workflow  
        filter_criteria_session = session.get('filter_criteria')
        if filter_criteria_session and filter_criteria_session.get('type') == 'criteria_only':
            print(f"🎯 STREAMLINED WORKFLOW: Found saved filter criteria: {filter_criteria_session.get('filters', {})}")
            
            # We have filter criteria but no processed results yet
            # This means the user came from /filters -> Apply Filters -> /legacy
            # We need to process their filters now
            
            try:
                # Use lazy loader to get filtered clusters based on saved criteria
                filters = filter_criteria_session.get('filters', {})
                
                # Ensure lazy loader cache is available (should be initialized by heatmap-data call)
                if not lazy_loader._cluster_cache or not lazy_loader._metadata_cache:
                    print("⚠️ Lazy loader cache not initialized, initializing now...")
                    stats, clusters = lazy_loader.get_library_metadata_fast()
                
                # Apply filters using lazy loader's filtering system
                filtered_clusters = lazy_loader.load_filtered_clusters(filters)
                print(f"📊 After applying filters: {len(filtered_clusters)} clusters remain")
                
                if not filtered_clusters:
                    return jsonify({
                        'success': True,
                        'groups': [],
                        'total_groups': 0,
                        'mode': 'criteria_no_results',
                        'message': 'No photos match the selected criteria'
                    })
                
                # Load and analyze photos from the top clusters (limit to reasonable number)
                max_clusters = min(limit * 2, len(filtered_clusters))  # Load 2x requested limit for better selection
                all_groups = []
                
                for cluster in filtered_clusters[:max_clusters]:
                    try:
                        # Analyze this cluster to get photo groups
                        cluster_groups = lazy_loader.analyze_cluster_photos(cluster.cluster_id)
                        all_groups.extend(cluster_groups)
                    except Exception as e:
                        print(f"⚠️ Error analyzing cluster {cluster.cluster_id}: {e}")
                        continue
                
                # Sort groups by potential savings (prioritize most impactful duplicates)
                final_groups = sorted(all_groups, key=lambda g: sum(p.file_size for p in g.photos), reverse=True)
                
                # Convert to API format
                groups_data = []
                for i, group in enumerate(final_groups[:limit]):
                    # Find recommended photo by UUID (groups have built-in recommendations)
                    recommended_photo = None
                    for photo in group.photos:
                        if photo.uuid == group.recommended_photo_uuid:
                            recommended_photo = photo
                            break
                    
                    # Fallback if UUID not found - use highest quality photo  
                    if not recommended_photo and group.photos:
                        recommended_photo = max(group.photos, key=lambda p: getattr(p, 'quality_score', 0.0))
                    
                    group_data = {
                        'group_id': f'streamlined_{i}',
                        'photos': [
                            {
                                'uuid': photo.uuid,
                                'filename': photo.filename,
                                'original_filename': photo.original_filename,
                                'timestamp': photo.timestamp.isoformat() if photo.timestamp else None,
                                'camera_model': photo.camera_model,
                                'file_size': photo.file_size,
                                'width': photo.width,
                                'height': photo.height,
                                'format': photo.format,
                                'quality_score': photo.quality_score,
                                'quality_method': photo.quality_method,
                                'organization_score': photo.organization_score,
                                'albums': photo.albums,
                                'folder_names': photo.folder_names,
                                'keywords': photo.keywords,
                                'recommended': (photo.uuid == recommended_photo.uuid) if recommended_photo else False
                            }
                            for photo in group.photos
                        ],
                        'time_window_start': group.time_window_start.isoformat() if group.time_window_start else None,
                        'time_window_end': group.time_window_end.isoformat() if group.time_window_end else None,
                        'camera_model': group.camera_model,
                        'total_size_bytes': sum(photo.file_size for photo in group.photos),
                        'potential_savings_bytes': sum(photo.file_size for photo in group.photos if photo.uuid != (recommended_photo.uuid if recommended_photo else None)),
                        'recommended_photo_uuid': recommended_photo.uuid if recommended_photo else None
                    }
                    groups_data.append(group_data)
                
                print(f"📊 Generated {len(groups_data)} groups from streamlined workflow")
                
                return jsonify({
                    'success': True,
                    'groups': groups_data,
                    'total_groups': len(final_groups),
                    'current_page': page,
                    'total_pages': (len(final_groups) + limit - 1) // limit,
                    'has_next': limit < len(final_groups),
                    'has_previous': page > 1,
                    'mode': 'streamlined_criteria',
                    'filter_criteria': filters,
                    'source_photos': sum(len(cluster.photo_uuids) for cluster in filtered_clusters), 
                    'message': f'Showing {len(groups_data)} groups from {len(filtered_clusters)} filtered clusters'
                })
                
            except Exception as e:
                print(f"❌ Error processing streamlined filter criteria: {e}")
                return jsonify({
                    'success': False,
                    'error': f'Error processing filter criteria: {str(e)}',
                    'mode': 'streamlined_error'
                }), 500
        
        # EXISTING: Check if we have a filtered session (the main workflow)
        filter_session = session.get('filter_session')
        print(f"🎯 Filter session: {filter_session is not None}")
        
        if filter_session:
            session_id = filter_session.get('session_id')
            server_data = server_side_sessions.get(session_id, {})
            
            if server_data and 'cluster_summaries' in server_data:
                cluster_summaries = server_data['cluster_summaries']
                selected_uuids = server_data.get('selected_photo_uuids', [])
                
                print(f"🎯 FILTERED SESSION: Using {len(cluster_summaries)} clusters with {len(selected_uuids)} photos from filtered analysis")
                
                # Convert cluster summaries to full groups format with actual photo data
                limited_clusters = cluster_summaries[:limit]
                groups_data = []
                
                # Get photo database to look up actual photo objects
                try:
                    # Use filtered photo set (excluding marked for deletion) for consistent lookup
                    filtered_photos, excluded_count = scanner.get_unprocessed_photos(include_videos=False)
                    photo_lookup = {p.uuid: p for p in filtered_photos}
                    print(f"🔍 Photo lookup ready: {len(photo_lookup)} photos indexed (excluded {excluded_count} marked for deletion)")
                    
                    for cluster in limited_clusters:
                        # Get actual photo objects for this cluster
                        cluster_photo_uuids = cluster.get('photo_uuids', [])
                        cluster_photos = []
                        
                        for photo_uuid in cluster_photo_uuids:
                            if photo_uuid in photo_lookup:
                                photo = photo_lookup[photo_uuid]
                                cluster_photos.append(photo)
                        
                        print(f"📊 Cluster {cluster.get('cluster_id', 'unknown')}: {len(cluster_photos)}/{len(cluster_photo_uuids)} photos found")
                        
                        if cluster_photos:
                            # Convert to PhotoData objects for compatibility
                            photo_data_list = []
                            for photo in cluster_photos:
                                photo_data = scanner.extract_photo_metadata(photo)
                                photo_data_list.append(photo_data)
                            
                            # Calculate required group metrics
                            total_size_bytes = sum(p.file_size for p in photo_data_list)
                            
                            # Find the recommended photo (highest quality score)
                            recommended_photo = max(photo_data_list, key=lambda p: p.quality_score or 0.0)
                            recommended_photo_uuid = recommended_photo.uuid
                            
                            # Calculate potential savings (total size minus largest file)
                            largest_file_size = max(p.file_size for p in photo_data_list) 
                            potential_savings_bytes = total_size_bytes - largest_file_size
                            
                            # Create a proper group object
                            from photo_scanner import PhotoGroup
                            group = PhotoGroup(
                                group_id=cluster.get('cluster_id', f'filtered_{len(groups_data)}'),
                                photos=photo_data_list,
                                recommended_photo_uuid=recommended_photo_uuid,
                                time_window_start=photo_data_list[0].timestamp,
                                time_window_end=photo_data_list[-1].timestamp,
                                camera_model=cluster.get('camera_model', 'Unknown'),
                                total_size_bytes=total_size_bytes,
                                potential_savings_bytes=potential_savings_bytes
                            )
                            
                            # Convert to the format expected by frontend  
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
                        else:
                            print(f"⚠️ No photos found for cluster {cluster.get('cluster_id', 'unknown')}")
                    
                except Exception as e:
                    print(f"❌ Error converting filtered clusters to groups: {e}")
                    # Fall back to basic cluster summary format
                    for cluster in limited_clusters:
                        group_data = {
                            'photos': cluster.get('photos', []),
                            'cluster_id': cluster.get('cluster_id', 'unknown'),
                            'time_span': cluster.get('time_span', 'Unknown time'),
                            'location_summary': cluster.get('location_summary', 'Unknown location'),
                            'camera_model': cluster.get('camera_model', 'Unknown camera'),
                            'duplicate_probability_score': cluster.get('duplicate_probability_score', 0),
                            'total_size_mb': cluster.get('total_size_mb', 0),
                            'potential_savings_mb': cluster.get('potential_savings_mb', 0),
                            'priority_level': cluster.get('priority_level', 'P5')
                        }
                        groups_data.append(group_data)
                
                return jsonify({
                    'success': True,
                    'groups': groups_data,
                    'total_groups': len(groups_data),
                    'mode': 'filtered',
                    'filter_criteria': filter_session.get('filter_criteria', {}),
                    'source_clusters': filter_session.get('total_clusters_in_filter', 0),
                    'source_photos': len(selected_uuids),
                    'message': f'Showing {len(groups_data)} filtered clusters'
                })
        
        # FALLBACK: Old priority-based logic (for backward compatibility)
        priority = request.args.get('priority')
        if priority and hasattr(scanner, 'cached_clusters') and scanner.cached_clusters:
            print(f"🎯 FALLBACK: Priority-based analysis requested: {priority} (limit: {limit})")
            
            # Get clusters for the specified priority  
            priority_clusters = [c for c in scanner.cached_clusters if hasattr(c, 'priority_level') and c.priority_level == priority]
            
            if not priority_clusters:
                return jsonify({
                    'success': True,
                    'groups': [],
                    'total_groups': 0,
                    'message': f'No {priority} priority clusters found'
                })
            
            # Sort by duplicate probability score and take top clusters
            priority_clusters.sort(key=lambda c: getattr(c, 'duplicate_probability_score', 0), reverse=True)
            selected_clusters = priority_clusters[:limit]
            
            print(f"📊 Analyzing top {len(selected_clusters)} {priority} priority clusters...")
            
            # Analyze each cluster and collect groups
            all_groups = []
            for cluster in selected_clusters:
                print(f"🔍 Analyzing cluster {cluster.cluster_id} (score: {cluster.duplicate_probability_score})")
                
                # Get the full photo objects for this cluster
                try:
                    db = scanner.get_photosdb()
                    photos = []
                    for uuid in cluster.photo_uuids:
                        # Use filtered photo set for consistency
                        filtered_photos, _ = scanner.get_unprocessed_photos(include_videos=False)
                        for photo in filtered_photos:
                            if photo.uuid == uuid:
                                photos.append(photo)
                                break
                except Exception as e:
                    print(f"❌ OSXPhotos error accessing database: {e}")
                    # Return empty result when OSXPhotos fails
                    return jsonify({
                        'success': False,
                        'groups': [],
                        'total_groups': 0,
                        'error': f'Photo database access error: {str(e)[:200]}',
                        'message': 'Unable to access Photos library. Please check compatibility.'
                    })
                
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
                try:
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
                except Exception as e:
                    print(f"❌ OSXPhotos error scanning photos: {e}")
                    complete_progress()
                    return jsonify({
                        'success': False,
                        'groups': [],
                        'total_groups': 0,
                        'error': f'Photo library scan error: {str(e)[:200]}',
                        'message': 'Unable to scan Photos library. Please check compatibility.'
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
                        'quality_method': getattr(photo, 'quality_method', 'unknown'),
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

@app.route('/api/analyze-filtered', methods=['POST'])
def api_analyze_filtered():
    """NEW FILTER-FIRST API: Apply filters first, then analyze only the filtered subset.
    
    This endpoint implements the correct architecture:
    1. Receives filter criteria from the client
    2. Applies filters to get a small subset (target: 50-200 photos)
    3. Analyzes ONLY that subset (should complete in 10-30 seconds)
    4. Returns duplicate groups immediately
    
    Request body should contain filter criteria:
    {
        "date_range": {"start": "2023-01-01", "end": "2023-12-31"},
        "file_types": ["HEIC", "JPEG"],
        "min_file_size_mb": 1.0,
        "max_photos": 200
    }
    """
    try:
        # Parse filter criteria from request
        filter_data = request.get_json()
        if not filter_data:
            return jsonify({
                'success': False,
                'error': 'No filter criteria provided'
            }), 400
        
        print(f"🎯 FILTER-FIRST ANALYSIS: Received filters: {filter_data}")
        
        # Step 1: Apply filters to get photo subset
        print("📋 Step 1: Applying filters to select photo subset...")
        
        # Get filter parameters
        date_range = filter_data.get('date_range')
        file_types = filter_data.get('file_types', [])
        min_file_size_mb = filter_data.get('min_file_size_mb', 0)
        max_photos = filter_data.get('max_photos', 200)  # Target: 50-200 photos
        
        # Use scanner to get filtered photos
        filtered_photos = []
        try:
            # Get all photos first (this is fast - just metadata)
            all_photos, excluded_count = scanner.get_unprocessed_photos(include_videos=False)
            print(f"📊 Retrieved {len(all_photos)} photos ({excluded_count} excluded)")
            
            # Apply date filter
            if date_range and date_range.get('start') and date_range.get('end'):
                start_date = datetime.fromisoformat(date_range['start'])
                end_date = datetime.fromisoformat(date_range['end'])
                all_photos = [p for p in all_photos if p.date and start_date <= p.date <= end_date]
            
            # Apply file type filter
            if file_types:
                # Map user-friendly names to extensions
                type_extensions = {
                    'HEIC': ['.heic', '.heif'],
                    'JPEG': ['.jpg', '.jpeg'],
                    'PNG': ['.png'],
                    'RAW': ['.raw', '.cr2', '.nef', '.arw']
                }
                allowed_extensions = []
                for file_type in file_types:
                    if file_type in type_extensions:
                        allowed_extensions.extend(type_extensions[file_type])
                
                if allowed_extensions:
                    all_photos = [p for p in all_photos if any(p.path.lower().endswith(ext) for ext in allowed_extensions)]
            
            # Apply file size filter (convert MB to bytes)
            if min_file_size_mb > 0:
                min_size_bytes = min_file_size_mb * 1024 * 1024
                all_photos = [p for p in all_photos if hasattr(p, 'filesize') and p.filesize >= min_size_bytes]
            
            # Limit to max_photos to ensure fast analysis
            filtered_photos = all_photos[:max_photos]
            
            print(f"📊 Filter results: {len(all_photos)} total → {len(filtered_photos)} filtered (limit: {max_photos})")
            
            if len(filtered_photos) == 0:
                return jsonify({
                    'success': True,
                    'groups': [],
                    'total_groups': 0,
                    'message': f'No photos match the filter criteria',
                    'stats': {
                        'photos_analyzed': 0,
                        'analysis_time_seconds': 0
                    }
                })
            
            if len(filtered_photos) > 200:
                print(f"⚠️ Warning: {len(filtered_photos)} photos selected. Consider more restrictive filters for faster analysis.")
        
        except Exception as e:
            print(f"❌ Error applying filters: {e}")
            return jsonify({
                'success': False,
                'error': f'Filter application error: {str(e)}'
            }), 500
        
        # Step 2: Analyze only the filtered subset
        print(f"🔬 Step 2: Analyzing {len(filtered_photos)} filtered photos...")
        analysis_start_time = datetime.now()
        
        try:
            # Create photo groups from filtered photos only
            photo_groups = []
            
            # Group photos by time windows (simplified approach for filtered subset)
            time_window_seconds = 10
            current_group = []
            last_timestamp = None
            
            # Sort photos by timestamp
            sorted_photos = sorted(filtered_photos, key=lambda p: p.date)
            
            for photo in sorted_photos:
                if (last_timestamp is None or 
                    (photo.date - last_timestamp).total_seconds() <= time_window_seconds):
                    # Add to current group
                    current_group.append(photo)
                else:
                    # Start new group
                    if len(current_group) > 1:  # Only keep groups with multiple photos
                        photo_groups.append(current_group)
                    current_group = [photo]
                
                last_timestamp = photo.date
            
            # Don't forget the last group
            if len(current_group) > 1:
                photo_groups.append(current_group)
            
            print(f"📊 Created {len(photo_groups)} potential duplicate groups from {len(filtered_photos)} photos")
            
            # Step 3: Convert to API response format
            api_groups = []
            for i, group in enumerate(photo_groups[:20]):  # Limit to 20 groups for now
                group_data = {
                    'group_id': f'filtered_group_{i}',
                    'photos': [],
                    'potential_savings_bytes': 0,
                    'recommended_photo_uuid': None
                }
                
                total_size = 0
                best_photo = None
                best_score = 0
                
                for photo in group:
                    # Simple quality score (can be enhanced later)
                    quality_score = 50.0  # Default
                    if hasattr(photo, 'favorite') and photo.favorite:
                        quality_score = 100.0
                    
                    photo_data = {
                        'uuid': photo.uuid,
                        'filename': photo.filename,
                        'original_filename': photo.original_filename if hasattr(photo, 'original_filename') else photo.filename,
                        'timestamp': photo.date.isoformat(),
                        'file_size': getattr(photo, 'filesize', 0),
                        'quality_score': quality_score,
                        'recommended': False  # Will be set below
                    }
                    
                    group_data['photos'].append(photo_data)
                    total_size += getattr(photo, 'filesize', 0)
                    
                    if quality_score > best_score:
                        best_score = quality_score
                        best_photo = photo.uuid
                
                # Set recommendation and savings
                group_data['recommended_photo_uuid'] = best_photo
                group_data['potential_savings_bytes'] = total_size - max(p['file_size'] for p in group_data['photos'])
                
                # Mark recommended photo
                for photo_data in group_data['photos']:
                    photo_data['recommended'] = (photo_data['uuid'] == best_photo)
                
                api_groups.append(group_data)
            
            analysis_end_time = datetime.now()
            analysis_duration = (analysis_end_time - analysis_start_time).total_seconds()
            
            print(f"✅ Filter-first analysis completed in {analysis_duration:.1f} seconds")
            
            return jsonify({
                'success': True,
                'groups': api_groups,
                'total_groups': len(api_groups),
                'message': f'Analyzed {len(filtered_photos)} filtered photos and found {len(api_groups)} duplicate groups',
                'stats': {
                    'photos_filtered': len(filtered_photos),
                    'photos_analyzed': len(filtered_photos),
                    'groups_found': len(api_groups),
                    'analysis_time_seconds': round(analysis_duration, 1),
                    'filters_applied': filter_data
                }
            })
            
        except Exception as e:
            print(f"❌ Error during filtered analysis: {e}")
            traceback.print_exc()
            return jsonify({
                'success': False,
                'error': f'Analysis error: {str(e)}'
            }), 500
    
    except Exception as e:
        print(f"❌ Error in analyze-filtered endpoint: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
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
        photos = db.photos(intrash=False, movies=False)  # Photos only - no videos
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
            print(f"Generating video thumbnail for {photo_uuid}: {photo_path}")
            try:
                # Create a simple video placeholder thumbnail
                from PIL import Image, ImageDraw, ImageFont
                
                # Create a 600x400 placeholder image
                img = Image.new('RGB', (600, 400), color=(64, 64, 64))
                draw = ImageDraw.Draw(img)
                
                # Add video icon and text
                # Draw a play button symbol
                play_triangle = [(250, 150), (250, 250), (350, 200)]
                draw.polygon(play_triangle, fill=(255, 255, 255))
                
                # Add text
                try:
                    font = ImageFont.load_default()
                except:
                    font = None
                
                text = f"VIDEO\n{photo_uuid[:8]}...\n{os.path.basename(photo_path)}"
                if font:
                    draw.text((300, 100), text, fill=(255, 255, 255), font=font, anchor="mm")
                else:
                    draw.text((300, 100), text, fill=(255, 255, 255), anchor="mm")
                
                # Save placeholder thumbnail
                img.save(thumbnail_path, 'JPEG', quality=85, optimize=True)
                print(f"Video placeholder thumbnail saved for {photo_uuid}: {thumbnail_path}")
                
                return send_file(thumbnail_path, mimetype='image/jpeg')
                
            except Exception as e:
                print(f"Error generating video placeholder for {photo_uuid}: {e}")
                return jsonify({'error': 'Could not generate video thumbnail'}), 500
        
        # Generate thumbnail
        try:
            # Ensure PIL Image is available in this scope
            from PIL import Image as PILImage
            with PILImage.open(photo_path) as img:
                print(f"Successfully opened image for {photo_uuid}: {img.size} {img.mode}")
                
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'P', 'LA'):
                    img = img.convert('RGB')
                    print(f"Converted {photo_uuid} to RGB mode")
                
                # Calculate thumbnail size maintaining aspect ratio
                # Use larger thumbnails for better quality assessment
                original_size = img.size
                img.thumbnail((600, 600), PILImage.Resampling.LANCZOS)
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

@app.route('/api/debug-filename/<filename>')
def api_debug_filename(filename):
    """Debug endpoint to search for photos by filename and check their keyword status."""
    try:
        db = scanner.get_photosdb()
        # Include photos in trash to see if that's where deleted ones are
        all_photos = db.photos(intrash=True)
        
        matches = []
        for photo in all_photos:
            photo_filename = photo.filename or photo.original_filename or ""
            if filename.lower() in photo_filename.lower():
                keywords = list(photo.keywords) if photo.keywords else []
                has_marked_for_deletion = "marked-for-deletion" in keywords
                
                matches.append({
                    "uuid": photo.uuid,
                    "filename": photo_filename,
                    "keywords": keywords,
                    "has_marked_for_deletion": has_marked_for_deletion,
                    "date": photo.date.isoformat() if photo.date else None,
                    "path": photo.path,
                    "albums": [album.title for album in photo.albums] if photo.albums else [],
                    "intrash": photo.intrash,
                    "edited": photo.hasadjustments
                })
        
        return jsonify({
            "success": True,
            "filename_searched": filename,
            "matches_found": len(matches),
            "matches": matches
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })

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
        
        session_id = f"session-{datetime.now().strftime('%Y-%m-%d %H-%M-%S')}"
        print(f"🚀 Starting complete workflow for {len(photo_uuids)} photos")
        
        # Execute the actual tagging workflow
        tagging_result = tagger.tag_photos_for_deletion(photo_uuids, session_id)
        
        # Add UUIDs to persistent tracking to prevent reappearance
        if tagging_result.photos_tagged > 0:
            scanner.add_processed_uuids(photo_uuids)
            print(f"💾 Added {len(photo_uuids)} UUIDs to persistent tracking")
        
        # Get photo details for export - use filtered photo set
        filtered_photos, excluded_count = scanner.get_unprocessed_photos(include_videos=False)
        photo_lookup = {p.uuid: p for p in filtered_photos}
        print(f"📤 Export lookup ready: {len(photo_lookup)} photos indexed (excluded {excluded_count} marked for deletion)")
        
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

# ========================================
# Stage 5A: Lazy Loading Foundation APIs
# ========================================

@app.route('/api/heatmap-data')
def api_heatmap_data():
    """Stage 5A: Fast metadata scan returning library stats + priority summary.
    
    Target: < 5 seconds for 14k+ photos
    Returns: Dashboard data with priority buckets and cluster counts
    """
    try:
        print("🚀 Stage 5A: Fast heatmap data requested...")
        
        # Use LazyPhotoLoader for fast metadata scan
        library_stats, clusters = lazy_loader.get_library_metadata_fast()
        
        # Package response with cluster information
        response_data = {
            'success': True,
            'library_stats': library_stats,
            'clusters': {
                'total_count': len(clusters),
                'priority_breakdown': library_stats['priority_summary']
            },
            'performance': {
                'scan_time_seconds': library_stats['scan_time_seconds'],
                'target_met': library_stats['scan_time_seconds'] < 5.0
            }
        }
        
        print(f"✅ Heatmap data ready: {library_stats['total_photos']} photos, {len(clusters)} clusters, {library_stats['scan_time_seconds']:.1f}s")
        
        return jsonify(response_data)
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Error in heatmap data: {error_msg}")
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'error': error_msg,
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/filter-clusters')
def api_filter_clusters():
    """Stage 5A: Apply filters to cached clusters without rescanning library.
    
    Query parameters:
    - year: int (2024, 2023, etc.)
    - min_size_mb: int 
    - max_size_mb: int
    - priority_levels: comma-separated string ("P1,P2")
    - camera_models: comma-separated string
    - file_types: comma-separated string ("HEIC,JPG,PNG")
    """
    try:
        # Parse query parameters
        filters = {}
        
        if request.args.get('year'):
            filters['year'] = int(request.args.get('year'))
        
        if request.args.get('min_size_mb'):
            filters['min_size_mb'] = int(request.args.get('min_size_mb'))
            
        if request.args.get('max_size_mb'):
            filters['max_size_mb'] = int(request.args.get('max_size_mb'))
        
        if request.args.get('priority_levels'):
            filters['priority_levels'] = request.args.get('priority_levels').split(',')
        
        if request.args.get('camera_models'):
            filters['camera_models'] = request.args.get('camera_models').split(',')
        
        if request.args.get('file_types'):
            filters['file_types'] = request.args.get('file_types').split(',')
        
        print(f"🔍 Cluster filtering requested with: {filters}")
        
        # Apply filters using LazyPhotoLoader
        filtered_clusters = lazy_loader.load_filtered_clusters(filters)
        
        # Check if photos should be included (for analysis preparation)
        include_photos = request.args.get('include_photos') == 'true'
        
        # Convert to JSON-serializable format
        clusters_data = []
        photo_loading_failures = 0
        total_photos_loaded = 0
        
        for cluster in filtered_clusters:
            cluster_data = {
                'cluster_id': cluster.cluster_id,
                'photo_count': cluster.photo_count,
                'time_span_start': cluster.time_span_start.isoformat(),
                'time_span_end': cluster.time_span_end.isoformat(),
                'total_size_mb': round(cluster.total_size_bytes / (1024*1024), 1),
                'potential_savings_mb': round(cluster.potential_savings_bytes / (1024*1024), 1),
                'duplicate_probability_score': cluster.duplicate_probability_score,
                'priority_level': cluster.priority_level,
                'camera_model': cluster.camera_model,
                'location_summary': cluster.location_summary
            }
            
            # Include photo UUIDs if requested (needed for analysis workflow)
            if include_photos and hasattr(cluster, 'photo_uuids'):
                cluster_data['photos'] = [{'uuid': uuid} for uuid in cluster.photo_uuids]
                total_photos_loaded += len(cluster.photo_uuids)
                print(f"✅ Used cached UUIDs: {len(cluster.photo_uuids)} photos for cluster {cluster.cluster_id}")
            elif include_photos:
                # Fallback: get photos from lazy loader
                try:
                    cluster_load_result = lazy_loader.load_cluster_photos(cluster.cluster_id)
                    if cluster_load_result and hasattr(cluster_load_result, 'photos') and cluster_load_result.photos:
                        cluster_data['photos'] = [{'uuid': photo.uuid} for photo in cluster_load_result.photos]
                        total_photos_loaded += len(cluster_load_result.photos)
                        print(f"✅ Loaded {len(cluster_load_result.photos)} photos for cluster {cluster.cluster_id}")
                    else:
                        print(f"⚠️ No photos found for cluster {cluster.cluster_id}")
                        cluster_data['photos'] = []
                        photo_loading_failures += 1
                except Exception as e:
                    print(f"❌ Error loading photos for cluster {cluster.cluster_id}: {e}")
                    cluster_data['photos'] = []
                    photo_loading_failures += 1
            
            clusters_data.append(cluster_data)
        
        # Sort by priority level then by duplicate probability score
        priority_order = {'P1': 1, 'P2': 2, 'P3': 3, 'P4': 4, 'P5': 5, 
                         'P6': 6, 'P7': 7, 'P8': 8, 'P9': 9, 'P10': 10}
        clusters_data.sort(key=lambda x: (priority_order.get(x['priority_level'], 99), -x['duplicate_probability_score']))
        
        # Validate photo loading if requested
        response_data = {
            'success': True,
            'filters_applied': filters,
            'clusters': clusters_data,
            'total_clusters': len(clusters_data)
        }
        
        if include_photos:
            print(f"📊 Photo loading summary: {total_photos_loaded} photos loaded, {photo_loading_failures} clusters failed")
            response_data['photo_loading_stats'] = {
                'total_photos_loaded': total_photos_loaded,
                'clusters_with_failures': photo_loading_failures,
                'success_rate': round((len(clusters_data) - photo_loading_failures) / max(len(clusters_data), 1) * 100, 1)
            }
            
            # Critical validation: Fail if too many clusters have no photos
            if photo_loading_failures > len(clusters_data) * 0.5:  # More than 50% failed
                print(f"❌ CRITICAL: {photo_loading_failures}/{len(clusters_data)} clusters failed to load photos")
                return jsonify({
                    'success': False,
                    'error': f'Photo loading failed for {photo_loading_failures} out of {len(clusters_data)} clusters. This may indicate a system issue.',
                    'photo_loading_stats': response_data['photo_loading_stats']
                }), 500
            elif photo_loading_failures > 0:
                print(f"⚠️ WARNING: {photo_loading_failures} clusters failed to load photos but continuing...")
                response_data['warning'] = f'{photo_loading_failures} clusters failed to load photos'
        
        return jsonify(response_data)
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Error in filter clusters: {error_msg}")
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'error': error_msg,
            'clusters': []
        }), 500

@app.route('/api/cluster-analysis/<cluster_id>')
def api_cluster_analysis(cluster_id):
    """Stage 5A: Deep analysis of specific cluster with lazy photo loading.
    
    Target: < 10 seconds total (load + analyze)
    Returns: Photo groups ready for user review
    """
    try:
        print(f"🔬 Cluster analysis requested: {cluster_id}")
        
        # Update progress
        update_progress(f"Loading cluster {cluster_id}", 0, 3, "Loading photos from metadata cache...")
        
        # Use LazyPhotoLoader for targeted analysis
        groups = lazy_loader.analyze_cluster_photos(cluster_id, progress_callback=update_progress)
        
        if not groups:
            complete_progress()
            return jsonify({
                'success': True,
                'cluster_id': cluster_id,
                'groups': [],
                'message': 'No photo groups found for this cluster'
            })
        
        # Update progress  
        update_progress(f"Formatting results", 2, 3, f"Converting {len(groups)} photo groups to JSON...")
        
        # Convert to JSON-serializable format
        groups_data = []
        for group in groups:
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
                        'quality_method': getattr(photo, 'quality_method', 'unknown'),
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
                'photo_count': len(group.photos),
                'cluster_source': cluster_id
            }
            groups_data.append(group_data)
        
        # Get cluster info for response
        cluster = lazy_loader.get_cluster_by_id(cluster_id)
        cluster_info = None
        if cluster:
            cluster_info = {
                'photo_count': cluster.photo_count,
                'duplicate_probability_score': cluster.duplicate_probability_score,
                'priority_level': cluster.priority_level,
                'total_size_mb': round(cluster.total_size_bytes / (1024*1024), 1),
                'potential_savings_mb': round(cluster.potential_savings_bytes / (1024*1024), 1)
            }
        
        complete_progress()
        
        print(f"✅ Cluster analysis complete: {len(groups_data)} groups ready for review")
        
        return jsonify({
            'success': True,
            'cluster_id': cluster_id,
            'groups': groups_data,
            'total_groups': len(groups_data),
            'cluster_info': cluster_info,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        complete_progress()
        error_msg = str(e)
        print(f"❌ Error in cluster analysis: {error_msg}")
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'error': error_msg,
            'cluster_id': cluster_id,
            'groups': []
        }), 500

@app.route('/api/priority-clusters/<priority>')
def api_priority_clusters(priority):
    """Stage 5A: Get all clusters for specific priority level (P1, P2, etc.)."""
    try:
        print(f"🎯 Priority clusters requested: {priority}")
        
        # Validate priority level
        valid_priorities = [f'P{i}' for i in range(1, 11)]
        if priority not in valid_priorities:
            return jsonify({
                'success': False,
                'error': f'Invalid priority. Must be one of: {valid_priorities}',
                'clusters': []
            }), 400
        
        # Get priority clusters using LazyPhotoLoader
        clusters = lazy_loader.get_priority_clusters(priority)
        
        if not clusters:
            return jsonify({
                'success': True,
                'priority': priority,
                'clusters': [],
                'message': f'No {priority} clusters found'
            })
        
        # Convert to JSON format
        clusters_data = []
        for cluster in clusters:
            cluster_data = {
                'cluster_id': cluster.cluster_id,
                'photo_count': cluster.photo_count,
                'time_span_start': cluster.time_span_start.isoformat(),
                'time_span_end': cluster.time_span_end.isoformat(),
                'total_size_mb': round(cluster.total_size_bytes / (1024*1024), 1),
                'potential_savings_mb': round(cluster.potential_savings_bytes / (1024*1024), 1),
                'duplicate_probability_score': cluster.duplicate_probability_score,
                'camera_model': cluster.camera_model,
                'location_summary': cluster.location_summary
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
        print(f"❌ Error getting priority clusters: {error_msg}")
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'error': error_msg,
            'priority': priority,
            'clusters': []
        }), 500

@app.route('/api/cache-stats')
def api_cache_stats():
    """Stage 5A: Get cache statistics for debugging and monitoring."""
    try:
        cache_stats = lazy_loader.get_cache_stats()
        
        return jsonify({
            'success': True,
            'cache_stats': cache_stats,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/clear-cache', methods=['POST'])
def api_clear_cache():
    """Stage 5A: Clear all cached data to free memory."""
    try:
        lazy_loader.clear_cache()
        
        # Also clear legacy caches
        global cached_groups, cached_timestamp, cached_library_stats, cached_clusters, cached_library_timestamp
        cached_groups = None
        cached_timestamp = None
        cached_library_stats = None
        cached_clusters = None
        cached_library_timestamp = None
        
        return jsonify({
            'success': True,
            'message': 'All caches cleared successfully',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/filter-distributions')
def api_filter_distributions():
    """Stage 5B: Get distribution statistics for all filter categories."""
    try:
        # Debug cache state
        cluster_cache_size = len(lazy_loader._cluster_cache) if lazy_loader._cluster_cache else 0
        metadata_cache_size = len(lazy_loader._metadata_cache) if lazy_loader._metadata_cache else 0
        print(f"🔍 Filter distributions: cluster_cache={cluster_cache_size}, metadata_cache={metadata_cache_size}")
        
        # Ensure we have cached data
        if not lazy_loader._cluster_cache or not lazy_loader._metadata_cache:
            return jsonify({
                'success': False,
                'error': f'No cached data available (clusters: {cluster_cache_size}, metadata: {metadata_cache_size}). Please load heatmap data first.'
            }), 400
        
        clusters = list(lazy_loader._cluster_cache.values())
        metadata = list(lazy_loader._metadata_cache.values())
        
        print(f"📊 Computing distribution statistics for {len(clusters)} clusters, {len(metadata)} photos...")
        
        # Year distribution
        year_distribution = {}
        for photo in metadata:
            year = photo.timestamp.year if photo.timestamp else 'Unknown'
            year_distribution[year] = year_distribution.get(year, 0) + 1
        
        # File type distribution  
        file_type_distribution = {}
        for photo in metadata:
            if '.' in photo.filename:
                ext = photo.filename.split('.')[-1].upper()
                # Normalize JPEG to JPG
                if ext == 'JPEG':
                    ext = 'JPG'
                file_type_distribution[ext] = file_type_distribution.get(ext, 0) + 1
        
        # Priority distribution with savings
        priority_distribution = {}
        for cluster in clusters:
            priority = cluster.priority_level
            if priority not in priority_distribution:
                priority_distribution[priority] = {
                    'cluster_count': 0,
                    'photo_count': 0,
                    'total_savings_bytes': 0,
                    'total_size_bytes': 0
                }
            
            priority_distribution[priority]['cluster_count'] += 1
            priority_distribution[priority]['photo_count'] += cluster.photo_count
            priority_distribution[priority]['total_savings_bytes'] += cluster.potential_savings_bytes
            priority_distribution[priority]['total_size_bytes'] += cluster.total_size_bytes
        
        # Size distribution (quintile-based histogram data)
        # Get all file sizes and sort them to create quintiles
        file_sizes_mb = []
        for photo in metadata:
            size_mb = photo.file_size / (1024 * 1024) if photo.file_size else 0
            file_sizes_mb.append(size_mb)
        
        file_sizes_mb.sort()
        total_photos = len(file_sizes_mb)
        
        # Calculate quintile thresholds (5 equal-photo-count bins)
        size_histogram = {}
        if total_photos > 0:
            quintile_size = total_photos // 5
            quintiles = []
            
            for i in range(5):
                start_idx = i * quintile_size
                end_idx = (i + 1) * quintile_size if i < 4 else total_photos  # Last bin gets remainder
                
                if start_idx < total_photos:
                    min_size = file_sizes_mb[start_idx]
                    max_size = file_sizes_mb[end_idx - 1] if end_idx > start_idx else min_size
                    count = end_idx - start_idx
                    
                    # Create descriptive bin labels
                    if min_size == max_size:
                        bin_label = f"{min_size:.1f}MB"
                    else:
                        bin_label = f"{min_size:.1f}-{max_size:.1f}MB"
                    
                    quintiles.append({
                        'label': bin_label,
                        'min_size': min_size,
                        'max_size': max_size,
                        'count': count,
                        'bin_index': i
                    })
                    
                    # Use bin index as key for histogram (0-4)
                    size_histogram[i] = count
        
        # Store quintile metadata for frontend use
        quintile_metadata = quintiles if total_photos > 0 else []
        
        # Calculate smart recommendations
        high_value_priorities = ['P1', 'P2']
        high_value_clusters = [c for c in clusters if c.priority_level in high_value_priorities]
        
        # Find most common year for recommendations
        most_common_year = max(year_distribution.items(), key=lambda x: x[1] if isinstance(x[0], int) and x[0] >= 2020 else 0)
        
        # Find dominant file type
        dominant_file_type = max(file_type_distribution.items(), key=lambda x: x[1])
        
        # Create smart recommendation
        smart_recommendation = {
            'title': f'Focus on {most_common_year[0]} {dominant_file_type[0]} files with P1-P2 priority',
            'filters': {
                'year': most_common_year[0] if isinstance(most_common_year[0], int) else None,
                'file_types': [dominant_file_type[0]],
                'priority_levels': ['P1', 'P2'],
                'min_size_mb': 5
            },
            'expected_clusters': len([c for c in high_value_clusters 
                                    if c.time_span_start.year == most_common_year[0]]),
            'expected_savings_gb': sum(c.potential_savings_bytes for c in high_value_clusters 
                                     if c.time_span_start.year == most_common_year[0]) / (1024**3)
        }
        
        response_data = {
            'success': True,
            'distributions': {
                'years': dict(sorted(year_distribution.items(), reverse=True)),
                'file_types': dict(sorted(file_type_distribution.items(), key=lambda x: x[1], reverse=True)),
                'priorities': dict(sorted(priority_distribution.items())),
                'size_histogram': dict(sorted(size_histogram.items())),
                'size_quintiles': quintile_metadata  # New quintile metadata for frontend
            },
            'smart_recommendation': smart_recommendation,
            'totals': {
                'photos': len(metadata),
                'clusters': len(clusters),
                'total_savings_gb': sum(c.potential_savings_bytes for c in clusters) / (1024**3)
            }
        }
        
        print(f"✅ Distribution statistics computed successfully")
        
        return jsonify(response_data)
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Error computing filter distributions: {error_msg}")
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'error': error_msg
        }), 500

@app.route('/api/save-filter-criteria', methods=['POST'])  
def api_save_filter_criteria():
    """Save just filter criteria to session for streamlined workflow."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        filters = data.get('filters', {})
        
        # Save simple filter criteria to session
        session['filter_criteria'] = {
            'filters': filters,
            'timestamp': datetime.now().isoformat(),
            'type': 'criteria_only'  # Distinguish from full cluster sessions
        }
        
        print(f"💾 Saved filter criteria to session: {filters}")
        
        return jsonify({
            'success': True,
            'message': 'Filter criteria saved successfully',
            'filters_saved': filters
        })
        
    except Exception as e:
        print(f"❌ Error saving filter criteria: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/save-filter-session', methods=['POST'])
def api_save_filter_session():
    """Save filter criteria and selected clusters to session for dashboard handoff."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # Validate incoming data quality
        selected_photo_uuids = data.get('selected_photo_uuids', [])
        total_photos = data.get('total_photos_in_filter', 0)
        total_clusters = data.get('total_clusters_in_filter', 0)
        
        # Critical validation checks
        if not selected_photo_uuids:
            return jsonify({
                'success': False, 
                'error': 'No photo UUIDs provided. Cannot create analysis session without photos to analyze.',
                'debug_info': {
                    'received_uuids': len(selected_photo_uuids),
                    'reported_total': total_photos,
                    'clusters': total_clusters
                }
            }), 400
        
        if total_photos != len(selected_photo_uuids):
            print(f"⚠️ WARNING: Reported photo count ({total_photos}) doesn't match UUID count ({len(selected_photo_uuids)})")
        
        if total_clusters == 0:
            return jsonify({
                'success': False,
                'error': 'No clusters selected. Cannot create analysis session without clusters to analyze.'
            }), 400
        
        # Create session ID for server-side storage
        session_id = secrets.token_hex(8)
        
        # Store large data server-side to avoid huge cookies
        server_side_sessions[session_id] = {
            'selected_photo_uuids': selected_photo_uuids,
            'cluster_summaries': data.get('cluster_summaries', []),
            'timestamp': datetime.now().isoformat(),
        }
        
        # Store only minimal data in Flask session
        filter_session = {
            'filter_criteria': data.get('filter_criteria', {}),
            'total_photos_in_filter': len(selected_photo_uuids),  # Use actual count
            'total_clusters_in_filter': total_clusters,
            'session_id': session_id
        }
        
        session['filter_session'] = filter_session
        session.permanent = True
        
        print(f"💾 Filter session saved: {filter_session['total_clusters_in_filter']} clusters, {filter_session['total_photos_in_filter']} photos")
        print(f"🔍 Filter criteria: {filter_session['filter_criteria']}")
        
        return jsonify({
            'success': True,
            'session_id': filter_session['session_id'],
            'message': f"Saved session with {filter_session['total_clusters_in_filter']} clusters for analysis"
        })
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Error saving filter session: {error_msg}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': error_msg}), 500

@app.route('/api/get-filter-session')
def api_get_filter_session():
    """Get current filter session data for dashboard mode detection."""
    try:
        filter_session = session.get('filter_session')
        
        if not filter_session:
            return jsonify({
                'success': True,
                'has_session': False,
                'mode': 'overview'
            })
        
        # Get server-side session data
        session_id = filter_session.get('session_id')
        server_data = server_side_sessions.get(session_id, {})
        
        # Check if session is still fresh (not older than 1 hour)  
        if server_data:
            session_time = datetime.fromisoformat(server_data['timestamp'])
        else:
            # Fallback to session creation time
            session_time = datetime.now()
        time_diff = (datetime.now() - session_time).total_seconds()
        
        if time_diff > 3600:  # 1 hour timeout
            session.pop('filter_session', None)
            if session_id in server_side_sessions:
                del server_side_sessions[session_id]
            return jsonify({
                'success': True,
                'has_session': False,
                'mode': 'overview',
                'message': 'Session expired'
            })
        
        # Merge server-side data with session data for full response
        full_session_data = {**filter_session}
        if server_data:
            full_session_data.update({
                'selected_photo_uuids': server_data.get('selected_photo_uuids', []),
                'cluster_summaries': server_data.get('cluster_summaries', []),
                'timestamp': server_data.get('timestamp')
            })
        
        return jsonify({
            'success': True,
            'has_session': True,
            'mode': 'filtered',
            'filter_session': full_session_data
        })
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Error getting filter session: {error_msg}")
        return jsonify({'success': False, 'error': error_msg}), 500

@app.route('/api/clear-filter-session', methods=['POST'])
def api_clear_filter_session():
    """Clear filter session to return to overview mode."""
    try:
        filter_session = session.get('filter_session')
        if filter_session:
            session_id = filter_session.get('session_id')
            if session_id and session_id in server_side_sessions:
                del server_side_sessions[session_id]
                
        session.pop('filter_session', None)
        print("🗑️ Filter session cleared - returning to overview mode")
        
        return jsonify({
            'success': True,
            'message': 'Filter session cleared'
        })
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Error clearing filter session: {error_msg}")
        return jsonify({'success': False, 'error': error_msg}), 500

def calculate_storage_impact(photo_group):
    """
    Calculate potential storage savings for a group
    Priority factors:
    1. Total file size of duplicates (primary)
    2. Number of photos in group (secondary) 
    3. Quality score confidence (tertiary)
    """
    photos = photo_group['photos']
    
    # Find best photo (highest quality score)
    best_photo = max(photos, key=lambda p: p.get('quality_score', 0))
    duplicate_photos = [p for p in photos if p['uuid'] != best_photo['uuid']]
    
    # Calculate savings
    duplicate_sizes = [p.get('file_size_bytes', 0) for p in duplicate_photos]
    total_savings_bytes = sum(duplicate_sizes)
    
    # Calculate priority score
    impact_score = (
        total_savings_bytes * 1.0 +           # Primary: raw savings
        len(duplicate_photos) * 10000000 +     # Secondary: photo count weight  
        best_photo.get('quality_score', 0) * 1000000  # Tertiary: confidence weight
    )
    
    return {
        'total_savings_bytes': total_savings_bytes,
        'duplicate_count': len(duplicate_photos),
        'impact_score': impact_score,
        'best_photo_uuid': best_photo['uuid']
    }

def sort_duplicate_groups(groups, sort_key='savings_desc'):
    """Sort duplicate groups by various criteria."""
    sort_functions = {
        'savings_desc': lambda g: g.get('impact', {}).get('total_savings_bytes', 0),
        'count_desc': lambda g: g.get('impact', {}).get('duplicate_count', 0), 
        'date_desc': lambda g: max((p.get('timestamp', '') for p in g.get('photos', [])), default=''),
        'quality_desc': lambda g: max((p.get('quality_score', 0) for p in g.get('photos', [])), default=0)
    }
    
    sort_func = sort_functions.get(sort_key, sort_functions['savings_desc'])
    return sorted(groups, key=sort_func, reverse=True)

def cache_analysis_results(groups, filter_criteria):
    """Cache complete analysis results with expiry management."""
    import uuid
    from datetime import timedelta
    
    # Generate unique cache key
    cache_key = f"analysis_{uuid.uuid4().hex[:8]}"
    
    # Clean expired cache entries
    now = datetime.now()
    expired_keys = [
        key for key, data in analysis_cache.items()
        if now - data['timestamp'] > timedelta(minutes=CACHE_EXPIRY_MINUTES)
    ]
    for key in expired_keys:
        del analysis_cache[key]
    
    # LRU eviction if cache is full
    if len(analysis_cache) >= MAX_CACHED_ANALYSES:
        oldest_key = min(analysis_cache.keys(), key=lambda k: analysis_cache[k]['timestamp'])
        del analysis_cache[oldest_key]
    
    # Cache the results
    analysis_cache[cache_key] = {
        'timestamp': now,
        'filter_criteria': filter_criteria,
        'all_groups': groups,
        'total_groups': len(groups),
        'analysis_metadata': {
            'cache_created': now.isoformat(),
            'total_photos_analyzed': sum(len(g.get('photos', [])) for g in groups),
            'potential_savings_gb': sum(g.get('impact', {}).get('total_savings_bytes', 0) for g in groups) / (1024**3)
        }
    }
    
    return cache_key

def paginate_groups(groups, page=1, limit=10):
    """Paginate group results."""
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    
    paginated_groups = groups[start_idx:end_idx]
    
    return {
        'groups': paginated_groups,
        'pagination': {
            'current_page': page,
            'total_pages': (len(groups) + limit - 1) // limit,
            'total_groups': len(groups),
            'groups_per_page': limit,
            'has_next': end_idx < len(groups),
            'has_previous': page > 1
        }
    }

@app.route('/api/analyze-duplicates', methods=['POST'])
def api_analyze_duplicates():
    """
    Single comprehensive endpoint that:
    1. Takes filter criteria from request
    2. Runs complete analysis pipeline
    3. Returns paginated results sorted by impact
    """
    try:
        print("🔄 Starting unified duplicate analysis...")
        start_time = datetime.now()
        
        # Parse request data
        request_data = request.get_json() or {}
        filter_criteria = request_data.get('filters', {})
        pagination_params = request_data.get('pagination', {'page': 1, 'limit': 10, 'sort': 'savings_desc'})
        
        # Step 1: Apply filters using existing filter logic
        photos, excluded_count = scanner.get_unprocessed_photos()
        print(f"📊 Found {len(photos)} photos ({excluded_count} already marked for deletion)")
        
        # Apply user filters using existing filter logic
        print(f"🔍 Applying filters: {filter_criteria}")
        filtered_photos = apply_filter_criteria(photos, filter_criteria)
        print(f"📊 Photos after filtering: {len(filtered_photos)} (from {len(photos)} total)")
        
        if len(filtered_photos) == 0:
            print("⚠️ No photos match filter criteria")
            return jsonify({
                'success': False,
                'message': 'No photos match the selected filter criteria',
                'groups': [],
                'total_groups': 0,
                'filtered_count': 0
            })
        
        # Step 2: Run complete duplicate analysis using existing detection system
        print("🔍 Running comprehensive duplicate analysis...")
        photo_groups = []
        
        # Use the same proven analysis pipeline from /api/groups
        scan_limit = min(len(filtered_photos), 5000)  # Reasonable limit for performance
        analysis_photos_raw = filtered_photos[:scan_limit]
        
        print(f"🔍 Converting {len(analysis_photos_raw)} PhotoInfo objects to PhotoData...")
        
        # Convert PhotoInfo objects to PhotoData objects
        analysis_photos = []
        for photo_info in analysis_photos_raw:
            try:
                photo_data = scanner.extract_photo_metadata(photo_info)
                analysis_photos.append(photo_data)
            except Exception as e:
                print(f"⚠️ Skipping photo {getattr(photo_info, 'uuid', 'unknown')}: {e}")
                continue
        
        print(f"✅ Successfully converted {len(analysis_photos)} photos for analysis")
        
        # Step 2.1: Group photos by time and camera (10-second windows)
        groups = scanner.group_photos_by_time_and_camera(analysis_photos)
        print(f"📊 Created {len(groups)} initial time-based groups")
        
        # Step 2.2: Enhanced grouping with quality analysis  
        groups = scanner.enhanced_grouping_with_similarity(groups, progress_callback=None)
        print(f"🎯 Enhanced grouping complete: {len(groups)} groups with quality scores")
        
        # Step 2.3: Visual similarity filtering (70% threshold)
        groups = scanner.filter_groups_by_visual_similarity(groups, similarity_threshold=70.0)
        print(f"✅ Visual similarity filtering: {len(groups)} final duplicate groups")
        
        # Step 2.4: Convert to unified format with impact calculation
        for group in groups:
            if len(group.photos) > 1:  # Only include actual duplicates
                # Convert PhotoData objects to API format
                photos_data = []
                for photo in group.photos:
                    photos_data.append({
                        'uuid': photo.uuid,
                        'filename': photo.filename or 'Unknown',
                        'original_filename': getattr(photo, 'original_filename', None),
                        'file_size_bytes': photo.file_size or 0,
                        'quality_score': getattr(photo, 'quality_score', 0.0),
                        'quality_method': getattr(photo, 'quality_method', 'unknown'),
                        'date_taken': photo.timestamp.isoformat() if photo.timestamp else '',
                        'camera_model': photo.camera_model or 'Unknown'
                    })
                
                # Create group with impact calculation
                unified_group = {
                    'id': group.group_id,
                    'photos': photos_data,
                    'timestamp': group.time_window_start.isoformat() if group.time_window_start else '',
                    'camera_model': group.camera_model or 'Unknown',
                    'similarity_score': 0.85  # Default similarity score for groups that passed filtering
                }
                
                # Calculate storage impact
                unified_group['impact'] = calculate_storage_impact(unified_group)
                photo_groups.append(unified_group)
        
        analysis_summary = {
            'total_photos_analyzed': len(analysis_photos),
            'total_groups_found': len(photo_groups),
            'potential_savings_gb': round(sum(g['impact']['total_savings_bytes'] for g in photo_groups) / (1024**3), 2),
            'analysis_duration_seconds': round((datetime.now() - start_time).total_seconds(), 1)
        }
        
        # Step 4: Sort by impact
        sorted_groups = sort_duplicate_groups(photo_groups, pagination_params.get('sort', 'savings_desc'))
        
        # Step 5: Cache and paginate
        cache_key = cache_analysis_results(sorted_groups, filter_criteria)
        paginated_results = paginate_groups(sorted_groups, pagination_params.get('page', 1), pagination_params.get('limit', 10))
        
        analysis_duration = (datetime.now() - start_time).total_seconds()
        
        print(f"✅ Analysis complete: {len(sorted_groups)} groups, {analysis_duration:.1f}s")
        
        return jsonify({
            'success': True,
            'analysis': analysis_summary,
            'results': paginated_results,
            'cache_key': cache_key if sorted_groups else None,
            'timestamp': datetime.now().isoformat(),
            'note': 'MVP implementation - full analysis integration coming in next iteration'
        })
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Error in unified analysis: {error_msg}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': error_msg}), 500

@app.route('/api/load-more-duplicates', methods=['GET'])
def api_load_more_duplicates():
    """
    Fast pagination endpoint for cached results:
    - Takes cache_key + page number
    - Returns next page of results
    - No re-analysis required
    """
    try:
        cache_key = request.args.get('cache_key')
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 10, type=int)
        
        if not cache_key or cache_key not in analysis_cache:
            return jsonify({'success': False, 'error': 'Analysis cache not found or expired'}), 404
        
        cached_analysis = analysis_cache[cache_key]
        
        # Check if cache is expired
        from datetime import timedelta
        if datetime.now() - cached_analysis['timestamp'] > timedelta(minutes=CACHE_EXPIRY_MINUTES):
            del analysis_cache[cache_key]
            return jsonify({'success': False, 'error': 'Analysis cache expired'}), 410
        
        # Paginate cached results
        all_groups = cached_analysis['all_groups']
        paginated_results = paginate_groups(all_groups, page, limit)
        
        print(f"📄 Loading page {page}: {len(paginated_results['groups'])} groups")
        
        return jsonify({
            'success': True,
            'results': paginated_results,
            'cache_key': cache_key,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Error loading more duplicates: {error_msg}")
        return jsonify({'success': False, 'error': error_msg}), 500

@app.route('/duplicates')
def duplicates_interface():
    """New streamlined duplicates review interface."""
    try:
        with open('/Users/urikogan/code/dedup/duplicates_interface.html', 'r') as f:
            return f.read()
    except FileNotFoundError:
        return "Duplicates interface not found", 404

@app.route('/api/health')
def api_health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'stage': 'Stage 5A: Lazy Loading Foundation'
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