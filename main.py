#!/usr/bin/env python3
"""
Video Compression Utility
A powerful video compression tool using FFmpeg with configurable quality settings.

Requirements:
- FFmpeg installed and accessible in PATH
- Python packages: ffmpeg-python, tqdm

Install dependencies:
pip install ffmpeg-python tqdm

Usage examples:
python video_compressor.py input.mp4 -q medium -o compressed.mp4
python video_compressor.py *.mp4 -q high --batch -d output/
python video_compressor.py input.mov -s 50MB -c h265
"""

import argparse
import os
import sys
import subprocess
import json
import math
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import ffmpeg
from tqdm import tqdm
import time
import shutil

class VideoCompressor:
    """Video compression utility with advanced options."""
    
    # Supported input formats
    SUPPORTED_FORMATS = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v'}
    
    # Quality presets
    QUALITY_PRESETS = {
        'high': {'crf': 18, 'preset': 'medium', 'bitrate_factor': 0.8},
        'medium': {'crf': 23, 'preset': 'medium', 'bitrate_factor': 0.6},
        'low': {'crf': 28, 'preset': 'fast', 'bitrate_factor': 0.4},
        'ultra': {'crf': 15, 'preset': 'slow', 'bitrate_factor': 0.9}
    }
    
    def __init__(self):
        self.ffmpeg_path = self._check_ffmpeg()
        
    def _check_ffmpeg(self) -> str:
        """Check if FFmpeg is installed and accessible."""
        ffmpeg_path = shutil.which('ffmpeg')
        if not ffmpeg_path:
            raise RuntimeError("FFmpeg not found. Please install FFmpeg and add it to PATH.")
        return ffmpeg_path
    
    def get_video_info(self, filepath: str) -> Dict:
        """Get video information using ffprobe."""
        try:
            probe = ffmpeg.probe(filepath)
            video_stream = next((stream for stream in probe['streams'] 
                               if stream['codec_type'] == 'video'), None)
            
            if not video_stream:
                raise ValueError("No video stream found")
            
            # Get file size
            file_size = os.path.getsize(filepath)
            
            info = {
                'duration': float(probe['format']['duration']),
                'size': file_size,
                'bitrate': int(probe['format']['bit_rate']),
                'width': int(video_stream['width']),
                'height': int(video_stream['height']),
                'codec': video_stream['codec_name'],
                'fps': eval(video_stream['r_frame_rate']),
                'format': probe['format']['format_name']
            }
            return info
        except Exception as e:
            raise ValueError(f"Could not analyze video {filepath}: {str(e)}")
    
    def calculate_target_bitrate(self, info: Dict, target_size_mb: Optional[float] = None, 
                               compression_ratio: Optional[float] = None) -> int:
        """Calculate target bitrate based on file size or compression ratio."""
        duration = info['duration']
        original_bitrate = info['bitrate']
        
        if target_size_mb:
            # Convert MB to bits and calculate bitrate
            target_size_bits = target_size_mb * 8 * 1024 * 1024
            # Reserve 10% for audio and container overhead
            video_bitrate = int((target_size_bits * 0.9) / duration)
            return max(video_bitrate, 100000)  # Minimum 100kbps
        
        elif compression_ratio:
            return int(original_bitrate * compression_ratio)
        
        return original_bitrate
    
    def get_compression_settings(self, quality: str, codec: str, info: Dict,
                               target_size_mb: Optional[float] = None,
                               compression_ratio: Optional[float] = None) -> Dict:
        """Get FFmpeg compression settings based on parameters."""
        if quality not in self.QUALITY_PRESETS:
            raise ValueError(f"Quality must be one of: {list(self.QUALITY_PRESETS.keys())}")
        
        preset = self.QUALITY_PRESETS[quality]
        settings = {
            'codec': codec,
            'crf': preset['crf'],
            'preset': preset['preset']
        }
        
        # Calculate bitrate if target size or ratio specified
        if target_size_mb or compression_ratio:
            if not compression_ratio:
                compression_ratio = preset['bitrate_factor']
            
            target_bitrate = self.calculate_target_bitrate(info, target_size_mb, compression_ratio)
            settings['bitrate'] = f"{target_bitrate // 1000}k"
            
        return settings
    
    def build_ffmpeg_command(self, input_path: str, output_path: str, 
                           settings: Dict, preserve_metadata: bool = True) -> List[str]:
        """Build FFmpeg command with specified settings."""
        cmd = [
            self.ffmpeg_path, '-i', input_path,
            '-c:v', settings['codec'],
            '-preset', settings['preset'],
            '-y'  # Overwrite output file
        ]
        
        # Add CRF or bitrate settings
        if 'bitrate' in settings:
            cmd.extend(['-b:v', settings['bitrate'], '-maxrate', settings['bitrate']])
        else:
            cmd.extend(['-crf', str(settings['crf'])])
        
        # Codec-specific settings
        if settings['codec'] == 'libx265':
            cmd.extend(['-x265-params', 'log-level=error'])
        elif settings['codec'] == 'libx264':
            cmd.extend(['-movflags', '+faststart'])
        
        # Audio settings
        cmd.extend(['-c:a', 'aac', '-b:a', '128k'])
        
        # Preserve metadata
        if preserve_metadata:
            cmd.extend(['-map_metadata', '0'])
        
        cmd.append(output_path)
        return cmd
    
    def compress_video_with_progress(self, input_path: str, output_path: str,
                                   settings: Dict, preserve_metadata: bool = True) -> bool:
        """Compress video with progress tracking."""
        try:
            # Get video info for progress calculation
            info = self.get_video_info(input_path)
            total_frames = int(info['duration'] * info['fps'])
            
            # Build FFmpeg command
            cmd = self.build_ffmpeg_command(input_path, output_path, settings, preserve_metadata)
            
            print(f"Compressing: {os.path.basename(input_path)}")
            print(f"Settings: {settings['codec']}, Quality: CRF {settings.get('crf', 'N/A')}")
            
            # Run FFmpeg with progress tracking
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            with tqdm(total=total_frames, unit='frames', desc='Progress') as pbar:
                while True:
                    output = process.stderr.readline()
                    if output == '' and process.poll() is not None:
                        break
                    
                    if 'frame=' in output:
                        try:
                            frame_num = int(output.split('frame=')[1].split()[0])
                            pbar.n = min(frame_num, total_frames)
                            pbar.refresh()
                        except (IndexError, ValueError):
                            pass
            
            return_code = process.poll()
            if return_code == 0:
                # Show compression results
                self._show_compression_results(input_path, output_path)
                return True
            else:
                error_output = process.stderr.read()
                print(f"Error compressing {input_path}: {error_output}")
                return False
                
        except Exception as e:
            print(f"Error compressing {input_path}: {str(e)}")
            return False
    
    def _show_compression_results(self, input_path: str, output_path: str):
        """Show compression statistics."""
        try:
            original_size = os.path.getsize(input_path)
            compressed_size = os.path.getsize(output_path)
            compression_ratio = (1 - compressed_size / original_size) * 100
            
            print(f"✓ Compression complete!")
            print(f"  Original: {self._format_size(original_size)}")
            print(f"  Compressed: {self._format_size(compressed_size)}")
            print(f"  Space saved: {compression_ratio:.1f}%")
            print()
        except Exception:
            print("✓ Compression complete!")
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        if size_bytes == 0:
            return "0 B"
        size_names = ["B", "KB", "MB", "GB"]
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return f"{s} {size_names[i]}"
    
    def process_files(self, input_paths: List[str], output_dir: str, 
                     quality: str, codec: str, target_size_mb: Optional[float] = None,
                     compression_ratio: Optional[float] = None, 
                     output_format: str = 'mp4', preserve_metadata: bool = True) -> Dict:
        """Process multiple video files."""
        results = {'success': [], 'failed': []}
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        for input_path in input_paths:
            try:
                if not self._is_supported_format(input_path):
                    print(f"Skipping unsupported format: {input_path}")
                    results['failed'].append(input_path)
                    continue
                
                # Get video info
                info = self.get_video_info(input_path)
                
                # Generate output path
                input_name = Path(input_path).stem
                output_path = os.path.join(output_dir, f"{input_name}_compressed.{output_format}")
                
                # Get compression settings
                settings = self.get_compression_settings(
                    quality, codec, info, target_size_mb, compression_ratio
                )
                
                # Compress video
                success = self.compress_video_with_progress(
                    input_path, output_path, settings, preserve_metadata
                )
                
                if success:
                    results['success'].append((input_path, output_path))
                else:
                    results['failed'].append(input_path)
                    
            except Exception as e:
                print(f"Error processing {input_path}: {str(e)}")
                results['failed'].append(input_path)
        
        return results
    
    def _is_supported_format(self, filepath: str) -> bool:
        """Check if file format is supported."""
        return Path(filepath).suffix.lower() in self.SUPPORTED_FORMATS

