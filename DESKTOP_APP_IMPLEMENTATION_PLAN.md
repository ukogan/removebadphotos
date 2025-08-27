# Desktop App Implementation Plan: Tauri with Embedded Frontend

## Executive Summary

**Approach**: Tauri wrapper with embedded Flask backend and preserved frontend (95%+ code reuse)
**Timeline**: 5 days (~15 hours)
**Key Benefit**: Native macOS experience while preserving all existing investment

## Current Architecture Analysis

Your dedup application is a **mature hybrid web application** with:
- **Flask backend** (app.py) with comprehensive REST API
- **Three HTML interfaces**: dashboard.html, duplicates_interface.html, filter_interface.html  
- **Sophisticated frontend**: Photo gallery UI, drag-drop, filtering, real-time analysis
- **Deep macOS integration**: osxphotos, photoscript, AppleScript for Photos app
- **Production-ready features**: Quality scoring, thumbnail generation, batch operations

## Implementation Strategy: Preserve 95%+ of Existing Code

### **Phase 1: Tauri Project Setup (Day 1)**

#### 1.1 Initialize Tauri Project
```bash
cd /Users/urikogan/code/dedup
npm create tauri-app@latest photo-dedup-desktop --template vanilla
cd photo-dedup-desktop
```

#### 1.2 Configure Tauri for Web Content Embedding
**File: `src-tauri/tauri.conf.json`**
```json
{
  "build": {
    "distDir": "../frontend",
    "devPath": "http://127.0.0.1:5000"
  },
  "tauri": {
    "bundle": {
      "identifier": "com.yourname.photo-dedup",
      "resources": [
        "../backend/*",
        "../frontend/*"
      ],
      "externalBin": [
        "../backend/python3"
      ]
    },
    "windows": [{
      "title": "Photo Dedup Tool",
      "width": 1400,
      "height": 900,
      "minWidth": 1200,
      "minHeight": 700,
      "resizable": true,
      "fullscreen": false
    }],
    "security": {
      "csp": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: http://127.0.0.1:5000"
    },
    "allowlist": {
      "all": false,
      "shell": {
        "all": false,
        "open": true
      },
      "fs": {
        "all": true,
        "readFile": true,
        "writeFile": true,
        "createDir": true
      },
      "notification": {
        "all": true
      }
    }
  }
}
```

#### 1.3 Directory Structure Setup
```bash
mkdir -p frontend backend
# Copy existing files
cp dashboard.html frontend/index.html
cp duplicates_interface.html frontend/
cp filter_interface.html frontend/
cp *.py backend/
cp requirements*.txt backend/
```

### **Phase 2: Backend Process Integration (Day 2)**

#### 2.1 Create Rust Backend Manager
**File: `src-tauri/src/backend_manager.rs`**
```rust
use std::process::{Command, Child, Stdio};
use std::path::PathBuf;
use tauri::Manager;
use serde_json::Value;

pub struct BackendManager {
    process: Option<Child>,
}

impl BackendManager {
    pub fn new() -> Self {
        Self { process: None }
    }
    
    pub fn start_flask(&mut self, app_handle: tauri::AppHandle) -> Result<(), String> {
        let resource_dir = app_handle
            .path_resolver()
            .resolve_resource("backend")
            .ok_or("Backend directory not found")?;
            
        let python_path = which::which("python3")
            .map_err(|_| "Python3 not found in PATH")?;
            
        let mut cmd = Command::new(python_path);
        cmd.current_dir(resource_dir)
           .arg("app.py")
           .env("FLASK_ENV", "production")
           .env("PORT", "5000")
           .stdout(Stdio::piped())
           .stderr(Stdio::piped());
           
        let child = cmd.spawn()
            .map_err(|e| format!("Failed to start Flask: {}", e))?;
            
        self.process = Some(child);
        
        // Wait for server startup
        std::thread::sleep(std::time::Duration::from_secs(2));
        
        Ok(())
    }
    
    pub fn stop_flask(&mut self) {
        if let Some(mut process) = self.process.take() {
            let _ = process.kill();
            let _ = process.wait();
        }
    }
}
```

