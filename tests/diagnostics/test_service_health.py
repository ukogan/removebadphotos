#!/usr/bin/env python3
"""
Diagnostic tests for photo dedup system health
Must complete in < 1 second
"""
import pytest
import sys
import os
from unittest.mock import Mock, patch

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

@pytest.mark.diagnostics
def test_python_environment():
    """Verify Python 3 environment is available"""
    assert sys.version_info.major == 3
    assert sys.version_info.minor >= 8

@pytest.mark.diagnostics  
def test_required_libraries_importable():
    """Verify core libraries can be imported"""
    try:
        import flask
        import PIL
        import osxphotos
        import cv2
        import imagehash
        import numpy
    except ImportError as e:
        pytest.fail(f"Required library not importable: {e}")

@pytest.mark.diagnostics
def test_flask_can_instantiate():
    """Verify Flask app can be created"""
    from flask import Flask
    app = Flask(__name__)
    assert app is not None
    assert app.name == '__main__'

@pytest.mark.diagnostics
@patch('osxphotos.PhotosDB')
def test_photos_library_accessible(mock_photos_db):
    """Verify Photos library access without actual system calls"""
    mock_db = Mock()
    mock_photos_db.return_value = mock_db
    
    from photo_scanner import PhotoScanner
    scanner = PhotoScanner()
    assert scanner is not None

@pytest.mark.diagnostics
def test_temp_directory_writable():
    """Verify temp directory for thumbnails is writable"""
    import tempfile
    temp_dir = os.path.join(tempfile.gettempdir(), 'photo_dedup_thumbnails')
    
    # Should be able to create directory
    os.makedirs(temp_dir, exist_ok=True)
    assert os.path.exists(temp_dir)
    assert os.access(temp_dir, os.W_OK)

@pytest.mark.diagnostics
def test_image_processing_libraries():
    """Verify image processing libraries can create basic objects"""
    from PIL import Image
    import cv2
    import numpy as np
    
    # PIL can create a test image
    test_image = Image.new('RGB', (100, 100), color='red')
    assert test_image.size == (100, 100)
    
    # OpenCV can create array
    test_array = np.zeros((100, 100, 3), dtype=np.uint8)
    assert test_array.shape == (100, 100, 3)

@pytest.mark.diagnostics
def test_json_serialization():
    """Verify JSON serialization works for API responses"""
    import json
    from datetime import datetime
    
    test_data = {
        'id': 'test-123',
        'timestamp': datetime.now().isoformat(),
        'photos': [],
        'metadata': {'test': True}
    }
    
    # Should serialize without error
    json_str = json.dumps(test_data)
    assert isinstance(json_str, str)
    
    # Should deserialize back
    parsed = json.loads(json_str)
    assert parsed['id'] == 'test-123'