# Video Compression Utility

A powerful and modular video compression tool using FFmpeg with configurable quality settings. This utility provides an easy-to-use command-line interface for compressing video files with various quality presets and advanced options.

## Features

- **Multiple Quality Presets**: Ultra, High, Medium, and Low quality settings
- **Codec Support**: H.264 (libx264) and H.265 (libx265) codecs
- **Flexible Sizing**: Target file size or compression ratio options
- **Batch Processing**: Process multiple files at once
- **Progress Tracking**: Real-time progress bars during compression
- **Format Support**: MP4, AVI, MOV, MKV, WMV, FLV, WebM, M4V
- **Metadata Preservation**: Option to preserve original metadata
- **Modular Architecture**: Clean, maintainable code structure

## Requirements

- **FFmpeg**: Must be installed and accessible in PATH
- **Python**: 3.7 or higher
- **Dependencies**: Listed in requirements.txt

## Installation

1. **Install FFmpeg**:

   - Windows: Download from [ffmpeg.org](https://ffmpeg.org/download.html) or use `winget install FFmpeg`
   - macOS: `brew install ffmpeg`
   - Linux: `sudo apt install ffmpeg` (Ubuntu/Debian) or equivalent

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Default Mode (No Arguments)

The easiest way to use the application is with no arguments:

```bash
# Automatically process all videos in ./videos/ folder
python main.py
```

**Default Mode Behavior:**

- 🔍 Automatically scans `./videos/` folder for video files
- ⚙️ Uses default settings: medium quality, libx264 codec
- 💾 Saves compressed videos in the same folder with `_compressed` suffix
- 🚫 Skips files already containing `_compressed` in the filename
- 📁 Example: `video.mp4` becomes `video_compressed.mp4`

### Basic Examples

```bash
# Default mode - process videos in ./videos/ folder
python main.py

# Compress specific file with medium quality (default)
python main.py video.mp4

# Compress with high quality and custom output
python main.py video.mp4 -q high -o compressed_video.mp4

# Compress to specific file size
python main.py video.mp4 -s 50MB -o small_video.mp4

# Use H.265 codec for better compression
python main.py video.mp4 -c libx265 -q high

# Compress to 50% of original size
python main.py video.mp4 -r 0.5
```

### Batch Processing

```bash
# Compress all MP4 files in current directory
python main.py *.mp4 --batch -d output/

# Compress multiple specific files
python main.py video1.mp4 video2.avi video3.mov --batch -d compressed/

# Batch compress with specific settings
python main.py *.mp4 --batch -q high -c libx265 -d output/
```

### Command Line Options

#### Input/Output

- `input`: Input video file(s) or glob pattern
- `-o, --output`: Output file path (single file mode)
- `-d, --output-dir`: Output directory (batch mode, default: ./compressed)

#### Compression Settings

- `-q, --quality`: Quality preset (ultra, high, medium, low) - default: medium
- `-c, --codec`: Video codec (libx264, libx265) - default: libx264
- `-s, --size`: Target file size (e.g., 50MB, 1GB)
- `-r, --ratio`: Compression ratio (0.5 = 50% of original size)
- `-f, --format`: Output format - default: mp4

#### Options

- `--batch`: Enable batch processing mode
- `--no-metadata`: Do not preserve metadata
- `--verbose`: Verbose output with detailed logging
- `--quiet`: Quiet mode with minimal output

## Quality Presets

| Preset | CRF | Description                      | Use Case                         |
| ------ | --- | -------------------------------- | -------------------------------- |
| Ultra  | 15  | Highest quality, largest files   | Archival, professional work      |
| High   | 18  | High quality, good for most uses | General high-quality compression |
| Medium | 23  | Balanced quality and size        | Default, good for most videos    |
| Low    | 28  | Lower quality, smaller files     | Quick sharing, storage-limited   |

## Project Structure

The application follows a modular architecture for better maintainability:

```
├── main.py                 # Main entry point and orchestration
├── cli.py                  # Command line interface handling
├── video_processor.py      # Core video processing logic
├── compression_settings.py # Quality presets and settings management
├── progress_tracker.py     # Progress tracking functionality
├── file_utils.py          # File handling utilities
├── requirements.txt       # Python dependencies
└── README.md             # This documentation
```

### Module Descriptions

- **main.py**: Entry point that orchestrates the entire workflow
- **cli.py**: Handles command line argument parsing and validation
- **video_processor.py**: Core video analysis and compression functionality
- **compression_settings.py**: Manages quality presets and compression settings
- **progress_tracker.py**: Provides progress tracking with tqdm
- **file_utils.py**: Utility functions for file operations and formatting

## Error Handling

The application includes comprehensive error handling:

- **FFmpeg availability check**: Ensures FFmpeg is installed
- **File format validation**: Checks for supported video formats
- **Input validation**: Validates command line arguments
- **Graceful failure**: Continues batch processing even if individual files fail
- **Detailed logging**: Optional verbose logging for troubleshooting

## Examples

### Default Mode

```bash
# Process all videos in ./videos/ folder automatically
python main.py

# This will:
# - Find all video files in ./videos/ (mp4, avi, mov, etc.)
# - Skip files already containing "_compressed" in the name
# - Compress each video with medium quality and libx264 codec
# - Save as: original_name_compressed.extension in the same folder
```

### Single File Compression

```bash
# Basic compression
python main.py input.mp4 -o output.mp4

# High quality with H.265
python main.py input.mp4 -q high -c libx265 -o output.mp4

# Target specific file size
python main.py large_video.mp4 -s 100MB -o compressed.mp4
```

### Batch Processing

```bash
# Process all videos in directory
python main.py *.mp4 *.avi --batch -d compressed_videos/

# High quality batch processing
python main.py *.mp4 --batch -q high -d high_quality_output/

# Compress all videos to 50% original size
python main.py *.* --batch -r 0.5 -d half_size_videos/
```

## Troubleshooting

### Common Issues

1. **"FFmpeg not found"**: Ensure FFmpeg is installed and in PATH
2. **"Unsupported format"**: Check if the input file format is supported
3. **Permission errors**: Ensure write permissions to output directory
4. **Out of disk space**: Check available disk space before compression

### Verbose Mode

Use `--verbose` flag for detailed logging:

```bash
python main.py video.mp4 --verbose
```

## Contributing

The modular architecture makes it easy to extend functionality:

1. **Adding new codecs**: Extend `compression_settings.py`
2. **New quality presets**: Modify quality presets in `compression_settings.py`
3. **Additional file formats**: Update supported formats in `file_utils.py`
4. **Enhanced progress tracking**: Modify `progress_tracker.py`

## License

This project is open source. Please ensure FFmpeg licensing compliance for your use case.
