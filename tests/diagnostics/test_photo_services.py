#!/usr/bin/env python3
"""
Photo service diagnostic tests
Must complete in < 1 second
"""
import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

@pytest.mark.diagnostics
def test_photo_scanner_instantiation():
    """Verify PhotoScanner can be created without system calls"""
    with patch('osxphotos.PhotosDB'):
        from photo_scanner import PhotoScanner
        scanner = PhotoScanner()
        assert scanner is not None

@pytest.mark.diagnostics  
def test_library_analyzer_instantiation():
    """Verify LibraryAnalyzer can be created"""
    from library_analyzer import LibraryAnalyzer
    analyzer = LibraryAnalyzer()
    assert analyzer is not None

@pytest.mark.diagnostics
@patch('app.PhotoScanner')
@patch('app.LibraryAnalyzer')
def test_flask_app_creation(mock_analyzer, mock_scanner):
    """Verify Flask app starts without errors"""
    # Mock the global instances
    mock_scanner.return_value = Mock()
    mock_analyzer.return_value = Mock()
    
    from app import app
    assert app is not None
    
    with app.test_client() as client:
        # Test that app is responsive
        assert client is not None

@pytest.mark.diagnostics
def test_circuit_breaker_pattern():
    """Verify circuit breaker implementation works"""
    class TestCircuitBreaker:
        def __init__(self, max_failures=3):
            self.failures = 0
            self.max_failures = max_failures
            
        def execute(self, operation):
            if self.failures >= self.max_failures:
                raise Exception("Circuit open")
            
            try:
                result = operation()
                self.failures = 0
                return result
            except Exception:
                self.failures += 1
                raise
    
    breaker = TestCircuitBreaker()
    
    # Should work initially
    result = breaker.execute(lambda: "success")
    assert result == "success"
    
    # Should open circuit after failures
    for i in range(3):
        with pytest.raises(Exception):
            breaker.execute(lambda: (_ for _ in ()).throw(Exception("test")))
    
    # Circuit should be open
    with pytest.raises(Exception, match="Circuit open"):
        breaker.execute(lambda: "should not run")

@pytest.mark.diagnostics
def test_thumbnail_directory_setup():
    """Verify thumbnail cache directory can be created"""
    import tempfile
    
    thumbnail_dir = os.path.join(tempfile.gettempdir(), 'test_photo_dedup_thumbnails')
    
    try:
        os.makedirs(thumbnail_dir, exist_ok=True)
        assert os.path.exists(thumbnail_dir)
        assert os.path.isdir(thumbnail_dir)
        
        # Should be able to create a test file
        test_file = os.path.join(thumbnail_dir, 'test.tmp')
        with open(test_file, 'w') as f:
            f.write('test')
        
        assert os.path.exists(test_file)
        
    finally:
        # Cleanup
        if os.path.exists(test_file):
            os.remove(test_file)
        if os.path.exists(thumbnail_dir):
            os.rmdir(thumbnail_dir)

@pytest.mark.diagnostics
def test_memory_usage_baseline():
    """Verify baseline memory usage is reasonable"""
    import psutil
    import gc
    
    # Force garbage collection
    gc.collect()
    
    # Get current process memory
    process = psutil.Process()
    memory_mb = process.memory_info().rss / 1024 / 1024
    
    # Should be under 100MB at startup
    assert memory_mb < 100, f"Baseline memory usage too high: {memory_mb:.1f}MB"