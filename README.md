# RemoveBadPhotos

An intelligent macOS photo management tool that uses computer vision to identify and help you remove low-quality photos from your Photos library. The app analyzes photos for blur, over/under-exposure, and other quality issues, then allows you to tag problematic photos for deletion.

## Features

- **Advanced Blur Detection**: Uses optimized Sobel variance algorithm (2.7x more effective than traditional Laplacian methods)
- **Chronological Analysis**: Processes photos in 1000-photo buckets from oldest to newest for predictable analysis times
- **Conservative Filtering**: Only shows truly problematic photos (blur score < 500) to avoid false positives
- **Interactive Review**: Full-screen preview with keyboard shortcuts for efficient photo review
- **Photos App Integration**: Tags photos with keywords for easy identification and deletion
- **iCloud Optimization Aware**: Handles photos stored in iCloud vs. locally cached photos

## Requirements

- **macOS**: Tested on macOS 10.12+ (Sequoia 15.6)
- **Python 3.8+**: Required for computer vision libraries
- **Photos Library**: Must have access to your Photos library
- **Local Storage**: Works best with photos that are locally downloaded (not just in iCloud)

## Installation

1. **Clone the repository**:
```bash
git clone <repository-url>
cd removebadphotos
```

2. **Install Python dependencies**:
```bash
pip3 install flask opencv-python pillow numpy osxphotos photoscript requests
```

3. **Install system dependencies** (if needed):
```bash
# For HEIC/HEIF support
brew install libheif
```

## Usage

1. **Start the application**:
```bash
python3 app.py
```

2. **Open in browser**:
Navigate to `http://127.0.0.1:5003` in your web browser

3. **Select a photo bucket**:
   - Photos are organized chronologically in 1000-photo buckets
   - Each bucket shows the date range and number of analyzable photos

4. **Run blur analysis**:
   - Click "Analyze for Blur" on your chosen bucket
   - Progress is shown in real-time
   - Only locally accessible photos will be analyzed

5. **Review results**:
   - Only photos with blur scores < 500 (very problematic) are shown
   - Use keyboard shortcuts: `←`/`→` for navigation, `D` to mark for deletion, `Space` for Photos app
   - Full-screen preview available by clicking photos

6. **Mark photos for deletion**:
   - Select problematic photos and click "Mark for deletion"
   - Photos are tagged with "marked-for-deletion" keyword in Photos app
   - Search for this keyword in Photos to find and delete tagged photos

## How It Works

### Computer Vision Analysis
- **Sobel Variance Algorithm**: Measures edge intensity to detect blur
- **Optimized Thresholds**: Based on Kaggle blur dataset evaluation
- **Quality Scoring**: 
  - Sharp: > 5000
  - Slightly blurry: 2000-5000  
  - Blurry: 500-2000
  - Very blurry: < 500 (shown for review)

### Photo Processing
- **Chronological Buckets**: Photos split into 1000-photo groups by date
- **Local vs. iCloud**: Only analyzes photos with accessible file paths
- **Conservative Approach**: Shows only the worst quality photos to minimize false positives

## Constraints & Limitations

### iCloud Photos Optimization
- **Major Limitation**: Many photos may not be locally available for analysis
- **Typical Scenario**: 1000-photo bucket may only have 50-100 analyzable photos
- **Workaround**: Download originals for photos you want analyzed, or use "Download Originals to this Mac" setting

### Performance
- **Analysis Speed**: ~10-50 photos per second depending on image size and complexity
- **Memory Usage**: Loads images into memory for analysis; large libraries may require sufficient RAM
- **Database Queries**: Fast metadata filtering but slower for actual computer vision analysis

### Compatibility
- **macOS Only**: Uses osxphotos and Photos app integration
- **Photos Library Format**: Requires modern Photos library format
- **File Formats**: Supports JPEG, HEIC, PNG; limited support for RAW formats

## Technical Architecture

### Backend (Flask)
- **app.py**: Main Flask application with API endpoints
- **blur_detector.py**: Computer vision blur detection module
- **photo_tagger.py**: Photos app integration for keyword tagging

### Frontend
- **blur_detection_interface.html**: Single-page application for photo review
- **Real-time Progress**: Polls backend every 500ms during analysis
- **Responsive Grid**: Displays photo thumbnails with quality scores

### Key APIs
- `/api/photo-buckets`: Get chronological photo buckets
- `/api/blur-analysis`: Run computer vision analysis
- `/api/blur-analysis-progress`: Real-time progress updates
- `/api/mark-blur-photos-for-deletion`: Tag photos in Photos app

## Development

The app follows a conservative approach - better to miss some bad photos than accidentally flag good ones. The Sobel variance algorithm was chosen after extensive testing against the Kaggle blur dataset, showing 2.7x better discrimination than traditional Laplacian methods.

### Algorithm Evaluation
Results from Kaggle blur dataset testing:
- **Sharp photos**: Average score ~1600+
- **Blurry photos**: Average score ~230
- **Discrimination ratio**: 7.1x (vs 1.97x for Laplacian)

## Troubleshooting

### "No photos found for analysis"
- Check if photos are downloaded locally vs. stored in iCloud only
- Try enabling "Download Originals to this Mac" in Photos preferences

### "Analysis very slow"
- Normal for high-resolution images
- Consider analyzing smaller buckets first
- Ensure sufficient RAM available

### "Can't find photos in Photos app"
- Search for "marked-for-deletion" keyword in Photos
- Check that Photos app has necessary permissions

## Contributing

This is a specialized tool for macOS Photos library management. When contributing:
- Maintain the conservative approach (avoid false positives)
- Test thoroughly with various photo types and qualities
- Consider iCloud storage optimization scenarios
- Follow the existing code patterns for Photos app integration

## License

[Add appropriate license]