#!/usr/bin/env python3
"""
Integration tests for photo processing pipeline
Service interactions - < 30 seconds
"""
import pytest
import sys
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
from PIL import Image
import json

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

@pytest.mark.integration
@patch('osxphotos.PhotosDB')
def test_photo_scanner_library_integration(mock_photos_db):
    """Test PhotoScanner with mocked Photos library"""
    # Mock Photos library response
    mock_db = Mock()
    mock_photo = Mock()
    mock_photo.uuid = 'test-uuid-123'
    mock_photo.date = Mock()
    mock_photo.date.timestamp.return_value = 1640995200.0  # 2022-01-01
    mock_photo.camera_make = 'Apple'
    mock_photo.camera_model = 'iPhone 13'
    mock_photo.path = '/fake/path/photo.jpg'
    mock_photo.original_filesize = 2500000
    mock_photo.width = 4032
    mock_photo.height = 3024
    
    mock_db.photos.return_value = [mock_photo]
    mock_photos_db.return_value = mock_db
    
    from photo_scanner import PhotoScanner
    scanner = PhotoScanner()
    
    # Get photos should work
    photos = scanner.get_recent_photos(days=30)
    assert len(photos) == 1
    assert photos[0]['id'] == 'test-uuid-123'
    assert photos[0]['camera_model'] == 'iPhone 13'

@pytest.mark.integration
def test_flask_api_endpoints():
    """Test Flask API endpoints integration"""
    with patch('app.PhotoScanner') as mock_scanner, \
         patch('app.LibraryAnalyzer') as mock_analyzer:
        
        # Mock scanner responses
        mock_scanner_instance = Mock()
        mock_scanner_instance.get_library_stats.return_value = {
            'total_photos': 1000,
            'date_range': {'start': '2020-01-01', 'end': '2023-12-31'}
        }
        mock_scanner.return_value = mock_scanner_instance
        
        # Mock analyzer responses  
        mock_analyzer_instance = Mock()
        mock_analyzer_instance.find_similar_groups.return_value = []
        mock_analyzer.return_value = mock_analyzer_instance
        
        from app import app
        client = app.test_client()
        
        # Test health endpoint
        response = client.get('/api/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        
        # Test stats endpoint
        response = client.get('/api/stats')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'total_photos' in data

@pytest.mark.integration
def test_thumbnail_generation_pipeline():
    """Test thumbnail generation and caching"""
    # Create a test image
    test_image = Image.new('RGB', (400, 300), color='red')
    
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
        test_image.save(temp_file.name, 'JPEG')
        temp_path = temp_file.name
    
    try:
        # Test thumbnail generation
        from PIL import Image
        
        # Load and resize
        with Image.open(temp_path) as img:
            # Calculate thumbnail size maintaining aspect ratio
            max_size = 200
            width, height = img.size
            ratio = min(max_size / width, max_size / height)
            new_size = (int(width * ratio), int(height * ratio))
            
            thumbnail = img.resize(new_size, Image.Resampling.LANCZOS)
            
            assert thumbnail.size[0] <= max_size
            assert thumbnail.size[1] <= max_size
            assert thumbnail.format == 'JPEG'
            
    finally:
        # Cleanup
        if os.path.exists(temp_path):
            os.remove(temp_path)

@pytest.mark.integration  
@patch('app.scanner')
def test_photo_groups_caching(mock_scanner):
    """Test photo groups caching mechanism"""
    # Mock scanner with consistent response
    mock_groups = [
        {
            'id': 'group-1',
            'photos': [{'id': 'photo-1'}, {'id': 'photo-2'}],
            'recommended_best': 'photo-1'
        }
    ]
    
    mock_scanner.get_recent_photos.return_value = [
        {'id': 'photo-1', 'timestamp': 1640995200.0},
        {'id': 'photo-2', 'timestamp': 1640995205.0}
    ]
    
    with patch('app.LibraryAnalyzer') as mock_analyzer_class:
        mock_analyzer = Mock()
        mock_analyzer.find_similar_groups.return_value = mock_groups
        mock_analyzer_class.return_value = mock_analyzer
        
        from app import app
        client = app.test_client()
        
        # First request should trigger analysis
        response1 = client.get('/api/groups')
        assert response1.status_code == 200
        data1 = json.loads(response1.data)
        
        # Second request should use cache (no additional analyzer calls)
        response2 = client.get('/api/groups')
        assert response2.status_code == 200
        data2 = json.loads(response2.data)
        
        # Responses should be identical
        assert data1 == data2
        
        # Analyzer should only be called once (cached)
        assert mock_analyzer.find_similar_groups.call_count == 1

@pytest.mark.integration
def test_error_handling_pipeline():
    """Test error handling across service boundaries"""
    with patch('app.PhotoScanner') as mock_scanner:
        
        # Mock scanner that raises exception
        mock_scanner_instance = Mock()
        mock_scanner_instance.get_library_stats.side_effect = Exception("Photos library error")
        mock_scanner.return_value = mock_scanner_instance
        
        from app import app
        client = app.test_client()
        
        # Should handle error gracefully
        response = client.get('/api/stats')
        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Photos library error' in str(data['error'])

@pytest.mark.integration
def test_memory_usage_during_processing():
    """Test memory usage stays reasonable during photo processing"""
    import psutil
    import gc
    
    # Get baseline memory
    gc.collect()
    process = psutil.Process()
    baseline_memory = process.memory_info().rss / 1024 / 1024
    
    # Simulate processing multiple photos
    test_images = []
    for i in range(10):
        # Create test images
        img = Image.new('RGB', (1000, 1000), color=(i * 25, 0, 0))
        test_images.append(img)
    
    # Check memory after processing
    current_memory = process.memory_info().rss / 1024 / 1024
    memory_increase = current_memory - baseline_memory
    
    # Should not increase by more than 200MB
    assert memory_increase < 200, f"Memory increased by {memory_increase:.1f}MB"
    
    # Cleanup
    del test_images
    gc.collect()