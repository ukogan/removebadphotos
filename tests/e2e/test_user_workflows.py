#!/usr/bin/env python3
"""
End-to-end user workflow tests
Complete user journeys - < 2 minutes
"""
import pytest
import sys
import os
import json
import time
from unittest.mock import Mock, patch

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

@pytest.mark.e2e
def test_complete_photo_analysis_workflow():
    """Test complete user workflow from startup to photo selection"""
    with patch('app.PhotoScanner') as mock_scanner, \
         patch('app.LibraryAnalyzer') as mock_analyzer:
        
        # Mock realistic photo data
        mock_photos = [
            {
                'id': 'photo-1',
                'timestamp': 1640995200.0,  # 2022-01-01 00:00:00
                'camera_model': 'iPhone 13',
                'file_size': 2500000,
                'resolution': (4032, 3024),
                'path': '/fake/path/photo1.jpg'
            },
            {
                'id': 'photo-2', 
                'timestamp': 1640995205.0,  # 5 seconds later
                'camera_model': 'iPhone 13',
                'file_size': 2300000,
                'resolution': (4032, 3024),
                'path': '/fake/path/photo2.jpg'
            }
        ]
        
        mock_groups = [
            {
                'id': 'group-1',
                'photos': mock_photos,
                'recommended_best': 'photo-1',
                'total_size': 4800000,
                'potential_savings': 2300000
            }
        ]
        
        # Setup mocks
        mock_scanner_instance = Mock()
        mock_scanner_instance.get_library_stats.return_value = {
            'total_photos': 1000,
            'date_range': {'start': '2020-01-01', 'end': '2023-12-31'},
            'total_size_gb': 45.2
        }
        mock_scanner_instance.get_recent_photos.return_value = mock_photos
        mock_scanner.return_value = mock_scanner_instance
        
        mock_analyzer_instance = Mock()
        mock_analyzer_instance.find_similar_groups.return_value = mock_groups
        mock_analyzer.return_value = mock_analyzer_instance
        
        from app import app
        client = app.test_client()
        
        # Step 1: User loads app
        response = client.get('/')
        assert response.status_code == 200
        assert b'Photo Deduplication Tool' in response.data
        
        # Step 2: User checks library stats
        response = client.get('/api/stats')
        assert response.status_code == 200
        stats = json.loads(response.data)
        assert stats['total_photos'] == 1000
        
        # Step 3: User analyzes for duplicates
        start_time = time.time()
        response = client.get('/api/groups')
        analysis_time = time.time() - start_time
        
        assert response.status_code == 200
        assert analysis_time < 30  # Should complete in reasonable time
        
        groups = json.loads(response.data)
        assert len(groups) == 1
        assert groups[0]['id'] == 'group-1'
        assert len(groups[0]['photos']) == 2
        
        # Step 4: User makes selections (simulated via API)
        selections = {
            'group-1': ['photo-2']  # User chooses to delete photo-2
        }
        
        response = client.post('/api/process-selections',
                             json={'selections': selections})
        
        # Should return processing result
        assert response.status_code == 200
        result = json.loads(response.data)
        assert 'total_deleted' in result
        assert 'space_saved_mb' in result

@pytest.mark.e2e  
def test_thumbnail_viewing_workflow():
    """Test user workflow for viewing photo thumbnails"""
    with patch('app.scanner') as mock_scanner, \
         patch('os.path.exists') as mock_exists, \
         patch('PIL.Image.open') as mock_image_open:
        
        # Mock photo with thumbnail
        mock_photo = Mock()
        mock_photo.uuid = 'test-uuid-123'
        mock_photo.path = '/fake/path/photo.jpg'
        
        mock_scanner.get_photo_by_id.return_value = mock_photo
        mock_exists.return_value = True
        
        # Mock PIL Image
        mock_image = Mock()
        mock_image.size = (4032, 3024)
        mock_image.resize.return_value = mock_image
        mock_image_open.return_value.__enter__.return_value = mock_image
        
        from app import app
        client = app.test_client()
        
        # User requests thumbnail
        response = client.get('/api/thumbnail/test-uuid-123')
        
        # Should generate and return thumbnail
        assert response.status_code == 200
        assert response.content_type.startswith('image/')

