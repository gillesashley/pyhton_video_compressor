#!/usr/bin/env python3
"""
Video processing and compression functionality.

This module contains the core video processing logic, including
video analysis, FFmpeg command building, and compression operations.
"""

import os
import subprocess
import shutil
import logging
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import ffmpeg

from file_utils import FileUtils
from compression_settings import CompressionSettings
from progress_tracker import ProgressTracker

logger = logging.getLogger(__name__)


class VideoProcessingError(Exception):
    """Custom exception for video processing errors."""
    pass


class VideoProcessor:
    """Handles video analysis and compression operations."""
    
    def __init__(self):
        """Initialize video processor and check FFmpeg availability."""
        self.ffmpeg_path = self._check_ffmpeg()
        logger.info("VideoProcessor initialized successfully")
    
    def _check_ffmpeg(self) -> str:
        """
        Check if FFmpeg is installed and accessible.
        
        Returns:
            Path to FFmpeg executable
            
        Raises:
            VideoProcessingError: If FFmpeg is not found
        """
        ffmpeg_path = shutil.which('ffmpeg')
        if not ffmpeg_path:
            raise VideoProcessingError(
                "FFmpeg not found. Please install FFmpeg and add it to PATH."
            )
        logger.debug(f"FFmpeg found at: {ffmpeg_path}")
        return ffmpeg_path
    
    def get_video_info(self, filepath: str) -> Dict:
        """
        Get comprehensive video information using ffprobe.
        
        Args:
            filepath: Path to video file
            
        Returns:
            Dictionary containing video information
            
        Raises:
            VideoProcessingError: If video analysis fails
        """
        try:
            if not os.path.isfile(filepath):
                raise VideoProcessingError(f"File not found: {filepath}")
            
            if not FileUtils.is_supported_format(filepath):
                raise VideoProcessingError(f"Unsupported format: {filepath}")
            
            probe = ffmpeg.probe(filepath)
            video_stream = next(
                (stream for stream in probe['streams'] 
                 if stream['codec_type'] == 'video'), 
                None
            )
            
            if not video_stream:
                raise VideoProcessingError(f"No video stream found in {filepath}")
            
            # Get file size
            file_size = os.path.getsize(filepath)
            
            # Calculate FPS safely
            fps_str = video_stream.get('r_frame_rate', '25/1')
            try:
                fps = eval(fps_str) if '/' in fps_str else float(fps_str)
            except (ZeroDivisionError, ValueError):
                fps = 25.0  # Default fallback
            
            info = {
                'filepath': filepath,
                'duration': float(probe['format']['duration']),
                'size': file_size,
                'bitrate': int(probe['format']['bit_rate']),
                'width': int(video_stream['width']),
                'height': int(video_stream['height']),
                'codec': video_stream['codec_name'],
                'fps': fps,
                'format': probe['format']['format_name'],
                'total_frames': int(float(probe['format']['duration']) * fps)
            }
            
            logger.debug(f"Video info extracted for {filepath}: "
                        f"{info['width']}x{info['height']}, "
                        f"{info['duration']:.1f}s, "
                        f"{FileUtils.format_file_size(info['size'])}")
            
            return info
            
        except ffmpeg.Error as e:
            raise VideoProcessingError(f"FFprobe error for {filepath}: {e}") from e
        except Exception as e:
            raise VideoProcessingError(f"Could not analyze video {filepath}: {e}") from e
    
    def build_ffmpeg_command(self, input_path: str, output_path: str,
                           settings: Dict, preserve_metadata: bool = True) -> List[str]:
        """
        Build FFmpeg command with specified compression settings.
        
        Args:
            input_path: Path to input video file
            output_path: Path to output video file
            settings: Compression settings dictionary
            preserve_metadata: Whether to preserve metadata
            
        Returns:
            List of command arguments for FFmpeg
        """
        cmd = [
            self.ffmpeg_path, '-i', input_path,
            '-c:v', settings['codec'],
            '-preset', settings['preset'],
            '-y'  # Overwrite output file
        ]
        
        # Add CRF or bitrate settings
        if 'bitrate' in settings:
            cmd.extend(['-b:v', settings['bitrate']])
            # Add maxrate for better quality control
            cmd.extend(['-maxrate', settings['bitrate']])
            logger.debug(f"Using bitrate mode: {settings['bitrate']}")
        else:
            cmd.extend(['-crf', str(settings['crf'])])
            logger.debug(f"Using CRF mode: {settings['crf']}")
        
        # Add codec-specific parameters
        codec_params = CompressionSettings.get_codec_specific_params(settings['codec'])
        if 'extra_params' in codec_params:
            cmd.extend(codec_params['extra_params'])
        
        # Audio settings - use AAC with reasonable bitrate
        cmd.extend(['-c:a', 'aac', '-b:a', '128k'])
        
        # Preserve metadata if requested
        if preserve_metadata:
            cmd.extend(['-map_metadata', '0'])
        
        cmd.append(output_path)
        
        logger.debug(f"Built FFmpeg command: {' '.join(cmd)}")
        return cmd

    def compress_video(self, input_path: str, output_path: str,
                      settings: Dict, preserve_metadata: bool = True,
                      show_progress: bool = True) -> bool:
        """
        Compress video with optional progress tracking.

        Args:
            input_path: Path to input video file
            output_path: Path to output video file
            settings: Compression settings dictionary
            preserve_metadata: Whether to preserve metadata
            show_progress: Whether to show progress bar

        Returns:
            True if compression successful, False otherwise

        Raises:
            VideoProcessingError: If compression fails
        """
        try:
            # Get video info for progress calculation
            info = self.get_video_info(input_path)

            # Ensure output directory exists
            output_dir = os.path.dirname(output_path)
            if output_dir:
                FileUtils.ensure_directory_exists(output_dir)

            # Build FFmpeg command
            cmd = self.build_ffmpeg_command(input_path, output_path, settings, preserve_metadata)

            logger.info(f"Starting compression: {os.path.basename(input_path)}")
            logger.info(f"Settings: {settings['codec_name']}, "
                       f"Quality: {settings.get('quality_name', 'custom')}")

            # Run FFmpeg with optional progress tracking
            if show_progress:
                return self._run_ffmpeg_with_progress(cmd, info['total_frames'], input_path)
            else:
                return self._run_ffmpeg_silent(cmd, input_path)

        except Exception as e:
            logger.error(f"Compression failed for {input_path}: {e}")
            raise VideoProcessingError(f"Compression failed: {e}") from e

    def _run_ffmpeg_with_progress(self, cmd: List[str], total_frames: int,
                                 input_path: str) -> bool:
        """
        Run FFmpeg command with progress tracking.

        Args:
            cmd: FFmpeg command arguments
            total_frames: Total frames for progress calculation
            input_path: Input file path for logging

        Returns:
            True if successful, False otherwise
        """
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )

            with ProgressTracker(total_frames, f"Compressing {os.path.basename(input_path)}") as tracker:
                while True:
                    output = process.stderr.readline()
                    if output == '' and process.poll() is not None:
                        break

                    if output:
                        tracker.update_from_ffmpeg_output(output)

            return_code = process.poll()
            if return_code == 0:
                logger.info(f"Compression completed successfully: {input_path}")
                return True
            else:
                error_output = process.stderr.read()
                logger.error(f"FFmpeg failed with code {return_code}: {error_output}")
                return False

        except Exception as e:
            logger.error(f"Error running FFmpeg: {e}")
            return False

    def _run_ffmpeg_silent(self, cmd: List[str], input_path: str) -> bool:
        """
        Run FFmpeg command without progress tracking.

        Args:
            cmd: FFmpeg command arguments
            input_path: Input file path for logging

        Returns:
            True if successful, False otherwise
        """
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )

            if result.returncode == 0:
                logger.info(f"Compression completed successfully: {input_path}")
                return True
            else:
                logger.error(f"FFmpeg failed: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Error running FFmpeg: {e}")
            return False

    def show_compression_results(self, input_path: str, output_path: str) -> None:
        """
        Display compression statistics.

        Args:
            input_path: Path to original file
            output_path: Path to compressed file
        """
        try:
            if not os.path.exists(output_path):
                logger.warning(f"Output file not found: {output_path}")
                return

            original_size = os.path.getsize(input_path)
            compressed_size = os.path.getsize(output_path)
            compression_ratio = FileUtils.calculate_compression_ratio(original_size, compressed_size)

            print(f"✓ Compression complete!")
            print(f"  Original: {FileUtils.format_file_size(original_size)}")
            print(f"  Compressed: {FileUtils.format_file_size(compressed_size)}")
            print(f"  Space saved: {compression_ratio:.1f}%")
            print()

            logger.info(f"Compression results - Original: {original_size} bytes, "
                       f"Compressed: {compressed_size} bytes, "
                       f"Ratio: {compression_ratio:.1f}%")

        except Exception as e:
            logger.warning(f"Could not display compression results: {e}")
            print("✓ Compression complete!")

    def process_batch(self, input_files: List[str], output_dir: str,
                     quality: str, codec: str,
                     target_size_mb: Optional[float] = None,
                     compression_ratio: Optional[float] = None,
                     output_format: str = 'mp4',
                     preserve_metadata: bool = True) -> Dict:
        """
        Process multiple video files in batch.

        Args:
            input_files: List of input file paths
            output_dir: Output directory
            quality: Quality preset name
            codec: Video codec name
            target_size_mb: Optional target file size in MB
            compression_ratio: Optional compression ratio
            output_format: Output file format
            preserve_metadata: Whether to preserve metadata

        Returns:
            Dictionary with 'success' and 'failed' lists
        """
        results = {'success': [], 'failed': []}

        # Ensure output directory exists
        FileUtils.ensure_directory_exists(output_dir)

        logger.info(f"Starting batch processing of {len(input_files)} files")

        for i, input_path in enumerate(input_files, 1):
            try:
                print(f"\n[{i}/{len(input_files)}] Processing: {os.path.basename(input_path)}")

                if not FileUtils.is_supported_format(input_path):
                    print(f"Skipping unsupported format: {input_path}")
                    results['failed'].append(input_path)
                    continue

                # Get video info
                info = self.get_video_info(input_path)

                # Generate output path
                output_path = FileUtils.generate_output_path(
                    input_path, output_dir, "_compressed", output_format
                )

                # Get compression settings
                settings = CompressionSettings.get_compression_settings(
                    quality, codec, info, target_size_mb, compression_ratio
                )

                # Compress video
                success = self.compress_video(
                    input_path, output_path, settings, preserve_metadata
                )

                if success:
                    self.show_compression_results(input_path, output_path)
                    results['success'].append((input_path, output_path))
                else:
                    results['failed'].append(input_path)

            except Exception as e:
                logger.error(f"Error processing {input_path}: {e}")
                print(f"Error processing {input_path}: {e}")
                results['failed'].append(input_path)

        logger.info(f"Batch processing complete. Success: {len(results['success'])}, "
                   f"Failed: {len(results['failed'])}")

        return results
