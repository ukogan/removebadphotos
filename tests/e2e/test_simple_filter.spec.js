/**
 * Simple Filter Test - Direct API Testing
 * Focus on identifying why UI filtering gets stuck
 */

import { test, expect } from '@playwright/test';

const BASE_URL = 'http://127.0.0.1:5003';

test('Simple API Filter Test', async ({ page }) => {
    test.setTimeout(180000); // 3 minutes
    
    console.log('🔍 Testing filter API endpoints directly...');
    
    // Test 1: Check backend endpoints are working
    const response1 = await page.request.get(`${BASE_URL}/api/filter-clusters?year=2024`);
    const data1 = await response1.json();
    console.log(`📋 API Test - Year 2024: ${response1.status()} - ${data1.clusters ? data1.clusters.length : 0} clusters`);
    
    const response2 = await page.request.get(`${BASE_URL}/api/filter-clusters?min_size_mb=2`);
    const data2 = await response2.json();
    console.log(`📋 API Test - Min 2MB: ${response2.status()} - ${data2.clusters ? data2.clusters.length : 0} clusters`);
    
    const response3 = await page.request.get(`${BASE_URL}/api/filter-clusters?year=2023&file_types=JPG`);
    const data3 = await response3.json();
    console.log(`📋 API Test - 2023+JPG: ${response3.status()} - ${data3.clusters ? data3.clusters.length : 0} clusters`);
    
    const response4 = await page.request.get(`${BASE_URL}/api/filter-clusters?min_size_mb=1`);
    const data4 = await response4.json();
    console.log(`📋 API Test - Min 1MB: ${response4.status()} - ${data4.clusters ? data4.clusters.length : 0} clusters`);
    
    const response5 = await page.request.get(`${BASE_URL}/api/filter-clusters?year=2024&min_size_mb=1&file_types=HEIC`);
    const data5 = await response5.json();
    console.log(`📋 API Test - Multi: ${response5.status()} - ${data5.clusters ? data5.clusters.length : 0} clusters`);
    
    // Test 2: Check include_photos parameter
    const responseWithPhotos = await page.request.get(`${BASE_URL}/api/filter-clusters?year=2024&include_photos=true`);
    const dataWithPhotos = await responseWithPhotos.json();
    console.log(`📋 API Test - With Photos: ${responseWithPhotos.status()}`);
    
    if (dataWithPhotos.clusters && dataWithPhotos.clusters.length > 0) {
        const firstCluster = dataWithPhotos.clusters[0];
        const hasPhotos = firstCluster.photos && firstCluster.photos.length > 0;
        const firstPhotoHasUuid = hasPhotos && firstCluster.photos[0].uuid;
        
        console.log(`📋 First cluster has ${firstCluster.photos ? firstCluster.photos.length : 0} photos`);
        console.log(`📋 First photo has UUID: ${firstPhotoHasUuid}`);
        
        if (firstPhotoHasUuid) {
            console.log(`📋 Sample photo UUID: ${firstCluster.photos[0].uuid}`);
        }
    }
    
    // Test 3: Test session save with photo UUIDs
    if (dataWithPhotos.success && dataWithPhotos.clusters) {
        console.log('📋 Testing session save with photo UUIDs...');
        
        const sessionData = {
            mode: 'filtered',
            filters: { year: 2024 },
            clusters: dataWithPhotos.clusters.slice(0, 5), // First 5 clusters
            photo_uuids: []
        };
        
        // Extract UUIDs from clusters
        dataWithPhotos.clusters.slice(0, 5).forEach(cluster => {
            if (cluster.photos) {
                cluster.photos.forEach(photo => {
                    if (photo.uuid) {
                        sessionData.photo_uuids.push(photo.uuid);
                    }
                });
            }
        });
        
        console.log(`📋 Extracted ${sessionData.photo_uuids.length} photo UUIDs`);
        
        const saveResponse = await page.request.post(`${BASE_URL}/api/session/save`, {
            data: sessionData
        });
        
        console.log(`📋 Session save response: ${saveResponse.status()}`);
        
        if (saveResponse.ok()) {
            const saveData = await saveResponse.json();
            console.log(`📋 Session save result: ${JSON.stringify(saveData)}`);
        }
    }
    
    // Assertions - all API calls should work
    expect(response1.status()).toBe(200);
    expect(response2.status()).toBe(200);
    expect(response3.status()).toBe(200);
    expect(response4.status()).toBe(200);
    expect(response5.status()).toBe(200);
    expect(responseWithPhotos.status()).toBe(200);
    
    // At least some filters should return clusters
    const totalClusters = (data1.clusters?.length || 0) + 
                         (data2.clusters?.length || 0) + 
                         (data3.clusters?.length || 0) + 
                         (data4.clusters?.length || 0) + 
                         (data5.clusters?.length || 0);
    
    console.log(`📋 Total clusters across all filters: ${totalClusters}`);
    expect(totalClusters).toBeGreaterThan(0);
});