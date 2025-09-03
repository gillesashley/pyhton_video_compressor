#!/usr/bin/env python3
"""
Video Compression Utility
A powerful video compression tool using FFmpeg with configurable quality settings.

This is the main entry point that orchestrates the video compression workflow
using a modular architecture for better maintainability and testability.

Requirements:
- FFmpeg installed and accessible in PATH
- Python packages: ffmpeg-python, tqdm

Install dependencies:
pip install -r requirements.txt

Usage examples:
python main.py input.mp4 -q medium -o compressed.mp4
python main.py *.mp4 -q high --batch -d output/
python main.py input.mov -s 50MB -c h265
"""

import sys
import os
import logging
from typing import Optional

from cli import VideoCompressionCLI, CLIError
from video_processor import VideoProcessor, VideoProcessingError
from compression_settings import CompressionSettings
from file_utils import FileUtils

logger = logging.getLogger(__name__)


def process_single_file(processor: VideoProcessor, input_file: str,
                       output_file: str, quality: str, codec: str,
                       target_size_mb: Optional[float] = None,
                       compression_ratio: Optional[float] = None,
                       preserve_metadata: bool = True) -> bool:
    """
    Process a single video file.

    Args:
        processor: VideoProcessor instance
        input_file: Path to input file
        output_file: Path to output file
        quality: Quality preset name
        codec: Video codec name
        target_size_mb: Optional target file size in MB
        compression_ratio: Optional compression ratio
        preserve_metadata: Whether to preserve metadata

    Returns:
        True if successful, False otherwise
    """
    try:
        # Get video info
        info = processor.get_video_info(input_file)

        # Get compression settings
        settings = CompressionSettings.get_compression_settings(
            quality, codec, info, target_size_mb, compression_ratio
        )

        # Compress video
        success = processor.compress_video(
            input_file, output_file, settings, preserve_metadata
        )

        if success:
            processor.show_compression_results(input_file, output_file)

        return success

    except VideoProcessingError as e:
        logger.error(f"Video processing error: {e}")
        print(f"Error: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error processing {input_file}: {e}")
        print(f"Unexpected error: {e}")
        return False


def process_batch_files(processor: VideoProcessor, input_files: list,
                       output_dir: str, quality: str, codec: str,
                       target_size_mb: Optional[float] = None,
                       compression_ratio: Optional[float] = None,
                       output_format: str = 'mp4',
                       preserve_metadata: bool = True) -> dict:
    """
    Process multiple video files in batch mode.

    Args:
        processor: VideoProcessor instance
        input_files: List of input file paths
        output_dir: Output directory
        quality: Quality preset name
        codec: Video codec name
        target_size_mb: Optional target file size in MB
        compression_ratio: Optional compression ratio
        output_format: Output file format
        preserve_metadata: Whether to preserve metadata

    Returns:
        Dictionary with processing results
    """
    return processor.process_batch(
        input_files, output_dir, quality, codec,
        target_size_mb, compression_ratio, output_format, preserve_metadata
    )


def process_default_videos(processor: VideoProcessor, input_files: list,
                          videos_folder: str = './videos') -> dict:
    """
    Process video files in default mode - compress videos in ./videos/ folder
    with default settings and save in the same folder with _compressed suffix.

    Args:
        processor: VideoProcessor instance
        input_files: List of input file paths from videos folder
        videos_folder: Path to videos folder

    Returns:
        Dictionary with processing results
    """
    results = {'success': [], 'failed': []}

    print(f"🎬 Default mode: Processing {len(input_files)} video(s) from {videos_folder}")
    print("📋 Using default settings: medium quality, libx264 codec")
    print("💾 Compressed videos will be saved in the same folder with '_compressed' suffix")
    print()

    for i, input_path in enumerate(input_files, 1):
        try:
            print(f"[{i}/{len(input_files)}] Processing: {os.path.basename(input_path)}")

            # Get video info
            info = processor.get_video_info(input_path)

            # Generate output path in the same folder with _compressed suffix
            input_dir = os.path.dirname(input_path)
            input_name = os.path.splitext(os.path.basename(input_path))[0]
            input_ext = os.path.splitext(input_path)[1]
            output_path = os.path.join(input_dir, f"{input_name}_compressed{input_ext}")

            # Use default settings: medium quality, libx264 codec
            settings = CompressionSettings.get_compression_settings(
                'medium', 'libx264', info
            )

            # Compress video
            success = processor.compress_video(
                input_path, output_path, settings, preserve_metadata=True
            )

            if success:
                processor.show_compression_results(input_path, output_path)
                results['success'].append((input_path, output_path))
            else:
                results['failed'].append(input_path)

        except Exception as e:
            logger.error(f"Error processing {input_path}: {e}")
            print(f"Error processing {input_path}: {e}")
            results['failed'].append(input_path)

    return results


def print_batch_summary(results: dict) -> None:
    """
    Print batch processing summary.

    Args:
        results: Processing results dictionary
    """
    print("=" * 50)
    print("Compression Summary:")
    print(f"Successfully processed: {len(results['success'])}")
    print(f"Failed: {len(results['failed'])}")

    if results['failed']:
        print("\nFailed files:")
        for failed in results['failed']:
            print(f"  - {failed}")

def main():
    """Main entry point for the video compression utility."""
    try:
        # Initialize CLI handler
        cli = VideoCompressionCLI()

        # Parse command line arguments
        args = cli.parse_arguments()

        # Setup logging based on verbosity
        cli.setup_logging(args.verbose, args.quiet)

        # Initialize video processor
        processor = VideoProcessor()

        # Expand input file patterns
        input_files = cli.expand_input_files(args.input)

        # Print processing information
        cli.print_processing_info(args, input_files)

        # Parse target size if provided
        target_size_mb = None
        if args.size:
            target_size_mb = FileUtils.parse_size_string(args.size)

        # Determine processing mode
        mode, output_path = cli.determine_processing_mode(args, input_files)

        if mode == 'single':
            # Single file processing
            logger.info(f"Processing single file: {input_files[0]} -> {output_path}")
            success = process_single_file(
                processor, input_files[0], output_path,
                args.quality, args.codec, target_size_mb, args.ratio,
                not args.no_metadata
            )
            sys.exit(0 if success else 1)

        elif mode == 'default':
            # Default processing mode - compress videos in ./videos/ folder
            logger.info(f"Default mode: Processing {len(input_files)} files from ./videos/ folder")
            results = process_default_videos(processor, input_files, output_path)

            # Print summary
            if not args.quiet:
                print_batch_summary(results)

            # Exit with appropriate code
            sys.exit(0 if not results['failed'] else 1)

        else:
            # Batch processing
            logger.info(f"Processing {len(input_files)} files in batch mode")
            results = process_batch_files(
                processor, input_files, output_path,
                args.quality, args.codec, target_size_mb, args.ratio,
                args.format, not args.no_metadata
            )

            # Print summary
            if not args.quiet:
                print_batch_summary(results)

            # Exit with appropriate code
            sys.exit(0 if not results['failed'] else 1)

    except CLIError as e:
        logger.error(f"CLI error: {e}")
        print(f"Error: {e}")
        sys.exit(1)

    except VideoProcessingError as e:
        logger.error(f"Video processing error: {e}")
        print(f"Error: {e}")
        sys.exit(1)

    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        print("\nOperation cancelled by user.")
        sys.exit(1)

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()