@pytest.mark.e2e
def test_error_recovery_workflow():
    """Test user workflow when errors occur"""
    with patch('app.PhotoScanner') as mock_scanner:
        
        # First request succeeds
        mock_scanner_instance = Mock()
        mock_scanner_instance.get_library_stats.return_value = {'total_photos': 1000}
        mock_scanner.return_value = mock_scanner_instance
        
        from app import app
        client = app.test_client()
        
        # Successful request
        response = client.get('/api/stats')
        assert response.status_code == 200
        
        # Simulate system error
        mock_scanner_instance.get_library_stats.side_effect = Exception("System error")
        
        # Error request
        response = client.get('/api/stats')
        assert response.status_code == 500
        error_data = json.loads(response.data)
        assert 'error' in error_data
        
        # User clears cache to recover
        response = client.get('/api/clear-cache')
        assert response.status_code == 200
        
        # Fix the error and retry
        mock_scanner_instance.get_library_stats.side_effect = None
        mock_scanner_instance.get_library_stats.return_value = {'total_photos': 1000}
        
        # Should work again
        response = client.get('/api/stats')
        assert response.status_code == 200

@pytest.mark.e2e
def test_large_library_performance():
    """Test performance with larger photo libraries"""
    with patch('app.PhotoScanner') as mock_scanner, \
         patch('app.LibraryAnalyzer') as mock_analyzer:
        
        # Simulate larger library
        large_photo_set = []
        for i in range(100):
            large_photo_set.append({
                'id': f'photo-{i}',
                'timestamp': 1640995200.0 + (i * 10),  # 10 second intervals
                'camera_model': 'iPhone 13',
                'file_size': 2500000,
                'resolution': (4032, 3024)
            })
        
        # Create multiple groups
        large_groups = []
        for i in range(0, 100, 5):  # Groups of 5
            group_photos = large_photo_set[i:i+5]
            large_groups.append({
                'id': f'group-{i//5}',
                'photos': group_photos,
                'recommended_best': group_photos[0]['id'],
                'total_size': len(group_photos) * 2500000,
                'potential_savings': (len(group_photos) - 1) * 2500000
            })
        
        # Setup mocks
        mock_scanner_instance = Mock()
        mock_scanner_instance.get_recent_photos.return_value = large_photo_set
        mock_scanner.return_value = mock_scanner_instance
        
        mock_analyzer_instance = Mock()  
        mock_analyzer_instance.find_similar_groups.return_value = large_groups
        mock_analyzer.return_value = mock_analyzer_instance
        
        from app import app
        client = app.test_client()
        
        # Test performance with large dataset
        start_time = time.time()
        response = client.get('/api/groups')
        processing_time = time.time() - start_time
        
        assert response.status_code == 200
        assert processing_time < 60  # Should complete within 1 minute
        
        groups = json.loads(response.data)
        assert len(groups) == 20  # 100 photos / 5 per group
        
        # Verify response structure
        for group in groups:
            assert 'id' in group
            assert 'photos' in group
            assert len(group['photos']) <= 5

@pytest.mark.e2e
def test_concurrent_user_requests():
    """Test handling multiple concurrent requests"""
    import threading
    import time
    
    with patch('app.PhotoScanner') as mock_scanner:
        
        mock_scanner_instance = Mock()
        mock_scanner_instance.get_library_stats.return_value = {'total_photos': 1000}
        mock_scanner.return_value = mock_scanner_instance
        
        from app import app
        client = app.test_client()
        
        # Function to make requests
        results = []
        def make_request():
            response = client.get('/api/stats')
            results.append(response.status_code)
        
        # Start multiple concurrent requests
        threads = []
        for i in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all to complete
        for thread in threads:
            thread.join()
        
        # All requests should succeed
        assert all(status == 200 for status in results)
        assert len(results) == 5