#### 2.2 Update Main Tauri Process
**File: `src-tauri/src/main.rs`**
```rust
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod backend_manager;

use backend_manager::BackendManager;
use std::sync::Mutex;
use tauri::{Manager, State};

struct AppState {
    backend: Mutex<BackendManager>,
}

#[tauri::command]
async fn start_backend(state: State<'_, AppState>, app_handle: tauri::AppHandle) -> Result<String, String> {
    let mut backend = state.backend.lock().unwrap();
    backend.start_flask(app_handle)?;
    Ok("Backend started successfully".to_string())
}

#[tauri::command]
async fn check_backend_health() -> Result<String, String> {
    let client = reqwest::Client::new();
    let response = client.get("http://127.0.0.1:5000/api/health")
        .send()
        .await
        .map_err(|e| format!("Backend health check failed: {}", e))?;
        
    if response.status().is_success() {
        Ok("Backend is healthy".to_string())
    } else {
        Err("Backend health check failed".to_string())
    }
}

fn main() {
    tauri::Builder::default()
        .manage(AppState {
            backend: Mutex::new(BackendManager::new()),
        })
        .invoke_handler(tauri::generate_handler![start_backend, check_backend_health])
        .setup(|app| {
            // Auto-start backend
            let app_handle = app.handle();
            let state = app.state::<AppState>();
            tauri::async_runtime::spawn(async move {
                if let Err(e) = start_backend(state, app_handle).await {
                    eprintln!("Failed to start backend: {}", e);
                }
            });
            Ok(())
        })
        .on_window_event(|event| {
            if let tauri::WindowEvent::CloseRequested { .. } = event.event() {
                // Clean shutdown of Flask backend
                let window = event.window();
                let state = window.state::<AppState>();
                let mut backend = state.backend.lock().unwrap();
                backend.stop_flask();
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

### **Phase 3: Frontend Integration (Day 3)**

#### 3.1 Minimal Frontend URL Updates
**Only change needed in your existing HTML files:**

**dashboard.html, duplicates_interface.html, filter_interface.html:**
```javascript
// Add at top of <script> sections:
const API_BASE = window.location.hostname === '127.0.0.1' 
    ? 'http://127.0.0.1:5000/api'  // Desktop app mode
    : '/api';                       // Web mode (fallback)

// Replace all API calls from:
fetch('/api/health')
// To:
fetch(`${API_BASE}/health`)
```

#### 3.2 Add Desktop-Specific Enhancements
**Add to each HTML file in `<head>` section:**
```html
<script>
// Desktop app detection and enhancements
if (window.__TAURI__) {
    // Add native menu bar integration
    document.addEventListener('DOMContentLoaded', async () => {
        const { invoke } = window.__TAURI__.tauri;
        
        // Ensure backend is running
        try {
            await invoke('check_backend_health');
            console.log('✅ Backend is running');
        } catch (error) {
            console.error('Backend startup issue:', error);
            await invoke('start_backend');
        }
    });
}
</script>
```

### **Phase 4: Native Desktop Features (Day 4)**

#### 4.1 Add Native Menu Bar
**File: `src-tauri/src/menu.rs`**
```rust
use tauri::{CustomMenuItem, Menu, MenuItem, Submenu};

pub fn create_menu() -> Menu {
    let quit = CustomMenuItem::new("quit".to_string(), "Quit");
    let close = CustomMenuItem::new("close".to_string(), "Close");
    let analyze = CustomMenuItem::new("analyze".to_string(), "Start Analysis");
    let about = CustomMenuItem::new("about".to_string(), "About");
    
    let submenu_app = Submenu::new("Photo Dedup", Menu::new()
        .add_item(about)
        .add_native_item(MenuItem::Separator)
        .add_item(quit));
        
    let submenu_file = Submenu::new("File", Menu::new()
        .add_item(analyze)
        .add_native_item(MenuItem::Separator) 
        .add_item(close));
        
    Menu::new()
        .add_submenu(submenu_app)
        .add_submenu(submenu_file)
}
```

#### 4.2 Add Native Notifications
**File: `src-tauri/src/notifications.rs`**
```rust
use tauri::api::notification::Notification;

#[tauri::command]
pub async fn show_completion_notification(title: String, body: String) -> Result<(), String> {
    Notification::new("com.yourname.photo-dedup")
        .title(&title)
        .body(&body)
        .show()
        .map_err(|e| format!("Notification failed: {}", e))?;
    Ok(())
}
```

### **Phase 5: Backend Adaptations (Day 2-3)**

#### 5.1 Keep Existing Flask Backend Unchanged
**Your current app.py continues to work exactly as-is** because:
- REST API endpoints remain identical
- Photo processing logic unchanged  
- osxphotos integration preserved
- Thumbnail serving continues working

#### 5.2 Optional: Add Desktop-Specific Endpoints
**Add to app.py (optional enhancements):**
```python
@app.route('/api/desktop/open-in-finder/<uuid>')
def open_in_finder(uuid):
    """Open photo location in Finder (desktop app only)"""
    try:
        photo_path = scanner.get_photo_path(uuid)
        if photo_path and os.path.exists(photo_path):
            import subprocess
            subprocess.run(['open', '-R', photo_path])
            return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/desktop/notification')
