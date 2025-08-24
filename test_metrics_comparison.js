/**
 * Metrics Comparison Test
 * Fetches metrics from all endpoints to compare them
 */

const BASE_URL = 'http://127.0.0.1:5003';

async function fetchMetrics() {
    console.log("🔍 Fetching metrics from all endpoints...\n");
    
    try {
        // Fetch Dashboard metrics
        console.log("1️⃣ Dashboard Metrics (/api/dashboard):");
        const dashboardResponse = await fetch(`${BASE_URL}/api/dashboard`);
        const dashboardData = await dashboardResponse.json();
        
        if (dashboardData.success) {
            console.log(`   📊 Total Photos: ${dashboardData.library_stats?.total_photos?.toLocaleString() || 'N/A'}`);
            console.log(`   📊 Potential Groups: ${dashboardData.library_stats?.potential_groups || 'N/A'}`);
            console.log(`   📊 Estimated Savings: ${dashboardData.library_stats?.estimated_savings || 'N/A'}`);
            console.log(`   📊 Top Priority Groups: ${dashboardData.clusters?.length || 'N/A'}`);
        } else {
            console.log(`   ❌ Error: ${dashboardData.error}`);
        }
        
        console.log("\n");
        
        // Fetch Stats API metrics
        console.log("2️⃣ Stats API Metrics (/api/stats):");
        const statsResponse = await fetch(`${BASE_URL}/api/stats`);
        const statsData = await statsResponse.json();
        
        if (statsData.success) {
            console.log(`   📊 Total Photos: ${statsData.total_photos?.toLocaleString() || 'N/A'}`);
            console.log(`   📊 Sample Groups: ${statsData.potential_groups || statsData.sample_groups || 'N/A'}`);
            console.log(`   📊 Estimated Savings: ${statsData.estimated_savings || 'N/A'}`);
        } else {
            console.log(`   ❌ Error: ${statsData.error}`);
        }
        
        console.log("\n");
        
        // Compare the two
        console.log("🔍 COMPARISON ANALYSIS:");
        
        if (dashboardData.success && statsData.success) {
            const dashPhotos = dashboardData.library_stats?.total_photos || 0;
            const statsPhotos = statsData.total_photos || 0;
            
            const dashGroups = dashboardData.library_stats?.potential_groups || 0;
            const statsGroups = statsData.potential_groups || statsData.sample_groups || 0;
            
            console.log(`   📸 Photos: Dashboard (${dashPhotos.toLocaleString()}) vs Stats API (${statsPhotos.toLocaleString()})`);
            console.log(`   📁 Groups: Dashboard (${dashGroups}) vs Stats API (${statsGroups})`);
            
            if (dashPhotos !== statsPhotos) {
                console.log(`   ⚠️  PHOTO COUNT MISMATCH: Dashboard has ${(dashPhotos - statsPhotos).toLocaleString()} more photos`);
            }
            
            if (dashGroups !== statsGroups) {
                console.log(`   ⚠️  GROUP COUNT MISMATCH: Dashboard has ${dashGroups - statsGroups} more groups`);
            }
            
            if (dashPhotos === statsPhotos && dashGroups === statsGroups) {
                console.log(`   ✅ METRICS MATCH: Both endpoints return identical numbers`);
            }
        }
        
        console.log("\n");
        
        // Fetch Legacy Groups for comparison
        console.log("3️⃣ Legacy Interface Groups (/api/groups):");
        const groupsResponse = await fetch(`${BASE_URL}/api/groups?priority=P5&limit=10`);
        const groupsData = await groupsResponse.json();
        
        if (groupsData.success && groupsData.groups) {
            console.log(`   📊 Groups returned: ${groupsData.groups.length}`);
            console.log(`   📊 Total photos in groups: ${groupsData.groups.reduce((sum, g) => sum + g.photo_count, 0)}`);
            
            // Show first group as example
            if (groupsData.groups.length > 0) {
                const firstGroup = groupsData.groups[0];
                console.log(`   📊 Example group: ${firstGroup.group_id} (${firstGroup.photo_count} photos, ${firstGroup.potential_savings_mb}MB savings)`);
            }
        } else {
            console.log(`   ❌ Error fetching groups: ${groupsData.error || 'Unknown error'}`);
        }
        
        console.log("\n");
        console.log("🎯 LIKELY EXPLANATION:");
        console.log("   - Dashboard: Uses comprehensive scan (4,708 photos) with caching");
        console.log("   - Stats API: Uses limited scan (200 photos) for quick response");  
        console.log("   - Legacy: Uses same groups as dashboard but may show different subset");
        console.log("   - This explains why numbers are different between interfaces!");
        
    } catch (error) {
        console.error("❌ Error fetching metrics:", error.message);
    }
}

// Run the comparison
fetchMetrics();