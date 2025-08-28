#!/usr/bin/env python3
"""
Backend Performance Monitoring for Photo Deletion Workflow
Target: Identify bottlenecks in LazyPhotoLoader and related backend functions
"""

import pytest
import time
import psutil
import os
import requests
import threading
from unittest.mock import patch
import sys

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from lazy_photo_loader import LazyPhotoLoader
from library_analyzer import LibraryAnalyzer
from photo_scanner import PhotoScanner


class PerformanceMonitor:
    """Monitor CPU, memory, and execution time for backend operations"""
    
    def __init__(self):
        self.process = psutil.Process()
        self.start_time = None
        self.start_cpu = None
        self.start_memory = None
        
    def start(self):
        """Start monitoring"""
        self.start_time = time.time()
        self.start_cpu = self.process.cpu_percent()
        self.start_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        
    def stop(self):
        """Stop monitoring and return metrics"""
        if self.start_time is None:
            return {}
            
        end_time = time.time()
        end_cpu = self.process.cpu_percent()
        end_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        
        return {
            'execution_time': end_time - self.start_time,
            'cpu_usage': end_cpu - self.start_cpu,
            'memory_usage_mb': end_memory,
            'memory_delta_mb': end_memory - self.start_memory
        }


class TestBackendPerformanceDiagnostics:
    """Comprehensive backend performance tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test environment"""
        self.monitor = PerformanceMonitor()
        self.base_url = 'http://127.0.0.1:5003'
        
    def test_api_groups_performance(self):
        """Test /api/groups endpoint performance with detailed metrics"""
        print("\n🧪 Testing /api/groups performance...")
        
        self.monitor.start()
        
        try:
            response = requests.get(f'{self.base_url}/api/groups?limit=10', timeout=15)
            metrics = self.monitor.stop()
            
            print(f"⏱️ /api/groups execution time: {metrics['execution_time']:.2f}s")
            print(f"🧠 Memory usage: {metrics['memory_usage_mb']:.1f} MB (Δ{metrics['memory_delta_mb']:+.1f})")
            print(f"🖥️ CPU usage change: {metrics['cpu_usage']:+.1f}%")
            print(f"📊 Response status: {response.status_code}")
            
            # Performance assertions
            assert metrics['execution_time'] < 10.0, f"API took {metrics['execution_time']:.2f}s - too slow!"
            assert response.status_code == 200, f"API returned {response.status_code}"
            
            if response.status_code == 200:
                data = response.json()
                print(f"📊 Groups returned: {len(data.get('groups', []))}")
                print(f"📊 Total photos: {data.get('total_photos', 0)}")
                
                # With only 4 photos, this should be very fast
                if metrics['execution_time'] > 5.0:
                    print(f"🚨 SLOW RESPONSE DETECTED: {metrics['execution_time']:.2f}s for only 4 photos")
                    
        except requests.exceptions.Timeout:
            metrics = self.monitor.stop()
            print(f"🚨 TIMEOUT DETECTED after {metrics['execution_time']:.2f}s")
            raise
            
    def test_api_complete_workflow_performance(self):
        """Test /api/complete-workflow with synthetic data"""
        print("\n🧪 Testing /api/complete-workflow performance...")
        
        # First get actual photo UUIDs
        try:
            groups_response = requests.get(f'{self.base_url}/api/groups?limit=1', timeout=10)
            if groups_response.status_code == 200:
                data = groups_response.json()
                if data.get('groups') and len(data['groups']) > 0:
                    photos = data['groups'][0].get('photos', [])
                    photo_uuids = [p['uuid'] for p in photos[:2]]  # Test with 2 photos max
                else:
                    print("⚠️ No groups available for workflow test")
                    return
            else:
                print(f"⚠️ Failed to get groups: {groups_response.status_code}")
                return
                
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Failed to get groups for workflow test: {e}")
            return
            
        print(f"🎯 Testing workflow with {len(photo_uuids)} photos")
        
        self.monitor.start()
        
        payload = {
            'photo_uuids': photo_uuids,
            'estimated_savings_mb': 5
        }
        
        try:
            response = requests.post(
                f'{self.base_url}/api/complete-workflow',
                json=payload,
                timeout=20
            )
            metrics = self.monitor.stop()
            
            print(f"⏱️ Workflow execution time: {metrics['execution_time']:.2f}s")
            print(f"🧠 Memory usage: {metrics['memory_usage_mb']:.1f} MB (Δ{metrics['memory_delta_mb']:+.1f})")
            print(f"📊 Response status: {response.status_code}")
            
            # Performance assertions for small photo set
            assert metrics['execution_time'] < 15.0, f"Workflow took {metrics['execution_time']:.2f}s - too slow!"
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Workflow result: {data}")
            else:
                print(f"❌ Workflow failed: {response.text}")
                
        except requests.exceptions.Timeout:
            metrics = self.monitor.stop()
            print(f"🚨 WORKFLOW TIMEOUT after {metrics['execution_time']:.2f}s")
            raise
            
    def test_lazy_photo_loader_performance(self):
        """Test LazyPhotoLoader methods directly"""
        print("\n🧪 Testing LazyPhotoLoader direct performance...")
        
        try:
            # Initialize components
            scanner = PhotoScanner()
            analyzer = LibraryAnalyzer()
            lazy_loader = LazyPhotoLoader(analyzer, scanner)
            
            # Test 1: get_library_metadata_fast
            print("🔬 Testing get_library_metadata_fast()...")
            self.monitor.start()
            
            def progress_callback(current, total, message):
                print(f"📊 Progress: {current}/{total} - {message}")
                
            stats, clusters = lazy_loader.get_library_metadata_fast(progress_callback)
            metrics = self.monitor.stop()
            
            print(f"⏱️ Metadata scan time: {metrics['execution_time']:.2f}s")
            print(f"🧠 Memory usage: {metrics['memory_usage_mb']:.1f} MB")
            print(f"📊 Clusters found: {len(clusters)}")
            print(f"📊 Library stats: {stats}")
            
            # Should be fast for small library
            assert metrics['execution_time'] < 10.0, f"Metadata scan took {metrics['execution_time']:.2f}s"
            
            # Test 2: analyze_cluster_photos for first cluster
            if clusters:
                print(f"\n🔬 Testing analyze_cluster_photos() for cluster {clusters[0].cluster_id}...")
                self.monitor.start()
                
                groups = lazy_loader.analyze_cluster_photos(clusters[0].cluster_id)
                metrics = self.monitor.stop()
                
                print(f"⏱️ Cluster analysis time: {metrics['execution_time']:.2f}s")
                print(f"🧠 Memory usage: {metrics['memory_usage_mb']:.1f} MB")
                print(f"📊 Groups generated: {len(groups)}")
                
                # Should be very fast for small cluster
                if metrics['execution_time'] > 5.0:
                    print(f"🚨 SLOW CLUSTER ANALYSIS: {metrics['execution_time']:.2f}s")
                    
        except Exception as e:
            print(f"❌ LazyPhotoLoader test failed: {e}")
            import traceback
            traceback.print_exc()
            
    def test_memory_leak_detection(self):
        """Test for memory leaks during repeated operations"""
        print("\n🧪 Testing for memory leaks...")
        
        initial_memory = self.monitor.process.memory_info().rss / 1024 / 1024
        print(f"📊 Initial memory: {initial_memory:.1f} MB")
        
        # Perform repeated API calls
        memory_readings = [initial_memory]
        
        for i in range(5):
            try:
                response = requests.get(f'{self.base_url}/api/groups?limit=2', timeout=10)
                if response.status_code == 200:
                    current_memory = self.monitor.process.memory_info().rss / 1024 / 1024
                    memory_readings.append(current_memory)
                    print(f"📊 Iteration {i+1} memory: {current_memory:.1f} MB (Δ{current_memory - initial_memory:+.1f})")
                    time.sleep(1)
                else:
                    print(f"⚠️ API call {i+1} failed: {response.status_code}")
                    break
            except Exception as e:
                print(f"⚠️ API call {i+1} error: {e}")
                break
                
        # Analyze memory trend
        if len(memory_readings) >= 3:
            memory_increases = 0
            for i in range(1, len(memory_readings)):
                if memory_readings[i] > memory_readings[i-1] + 1.0:  # >1MB increase
                    memory_increases += 1
                    
            if memory_increases >= 3:
                print("🚨 POTENTIAL MEMORY LEAK DETECTED - Memory consistently increasing")
                print(f"📊 Memory trend: {memory_readings}")
            else:
                print("✅ No obvious memory leak detected")
                
    def test_concurrent_api_load(self):
        """Test API behavior under concurrent load"""
        print("\n🧪 Testing concurrent API load...")
        
        def make_api_call(call_id):
            start_time = time.time()
            try:
                response = requests.get(f'{self.base_url}/api/groups?limit=2', timeout=15)
                end_time = time.time()
                return {
                    'call_id': call_id,
                    'status': response.status_code,
                    'time': end_time - start_time,
                    'success': response.status_code == 200
                }
            except Exception as e:
                return {
                    'call_id': call_id,
                    'status': 0,
                    'time': time.time() - start_time,
                    'success': False,
                    'error': str(e)
                }
                
        # Launch 3 concurrent requests
        threads = []
        results = []
        
        for i in range(3):
            thread = threading.Thread(target=lambda i=i: results.append(make_api_call(i)))
            threads.append(thread)
            thread.start()
            
        # Wait for all threads
        for thread in threads:
            thread.join(timeout=20)
            
        # Analyze results
        print(f"📊 Concurrent requests completed: {len(results)}")
        
        for result in results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} Call {result['call_id']}: {result['status']} ({result['time']:.2f}s)")
            if 'error' in result:
                print(f"   Error: {result['error']}")
                
        successful_calls = [r for r in results if r['success']]
        if successful_calls:
            avg_time = sum(r['time'] for r in successful_calls) / len(successful_calls)
            print(f"📊 Average response time: {avg_time:.2f}s")
            
            if avg_time > 5.0:
                print("🚨 SLOW CONCURRENT PERFORMANCE DETECTED")
                
    def test_api_health_endpoints(self):
        """Test basic health endpoints for quick diagnostics"""
        print("\n🧪 Testing API health endpoints...")
        
        health_endpoints = [
            '/api/health',
            '/api/stats',
            '/api/cache-stats'
        ]
        
        for endpoint in health_endpoints:
            self.monitor.start()
            try:
                response = requests.get(f'{self.base_url}{endpoint}', timeout=5)
                metrics = self.monitor.stop()
                
                status = "✅" if response.status_code == 200 else "❌"
                print(f"{status} {endpoint}: {response.status_code} ({metrics['execution_time']:.2f}s)")
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        # Print relevant info without overwhelming output
                        if 'total_photos' in data:
                            print(f"   📊 Total photos: {data['total_photos']}")
                        if 'cache_size' in data:
                            print(f"   📊 Cache size: {data['cache_size']}")
                            
                    except Exception as e:
                        print(f"   ⚠️ Could not parse JSON: {e}")
                        
            except requests.exceptions.Timeout:
                metrics = self.monitor.stop()
                print(f"❌ {endpoint}: TIMEOUT ({metrics['execution_time']:.2f}s)")
            except Exception as e:
                print(f"❌ {endpoint}: ERROR - {e}")


if __name__ == '__main__':
    # Can be run directly for quick testing
    import subprocess
    
    print("🚀 Running backend performance diagnostics...")
    print("📋 Make sure the Flask app is running on http://127.0.0.1:5003")
    print("="*60)
    
    # Run with pytest for proper test execution
    subprocess.run([
        'python3', '-m', 'pytest', __file__, '-v', '-s', '--tb=short'
    ])