def send_desktop_notification():
    """Trigger native desktop notification"""
    return jsonify({'trigger_notification': True})
```

### **Phase 6: Asset Bundling & Distribution (Day 5)**

#### 6.1 Bundle Configuration
**Update `src-tauri/tauri.conf.json`:**
```json
{
  "tauri": {
    "bundle": {
      "active": true,
      "targets": ["dmg", "app"],
      "identifier": "com.yourname.photo-dedup",
      "icon": ["icons/32x32.png", "icons/128x128.png", "icons/128x128@2x.png"],
      "resources": [
        "../backend/**/*",
        "../frontend/**/*"
      ],
      "copyright": "Copyright © 2025 Your Name",
      "category": "Photography",
      "shortDescription": "Photo deduplication tool for macOS",
      "longDescription": "Intelligent photo deduplication tool with Photos app integration"
    }
  }
}
```

#### 6.2 Build Commands
```bash
# Development mode
npm run tauri dev

# Production build
npm run tauri build
```

## File Change Summary

### **Files That Need Changes:**
1. **dashboard.html** - Add `API_BASE` constant (3 lines)
2. **duplicates_interface.html** - Add `API_BASE` constant (3 lines)  
3. **filter_interface.html** - Add `API_BASE` constant (3 lines)

### **Files That Stay Unchanged:**
- **app.py** - Complete Flask backend preserved
- **photo_scanner.py** - All photo analysis logic unchanged
- **library_analyzer.py** - Similarity detection unchanged  
- **photo_tagger.py** - Photos app integration unchanged
- **lazy_photo_loader.py** - Image loading unchanged
- **All CSS styling** - Visual design preserved
- **All JavaScript logic** - Photo selection, filtering, UI interactions unchanged

### **New Files Created:**
- **Tauri Rust files** - Native app wrapper (~200 lines total)
- **Menu & notification support** - Desktop enhancements (~100 lines)

## Development Timeline

| Day | Task | Changes Required | Effort |
|-----|------|------------------|--------|
| 1 | Tauri project setup | New project creation | 2-3 hours |
| 2 | Backend process integration | Rust backend manager | 4-6 hours |
| 3 | Frontend URL updates | 3-line changes to HTML files | 1-2 hours |
| 4 | Native desktop features | Menu bar, notifications | 3-4 hours |
| 5 | Build & test | Configuration tweaks | 2-3 hours |

**Total: ~15 hours over 5 days**

## Testing Strategy

### **Development Testing:**
```bash
# Test existing web version still works
cd /Users/urikogan/code/dedup
python3 app.py
# Open browser to localhost:5000

# Test desktop version
cd photo-dedup-desktop  
npm run tauri dev
```

### **Functionality Verification:**
- [ ] All three interfaces load in desktop window
- [ ] Photo analysis workflows work identically
- [ ] Thumbnail generation and serving works
- [ ] Photos app integration preserved
- [ ] Native menu bar responds
- [ ] Desktop notifications work

## Risk Mitigation

### **Low Risk Items:**
- **Frontend preservation** - Only URL changes needed
- **Backend compatibility** - Flask continues unchanged
- **Build process** - Tauri handles bundling automatically

### **Medium Risk Items:**
- **Python environment** - Bundle correct Python3 + dependencies
- **File permissions** - Ensure Photos library access in bundled app
- **Performance** - Monitor startup time and memory usage

### **Mitigation Strategies:**
1. **Keep web version working** - Users can fall back during transition
2. **Incremental testing** - Test each phase before proceeding  
3. **Bundle validation** - Verify all Python modules included correctly

## Success Metrics

- **Code preservation**: 95%+ of existing code unchanged
- **Feature parity**: All current functionality works identically  
- **Native experience**: Menu bar, notifications, better performance
- **Distribution ready**: Single .dmg file for easy installation
- **Development time**: Under 20 hours total implementation

## Benefits of This Approach

### **Immediate Benefits:**
- Native macOS app experience (dock icon, menu bar, notifications)
- Better security model (no web server exposed to network)
- Improved startup performance 
- Professional distribution via .dmg installer

### **Future Benefits:**
- App Store distribution capability
- Auto-update system integration
- Enhanced file system permissions
- Better macOS integration opportunities

This plan preserves your substantial frontend investment while providing a true native macOS experience with minimal development overhead.