def parse_size(size_str: str) -> float:
    """Parse size string like '100MB' to float in MB."""
    size_str = size_str.upper().replace(' ', '')
    
    if size_str.endswith('GB'):
        return float(size_str[:-2]) * 1024
    elif size_str.endswith('MB'):
        return float(size_str[:-2])
    elif size_str.endswith('KB'):
        return float(size_str[:-2]) / 1024
    else:
        # Assume MB if no unit
        return float(size_str)

def main():
    parser = argparse.ArgumentParser(
        description='Video Compression Utility - Compress videos with configurable quality settings',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s video.mp4 -q medium                    # Compress with medium quality
  %(prog)s video.mp4 -s 50MB -o small.mp4        # Compress to 50MB target size
  %(prog)s *.mp4 --batch -d output/               # Batch compress all MP4s
  %(prog)s video.mov -c h265 -q high              # Use H.265 codec with high quality
  %(prog)s video.avi -r 0.5                      # Compress to 50% of original size
        """
    )
    
    # Input arguments
    parser.add_argument('input', nargs='+', help='Input video file(s) or glob pattern')
    parser.add_argument('-o', '--output', help='Output file path (single file mode)')
    parser.add_argument('-d', '--output-dir', default='./compressed', 
                       help='Output directory (batch mode, default: ./compressed)')
    
    # Compression settings
    parser.add_argument('-q', '--quality', choices=['ultra', 'high', 'medium', 'low'],
                       default='medium', help='Quality preset (default: medium)')
    parser.add_argument('-c', '--codec', choices=['libx264', 'libx265'], 
                       default='libx264', help='Video codec (default: libx264)')
    parser.add_argument('-s', '--size', help='Target file size (e.g., 50MB, 1GB)')
    parser.add_argument('-r', '--ratio', type=float, 
                       help='Compression ratio (0.5 = 50% of original size)')
    parser.add_argument('-f', '--format', default='mp4',
                       help='Output format (default: mp4)')
    
    # Options
    parser.add_argument('--batch', action='store_true',
                       help='Enable batch processing mode')
    parser.add_argument('--no-metadata', action='store_true',
                       help='Do not preserve metadata')
    parser.add_argument('--verbose', action='store_true',
                       help='Verbose output')
    
    args = parser.parse_args()
    
    try:
        compressor = VideoCompressor()
        
        # Parse target size if provided
        target_size_mb = None
        if args.size:
            target_size_mb = parse_size(args.size)
        
        # Expand file patterns
        import glob
        input_files = []
        for pattern in args.input:
            matches = glob.glob(pattern)
            if matches:
                input_files.extend(matches)
            else:
                input_files.append(pattern)
        
        # Remove duplicates and filter existing files
        input_files = list(set([f for f in input_files if os.path.isfile(f)]))
        
        if not input_files:
            print("No valid input files found.")
            sys.exit(1)
        
        print(f"Found {len(input_files)} file(s) to process.")
        print(f"Codec: {args.codec}, Quality: {args.quality}")
        if target_size_mb:
            print(f"Target size: {target_size_mb}MB")
        if args.ratio:
            print(f"Compression ratio: {args.ratio}")
        print()
        
        # Process files
        if len(input_files) == 1 and args.output and not args.batch:
            # Single file mode
            input_file = input_files[0]
            info = compressor.get_video_info(input_file)
            settings = compressor.get_compression_settings(
                args.quality, args.codec, info, target_size_mb, args.ratio
            )
            
            success = compressor.compress_video_with_progress(
                input_file, args.output, settings, not args.no_metadata
            )
            
            sys.exit(0 if success else 1)
        else:
            # Batch mode
            results = compressor.process_files(
                input_files, args.output_dir, args.quality, args.codec,
                target_size_mb, args.ratio, args.format, not args.no_metadata
            )
            
            # Print summary
            print("=" * 50)
            print(f"Compression Summary:")
            print(f"Successfully processed: {len(results['success'])}")
            print(f"Failed: {len(results['failed'])}")
            
            if results['failed']:
                print("\nFailed files:")
                for failed in results['failed']:
                    print(f"  - {failed}")
            
            sys.exit(0 if not results['failed'] else 1)
            
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()